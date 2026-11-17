from datetime import timedelta

import pytest
from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from apps.accounts.admin import AuditedGroupAdmin, AuditedUserAdmin
from apps.audit.admin import AuditLogAdmin
from apps.audit.models import AuditLog
from apps.catalog.admin import CategoryAdmin, ProductAdmin
from apps.catalog.models import Category, Product, ProductTranslation
from apps.operations.admin import OperationalTaskAdmin
from apps.operations.models import OperationalTask


@pytest.mark.django_db
def test_audit_list_permissions_filters_and_htmx_fragment(client, user):
    url = reverse("audit:list")
    client.force_login(user)
    assert client.get(url).status_code == 403

    user.user_permissions.add(*Permission.objects.filter(codename="view_auditlog"))
    AuditLog.objects.create(user=user, action="created", entity="catalog.Product", entity_id="p1")
    AuditLog.objects.create(user=user, action="deleted", entity="auth.User", entity_id="u1")

    resp = client.get(url, {"entity": "catalog", "action": "created"})
    assert resp.status_code == 200
    assert "catalog.Product" in resp.content.decode()
    assert "auth.User" not in resp.content.decode()

    htmx = client.get(url, HTTP_HX_REQUEST="true")
    assert htmx.status_code == 200
    assert b"<html" not in htmx.content


@pytest.mark.django_db
def test_user_list_search_group_filter_pagination_and_405(client, django_user_model):
    staff = django_user_model.objects.create_user(
        username="staff-admin", password="safe-test-password", is_staff=True
    )
    grp = Group.objects.create(name="Searchable Group")
    u1 = django_user_model.objects.create_user(
        username="alpha-user", email="alpha@olokuti.local", password="safe-test-password"
    )
    u1.groups.add(grp)
    django_user_model.objects.create_user(username="beta-user", password="safe-test-password")

    client.force_login(staff)
    resp = client.get(reverse("accounts:user-list"), {"q": "alpha", "group": str(grp.pk)})
    assert resp.status_code == 200
    html = resp.content.decode()
    assert "alpha-user" in html
    assert "beta-user" not in html

    assert client.get(reverse("accounts:user-create")).status_code == 200
    assert client.get(reverse("accounts:user-update", args=[u1.pk])).status_code == 200
    assert client.get(reverse("accounts:setup-groups")).status_code == 405


@pytest.mark.django_db
def test_catalog_update_translation_delete_and_category_edge_cases(client, user):
    user.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "view_product",
                "add_product",
                "change_product",
                "delete_product",
                "view_category",
                "add_category",
                "change_category",
            ]
        )
    )
    category = Category.objects.create(name="Eco Goods")
    product = Product.objects.create(name="Bamboo Brush", category=category)
    trans = ProductTranslation.objects.create(product=product, locale="pt-br", name="Escova")
    client.force_login(user)

    # Filter by category
    list_resp = client.get(reverse("catalog:product-list"), {"category": str(category.pk)})
    assert list_resp.status_code == 200
    assert "Bamboo Brush" in list_resp.content.decode()

    # Create form GET and update GET/POST
    assert client.get(reverse("catalog:product-create")).status_code == 200
    assert client.get(reverse("catalog:product-update", args=[product.pk])).status_code == 200
    upd_resp = client.post(
        reverse("catalog:product-update", args=[product.pk]),
        {"name": "Bamboo Toothbrush", "category": str(category.pk)},
    )
    assert upd_resp.status_code == 302
    product.refresh_from_db()
    assert str(product) == "Bamboo Toothbrush"

    # Translation save GET 405 + invalid POST + delete POST & GET 405
    save_url = reverse("catalog:product-translation-save", args=[product.pk])
    assert client.get(save_url).status_code == 405
    bad_trans = client.post(save_url, {"locale": "invalid-loc", "name": ""})
    assert bad_trans.status_code == 200

    del_trans_url = reverse("catalog:product-translation-delete", args=[product.pk, trans.pk])
    assert client.get(del_trans_url).status_code == 405
    assert client.post(del_trans_url).status_code == 302
    assert not ProductTranslation.objects.filter(pk=trans.pk).exists()

    # Delete product HTTP 405 on PUT
    assert client.put(reverse("catalog:product-delete", args=[product.pk])).status_code == 405

    # Category list, invalid create (400), update GET + invalid POST + PUT 405
    assert client.get(reverse("catalog:category-list")).status_code == 200
    assert client.post(reverse("catalog:category-create"), {"name": ""}).status_code == 400
    cat_upd_url = reverse("catalog:category-update", args=[category.pk])
    assert client.get(cat_upd_url).status_code == 200
    assert client.post(cat_upd_url, {"name": ""}).status_code == 400
    assert client.put(cat_upd_url).status_code == 405


