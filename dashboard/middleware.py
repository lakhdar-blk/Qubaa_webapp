"""Middleware specific to the staff dashboard."""


class DashboardNoStoreMiddleware:
    """Keep dashboard pages out of the browser cache.

    Phones hold on to pages for a long time: an old copy of the announcement
    list or of the editor can be restored from the cache or from the
    back-forward cache, showing a stale layout, a stale row, or no
    confirmation message after an action. ``no-store`` forces a fresh request
    every time, so the page always reflects what is really in the database.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if self._is_dashboard(request):
            response["Cache-Control"] = "no-store"
            response["Pragma"] = "no-cache"

        return response

    @staticmethod
    def _is_dashboard(request):
        match = getattr(request, "resolver_match", None)
        return bool(match and match.app_name == "dashboard")
