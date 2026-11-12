import pytest
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
