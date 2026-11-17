from django.db.models import Q

from .models import StockItem, StockLocation, StockMovement


def filter_stock_items(
    *,
    query: str = "",
    location_id: str = "",
    low_stock_only: bool = False,
):
    """Filter current stock balances by search query, location, and low-stock state."""
    items = StockItem.objects.with_relations()
    if query:
        items = items.filter(
            Q(product__name__icontains=query)
            | Q(product__sku__icontains=query)
            | Q(product__barcode__icontains=query)
            | Q(location__name__icontains=query)
            | Q(location__code__icontains=query)
        )
    if location_id:
        items = items.filter(location_id=location_id)
    if low_stock_only:
        items = items.low_stock()
    return items.order_by("product__name", "location__name")


def get_low_stock_items(*, limit: int | None = None):
    """Return active stock balances at or below their configured minimum threshold."""
    qs = (
        StockItem.objects.active()
        .low_stock()
        .with_relations()
        .order_by("quantity", "product__name")
    )
    return qs[:limit] if limit is not None else qs


def filter_stock_movements(
    *,
    query: str = "",
    location_id: str = "",
    movement_type: str = "",
):
    """Filter immutable stock ledger entries with related product, location, and actor."""
    movements = StockMovement.objects.select_related(
        "stock_item__product",
        "stock_item__location",
        "performed_by",
    )
    if query:
        movements = movements.filter(
            Q(stock_item__product__name__icontains=query)
            | Q(stock_item__product__sku__icontains=query)
            | Q(reference__icontains=query)
            | Q(reason__icontains=query)
        )
    if location_id:
        movements = movements.filter(stock_item__location_id=location_id)
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    return movements


def get_active_locations():
    return StockLocation.objects.filter(is_active=True).order_by("name")


def iter_stock_items_for_csv(stock_items):
    """Stream stock balance rows incrementally for CSV export."""
    for item in stock_items.iterator(chunk_size=500):
        yield [
            item.product.name,
            item.product.sku,
            item.location.name,
            item.location.code,
            item.quantity,
            item.minimum_stock,
            "yes" if item.is_low_stock else "no",
            item.updated_at.isoformat(),
        ]
