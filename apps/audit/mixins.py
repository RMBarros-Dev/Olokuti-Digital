from django.db import transaction

from apps.audit.services import record_event


class AuditedAdminMixin:
    """Record atomic AuditLog events across Django Admin create, update, and delete actions."""

    def _audit_entity_label(self, obj) -> str:
        return obj._meta.label

    def _resolve_save_action(self, request, obj, form, change: bool) -> str:
        return "updated" if change else "created"

    def _collect_save_details(self, request, obj, form, change: bool) -> dict:
        changed = list(getattr(form, "changed_data", []))
        return {"changed_fields": changed} if changed else {}

    def _after_audited_save(self, request, obj, form, change: bool) -> None:
        return None

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        action = self._resolve_save_action(request, obj, form, change)
        details = self._collect_save_details(request, obj, form, change)
        super().save_model(request, obj, form, change)
        self._after_audited_save(request, obj, form, change)
        record_event(
            user=request.user,
            action=action,
            entity=self._audit_entity_label(obj),
            entity_id=obj.pk,
            details=details,
        )

    @transaction.atomic
    def delete_model(self, request, obj):
        record_event(
            user=request.user,
            action="deleted",
            entity=self._audit_entity_label(obj),
            entity_id=obj.pk,
        )
        super().delete_model(request, obj)

    @transaction.atomic
    def delete_queryset(self, request, queryset):
        for obj in queryset.only("pk"):
            record_event(
                user=request.user,
                action="deleted",
                entity=self._audit_entity_label(obj),
                entity_id=obj.pk,
            )
        super().delete_queryset(request, queryset)
