from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import include, path
from django.utils.translation import get_language


def root_redirect(request):
    return HttpResponseRedirect(f"/{get_language()}/")


urlpatterns = [
    path("", root_redirect, name="root"),
    path("i18n/", include("django.conf.urls.i18n")),
]
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("operations/", include("apps.operations.urls")),
    path("reports/", include("apps.reports.urls")),
    path("audit/", include("apps.audit.urls")),
    prefix_default_language=True,
)
