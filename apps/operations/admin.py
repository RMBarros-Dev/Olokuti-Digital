from django.contrib import admin
from django.db import transaction

from apps.audit.services import record_event

from .models import OperationalTask


@admin.register(OperationalTask)
class OperationalTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "priority", "assigned_to", "due_date")
    list_filter = ("status", "priority")
    search_fields = ("title",)

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous_status = (
                OperationalTask.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
            )
        super().save_model(request, obj, form, change)
        action = (
            "status_changed"
            if previous_status and previous_status != obj.status
            else ("updated" if change else "created")
        )
        record_event(user=request.user, action=action, entity=obj._meta.label, entity_id=obj.pk)

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
