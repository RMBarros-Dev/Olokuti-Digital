from .models import AuditLog


def record_event(*, user, action: str, entity: str, entity_id, details=None) -> AuditLog:
    """Write a minimal audit event; callers should not put personal data in details."""
    actor = user if getattr(user, "is_authenticated", False) else None
    return AuditLog.objects.create(
        user=actor,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        details=details or {},
    )
