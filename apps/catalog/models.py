import uuid

from django.conf import settings
from django.db import models


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


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
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
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_products",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"], name="product_name_idx")]

    def __str__(self):
        return self.name

    def get_translation(self, language_code: str | None):
        """Return matching ProductTranslation for language_code without mutating original fields."""
        if not language_code:
            return None
        normalized = language_code.lower()
        base_lang = normalized.split("-")[0]
        translations = list(self.translations.all())
        for item in translations:
            if item.locale.lower() == normalized:
                return item
        for item in translations:
            if item.locale.lower().split("-")[0] == base_lang:
                return item
        return None


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
