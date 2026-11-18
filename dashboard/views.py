"""Mosque dashboard: a simple Arabic/English workspace for staff."""

from django.contrib import messages
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth import logout as auth_logout
from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, Sum, Value, When
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from announcements.models import Announcement

from .decorators import staff_required
from .forms import (
    AnnouncementForm,
    DashboardAuthenticationForm,
    DashboardPasswordChangeForm,
)

PER_PAGE = 12


def _valid_choice(value, choices):
    allowed = {choice for choice, _label in choices}
    return value if value in allowed else ""


def _safe_redirect(request, fallback):
    """Return to the page the action came from, without open redirects."""
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return HttpResponseRedirect(target)
    return redirect(fallback)


class DashboardLoginView(LoginView):
    template_name = "dashboard/login.html"
    form_class = DashboardAuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = self.get_redirect_url()
        context["redirect_field_name"] = self.redirect_field_name
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Welcome back."))
        return response


class DashboardPasswordChangeView(PasswordChangeView):
    template_name = "dashboard/password_change.html"
    form_class = DashboardPasswordChangeForm
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Your password has been changed."))
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active"] = "password"
        return context


@require_POST
def logout_view(request):
    auth_logout(request)
    messages.success(request, _("You have been signed out."))
    return redirect("dashboard:login")


@staff_required
def home(request):
    announcements = Announcement.objects.all()

    stats = {
        "total": announcements.count(),
        "published": announcements.filter(is_published=True).count(),
        "drafts": announcements.filter(is_published=False).count(),
        "open": announcements.filter(status=Announcement.Status.OPEN).count(),
        "fulfilled": announcements.filter(
            status=Announcement.Status.FULFILLED
        ).count(),
        "people": announcements.filter(type=Announcement.Type.PERSON).count(),
        "mosque": announcements.filter(type=Announcement.Type.MOSQUE).count(),
    }

    totals = (
        announcements.exclude(goal_amount__isnull=True)
        .values("currency")
        .annotate(goal=Sum("goal_amount"), raised=Sum("raised_amount"))
        .order_by("-goal")
    )

    recent = announcements.select_related("created_by").order_by("-updated_at")[:6]

    return render(
        request,
        "dashboard/home.html",
        {
            "active": "home",
            "stats": stats,
            "totals": totals,
            "recent": recent,
        },
    )


