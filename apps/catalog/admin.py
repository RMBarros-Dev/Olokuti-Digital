from django.contrib import admin

from apps.audit.mixins import AuditedAdminMixin

from .models import Category, Product, ProductTranslation


@admin.register(Category)
class CategoryAdmin(AuditedAdminMixin, admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(AuditedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "category", "origin", "updated_at")
    list_filter = ("category",)
    search_fields = ("name", "origin")
    readonly_fields = ("id", "created_by", "created_at", "updated_at")


@admin.register(ProductTranslation)
class ProductTranslationAdmin(AuditedAdminMixin, admin.ModelAdmin):
    list_display = ("product", "locale", "name", "updated_at")
    list_filter = ("locale",)
