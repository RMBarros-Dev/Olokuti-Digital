from django.contrib import admin

from apps.audit.mixins import AuditedAdminMixin

from .models import Category, Product, ProductTranslation


@admin.register(Category)
class CategoryAdmin(AuditedAdminMixin, admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(AuditedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "currency", "is_active", "updated_at")
    list_filter = ("is_active", "category", "currency")
    search_fields = ("name", "sku", "barcode", "origin")
    readonly_fields = ("id", "created_by", "created_at", "updated_at")


@admin.register(ProductTranslation)
class ProductTranslationAdmin(AuditedAdminMixin, admin.ModelAdmin):
    list_display = ("product", "locale", "name", "updated_at")
    list_filter = ("locale",)
