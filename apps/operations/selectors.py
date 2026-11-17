from django.db.models import Q

from apps.audit.models import AuditLog

from .models import OperationalTask


def filter_operational_tasks(
    user,
    *,
    status: str = "",
    priority: str = "",
    category: str = "",
    scope: str = "",
    query: str = "",
):
    """Filter operational tasks with related user/product preloaded."""
    tasks = OperationalTask.objects.select_related("assigned_to", "product")
    if status in OperationalTask.Status.values:
        tasks = tasks.filter(status=status)
    if priority in OperationalTask.Priority.values:
        tasks = tasks.filter(priority=priority)
    if category in OperationalTask.Category.values:
        tasks = tasks.filter(category=category)
    if scope == "mine":
        tasks = tasks.filter(assigned_to=user)
    elif scope == "overdue":
        tasks = tasks.overdue()
    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))
    return tasks


def get_task_history(task: OperationalTask):
    """Return recent audit events recorded for the given operational task."""
    return AuditLog.objects.filter(
        entity="operations.OperationalTask",
        entity_id=str(task.pk),
    ).select_related("user")[:20]
