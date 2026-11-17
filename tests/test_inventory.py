import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.urls import reverse

from apps.accounts.services import ensure_default_role_groups
from apps.audit.models import AuditLog
from apps.catalog.models import Category, Product
from apps.inventory.admin import StockMovementAdmin
from apps.inventory.models import StockItem, StockLocation, StockMovement
from apps.inventory.selectors import get_low_stock_items
from apps.inventory.services import InsufficientStockError, record_stock_movement
from tests.conftest import grant_permissions


@pytest.mark.django_db
def test_stock_movement_service_inbound_outbound_adjustment_and_audit(user):
    category = Category.objects.create(name="Homeware")
    product = Product.objects.create(name="Ceramic Pitcher", sku="CER-01", category=category)
    location = StockLocation.objects.create(name="Main Warehouse", code="MAIN")

    inbound = record_stock_movement(
        product=product,
        location=location,
        movement_type=StockMovement.MovementType.INBOUND,
        quantity=15,
        minimum_stock=5,
        reference="PO-100",
        reason="Supplier delivery",
        user=user,
    )
    item = StockItem.objects.get(product=product, location=location)
    assert item.quantity == 15
    assert item.minimum_stock == 5
    assert item.is_low_stock is False
    assert inbound.quantity_delta == 15
    assert inbound.balance_after == 15

    outbound = record_stock_movement(
        product=product,
        location=location,
        movement_type=StockMovement.MovementType.OUTBOUND,
        quantity=11,
        reason="Store replenishment",
        user=user,
    )
    item.refresh_from_db()
    assert item.quantity == 4
    assert item.is_low_stock is True
    assert outbound.quantity_delta == -11
    assert outbound.balance_after == 4
    assert list(get_low_stock_items()) == [item]

    adjustment = record_stock_movement(
        product=product,
        location=location,
        movement_type=StockMovement.MovementType.ADJUSTMENT,
        quantity=9,
        reason="Cycle count recount",
        user=user,
    )
    item.refresh_from_db()
    assert item.quantity == 9
    assert item.is_low_stock is False
    assert adjustment.quantity_delta == 5
    assert adjustment.balance_after == 9
    assert AuditLog.objects.filter(entity="inventory.StockMovement").count() == 3


@pytest.mark.django_db
def test_stock_movement_validation_and_insufficient_stock_guards(user):
    product = Product.objects.create(name="Bamboo Comb", sku="BAM-01")
    archived = Product.objects.create(name="Retired Comb", sku="BAM-OLD", is_active=False)
    active_loc = StockLocation.objects.create(name="Central", code="CTR")
    inactive_loc = StockLocation.objects.create(name="Closed", code="OLD", is_active=False)

    record_stock_movement(
        product=product,
        location=active_loc,
        movement_type=StockMovement.MovementType.INBOUND,
        quantity=3,
        reason="Initial stock",
        user=user,
    )

    with pytest.raises(InsufficientStockError):
        record_stock_movement(
            product=product,
            location=active_loc,
            movement_type=StockMovement.MovementType.OUTBOUND,
            quantity=4,
            reason="Oversold order",
            user=user,
        )

    with pytest.raises(ValidationError, match="inactive location"):
        record_stock_movement(
            product=product,
            location=inactive_loc,
            movement_type=StockMovement.MovementType.INBOUND,
            quantity=1,
            reason="Blocked",
            user=user,
        )

    with pytest.raises(ValidationError, match="inactive product"):
        record_stock_movement(
            product=archived,
            location=active_loc,
            movement_type=StockMovement.MovementType.INBOUND,
            quantity=1,
            reason="Blocked",
            user=user,
        )

    for bad_kwargs in [
        {"quantity": 0, "movement_type": StockMovement.MovementType.INBOUND},
        {"quantity": -1, "movement_type": StockMovement.MovementType.ADJUSTMENT},
        {"quantity": 3, "movement_type": StockMovement.MovementType.ADJUSTMENT},
        {"quantity": 1, "movement_type": "invalid"},
        {"quantity": 1, "movement_type": StockMovement.MovementType.INBOUND, "reason": "   "},
        {
            "quantity": 1,
            "movement_type": StockMovement.MovementType.INBOUND,
            "minimum_stock": -2,
        },
    ]:
        kwargs = {
            "product": product,
            "location": active_loc,
            "reason": "Validation check",
            "user": user,
            **bad_kwargs,
        }
        with pytest.raises(ValidationError):
            record_stock_movement(**kwargs)

    item = StockItem.objects.get(product=product, location=active_loc)
    assert item.quantity == 3
    assert item.movements.count() == 1


@pytest.mark.django_db
def test_inventory_database_constraints_and_admin_immutability():
    product = Product.objects.create(name="Soap Bar", sku="SOAP-01")
    location = StockLocation.objects.create(name="Shop Floor", code="SHOP")
    item = StockItem.objects.create(product=product, location=location, quantity=2)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            StockItem.objects.create(product=product, location=location, quantity=1)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            StockItem.objects.filter(pk=item.pk).update(quantity=-1)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            StockMovement.objects.create(
                stock_item=item,
                movement_type=StockMovement.MovementType.ADJUSTMENT,
                quantity_delta=0,
                balance_after=2,
                reason="Zero delta",
            )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            StockMovement.objects.create(
                stock_item=item,
                movement_type=StockMovement.MovementType.OUTBOUND,
                quantity_delta=-5,
                balance_after=-3,
                reason="Negative balance",
            )

    admin_view = StockMovementAdmin(StockMovement, AdminSite())
    assert admin_view.has_add_permission(None) is False
    assert admin_view.has_change_permission(None) is False
    assert admin_view.has_delete_permission(None) is False


