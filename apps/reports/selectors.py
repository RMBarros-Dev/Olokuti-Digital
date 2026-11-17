from datetime import datetime, time

from django.db.models import Count
from django.utils import timezone

from apps.operations.models import OperationalTask


def filter_tasks_for_report(form, *, has_query_params: bool):
    """Filter operational tasks for report views and CSV exports using validated date bounds."""
    tasks = OperationalTask.objects.select_related("assigned_to", "product").order_by("-created_at")
    if form.is_valid():
        start = form.cleaned_data.get("start_date")
        end = form.cleaned_data.get("end_date")
        if start:
            start_at = timezone.make_aware(datetime.combine(start, time.min))
            tasks = tasks.filter(created_at__gte=start_at)
        if end:
            end_at = timezone.make_aware(datetime.combine(end, time.max))
            tasks = tasks.filter(created_at__lte=end_at)
    elif has_query_params:
        tasks = tasks.none()
    return tasks


def summarize_task_counts(tasks) -> tuple[list[tuple[str, str, int]], int]:
    """Return ordered per-status counts and overall total for a task queryset."""
    totals_by_status = {
        row["status"]: row["total"]
        for row in tasks.values("status").annotate(total=Count("id")).order_by()
    }
    counts = [
        (status, label, totals_by_status.get(status, 0))
        for status, label in OperationalTask.Status.choices
    ]
    return counts, sum(totals_by_status.values())
