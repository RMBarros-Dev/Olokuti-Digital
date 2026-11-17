import logging

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.db import DatabaseError, connection
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import include, path
from django.utils.translation import get_language

from apps.accounts.ratelimit import check_rate_limit, rate_limit_response

logger = logging.getLogger(__name__)


def root_redirect(request):
    return HttpResponseRedirect(f"/{get_language()}/")


def health_check(request):
    if request.GET.get("db") == "1":
        blocked, retry_after = check_rate_limit(
            request,
            "health_db",
            limit=settings.RATE_LIMIT_HEALTH_DB_MAX,
            window_seconds=settings.RATE_LIMIT_HEALTH_DB_WINDOW,
        )
        if blocked:
            return rate_limit_response(retry_after)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except DatabaseError:
            logger.warning("Database health check failed")
            return HttpResponse("unavailable", status=503, content_type="text/plain")
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("health", health_check, name="health_check"),
    path("", root_redirect, name="root"),
    path("i18n/", include("django.conf.urls.i18n")),
]
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("operations/", include("apps.operations.urls")),
    path("reports/", include("apps.reports.urls")),
    path("audit/", include("apps.audit.urls")),
    prefix_default_language=True,
)