@pytest.mark.django_db
def test_inventory_views_permissions_htmx_csv_and_product_detail(client, user):
    product = Product.objects.create(name="=Formula Linen Apron", sku="LIN-01")
    location = StockLocation.objects.create(name="Madrid Hub", code="MAD")
    record_stock_movement(
        product=product,
        location=location,
        movement_type=StockMovement.MovementType.INBOUND,
        quantity=4,
        minimum_stock=5,
        reference="GRN-1",
        reason="Opening balance",
        user=user,
    )

    client.force_login(user)
    assert client.get(reverse("inventory:stock-list")).status_code == 403
    assert client.get(reverse("inventory:movement-list")).status_code == 403
    assert client.get(reverse("inventory:movement-create")).status_code == 403
    assert client.get(reverse("inventory:location-list")).status_code == 403

    grant_permissions(
        user,
        "view_product",
        "view_stockitem",
        "change_stockitem",
        "view_stockmovement",
        "add_stockmovement",
        "view_stocklocation",
        "add_stocklocation",
        "change_stocklocation",
    )

    list_resp = client.get(
        reverse("inventory:stock-list"),
        {"q": "LIN-01", "location": str(location.pk), "low_stock": "1"},
        HTTP_HX_REQUEST="true",
    )
    assert list_resp.status_code == 200
    assert "inventory/_stock_table.html" in [t.name for t in list_resp.templates]
    assert b"MAD" in list_resp.content

    full_resp = client.get(reverse("inventory:stock-list"))
    assert full_resp.status_code == 200

    assert str(location) == "Madrid Hub (MAD)"
    latest_move = StockMovement.objects.latest("created_at")
    assert "+4" in str(latest_move)

    create_get = client.get(
        reverse("inventory:movement-create"),
        {"product": str(product.pk), "location": str(location.pk)},
    )
    assert create_get.status_code == 200

    csv_resp = client.get(reverse("inventory:stock-export-csv"), {"low_stock": "1"})
    assert csv_resp.status_code == 200
    csv_body = csv_resp.content.decode("utf-8")
    assert "'=Formula Linen Apron" in csv_body

    bad_move = client.post(
        reverse("inventory:movement-create"),
        {
            "product": str(product.pk),
            "location": str(location.pk),
            "movement_type": StockMovement.MovementType.OUTBOUND,
            "quantity": "10",
            "reason": "Too much",
        },
    )
    assert bad_move.status_code == 200
    assert b"Insufficient stock" in bad_move.content

    good_move = client.post(
        reverse("inventory:movement-create"),
        {
            "product": str(product.pk),
            "location": str(location.pk),
            "movement_type": StockMovement.MovementType.INBOUND,
            "quantity": "6",
            "minimum_stock": "3",
            "reference": "PO-202",
            "reason": "Restocked",
        },
    )
    assert good_move.status_code == 302
    assert StockItem.objects.get(product=product, location=location).quantity == 10

    move_list = client.get(
        reverse("inventory:movement-list"),
        {"q": "PO-202", "location": str(location.pk), "movement_type": "inbound"},
        HTTP_HX_REQUEST="true",
    )
    assert move_list.status_code == 200
    assert b"Restocked" in move_list.content
    assert client.get(reverse("inventory:movement-list")).status_code == 200

    item = StockItem.objects.get(product=product, location=location)
    assert client.get(reverse("inventory:threshold-update", args=[item.pk])).status_code == 200
    thresh_resp = client.post(
        reverse("inventory:threshold-update", args=[item.pk]),
        {"minimum_stock": "12"},
    )
    assert thresh_resp.status_code == 302
    item.refresh_from_db()
    assert item.minimum_stock == 12

    assert client.get(reverse("inventory:location-create")).status_code == 200
    create_loc = client.post(
        reverse("inventory:location-create"),
        {"name": "Porto Annex", "code": "opo", "is_active": "on", "description": "North hub"},
    )
    assert create_loc.status_code == 302
    new_loc = StockLocation.objects.get(code="OPO")
    assert client.get(reverse("inventory:location-update", args=[new_loc.pk])).status_code == 200
    assert (
        client.post(
            reverse("inventory:location-update", args=[new_loc.pk]),
            {"name": "Porto Hub", "code": "opo", "is_active": "on", "description": "Updated"},
        ).status_code
        == 302
    )
    assert client.get(reverse("inventory:location-list")).status_code == 200

    detail_resp = client.get(reverse("catalog:product-detail", args=[product.pk]))
    assert detail_resp.status_code == 200
    assert b"Madrid Hub" in detail_resp.content


@pytest.mark.django_db
def test_default_role_groups_and_seed_demo_include_inventory(settings):
    settings.DEBUG = True
    ensure_default_role_groups()
    ops_group = Group.objects.get(name="Operations Team")
    assert ops_group.permissions.filter(codename="add_stockmovement").exists()
    assert not ops_group.permissions.filter(codename="delete_stockmovement").exists()

    call_command("seed_demo")
    call_command("seed_demo")
    assert StockLocation.objects.filter(code="MAIN").exists()
    assert StockItem.objects.filter(location__code="MAIN").count() == 3
    assert StockMovement.objects.count() == 3
