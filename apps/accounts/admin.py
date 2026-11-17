from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group

from apps.audit.mixins import AuditedAdminMixin
from apps.audit.services import record_event

from .services import invalidate_user_sessions

User = get_user_model()
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class AuditedUserAdmin(AuditedAdminMixin, UserAdmin):
    def _after_audited_save(self, request, obj, form, change: bool) -> None:
        changed = list(getattr(form, "changed_data", []))
        if change and (not obj.is_active or "password" in changed or "is_staff" in changed):
            invalidate_user_sessions(obj)


@admin.register(Group)
class AuditedGroupAdmin(AuditedAdminMixin, GroupAdmin):
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        group = form.instance
        record_event(
            user=request.user,
            action="updated" if change else "created",
            entity=group._meta.label,
            entity_id=group.pk,
        )