@pytest.mark.django_db
def test_operations_filters_update_delete_and_report_date_range(client, user):
    user.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "view_product",
                "view_operationaltask",
                "add_operationaltask",
                "change_operationaltask",
                "delete_operationaltask",
            ]
        )
    )
    client.force_login(user)

    overdue_task = OperationalTask.objects.create(
        title="Overdue task",
        status=OperationalTask.Status.TODO,
        priority=OperationalTask.Priority.HIGH,
        assigned_to=user,
        due_date=timezone.localdate() - timedelta(days=3),
    )
    assert overdue_task.is_overdue is True
    assert str(overdue_task) == "Overdue task"

    done_task = OperationalTask.objects.create(
        title="Finished task",
        status=OperationalTask.Status.DONE,
        priority=OperationalTask.Priority.LOW,
        due_date=timezone.localdate() - timedelta(days=5),
    )
    assert done_task.is_overdue is False

    # Task list filters
    list_url = reverse("operations:task-list")
    assert (
        client.get(list_url, {"status": "todo", "priority": "high", "scope": "mine"}).status_code
        == 200
    )
    overdue_resp = client.get(list_url, {"scope": "overdue"})
    assert "Overdue task" in overdue_resp.content.decode()
    assert "Finished task" not in overdue_resp.content.decode()

    assert client.get(reverse("operations:task-create")).status_code == 200
    assert client.get(reverse("operations:task-update", args=[overdue_task.pk])).status_code == 200
    assert client.get(reverse("operations:task-status", args=[overdue_task.pk])).status_code == 405

    del_url = reverse("operations:task-delete", args=[done_task.pk])
    assert client.get(del_url).status_code == 200
    assert client.put(del_url).status_code == 405
    assert client.post(del_url).status_code == 302
    assert not OperationalTask.objects.filter(pk=done_task.pk).exists()

    # Reports date filter validation + range query
    today_iso = timezone.localdate().isoformat()
    rep_ok = client.get(
        reverse("reports:summary"), {"start_date": today_iso, "end_date": today_iso}
    )
    assert rep_ok.status_code == 200
    bad_csv = client.get(
        reverse("reports:tasks-csv"),
        {"start_date": "2026-12-31", "end_date": "2026-01-01"},
    )
    assert bad_csv.status_code == 400


@pytest.mark.django_db
def test_admin_audit_wrappers_and_seed_demo_when_debug_enabled(settings):
    settings.DEBUG = True
    call_command("seed_demo")
    assert Product.objects.filter(name__startswith="[DEMO]").count() == 3

    User = get_user_model()
    admin_user = User.objects.create_superuser(
        username="super", email="super@example.com", password="safe-test-password"
    )
    rf = RequestFactory()
    req = rf.post("/admin/")
    req.user = admin_user

    # AuditLogAdmin is strictly read-only
    audit_admin = AuditLogAdmin(AuditLog, django_admin.site)
    assert audit_admin.has_add_permission(req) is False
    assert audit_admin.has_change_permission(req) is False
    assert audit_admin.has_delete_permission(req) is False

    # Catalog Admin audit hooks
    cat_admin = CategoryAdmin(Category, django_admin.site)
    cat = Category(name="Admin Category")
    cat_admin.save_model(req, cat, None, change=False)
    assert AuditLog.objects.filter(entity="catalog.Category", action="created").exists()
    cat_admin.delete_model(req, cat)
    assert AuditLog.objects.filter(entity="catalog.Category", action="deleted").exists()

    prod = Product.objects.create(name="Admin Product")
    prod_admin = ProductAdmin(Product, django_admin.site)
    prod_admin.delete_queryset(req, Product.objects.filter(pk=prod.pk))

    # Operations Admin audit hooks
    task = OperationalTask.objects.create(title="Admin Task", status="todo")
    task_admin = OperationalTaskAdmin(OperationalTask, django_admin.site)
    task.status = "done"
    task_admin.save_model(req, task, None, change=True)
    assert AuditLog.objects.filter(
        entity="operations.OperationalTask", entity_id=str(task.pk), action="status_changed"
    ).exists()
    task_admin.delete_model(req, task)

    # Accounts UserAdmin & GroupAdmin hooks
    target = User.objects.create_user(username="adm-target", password="safe-test-password")
    u_admin = AuditedUserAdmin(User, django_admin.site)
    u_admin.save_model(req, target, None, change=True)
    u_admin.delete_model(req, target)

    grp = Group.objects.create(name="Adm Group")
    g_admin = AuditedGroupAdmin(Group, django_admin.site)
    g_admin.delete_model(req, grp)
