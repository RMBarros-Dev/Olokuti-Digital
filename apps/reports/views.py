from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Product
from config.csv import build_csv_response

from .forms import ReportFilterForm
from .selectors import filter_tasks_for_report, summarize_task_counts


@permission_required(
    ["operations.view_operationaltask", "catalog.view_product"], raise_exception=True
)
def summary(request):
    form = ReportFilterForm(request.GET)
    tasks = filter_tasks_for_report(form, has_query_params=bool(request.GET))
    counts, task_total = summarize_task_counts(tasks)
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
    form = ReportFilterForm(request.GET)
    tasks = filter_tasks_for_report(form, has_query_params=bool(request.GET))
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

    headers = [_("Title"), _("Status"), _("Priority"), _("Due date"), _("Product")]
    rows = (
        [
            task.title,
            task.get_status_display(),
            task.get_priority_display(),
            task.due_date or "",
            task.product.name if task.product else "",
        ]
        for task in tasks.iterator(chunk_size=200)
    )
    return build_csv_response("olokuti-task-report.csv", headers, rows)
