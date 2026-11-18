from django.apps import AppConfig
from django.db import connection
from django.db.backends.signals import connection_created
from django.utils.translation import gettext_lazy as _


def _enable_sqlite_wal(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA busy_timeout=30000;")


class AnnouncementsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "announcements"
    verbose_name = _("Announcements")

    def ready(self):
        connection_created.connect(_enable_sqlite_wal)
