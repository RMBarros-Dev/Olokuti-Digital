from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.catalog.models import Product
from apps.operations.models import OperationalTask


@pytest.mark.django_db
def test_dashboard_uses_database_counts_and_hides_activity_without_permission(client, user):
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["view_product", "view_operationaltask"])
    )
    Product.objects.create(name="Recorded product")
    OperationalTask.objects.create(title="Open task", status="todo")
    AuditLog.objects.create(user=user, action="created", entity="catalog.Product", entity_id="demo")
    client.force_login(user)

    response = client.get(reverse("accounts:dashboard"))

    assert response.status_code == 200
    assert response.context["product_count"] == 1
    assert response.context["pending_count"] == 1
    assert response.context["recent_activity"] == []


@pytest.mark.django_db
def test_catalog_htmx_search_returns_only_the_table_fragment(client, user):
    user.user_permissions.add(*Permission.objects.filter(codename="view_product"))
    Product.objects.create(name="Searchable example")
    client.force_login(user)

    response = client.get(
        reverse("catalog:product-list"), {"q": "Searchable"}, HTTP_HX_REQUEST="true"
    )

    assert response.status_code == 200
    assert b"Searchable example" in response.content
    assert b"<html" not in response.content


@pytest.mark.django_db
def test_report_summary_renders_database_aggregates(client, user):
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["view_product", "view_operationaltask"])
    )
    Product.objects.create(name="Recorded product")
    OperationalTask.objects.create(title="Recorded task", status="done")
    client.force_login(user)

    response = client.get(reverse("reports:summary"))

    assert response.status_code == 200
    assert response.context["product_count"] == 1
    assert response.context["task_total"] == 1
    assert "Task summary" in response.content.decode()


@pytest.mark.django_db
def test_high_contrast_accessibility_control_renders_on_public_and_authenticated_pages(
    client, user
):
    """Ensure the accessible High Contrast toggle, ARIA attributes, and FOUC script render across pages."""
    for public_url in (reverse("accounts:login"), reverse("accounts:register")):
        response = client.get(public_url)
        html = response.content.decode()
        assert response.status_code == 200
        assert 'id="high-contrast-toggle-anon"' in html
        assert "data-contrast-toggle" in html
        assert 'type="button"' in html
        assert 'aria-pressed="false"' in html
        assert "aria-label=" in html
        assert "data-contrast-state" in html
        assert 'id="a11y-contrast-status"' in html
        assert 'aria-live="polite"' in html
        assert "olokuti_high_contrast" in html

    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["view_product", "view_operationaltask"])
    )
    client.force_login(user)

    for auth_url in (
        reverse("accounts:dashboard"),
        reverse("catalog:product-list"),
        reverse("operations:task-list"),
        reverse("reports:summary"),
    ):
        response = client.get(auth_url)
        html = response.content.decode()
        assert response.status_code == 200
        assert 'id="high-contrast-toggle"' in html
        assert 'aria-pressed="false"' in html
        assert 'id="a11y-contrast-status"' in html


def test_high_contrast_static_js_and_css_contracts():
    """Verify the High Contrast toggle, persistence, and WCAG CSS rules exist in static assets."""
    base_dir = Path(settings.BASE_DIR)
    js_content = (base_dir / "static" / "js" / "app.js").read_text(encoding="utf-8")
    css_content = (base_dir / "static" / "css" / "app.css").read_text(encoding="utf-8")

    # JavaScript activation, deactivation, and localStorage persistence contract
    assert 'CONTRAST_STORAGE_KEY = "olokuti_high_contrast"' in js_content
    assert 'setAttribute("data-contrast", "high")' in js_content
    assert 'removeAttribute("data-contrast")' in js_content
    assert 'setAttribute("aria-pressed", enabled ? "true" : "false")' in js_content
    assert 'localStorage.setItem(CONTRAST_STORAGE_KEY, enabled ? "true" : "false")' in js_content
    assert "✓ ON" in js_content
    assert "OFF" in js_content

    # CSS high-contrast palette, focus visibility, and prefers-reduced-motion contract
    assert ':root[data-contrast="high"]' in css_content
    assert ":focus-visible" in css_content
    assert "@media (prefers-reduced-motion: reduce)" in css_content
