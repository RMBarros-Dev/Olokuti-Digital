from datetime import timedelta

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.catalog.models import Product
from apps.inventory.models import StockLocation, StockMovement
from apps.inventory.services import record_stock_movement
from apps.operations.models import OperationalTask, TaskComment
from config.pdf import build_pdf_document
from tests.conftest import grant_permissions


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


@pytest.mark.django_db
def test_task_detail_comments_categories_and_permissions(client, user):
    task = OperationalTask.objects.create(
        title="Audit warehouse rack",
        category=OperationalTask.Category.INVENTORY,
        assigned_to=user,
    )
    grant_permissions(user, "view_operationaltask")
    client.force_login(user)

    # Filtering by category works via HTMX
    cat_resp = client.get(
        reverse("operations:task-list"),
        {"category": OperationalTask.Category.INVENTORY},
        HTTP_HX_REQUEST="true",
    )
    assert cat_resp.status_code == 200
    assert b"Audit warehouse rack" in cat_resp.content

    # Commenting requires add_taskcomment or change_operationaltask
    detail = client.get(reverse("operations:task-detail", args=[task.pk]))
    assert detail.status_code == 200
    denied = client.post(reverse("operations:task-comment", args=[task.pk]), {"body": "Note"})
    assert denied.status_code == 403

    grant_permissions(user, "add_taskcomment", "view_auditlog")
    blank = client.post(reverse("operations:task-comment", args=[task.pk]), {"body": "   "})
    assert blank.status_code == 200
    assert TaskComment.objects.count() == 0

    ok = client.post(
        reverse("operations:task-comment", args=[task.pk]),
        {"body": "Rack B2 verified."},
    )
    assert ok.status_code == 302
    assert TaskComment.objects.filter(task=task, author=user).exists()
    assert AuditLog.objects.filter(
        entity="operations.OperationalTask",
        entity_id=str(task.pk),
        action="comment_added",
    ).exists()
    detail_after = client.get(reverse("operations:task-detail", args=[task.pk]))
    assert b"Rack B2 verified." in detail_after.content


@pytest.mark.django_db
def test_reports_inventory_csv_pdf_and_dashboard_kpis(client, user):
    product = Product.objects.create(name="Cork Yoga Mat", sku="MAT-01")
    location = StockLocation.objects.create(name="Lisbon Depot", code="LIS")
    record_stock_movement(
        product=product,
        location=location,
        movement_type=StockMovement.MovementType.INBOUND,
        quantity=2,
        minimum_stock=8,
        reason="Initial",
        user=user,
    )
    OperationalTask.objects.create(
        title="Restock mats",
        category=OperationalTask.Category.INVENTORY,
        assigned_to=user,
        due_date=timezone.localdate() - timedelta(days=1),
    )

    grant_permissions(
        user,
        "view_product",
        "view_operationaltask",
        "view_stockitem",
        "add_stockmovement",
    )
    client.force_login(user)

    dash = client.get(reverse("accounts:dashboard"))
    assert dash.status_code == 200
    assert b"Low-stock watchlist" in dash.content
    assert b"Lisbon Depot" in dash.content

    summary_resp = client.get(reverse("reports:summary"))
    assert summary_resp.status_code == 200
    assert b"Collaborator activity" in summary_resp.content
    assert b"Lisbon Depot" in summary_resp.content

    inv_csv = client.get(reverse("reports:inventory-csv"))
    assert inv_csv.status_code == 200
    assert b"MAT-01" in inv_csv.content

    pdf_resp = client.get(reverse("reports:summary-pdf"))
    assert pdf_resp.status_code == 200
    assert pdf_resp["Content-Type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-1.4")
    assert b"xref" in pdf_resp.content
    assert pdf_resp.content.rstrip().endswith(b"%%EOF")

    bad_pdf = client.get(reverse("reports:summary-pdf"), {"start_date": "not-a-date"})
    assert bad_pdf.status_code == 400

    # Multi-page pure-Python PDF check
    long_pdf = build_pdf_document(
        title="Multi (Page) \\ Test", lines=[f"Line {i}" for i in range(95)]
    )
    assert long_pdf.startswith(b"%PDF-1.4")
    assert b"Page 1 of 3" in long_pdf
    assert b"Page 3 of 3" in long_pdf
