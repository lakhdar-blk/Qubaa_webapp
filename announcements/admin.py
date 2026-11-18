from django.conf import settings
from django.contrib import admin, messages
from django.db import models
from django.forms import Textarea
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Announcement

admin.site.site_header = _("Qubaa Mosque Administration")
admin.site.site_title = _("Qubaa Mosque")
admin.site.index_title = _("Manage announcements")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "display_title",
        "type",
        "category",
        "status",
        "is_published",
        "goal_amount",
        "raised_amount",
        "created_at",
    )
    list_display_links = ("display_title",)
    list_editable = ("is_published",)
    list_filter = ("type", "category", "status", "is_published")
    search_fields = (
        "title_ar",
        "title_en",
        "description_ar",
        "description_en",
        "beneficiary_name",
        "city",
        "country",
        "contact_name",
        "contact_address",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 25
    empty_value_display = "—"

    readonly_fields = ("preview", "created_by", "created_at", "updated_at")

    fieldsets = (
        (
            _("Content"),
            {
                "fields": (
                    "type",
                    "category",
                    "title_ar",
                    "title_en",
                    "description_ar",
                    "description_en",
                )
            },
        ),
        (
            _("Beneficiary & location"),
            {"fields": ("beneficiary_name", "city", "country")},
        ),
        (
            _("Fundraising"),
            {"fields": ("goal_amount", "raised_amount", "currency")},
        ),
        (_("Media"), {"fields": ("image_url", "preview")}),
        (
            _("Contact"),
            {"fields": ("contact_name", "contact_address", "contact_phone", "contact_email")},
        ),
        (
            _("Publication"),
            {
                "fields": (
                    "status",
                    "is_published",
                    "created_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    formfield_overrides = {
        models.TextField: {
            "widget": Textarea(
                attrs={"rows": 5, "class": "vLargeTextField", "dir": "auto"}
            )
        },
    }

    actions = (
        "publish_selected",
        "unpublish_selected",
        "mark_fulfilled",
        "mark_open",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by")

    @admin.display(description=_("Title"))
    def display_title(self, obj):
        title = obj.title
        if title:
            return title
        return _("Announcement #%(pk)s") % {"pk": obj.pk}

    @admin.display(description=_("Preview"))
    def preview(self, obj):
        if obj and obj.image_url:
            return format_html(
                '<img src="{}" alt="" '
                'style="max-width:360px;max-height:220px;border-radius:10px;'
                'object-fit:cover;border:1px solid #ddd">',
                obj.image_url,
            )
        return _("No image")

    def save_model(self, request, obj, form, change):
        if obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def _notify(self, request, count, message):
        self.message_user(
            request,
            message % {"count": count},
            messages.SUCCESS,
        )

    @admin.action(description=_("Publish selected announcements"))
    def publish_selected(self, request, queryset):
        count = queryset.update(is_published=True, updated_at=timezone.now())
        self._notify(request, count, _("Published announcements: %(count)s"))

    @admin.action(description=_("Hide selected announcements"))
    def unpublish_selected(self, request, queryset):
        count = queryset.update(is_published=False, updated_at=timezone.now())
        self._notify(request, count, _("Hidden announcements: %(count)s"))

    @admin.action(description=_("Mark selected announcements as fulfilled"))
    def mark_fulfilled(self, request, queryset):
        count = queryset.update(status=Announcement.Status.FULFILLED, updated_at=timezone.now())
        self._notify(request, count, _("Fulfilled announcements: %(count)s"))

    @admin.action(description=_("Mark selected announcements as open"))
    def mark_open(self, request, queryset):
        count = queryset.update(status=Announcement.Status.OPEN, updated_at=timezone.now())
        self._notify(request, count, _("Open announcements: %(count)s"))
