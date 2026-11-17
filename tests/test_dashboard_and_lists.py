import re
from io import StringIO

import pytest
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.catalog.models import Category, Product, ProductTranslation
from apps.inventory.models import StockLocation, StockMovement
from apps.inventory.services import record_stock_movement
from apps.operations.models import OperationalTask
from tests.conftest import grant_permissions


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
def test_high_contrast_controls_csp_nonce_and_landmark_render(client, user):
    anon_resp = client.get(reverse("accounts:login"))
    assert anon_resp.status_code == 200
    anon_html = anon_resp.content.decode("utf-8")
    assert 'id="high-contrast-toggle-anon"' in anon_html
    assert "data-contrast-toggle" in anon_html
    assert 'aria-pressed="false"' in anon_html
    assert 'id="a11y-contrast-status"' in anon_html
    assert anon_html.count("<main ") == 1
    assert 'id="main-content"' in anon_html

    # Verify the inline anti-FOUC script carries the response CSP nonce
    csp_header = anon_resp["Content-Security-Policy"]
    nonce_match = re.search(r"'nonce-([^']+)'", csp_header)
    assert nonce_match is not None
    assert f'<script nonce="{nonce_match.group(1)}">' in anon_html

    client.force_login(user)
    auth_resp = client.get(reverse("accounts:dashboard"))
    assert auth_resp.status_code == 200
    auth_html = auth_resp.content.decode("utf-8")
    assert 'id="high-contrast-toggle"' in auth_html
    assert 'id="high-contrast-toggle-anon"' not in auth_html
    assert auth_html.count("<main ") == 1


@pytest.mark.django_db
def test_localized_navigation_and_compile_locales_command(client, user, tmp_path):
    grant_permissions(user, "view_product", "view_stockitem")
    client.force_login(user)

    pt_resp = client.get("/pt-br/")
    assert pt_resp.status_code == 200
    pt_html = pt_resp.content.decode("utf-8")
    assert "Alto contraste" in pt_html
    assert "Estoque" in pt_html

    in_resp = client.get("/en-in/")
    assert in_resp.status_code == 200
    assert "High contrast" in in_resp.content.decode("utf-8")

    # Test compile_locales pure-Python compilation directly on temporary .po
    from apps.catalog.management.commands.compile_locales import compile_po_to_mo

    po = tmp_path / "django.po"
    mo = tmp_path / "django.mo"
    po.write_text(
        'msgid ""\n'
        'msgstr "Content-Type: text/plain; charset=UTF-8\\n"\n\n'
        "#, fuzzy\n"
        'msgid "Skip"\n'
        'msgstr "Ignored"\n\n'
        'msgid "Plural"\n'
        'msgid_plural "Plurals"\n'
        'msgstr[0] "One"\n'
        'msgstr[1] "Many"\n\n'
        'msgid "High contrast"\n'
        'msgstr "Alto contraste"\n',
        encoding="utf-8",
    )
    compile_po_to_mo(po, mo)
    assert mo.exists() and mo.stat().st_size > 0

    out = StringIO()
    call_command("compile_locales", stdout=out)
    assert out.getvalue() != ""


@pytest.mark.django_db
def test_list_and_summary_views_avoid_n_plus_1_queries(client, user, django_assert_max_num_queries):
    grant_permissions(
        user,
        "view_product",
        "view_stockitem",
        "view_operationaltask",
        "view_auditlog",
    )
    cat = Category.objects.create(name="Home")
    loc = StockLocation.objects.create(name="Depot", code="DEP")
    for idx in range(10):
        prod = Product.objects.create(name=f"Prod {idx}", sku=f"SKU-{idx}", category=cat)
        ProductTranslation.objects.create(product=prod, locale="en", name=f"EN Prod {idx}")
        record_stock_movement(
            product=prod,
            location=loc,
            movement_type=StockMovement.MovementType.INBOUND,
            quantity=10 + idx,
            minimum_stock=20,
            reason="Seed",
            user=user,
        )
        OperationalTask.objects.create(title=f"Task {idx}", product=prod, assigned_to=user)

    client.force_login(user)

    with django_assert_max_num_queries(9):
        assert client.get(reverse("catalog:product-list")).status_code == 200
    with django_assert_max_num_queries(9):
        assert client.get(reverse("inventory:stock-list")).status_code == 200
    with django_assert_max_num_queries(14):
        assert client.get(reverse("reports:summary")).status_code == 200
    with django_assert_max_num_queries(14):
        assert client.get(reverse("accounts:dashboard")).status_code == 200
