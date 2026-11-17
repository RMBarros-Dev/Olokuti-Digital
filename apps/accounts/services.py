from django.contrib.auth.models import Group, Permission
from django.contrib.sessions.models import Session
from django.utils import timezone

DEFAULT_ROLE_GROUPS = {
    "Catalogue Team": [
        "view_product",
        "add_product",
        "change_product",
        "delete_product",
        "view_category",
        "add_category",
        "change_category",
        "delete_category",
    ],
    "Operations Team": [
        "view_operationaltask",
        "add_operationaltask",
        "change_operationaltask",
        "delete_operationaltask",
        "view_product",
    ],
    "Auditors & Managers": [
        "view_product",
        "add_product",
        "change_product",
        "delete_product",
        "view_operationaltask",
        "add_operationaltask",
        "change_operationaltask",
        "delete_operationaltask",
        "view_auditlog",
    ],
}


def ensure_default_role_groups():
    for group_name, codenames in DEFAULT_ROLE_GROUPS.items():
        group, _created = Group.objects.get_or_create(name=group_name)
        perms = Permission.objects.filter(codename__in=codenames)
        # Add defaults without wiping permissions an administrator customized.
        group.permissions.add(*perms)


def can_manage_target_user(actor, target) -> bool:
    """Only superusers may manage superuser accounts; staff manages non-superuser accounts."""
    if not getattr(actor, "is_authenticated", False) or not actor.is_active or not actor.is_staff:
        return False
    if target.is_superuser and not actor.is_superuser:
        return False
    return True


def invalidate_user_sessions(user) -> int:
    """Delete all active sessions belonging to `user` without affecting other users."""
    target_id = str(user.pk)
    invalidated = 0
    now = timezone.now()
    for session in Session.objects.filter(expire_date__gte=now).iterator(chunk_size=200):
        data = session.get_decoded()
        if str(data.get("_auth_user_id", "")) == target_id:
            session.delete()
            invalidated += 1
    return invalidated
