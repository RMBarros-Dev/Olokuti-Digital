from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.shortcuts import render

from .selectors import filter_audit_events, get_distinct_audit_actions


@permission_required("audit.view_auditlog", raise_exception=True)
def audit_list(request):
    entity = request.GET.get("entity", "").strip()
    action = request.GET.get("action", "").strip()
    events = filter_audit_events(entity=entity, action=action)
    page = Paginator(events, 25).get_page(request.GET.get("page"))
    actions = get_distinct_audit_actions()
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
