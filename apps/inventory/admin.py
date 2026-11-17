from django.contrib import admin

from apps.audit.mixins import AuditedAdminMixin

from .models import StockItem, StockLocation, StockMovement


@admin.register(StockLocation)
class StockLocationAdmin(AuditedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    readonly_fields = ("created_at", "updated_at")


@admin.register(StockItem)
class StockItemAdmin(AuditedAdminMixin, admin.ModelAdmin):
    list_display = ("product", "location", "quantity", "minimum_stock", "updated_at")
    list_filter = ("location",)
    search_fields = ("product__name", "product__sku", "location__code")
    readonly_fields = ("id", "quantity", "updated_at")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Read-only admin view enforcing append-only stock movement immutability."""

    list_display = (
        "created_at",
        "stock_item",
        "movement_type",
        "quantity_delta",
        "balance_after",
        "performed_by",
    )
    list_filter = ("movement_type", "created_at")
    search_fields = (
        "stock_item__product__name",
        "stock_item__product__sku",
        "reference",
        "reason",
    )
    readonly_fields = (
        "id",
        "stock_item",
        "movement_type",
        "quantity_delta",
        "balance_after",
        "reference",
        "reason",
        "performed_by",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
