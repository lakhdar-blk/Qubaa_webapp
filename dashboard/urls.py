from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.DashboardLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("password/", views.DashboardPasswordChangeView.as_view(), name="password_change"),
    path("announcements/", views.announcement_list, name="list"),
    path("announcements/new/", views.announcement_create, name="create"),
    path("announcements/actions/", views.announcement_bulk_action, name="bulk_action"),
    path("announcements/<int:pk>/", views.announcement_edit, name="edit"),
    path("announcements/<int:pk>/delete/", views.announcement_delete, name="delete"),
    path(
        "announcements/<int:pk>/publish/",
        views.announcement_toggle_publish,
        name="toggle_publish",
    ),
]
