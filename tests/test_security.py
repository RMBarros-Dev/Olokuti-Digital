from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.sessions.models import Session
from django.core import mail
from django.db import DatabaseError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.services import ensure_default_role_groups, invalidate_user_sessions
from apps.audit.models import AuditLog
from apps.audit.services import record_event
from apps.catalog.models import Product


@pytest.mark.django_db
def test_non_staff_authenticated_user_receives_403_on_admin_endpoints(client, django_user_model):
    ensure_default_role_groups()
    manager = django_user_model.objects.create_user(
        username="manager", password="safe-test-password", is_staff=False
    )
    manager.groups.add(Group.objects.get(name="Auditors & Managers"))
    other = django_user_model.objects.create_user(username="other", password="safe-test-password")
    client.force_login(manager)

    for url in (
        reverse("accounts:user-list"),
        reverse("accounts:user-create"),
        reverse("accounts:user-update", args=[other.pk]),
    ):
        assert client.get(url).status_code == 403

    assert client.post(reverse("accounts:setup-groups")).status_code == 403
    assert client.post(reverse("accounts:user-create"), {"username": "x"}).status_code == 403


@pytest.mark.django_db
def test_non_superuser_staff_cannot_manage_superuser_or_assign_audit_group(
    client, django_user_model
):
    ensure_default_role_groups()
    staff = django_user_model.objects.create_user(
        username="staff-op", password="safe-test-password", is_staff=True, is_superuser=False
    )
    superuser = django_user_model.objects.create_superuser(
        username="root-admin", email="root@example.com", password="safe-test-password"
    )
    member = django_user_model.objects.create_user(username="member", password="safe-test-password")
    audit_group = Group.objects.get(name="Auditors & Managers")

    client.force_login(staff)
    assert client.get(reverse("accounts:user-update", args=[superuser.pk])).status_code == 403
    assert (
        client.post(
            reverse("accounts:user-update", args=[superuser.pk]),
            {"username": "root-admin", "is_active": "on"},
        ).status_code
        == 403
    )

    resp = client.post(
        reverse("accounts:user-update", args=[member.pk]),
        {
            "username": "member",
            "is_active": "on",
            "groups": [str(audit_group.pk)],
        },
    )
    assert resp.status_code == 200
    assert not member.groups.filter(pk=audit_group.pk).exists()

    self_deactivate = client.post(
        reverse("accounts:user-update", args=[staff.pk]),
        {"username": "staff-op"},
    )
    assert self_deactivate.status_code == 200
    staff.refresh_from_db()
    assert staff.is_active is True
    assert staff.is_staff is True


@pytest.mark.django_db
def test_public_registration_ignores_injected_privilege_fields(client, django_user_model):
    response = client.post(
        reverse("accounts:register"),
        {
            "username": "tamper-user",
            "email": "tamper@olokuti.local",
            "password1": "Strong-Unique-Password-2026!",
            "password2": "Strong-Unique-Password-2026!",
            "is_staff": "on",
            "is_superuser": "on",
            "is_active": "off",
        },
    )
    assert response.status_code == 302
    created = django_user_model.objects.get(username="tamper-user")
    assert created.is_active is True
    assert created.is_staff is False
    assert created.is_superuser is False
    assert created.groups.count() == 0


@pytest.mark.django_db
def test_deactivating_user_or_resetting_password_invalidates_only_target_sessions(
    client, django_user_model
):
    admin = django_user_model.objects.create_superuser(
        username="root", email="root@example.com", password="safe-test-password"
    )
    target = django_user_model.objects.create_user(
        username="target", password="Target-Password-2026!"
    )
    django_user_model.objects.create_user(username="bystander", password="Bystander-Password-2026!")

    target_client = client
    assert target_client.login(username="target", password="Target-Password-2026!")

    bystander_client = type(client)()
    assert bystander_client.login(username="bystander", password="Bystander-Password-2026!")

    admin_client = type(client)()
    admin_client.force_login(admin)

    assert target_client.get(reverse("accounts:dashboard")).status_code == 200
    assert bystander_client.get(reverse("accounts:dashboard")).status_code == 200

    # Deactivate target via admin view
    update_resp = admin_client.post(
        reverse("accounts:user-update", args=[target.pk]),
        {"username": "target", "email": "", "first_name": "", "last_name": ""},
    )
    assert update_resp.status_code == 302
    target.refresh_from_db()
    assert target.is_active is False

    # Target's existing session is immediately invalid
    assert target_client.get(reverse("accounts:dashboard")).status_code == 302
    # Inactive user cannot sign back in
    assert target_client.login(username="target", password="Target-Password-2026!") is False
    # Bystander session remains unaffected
    assert bystander_client.get(reverse("accounts:dashboard")).status_code == 200


