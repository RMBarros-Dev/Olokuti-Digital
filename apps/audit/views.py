from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.shortcuts import render

from .models import AuditLog


@permission_required("audit.view_auditlog", raise_exception=True)
def audit_list(request):
    events = AuditLog.objects.select_related("user").all()
    entity = request.GET.get("entity", "").strip()
    action = request.GET.get("action", "").strip()
    if entity:
        events = events.filter(entity__icontains=entity)
    if action:
        events = events.filter(action=action)
    page = Paginator(events, 25).get_page(request.GET.get("page"))
    actions = AuditLog.objects.order_by().values_list("action", flat=True).distinct()
    template = (
        "audit/_audit_table.html"
        if request.headers.get("HX-Request") == "true"
        else "audit/audit_list.html"
    )
    return render(
        request,
        template,
        {"events": page, "actions": actions, "selected_action": action, "entity_query": entity},
    )
