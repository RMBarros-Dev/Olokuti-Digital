from .models import AuditLog

_SENSITIVE_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "cookie",
    "session",
    "authorization",
    "api_key",
    "credential",
    "uid",
)


def sanitize_audit_details(value):
    """Recursively redact sensitive keys before writing structured details to AuditLog."""
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            key_str = str(key)
            lowered = key_str.lower()
            if any(fragment in lowered for fragment in _SENSITIVE_FRAGMENTS):
                sanitized[key_str] = "***REDACTED***"
            else:
                sanitized[key_str] = sanitize_audit_details(item)
        return sanitized
    if isinstance(value, (list, tuple)):
        return [sanitize_audit_details(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def record_event(*, user, action: str, entity: str, entity_id, details=None) -> AuditLog:
    """Write a minimal audit event with sensitive details redacted."""
    actor = user if getattr(user, "is_authenticated", False) else None
    safe_details = sanitize_audit_details(details or {})
    return AuditLog.objects.create(
        user=actor,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        details=safe_details,
    )