@pytest.mark.django_db
def test_deactivated_user_is_rejected_and_active_user_middleware_handles_inactive_user(
    client, django_user_model
):
    from django.contrib.sessions.backends.db import SessionStore
    from django.http import HttpResponse
    from django.test import RequestFactory

    from config.middleware import ActiveUserRequiredMiddleware

    member = django_user_model.objects.create_user(
        username="deactivated-mid", password="safe-test-password"
    )
    client.force_login(member)
    assert client.get(reverse("accounts:dashboard")).status_code == 200

    member.is_active = False
    member.save(update_fields=["is_active"])

    resp = client.get(reverse("accounts:dashboard"))
    assert resp.status_code == 302
    assert "/accounts/login/" in resp.url

    # Direct defense-in-depth middleware test (for backends not filtering is_active in get_user)
    mw = ActiveUserRequiredMiddleware(lambda req: HttpResponse("ok"))
    rf = RequestFactory()
    for is_htmx, expected_code in ((False, 302), (True, 403)):
        req = rf.get("/", HTTP_HX_REQUEST="true" if is_htmx else "")
        req.session = SessionStore()
        req.user = member
        mw_resp = mw(req)
        assert mw_resp.status_code == expected_code


@pytest.mark.django_db
def test_invalidate_user_sessions_clears_matching_db_session(client, django_user_model):
    user_a = django_user_model.objects.create_user(username="ua", password="safe-test-password")
    client.force_login(user_a)
    assert Session.objects.count() >= 1
    assert invalidate_user_sessions(user_a) >= 1
    assert client.get(reverse("accounts:dashboard")).status_code == 302


@pytest.mark.django_db
def test_password_reset_flow_single_use_and_audit_without_token_leak(client, django_user_model):
    account = django_user_model.objects.create_user(
        username="resetme", email="reset@olokuti.local", password="Old-Password-2026!"
    )

    reset_req = client.post(
        reverse("accounts:password_reset"),
        {"email": "reset@olokuti.local"},
        follow=True,
    )
    assert reset_req.status_code == 200
    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    assert "/reset/" in body

    req_event = AuditLog.objects.filter(action="password_reset_requested").first()
    assert req_event is not None
    assert "reset@olokuti.local" not in str(req_event.details)

    # Same neutral page shown for nonexistent email (anti-enumeration)
    anon_req = client.post(
        reverse("accounts:password_reset"),
        {"email": "nonexistent@olokuti.local"},
        follow=True,
    )
    assert anon_req.status_code == 200
    assert len(mail.outbox) == 1

    reset_url_line = next(line for line in body.splitlines() if "/reset/" in line)
    reset_path = "/" + reset_url_line.split("://", 1)[1].split("/", 1)[1]

    # Follow initial GET to the session-backed set-password URL
    get_reset = client.get(reset_path, follow=True)
    assert get_reset.status_code == 200
    set_password_url = get_reset.redirect_chain[-1][0]

    confirm_resp = client.post(
        set_password_url,
        {
            "new_password1": "BrandNew-Password-2026!",
            "new_password2": "BrandNew-Password-2026!",
        },
        follow=True,
    )
    assert confirm_resp.status_code == 200
    account.refresh_from_db()
    assert account.check_password("BrandNew-Password-2026!")
    assert AuditLog.objects.filter(action="password_reset_completed", user=account).exists()

    # Second use of the exact same reset link must fail (single-use token)
    reuse_resp = client.get(reset_path)
    assert reuse_resp.status_code == 200
    assert "no longer valid" in reuse_resp.content.decode()

    # Expired token test (PASSWORD_RESET_TIMEOUT = 0 after token generation)
    mail.outbox.clear()
    client.post(reverse("accounts:password_reset"), {"email": "reset@olokuti.local"})
    new_body = mail.outbox[0].body
    new_reset_line = next(line for line in new_body.splitlines() if "/reset/" in line)
    new_reset_path = "/" + new_reset_line.split("://", 1)[1].split("/", 1)[1]
    with override_settings(PASSWORD_RESET_TIMEOUT=-1):
        expired_resp = client.get(new_reset_path)
        assert expired_resp.status_code == 200
        assert "no longer valid" in expired_resp.content.decode()


