"""Small template helpers: inline SVG icons and a few formatting filters."""

import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.urls import translate_url
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def vstatic(path):
    """Static URL with a version stamp so phones do not keep old CSS/JS.

    The browser caches static files aggressively. When a stylesheet changes,
    a phone can keep the previous copy and show a broken layout until the
    cache is cleared by hand. The file modification time makes the URL change
    whenever the file does.
    """
    url = static(path)
    found = finders.find(path)
    if not found:
        return url
    try:
        version = int(os.path.getmtime(found))
    except OSError:
        return url
    return f"{url}?v={version}"


@register.simple_tag(takes_context=True)
def lang_url(context, language):
    """Return the current page URL in another language (used by the switcher)."""
    request = context.get("request")
    if request is None:
        return ""
    try:
        return translate_url(request.get_full_path(), language)
    except Exception:
        # On error pages the current path may not be reversible.
        return request.path

ICONS = {
    "mosque": (
        '<path d="M3 21h18"/><path d="M5 21v-8"/><path d="M19 21v-8"/>'
        '<path d="M7 21v-5a5 5 0 0 1 10 0v5"/><path d="M12 11V8"/>'
        '<path d="M10.5 8a1.5 1.5 0 0 1 3 0"/>'
        '<path d="M10 21v-4a2 2 0 0 1 4 0v4"/>'
    ),
    "heart": (
        '<path d="M12 20.5s-7.5-4.7-7.5-10.3A4.2 4.2 0 0 1 12 7.4'
        'a4.2 4.2 0 0 1 7.5 2.8c0 5.6-7.5 10.3-7.5 10.3z"/>'
    ),
    "arrow-right": '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    "arrow-left": '<path d="M19 12H5"/><path d="m11 18-6-6 6-6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.2-3.2"/>',
    "map-pin": (
        '<path d="M12 21s-6.5-5.4-6.5-10a6.5 6.5 0 0 1 13 0c0 4.6-6.5 10-6.5 10z"/>'
        '<circle cx="12" cy="11" r="2.4"/>'
    ),
    "calendar": (
        '<rect x="3" y="5" width="18" height="16" rx="3"/>'
        '<path d="M8 3v4"/><path d="M16 3v4"/><path d="M3 10h18"/>'
    ),
    "phone": (
        '<path d="M6.6 3h2.2l1.6 4-2 1.3a12.5 12.5 0 0 0 6.3 6.3l1.3-2 '
        '4 1.6v2.2A2.6 2.6 0 0 1 17.4 19 14.4 14.4 0 0 1 5 6.6 2.6 2.6 0 0 1 6.6 3z"/>'
    ),
    "mail": (
        '<rect x="3" y="5" width="18" height="14" rx="3"/>'
        '<path d="m4 7 8 6 8-6"/>'
    ),
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "check-circle": (
        '<circle cx="12" cy="12" r="9"/><path d="m8.5 12.5 2.5 2.5 4.5-5"/>'
    ),
    "users": (
        '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 20a5.5 5.5 0 0 1 11 0"/>'
        '<path d="M16 5.2a3.2 3.2 0 0 1 0 5.6"/>'
        '<path d="M17.5 14.5A5.5 5.5 0 0 1 20.5 20"/>'
    ),
    "wallet": (
        '<path d="M4 8a2.5 2.5 0 0 1 2.5-2.5H18a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H6.5A2.5 2.5 0 0 1 4 17.5z"/>'
        '<path d="M4 8h16"/><circle cx="16.5" cy="13" r="1.2"/>'
    ),
    "share": (
        '<circle cx="18" cy="5" r="2.5"/><circle cx="6" cy="12" r="2.5"/>'
        '<circle cx="18" cy="19" r="2.5"/>'
        '<path d="m8.2 10.8 7.6-4.4"/><path d="m8.2 13.2 7.6 4.4"/>'
    ),
    "link": (
        '<path d="M10 13a5 5 0 0 0 7.5.5l2-2a5 5 0 0 0-7-7l-1.2 1.2"/>'
        '<path d="M14 11a5 5 0 0 0-7.5-.5l-2 2a5 5 0 0 0 7 7l1.2-1.2"/>'
    ),
    "external": (
        '<path d="M14 4h6v6"/><path d="M20 4 11 13"/>'
        '<path d="M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"/>'
    ),
    "image": (
        '<rect x="3" y="4" width="18" height="16" rx="3"/>'
        '<circle cx="8.5" cy="9.5" r="1.6"/>'
        '<path d="m4 17 4.5-4.5a2 2 0 0 1 3 0L15 16"/>'
        '<path d="m13 14 1.5-1.5a2 2 0 0 1 3 0L20 15"/>'
    ),
    "copy": (
        '<rect x="9" y="9" width="11" height="11" rx="2"/>'
        '<path d="M5 15V6a2 2 0 0 1 2-2h9"/>'
    ),
    "menu": '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
    "close": '<path d="M6 6l12 12"/><path d="M18 6 6 18"/>',
    "shield": (
        '<path d="M12 3 5 6v5.5c0 4.4 3 7.6 7 9.5 4-1.9 7-5.1 7-9.5V6z"/>'
        '<path d="m9 12 2 2 4-4"/>'
    ),
    "filter": '<path d="M4 6h16"/><path d="M7 12h10"/><path d="M10 18h4"/>',
    "inbox": (
        '<path d="M4 13h4l1.5 2h5L16 13h4"/>'
        '<path d="M5.5 5h13l2.5 8v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4z"/>'
    ),
    "eye": (
        '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
    "globe": (
        '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/>'
        '<path d="M12 3a15 15 0 0 1 0 18a15 15 0 0 1 0-18z"/>'
    ),
    "sparkle": (
        '<path d="M12 3v4"/><path d="M12 17v4"/><path d="M3 12h4"/>'
        '<path d="M17 12h4"/><path d="m6 6 2.5 2.5"/><path d="m15.5 15.5 2.5 2.5"/>'
        '<path d="m18 6-2.5 2.5"/><path d="m8.5 15.5-2.5 2.5"/>'
    ),
    "quote": (
        '<path d="M4 11h5v5a5 5 0 0 1-5 5"/>'
        '<path d="M15 11h5v5a5 5 0 0 1-5 5"/>'
    ),
    "plus": '<path d="M12 5v14"/><path d="M5 12h14"/>',
    "pencil": (
        '<path d="M4 20h4L18.5 9.5a2.5 2.5 0 0 0-3.5-3.5L4.5 16.5z"/>'
        '<path d="m13.5 6.5 3.5 3.5"/>'
    ),
    "trash": (
        '<path d="M4 7h16"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/>'
        '<path d="m6.5 7 1 13h9l1-13"/><path d="M10 11v6"/><path d="M14 11v6"/>'
    ),
    "logout": (
        '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/>'
        '<path d="m10 17-5-5 5-5"/><path d="M5 12h10"/>'
    ),
    "grid": (
        '<rect x="3" y="3" width="7" height="7" rx="1.5"/>'
        '<rect x="14" y="3" width="7" height="7" rx="1.5"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1.5"/>'
        '<rect x="14" y="14" width="7" height="7" rx="1.5"/>'
    ),
    "megaphone": (
        '<path d="M4 10v4a1 1 0 0 0 1 1h2l7 4V5L7 9H5a1 1 0 0 0-1 1z"/>'
        '<path d="M18 9a4 4 0 0 1 0 6"/>'
    ),
    "lock": (
        '<rect x="4" y="10" width="16" height="10" rx="2.5"/>'
        '<path d="M8 10V7a4 4 0 0 1 8 0v3"/>'
    ),
    "chart": (
        '<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/>'
        '<path d="M22 20H2"/>'
    ),
}


@register.filter
def money(value):
    """Format an amount with thousands separators and no decimals.

    Uses Western digits and commas in both languages, which is the common
    convention for prices in Arabic-language websites.
    """
    try:
        return f"{int(round(float(value))):,}"
    except (TypeError, ValueError):
        return value


@register.simple_tag
def icon(name, css_class="icon"):
    body = ICONS.get(name)
    if not body:
        return ""
    return format_html(
        '<svg class="{}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true" focusable="false">{}</svg>',
        css_class,
        mark_safe(body),
    )
