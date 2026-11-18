"""Access control helpers for the mosque dashboard."""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def staff_required(view_func):
    """Require a signed-in staff member; hide the page from everyone else.

    Anonymous visitors are sent to the dashboard login page, while signed-in
    users without staff rights get a 403 instead of a confusing redirect loop.
    """

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied(
                "This area is reserved for the mosque staff."
            )
        return view_func(request, *args, **kwargs)

    return wrapper
