from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.audit.services import record_event

from .models import StockItem, StockLocation, StockMovement


class InsufficientStockError(ValidationError):
    """Raised when a requested stock movement would drive inventory below zero."""


@transaction.atomic
def record_stock_movement(
    *,
    product,
    location: StockLocation,
    movement_type: str,
    quantity: int,
    reason: str,
    reference: str = "",
    user=None,
    minimum_stock: int | None = None,
) -> StockMovement:
    """Atomically lock the stock balance, apply the movement, and record audit history."""
    if not location.is_active:
        raise ValidationError(
            _("Cannot record stock movements for an inactive location."),
            code="inactive_location",
        )
    if not reason.strip():
        raise ValidationError(_("A movement reason is required."), code="missing_reason")
    if minimum_stock is not None and minimum_stock < 0:
        raise ValidationError(
            _("Minimum stock threshold cannot be negative."),
            code="invalid_minimum_stock",
        )

    valid_types = {
        StockMovement.MovementType.INBOUND,
        StockMovement.MovementType.OUTBOUND,
        StockMovement.MovementType.ADJUSTMENT,
    }
    if movement_type not in valid_types:
        raise ValidationError(_("Unsupported stock movement type."), code="invalid_movement_type")

    if movement_type == StockMovement.MovementType.INBOUND and not product.is_active:
        raise ValidationError(
            _("Cannot receive inbound stock for an inactive product."),
            code="inactive_product",
        )

    if movement_type in (
        StockMovement.MovementType.INBOUND,
        StockMovement.MovementType.OUTBOUND,
    ):
        if quantity <= 0:
            raise ValidationError(
                _("Quantity must be greater than zero for inbound and outbound movements."),
                code="non_positive_quantity",
            )
    elif quantity < 0:
        raise ValidationError(
            _("Counted stock quantity cannot be negative."),
            code="negative_adjustment",
        )

    item, _created = StockItem.objects.get_or_create(
        product=product,
        location=location,
        defaults={
            "quantity": 0,
            "minimum_stock": minimum_stock if minimum_stock is not None else 0,
        },
    )
    # Lock the balance row inside the transaction before reading/updating it on PostgreSQL.
    locked_item = StockItem.objects.select_for_update().get(pk=item.pk)

    if movement_type == StockMovement.MovementType.INBOUND:
        delta = quantity
        new_balance = locked_item.quantity + quantity
    elif movement_type == StockMovement.MovementType.OUTBOUND:
        delta = -quantity
        new_balance = locked_item.quantity - quantity
    else:
        delta = quantity - locked_item.quantity
        new_balance = quantity

    if new_balance < 0:
        raise InsufficientStockError(
            _("Insufficient stock at %(location)s: available %(available)s, requested %(req)s.")
            % {
                "location": location.name,
                "available": locked_item.quantity,
                "req": quantity,
            },
            code="insufficient_stock",
        )
    if delta == 0:
        raise ValidationError(
            _("Counted stock matches the current balance (no net change)."),
            code="zero_delta",
        )

    update_fields = ["quantity", "updated_at"]
    locked_item.quantity = new_balance
    if minimum_stock is not None:
        locked_item.minimum_stock = minimum_stock
        update_fields.append("minimum_stock")
    locked_item.save(update_fields=update_fields)

    movement = StockMovement.objects.create(
        stock_item=locked_item,
        movement_type=movement_type,
        quantity_delta=delta,
        balance_after=new_balance,
        reference=reference.strip(),
        reason=reason.strip(),
        performed_by=user if getattr(user, "is_authenticated", False) else None,
    )

    record_event(
        user=user,
        action="stock_moved",
        entity="inventory.StockMovement",
        entity_id=movement.pk,
        details={
            "product_id": str(product.pk),
            "location_id": location.pk,
            "movement_type": movement_type,
            "quantity_delta": delta,
            "balance_after": new_balance,
        },
    )
    return movement
