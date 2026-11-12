from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.db import transaction

from apps.audit.services import record_event

User = get_user_model()
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class AuditedUserAdmin(UserAdmin):
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


@admin.register(Group)
class AuditedGroupAdmin(GroupAdmin):
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        group = form.instance
        record_event(
            user=request.user,
            action="updated" if change else "created",
            entity=group._meta.label,
            entity_id=group.pk,
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