@staff_required
def announcement_list(request):
    query = request.GET.get("q", "").strip()
    type_filter = _valid_choice(request.GET.get("type", ""), Announcement.Type.choices)
    category_filter = _valid_choice(
        request.GET.get("category", ""), Announcement.Category.choices
    )
    status_filter = _valid_choice(
        request.GET.get("status", ""), Announcement.Status.choices
    )
    visibility = request.GET.get("visibility", "")
    if visibility not in {"published", "draft"}:
        visibility = ""

    announcements = Announcement.objects.select_related("created_by")

    if query:
        announcements = announcements.filter(
            Q(title_ar__icontains=query)
            | Q(title_en__icontains=query)
            | Q(description_ar__icontains=query)
            | Q(description_en__icontains=query)
            | Q(beneficiary_name__icontains=query)
            | Q(city__icontains=query)
            | Q(country__icontains=query)
        )
    if type_filter:
        announcements = announcements.filter(type=type_filter)
    if category_filter:
        announcements = announcements.filter(category=category_filter)
    if status_filter:
        announcements = announcements.filter(status=status_filter)
    if visibility == "published":
        announcements = announcements.filter(is_published=True)
    elif visibility == "draft":
        announcements = announcements.filter(is_published=False)

    announcements = announcements.annotate(
        open_first=Case(
            When(status=Announcement.Status.OPEN, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by("open_first", "-updated_at")

    paginator = Paginator(announcements, PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    page_range = (
        paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1)
        if paginator.num_pages > 1
        else []
    )

    params = request.GET.copy()
    params.pop("page", None)
    querystring = params.urlencode()

    return render(
        request,
        "dashboard/list.html",
        {
            "active": "announcements",
            "page_obj": page_obj,
            "page_range": page_range,
            "total": paginator.count,
            "query": query,
            "type_filter": type_filter,
            "category_filter": category_filter,
            "status_filter": status_filter,
            "visibility": visibility,
            "type_choices": Announcement.Type.choices,
            "category_choices": Announcement.Category.choices,
            "status_choices": Announcement.Status.choices,
            "querystring": querystring,
            "has_filters": any(
                [query, type_filter, category_filter, status_filter, visibility]
            ),
        },
    )


@staff_required
def announcement_create(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            messages.success(request, _("Announcement created."))
            if "_add_another" in request.POST:
                return redirect("dashboard:create")
            return redirect("dashboard:edit", pk=announcement.pk)
    else:
        form = AnnouncementForm()

    return render(
        request,
        "dashboard/form.html",
        {"active": "announcements", "form": form, "is_create": True},
    )


@staff_required
def announcement_edit(request, pk):
    # The phone, a second staff member or the Back button can open the editor
    # of an announcement that was deleted meanwhile. Show the list with a
    # message instead of an unstyled 404 page.
    announcement = Announcement.objects.filter(pk=pk).first()

    if announcement is None:
        messages.info(request, _("This announcement no longer exists."))
        return _safe_redirect(request, "dashboard:list")

    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, _("Announcement saved."))
            if "_add_another" in request.POST:
                return redirect("dashboard:create")
            return redirect("dashboard:edit", pk=announcement.pk)
    else:
        form = AnnouncementForm(instance=announcement)

    return render(
        request,
        "dashboard/form.html",
        {
            "active": "announcements",
            "form": form,
            "announcement": announcement,
            "is_create": False,
        },
    )


@staff_required
@require_POST
def announcement_toggle_publish(request, pk):
    announcement = Announcement.objects.filter(pk=pk).first()

    if announcement is None:
        messages.info(request, _("This announcement no longer exists."))
        return _safe_redirect(request, "dashboard:list")

    announcement.is_published = not announcement.is_published
    announcement.save(update_fields=["is_published", "updated_at"])

    if announcement.is_published:
        messages.success(request, _("Announcement published."))
    else:
        messages.success(request, _("Announcement hidden from the public site."))

    return _safe_redirect(request, "dashboard:list")


@staff_required
@require_POST
def announcement_delete(request, pk):
    # A stale list (or the browser Back button on the edit page) can post the
    # id of an announcement that was just deleted. Treat that as a no-op with a
    # clear message instead of showing a 404 page.
    announcement = Announcement.objects.filter(pk=pk).first()

    if announcement is None:
        messages.info(request, _("This announcement no longer exists."))
        return _safe_redirect(request, "dashboard:list")

    if not request.user.is_superuser:
        messages.error(request, _("Only a superuser can delete an announcement."))
        return redirect("dashboard:edit", pk=announcement.pk)

    announcement.delete()
    messages.success(request, _("Announcement deleted."))
    return _safe_redirect(request, "dashboard:list")


@staff_required
@require_POST
def announcement_bulk_action(request):
    action = request.POST.get("action", "")
    selected = request.POST.getlist("selected")

    if not selected:
        messages.warning(request, _("Select at least one announcement."))
        return _safe_redirect(request, "dashboard:list")

    announcements = Announcement.objects.filter(pk__in=selected)
    now = timezone.now()

    if action == "publish":
        count = announcements.update(is_published=True, updated_at=now)
        messages.success(request, _("Announcements published: %(count)s") % {"count": count})
    elif action == "hide":
        count = announcements.update(is_published=False, updated_at=now)
        messages.success(request, _("Announcements hidden: %(count)s") % {"count": count})
    elif action == "fulfil":
        count = announcements.update(
            status=Announcement.Status.FULFILLED, updated_at=now
        )
        messages.success(
            request,
            _("Announcements marked as fulfilled: %(count)s") % {"count": count},
        )
    elif action == "open":
        count = announcements.update(status=Announcement.Status.OPEN, updated_at=now)
        messages.success(
            request,
            _("Announcements marked as open: %(count)s") % {"count": count},
        )
    else:
        messages.error(request, _("Unknown action."))

    return _safe_redirect(request, "dashboard:list")
