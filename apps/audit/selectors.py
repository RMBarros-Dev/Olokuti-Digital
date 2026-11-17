from .models import AuditLog


def filter_audit_events(*, entity: str = "", action: str = ""):
    """Query read-only audit events with optional entity substring and action filters."""
    events = AuditLog.objects.select_related("user").all()
    if entity:
        events = events.filter(entity__icontains=entity)
    if action:
        events = events.filter(action=action)
    return events


def get_distinct_audit_actions():
    return AuditLog.objects.order_by().values_list("action", flat=True).distinct()
