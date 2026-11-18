from django.urls import path

from . import views

app_name = "announcements"

urlpatterns = [
    path("", views.home, name="home"),
    path("announcements/", views.announcement_list, name="list"),
    path("announcements/<int:pk>/", views.announcement_detail, name="detail"),
    path("about/", views.about, name="about"),
]
