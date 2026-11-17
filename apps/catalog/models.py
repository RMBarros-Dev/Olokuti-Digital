import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    """Reusable domain filters for active vs archived catalogue records."""

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class Product(models.Model):
    class Currency(models.TextChoices):
        EUR = "EUR", "EUR (€)"
        BRL = "BRL", "BRL (R$)"
        USD = "USD", "USD ($)"
        GBP = "GBP", "GBP (£)"
        INR = "INR", "INR (₹)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    sku = models.CharField(max_length=64, blank=True, default="")
    barcode = models.CharField(max_length=64, blank=True, default="", db_index=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="products",
    )
    origin = models.CharField(max_length=180, blank=True)
    sustainability_info = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True, default="")
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EUR)
    attributes = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_products",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"], name="product_name_idx"),
            models.Index(fields=["is_active", "name"], name="product_active_name_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["sku"],
                condition=Q(sku__gt=""),
                name="unique_non_empty_product_sku",
            ),
            models.CheckConstraint(
                condition=Q(price__isnull=True) | Q(price__gte=0),
                name="product_price_non_negative",
            ),
        ]

    def __str__(self):
        return self.name

    def get_translation(self, language_code: str | None):
        """Return matching ProductTranslation for language_code without mutating original fields."""
        if not language_code:
            return None
        cache = getattr(self, "_prefetched_objects_cache", {})
        if "translations" in cache:
            normalized = language_code.lower()
            for item in cache["translations"]:
                if item.locale.lower() == normalized:
                    return item
            return None
        return self.translations.filter(locale__iexact=language_code).first()


class ProductTranslation(models.Model):
    """Optional display translation; Product fields remain the original record."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="translations")
    locale = models.CharField(max_length=10, choices=settings.LANGUAGES)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    sustainability_info = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["locale"]
        constraints = [
            models.UniqueConstraint(fields=["product", "locale"], name="unique_product_locale")
        ]

    def __str__(self):
        return f"{self.product.name} [{self.locale}]"
