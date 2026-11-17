import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _


class StockLocation(models.Model):
    """Physical or logical warehouse location holding product stock."""

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=32, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class StockItemQuerySet(models.QuerySet):
    """Reusable domain filters for active and low-stock inventory balances."""

    def active(self):
        return self.filter(location__is_active=True, product__is_active=True)

    def low_stock(self):
        return self.filter(quantity__lte=F("minimum_stock"))

    def with_relations(self):
        return self.select_related("product", "product__category", "location")


class StockItem(models.Model):
    """Current inventory quantity for a given product at a given location."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="stock_items",
    )
    location = models.ForeignKey(
        StockLocation,
        on_delete=models.PROTECT,
        related_name="stock_items",
    )
    quantity = models.IntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    objects = StockItemQuerySet.as_manager()

    class Meta:
        ordering = ["product__name", "location__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "location"],
                name="unique_stock_item_product_location",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name="stock_item_quantity_non_negative",
            ),
        ]
        indexes = [
            models.Index(fields=["location", "quantity"], name="stock_loc_qty_idx"),
            models.Index(fields=["product", "quantity"], name="stock_prod_qty_idx"),
        ]

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.minimum_stock

    def __str__(self) -> str:
        return f"{self.product} @ {self.location.code}: {self.quantity}"


class StockMovement(models.Model):
    """Immutable append-only ledger entry recording every stock quantity change."""

    class MovementType(models.TextChoices):
        INBOUND = "inbound", _("Inbound")
        OUTBOUND = "outbound", _("Outbound")
        ADJUSTMENT = "adjustment", _("Adjustment")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name="movements",
    )
    movement_type = models.CharField(
        max_length=16,
        choices=MovementType.choices,
        db_index=True,
    )
    quantity_delta = models.IntegerField()
    balance_after = models.IntegerField()
    reference = models.CharField(max_length=120, blank=True)
    reason = models.CharField(max_length=255)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stock_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(quantity_delta=0),
                name="stock_movement_non_zero_delta",
            ),
            models.CheckConstraint(
                condition=Q(balance_after__gte=0),
                name="stock_movement_non_negative_balance",
            ),
        ]
        indexes = [
            models.Index(fields=["stock_item", "-created_at"], name="movement_item_created_idx"),
        ]

    def __str__(self) -> str:
        sign = "+" if self.quantity_delta > 0 else ""
        return f"{self.stock_item.product} ({sign}{self.quantity_delta}) -> {self.balance_after}"
