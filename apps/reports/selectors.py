from datetime import datetime, time

from django.db.models import Count, F, Q, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.inventory.models import StockItem, StockLocation
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


def summarize_collaborator_activity(tasks) -> list[dict]:
    """Aggregate task workload and completion metrics per assigned collaborator."""
    today = timezone.localdate()
    open_statuses = [OperationalTask.Status.TODO, OperationalTask.Status.IN_PROGRESS]
    rows = (
        tasks.values("assigned_to__username")
        .annotate(
            total=Count("id"),
            done=Count("id", filter=Q(status=OperationalTask.Status.DONE)),
            open_count=Count("id", filter=Q(status__in=open_statuses)),
            overdue=Count("id", filter=Q(status__in=open_statuses, due_date__lt=today)),
        )
        .order_by("-total", "assigned_to__username")
    )
    return [
        {
            "username": row["assigned_to__username"] or _("Unassigned"),
            "total": row["total"],
            "done": row["done"],
            "open_count": row["open_count"],
            "overdue": row["overdue"],
        }
        for row in rows
    ]


def summarize_inventory_metrics() -> dict:
    """Aggregate active inventory quantities, low-stock alerts, and per-location totals."""
    active_items = StockItem.objects.active()
    totals = active_items.aggregate(
        item_count=Count("id"),
        total_units=Sum("quantity"),
        low_stock_count=Count("id", filter=Q(quantity__lte=F("minimum_stock"))),
    )
    by_location = list(
        active_items.values("location__name", "location__code")
        .annotate(
            item_count=Count("id"),
            total_units=Sum("quantity"),
            low_stock_count=Count("id", filter=Q(quantity__lte=F("minimum_stock"))),
        )
        .order_by("location__name")
    )
    return {
        "location_count": StockLocation.objects.filter(is_active=True).count(),
        "item_count": totals["item_count"] or 0,
        "total_units": totals["total_units"] or 0,
        "low_stock_count": totals["low_stock_count"] or 0,
        "by_location": by_location,
    }