@pytest.mark.django_db
@override_settings(RATE_LIMIT_LOGIN_MAX=2, RATE_LIMIT_LOGIN_WINDOW=120)
def test_login_success_and_rate_limiting_plus_audit_logging(client, django_user_model):
    from django.core.cache import cache

    django_user_model.objects.create_user(username="real-login", password="Valid-Password-2026!")
    login_url = reverse("accounts:login")

    success = client.post(
        login_url,
        {"username": "real-login", "password": "Valid-Password-2026!"},
    )
    assert success.status_code == 302
    assert success.url == reverse("accounts:dashboard")
    assert AuditLog.objects.filter(action="login_succeeded").exists()
    client.logout()
    cache.clear()

    for _ in range(2):
        resp = client.post(login_url, {"username": "tester", "password": "wrong"})
        assert resp.status_code == 200

    blocked = client.post(login_url, {"username": "tester", "password": "wrong"})
    assert blocked.status_code == 429
    assert blocked["Retry-After"] == "120"

    # Repeat attempt stays blocked without flooding audit table
    blocked_again = client.post(login_url, {"username": "tester", "password": "wrong"})
    assert blocked_again.status_code == 429
    assert AuditLog.objects.filter(action="rate_limited", entity_id="login").count() == 1
    assert AuditLog.objects.filter(action="login_failed").count() == 2


@pytest.mark.django_db
@override_settings(
    RATE_LIMIT_REGISTER_MAX=1,
    RATE_LIMIT_REGISTER_WINDOW=60,
    RATE_LIMIT_PASSWORD_RESET_MAX=1,
    RATE_LIMIT_PASSWORD_RESET_WINDOW=60,
    RATE_LIMIT_HEALTH_DB_MAX=1,
    RATE_LIMIT_HEALTH_DB_WINDOW=60,
)
def test_register_reset_and_health_rate_limits_plus_trusted_proxy_ip(client):
    reg_url = reverse("accounts:register")
    assert client.post(reg_url, {"username": "invalid"}).status_code == 200
    assert client.post(reg_url, {"username": "invalid"}).status_code == 429

    pr_url = reverse("accounts:password_reset")
    assert client.post(pr_url, {"email": "a@example.com"}).status_code == 302
    assert client.post(pr_url, {"email": "a@example.com"}).status_code == 429

    # Untrusted X-Forwarded-For spoofing does NOT bypass health?db=1 limit
    assert client.get("/health?db=1", HTTP_X_FORWARDED_FOR="1.1.1.1").status_code == 200
    assert client.get("/health?db=1", HTTP_X_FORWARDED_FOR="2.2.2.2").status_code == 429
    # Plain health probe stays up
    assert client.get("/health").status_code == 200

    # When TRUST_X_FORWARDED_FOR=True, rightmost trusted proxy hop isolates clients
    with override_settings(TRUST_X_FORWARDED_FOR=True, TRUSTED_PROXY_HOPS=1):
        resp_new_client = client.get("/health?db=1", HTTP_X_FORWARDED_FOR="9.9.9.9, 198.51.100.42")
        assert resp_new_client.status_code == 200
        # Spoofing left-most hop while keeping rightmost real proxy IP 198.51.100.42 still hits limit
        resp_spoofed = client.get("/health?db=1", HTTP_X_FORWARDED_FOR="8.8.8.8, 198.51.100.42")
        assert resp_spoofed.status_code == 429


@pytest.mark.django_db
def test_health_db_returns_503_safely_on_database_error(client):
    with patch("config.urls.connection.cursor", side_effect=DatabaseError("db down")):
        resp = client.get("/health?db=1")
    assert resp.status_code == 503
    assert resp.content == b"unavailable"


@pytest.mark.django_db
def test_http_security_headers_csp_and_audit_redaction(client, user):
    resp = client.get(reverse("accounts:login"))
    assert resp.status_code == 200
    assert resp["X-Frame-Options"] == "DENY"
    assert resp["X-Content-Type-Options"] == "nosniff"
    assert resp["Referrer-Policy"] == "same-origin"
    assert resp["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
    csp = resp["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in csp
    assert "object-src 'none'" in csp
    assert "'nonce-" in csp
    assert "script-src 'self' 'nonce-" in csp

    event = record_event(
        user=user,
        action="updated",
        entity="auth.User",
        entity_id=user.pk,
        details={
            "changed_fields": ["email"],
            "password": "plain-secret-value",
            "nested": {"reset_token": "tok-123", "safe_note": "kept"},
            "expires_at": timezone.now() + timedelta(hours=1),
        },
    )
    event.refresh_from_db()
    assert event.details["password"] == "***REDACTED***"
    assert event.details["nested"]["reset_token"] == "***REDACTED***"
    assert event.details["nested"]["safe_note"] == "kept"
    assert event.details["changed_fields"] == ["email"]


@pytest.mark.django_db
def test_product_create_is_atomic_with_audit_log_failure(client, user):
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["add_product", "view_product"])
    )
    client.force_login(user)

    with patch("apps.catalog.views.record_event", side_effect=RuntimeError("audit boom")):
        with pytest.raises(RuntimeError, match="audit boom"):
            client.post(
                reverse("catalog:product-create"),
                {"name": "Rollback Product", "description": "desc"},
            )

    assert not Product.objects.filter(name="Rollback Product").exists()
