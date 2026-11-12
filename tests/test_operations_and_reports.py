import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.catalog.models import Product
from apps.operations.models import OperationalTask


@pytest.mark.django_db
def test_task_status_change_is_audited(client, user):
    user.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["add_operationaltask", "change_operationaltask", "view_operationaltask"]
        )
    )
    client.force_login(user)
    response = client.post(
        reverse("operations:task-create"),
        {
            "title": "Review sample record",
            "description": "",
            "product": "",
            "status": "todo",
            "priority": "normal",
            "assigned_to": "",
            "due_date": "",
        },
    )
    assert response.status_code == 302
    task = OperationalTask.objects.get(title="Review sample record")
    response = client.post(
        reverse("operations:task-update", args=[task.pk]),
        {
            "title": task.title,
            "description": "",
            "product": "",
            "status": "in_progress",
            "priority": "normal",
            "assigned_to": "",
            "due_date": "",
        },
    )
    assert response.status_code == 302
    assert AuditLog.objects.filter(
        entity="operations.OperationalTask", entity_id=str(task.pk), action="status_changed"
    ).exists()


@pytest.mark.django_db
def test_csv_export_safeguards_spreadsheet_formulas(client, user):
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["view_product", "view_operationaltask"])
    )
    Product.objects.create(name="Example")
    OperationalTask.objects.create(title="=1+1")
    client.force_login(user)
    response = client.get(reverse("reports:tasks-csv"))
    assert response.status_code == 200
    assert "'=1+1" in response.content.decode("utf-8-sig")


@pytest.mark.django_db
def test_task_quick_status_and_htmx_filter(client, user):
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["change_operationaltask", "view_operationaltask"])
    )
    task = OperationalTask.objects.create(title="Verify supplier certificate", status="todo")
    client.force_login(user)

    status_resp = client.post(
        reverse("operations:task-status", args=[task.pk]),
        {"status": "done"},
    )
    assert status_resp.status_code == 302
    task.refresh_from_db()
    assert task.status == "done"
    assert AuditLog.objects.filter(
        entity="operations.OperationalTask", entity_id=str(task.pk), action="status_changed"
    ).exists()

    htmx_resp = client.get(
        reverse("operations:task-list"),
        {"q": "supplier"},
        HTTP_HX_REQUEST="true",
    )
    assert htmx_resp.status_code == 200
    assert b"Verify supplier certificate" in htmx_resp.content
    assert b"<html" not in htmx_resp.content

