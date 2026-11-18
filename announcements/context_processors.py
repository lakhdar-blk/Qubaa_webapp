from django.conf import settings
from django.utils import timezone
from django.utils.translation import get_language


def site(request):
    """Expose mosque identity and contact details to every template."""
    language = (get_language() or settings.LANGUAGE_CODE).split("-")[0]

    if language == "en":
        name = settings.SITE_NAME_EN
        tagline = settings.SITE_TAGLINE_EN
        address = settings.CONTACT_ADDRESS_EN
    else:
        name = settings.SITE_NAME_AR
        tagline = settings.SITE_TAGLINE_AR
        address = settings.CONTACT_ADDRESS_AR

    return {
        "SITE_NAME": name or settings.SITE_NAME_EN,
        "SITE_TAGLINE": tagline,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "CONTACT_PHONE": settings.CONTACT_PHONE,
        "CONTACT_ADDRESS": address,
        "CURRENT_YEAR": timezone.now().year,
        "IS_RTL": language == "ar",
    }
