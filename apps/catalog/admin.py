from django.contrib import admin
from django.db import transaction

from apps.audit.services import record_event

from .models import Category, Product, ProductTranslation


class AuditedModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        record_event(
            user=request.user,
            action="updated" if change else "created",
            entity=obj._meta.label,
            entity_id=obj.pk,
        )

    @transaction.atomic
    def delete_model(self, request, obj):
        record_event(user=request.user, action="deleted", entity=obj._meta.label, entity_id=obj.pk)
        super().delete_model(request, obj)

    @transaction.atomic
    def delete_queryset(self, request, queryset):
        for obj in queryset.only("pk"):
            record_event(
                user=request.user, action="deleted", entity=obj._meta.label, entity_id=obj.pk
            )
        super().delete_queryset(request, queryset)


@admin.register(Category)
class CategoryAdmin(AuditedModelAdmin):
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(AuditedModelAdmin):
    list_display = ("name", "category", "origin", "updated_at")
    list_filter = ("category",)
    search_fields = ("name", "origin")
    readonly_fields = ("id", "created_by", "created_at", "updated_at")


@admin.register(ProductTranslation)
class ProductTranslationAdmin(AuditedModelAdmin):
    list_display = ("product", "locale", "name", "updated_at")
    list_filter = ("locale",)
