from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from announcements import views as site_views

urlpatterns = [
    # Django's language switcher (used by the admin language selector).
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin/", admin.site.urls),
    path("healthz/", site_views.healthz, name="healthz"),
    # Browsers request /favicon.ico by default; point it at the SVG icon.
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/img/favicon.svg", permanent=True),
    ),
    path("robots.txt", site_views.robots_txt, name="robots_txt"),
]

# Public pages live under /ar/... and /en/...
urlpatterns += i18n_patterns(
    path("", include("announcements.urls")),
    path("dashboard/", include("dashboard.urls")),
    prefix_default_language=True,
)
