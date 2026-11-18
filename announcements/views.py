from django.conf import settings
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.db import connection

from .models import Announcement

PER_PAGE = 9


def _valid_choice(value, choices):
    allowed = {choice for choice, _label in choices}
    return value if value in allowed else ""


def home(request):
    published = Announcement.objects.filter(is_published=True)

    latest = published.order_by("-created_at")[:6]

    stats = {
        "published": published.count(),
        "open": published.filter(status=Announcement.Status.OPEN).count(),
        "person": published.filter(type=Announcement.Type.PERSON).count(),
        "mosque": published.filter(type=Announcement.Type.MOSQUE).count(),
    }

    return render(
        request,
        "home.html",
        {"latest": latest, "stats": stats, "active": "home"},
    )


def announcement_list(request):
    query = request.GET.get("q", "").strip()
    type_filter = _valid_choice(request.GET.get("type", ""), Announcement.Type.choices)
    category_filter = _valid_choice(
        request.GET.get("category", ""), Announcement.Category.choices
    )
    status_filter = _valid_choice(
        request.GET.get("status", ""), Announcement.Status.choices
    )

    announcements = Announcement.objects.filter(is_published=True)

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

    announcements = announcements.annotate(
        open_first=Case(
            When(status=Announcement.Status.OPEN, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by("open_first", "-created_at")

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

    context = {
        "page_obj": page_obj,
        "page_range": page_range,
        "total": paginator.count,
        "query": query,
        "type_filter": type_filter,
        "category_filter": category_filter,
        "status_filter": status_filter,
        "type_choices": Announcement.Type.choices,
        "category_choices": Announcement.Category.choices,
        "status_choices": Announcement.Status.choices,
        "querystring": querystring,
        "has_filters": any(
            [query, type_filter, category_filter, status_filter]
        ),
        "active": "announcements",
    }
    return render(request, "announcements/list.html", context)


def announcement_detail(request, pk):
    announcement = get_object_or_404(
        Announcement.objects.filter(is_published=True), pk=pk
    )

    related = (
        Announcement.objects.filter(is_published=True)
        .exclude(pk=announcement.pk)
        .filter(
            Q(category=announcement.category) | Q(type=announcement.type)
        )
        .order_by("-created_at")[:3]
    )

    return render(
        request,
        "announcements/detail.html",
        {
            "announcement": announcement,
            "related": related,
            "active": "announcements",
        },
    )


def about(request):
    return render(request, "pages/about.html", {"active": "about"})


def healthz(request):
    """Lightweight health check used by Render."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse(
            {"status": "error", "database": "unavailable"}, status=503
        )
    return JsonResponse({"status": "ok"})


def robots_txt(request):
    """Keep search engines out of the private areas."""
    lines = [
        "User-agent: *",
        "Disallow: /ar/dashboard/",
        "Disallow: /en/dashboard/",
        "Disallow: /admin/",
        "Disallow: /i18n/",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
