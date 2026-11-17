from django.contrib import admin

from apps.audit.mixins import AuditedAdminMixin

from .models import OperationalTask, TaskComment


@admin.register(OperationalTask)
class OperationalTaskAdmin(AuditedAdminMixin, admin.ModelAdmin):
    list_display = ("title", "category", "status", "priority", "assigned_to", "due_date")
    list_filter = ("category", "status", "priority")
    search_fields = ("title",)

    def _resolve_save_action(self, request, obj, form, change: bool) -> str:
        if change:
            previous_status = (
                OperationalTask.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
            )
            if previous_status and previous_status != obj.status:
                return "status_changed"
            return "updated"
        return "created"


@admin.register(TaskComment)
class TaskCommentAdmin(AuditedAdminMixin, admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    search_fields = ("task__title", "body")
    readonly_fields = ("id", "created_at")
