import csv
from datetime import datetime, time

from django.contrib.auth.decorators import permission_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Product
from apps.operations.models import OperationalTask

from .forms import ReportFilterForm


def _filtered_tasks(request):
    form = ReportFilterForm(request.GET)
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
    elif request.GET:
        tasks = tasks.none()
    return form, tasks


@permission_required(
    ["operations.view_operationaltask", "catalog.view_product"], raise_exception=True
)
def summary(request):
    form, tasks = _filtered_tasks(request)
    totals_by_status = {
        row["status"]: row["total"]
        for row in tasks.values("status").annotate(total=Count("id")).order_by()
    }
    counts = [
        (status, label, totals_by_status.get(status, 0))
        for status, label in OperationalTask.Status.choices
    ]
    task_total = sum(totals_by_status.values())
    context = {
        "form": form,
        "tasks": tasks[:100],
        "task_counts": counts,
        "task_total": task_total,
        "product_count": Product.objects.count(),
    }
    return render(request, "reports/summary.html", context)


@permission_required(
    ["operations.view_operationaltask", "catalog.view_product"], raise_exception=True
)
def export_tasks_csv(request):
    form, tasks = _filtered_tasks(request)
    if not form.is_valid():
        return render(
            request,
            "reports/summary.html",
            {
                "form": form,
                "tasks": [],
                "task_counts": [],
                "task_total": 0,
                "product_count": Product.objects.count(),
            },
            status=400,
        )

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="olokuti-task-report.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow([_("Title"), _("Status"), _("Priority"), _("Due date"), _("Product")])
    for task in tasks.iterator():
        values = [
            task.title,
            task.get_status_display(),
            task.get_priority_display(),
            task.due_date or "",
            task.product.name if task.product else "",
        ]
        writer.writerow([_csv_safe(value) for value in values])
    return response


def _csv_safe(value):
    text = str(value)
    if text[:1] in {"\t", "\r"} or text.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + text
    return text
