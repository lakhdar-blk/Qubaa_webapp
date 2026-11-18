from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _


def default_currency():
    """Return the currency configured by the administrator."""
    return getattr(settings, "DEFAULT_CURRENCY", "EUR")


class Announcement(models.Model):
    """A need (for a person or for the mosque) published by the mosque."""

    class Type(models.TextChoices):
        PERSON = "person", _("A person")
        MOSQUE = "mosque", _("The mosque")

    class Category(models.TextChoices):
        FOOD = "food", _("Food")
        CLOTHING = "clothing", _("Clothing")
        MEDICAL = "medical", _("Medical")
        EDUCATION = "education", _("Education")
        HOUSING = "housing", _("Housing")
        MOSQUE_MAINTENANCE = "mosque_maintenance", _("Mosque maintenance")
        QURAN = "quran", _("Quran & teaching")
        RAMADAN = "ramadan", _("Ramadan")
        ORPHANS = "orphans", _("Widows & orphans")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        FULFILLED = "fulfilled", _("Fulfilled")
        CLOSED = "closed", _("Closed")

    class Currency(models.TextChoices):
        EUR = "EUR", _("Euro (EUR)")
        USD = "USD", _("US Dollar (USD)")
        MAD = "MAD", _("Moroccan Dirham (MAD)")
        DZD = "DZD", _("Algerian Dinar (DZD)")
        TND = "TND", _("Tunisian Dinar (TND)")
        EGP = "EGP", _("Egyptian Pound (EGP)")
        SAR = "SAR", _("Saudi Riyal (SAR)")
        AED = "AED", _("UAE Dirham (AED)")
        GBP = "GBP", _("British Pound (GBP)")

    type = models.CharField(
        _("type"), max_length=10, choices=Type.choices, default=Type.PERSON
    )
    category = models.CharField(
        _("category"), max_length=32, choices=Category.choices, default=Category.OTHER
    )

    title_ar = models.CharField(_("title (Arabic)"), max_length=200, blank=True)
    title_en = models.CharField(_("title (English)"), max_length=200, blank=True)
    description_ar = models.TextField(_("description (Arabic)"), blank=True)
    description_en = models.TextField(_("description (English)"), blank=True)

    beneficiary_name = models.CharField(
        _("beneficiary name"), max_length=160, blank=True
    )
    city = models.CharField(_("city"), max_length=120, blank=True)
    country = models.CharField(_("country"), max_length=120, blank=True)

    goal_amount = models.DecimalField(
        _("goal amount"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
        help_text=_("Leave empty if no specific amount is needed."),
    )
    raised_amount = models.DecimalField(
        _("amount raised"),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
        help_text=_("Amount already collected, if any."),
    )
    currency = models.CharField(
        _("currency"),
        max_length=3,
        choices=Currency.choices,
        default=default_currency,
    )

    image_url = models.URLField(
        _("image URL"),
        max_length=500,
        blank=True,
        help_text=_("Paste a link to an image starting with https://"),
    )

    contact_name = models.CharField(_("contact name"), max_length=160, blank=True)
    contact_address = models.CharField(
        _("contact address"),
        max_length=200,
        blank=True,
        help_text=_(
            "Address of the person responsible for this announcement. "
            "Leave empty to show the mosque address instead."
        ),
    )
    contact_phone = models.CharField(_("contact phone"), max_length=60, blank=True)
    contact_email = models.EmailField(_("contact email"), blank=True)

    status = models.CharField(
        _("status"), max_length=12, choices=Status.choices, default=Status.OPEN
    )
    is_published = models.BooleanField(
        _("published"),
        default=True,
        help_text=_("Only published announcements are visible on the website."),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="announcements",
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("announcement")
        verbose_name_plural = _("announcements")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["is_published", "status", "-created_at"],
                name="ann_pub_status_idx",
            ),
            models.Index(fields=["type"], name="ann_type_idx"),
            models.Index(fields=["category"], name="ann_category_idx"),
        ]

    def __str__(self):
        title = self.title
        if title:
            return title
        return _("Announcement #%(pk)s") % {"pk": self.pk}

    def clean(self):
        super().clean()
        errors = {}

        if not (self.title_ar or "").strip() and not (self.title_en or "").strip():
            errors["title_ar"] = _("Provide a title in at least one language.")
            errors["title_en"] = _("Provide a title in at least one language.")

        if not (self.description_ar or "").strip() and not (
            self.description_en or ""
        ).strip():
            errors["description_ar"] = _(
                "Provide a description in at least one language."
            )
            errors["description_en"] = _(
                "Provide a description in at least one language."
            )

        if self.goal_amount is not None and self.goal_amount < 0:
            errors["goal_amount"] = _("The amount cannot be negative.")
        if self.raised_amount is not None and self.raised_amount < 0:
            errors["raised_amount"] = _("The amount cannot be negative.")

        if self.contact_email and "@" not in self.contact_email:
            errors["contact_email"] = _("Enter a valid email address.")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Keep amounts clean even when the object is saved programmatically.
        if self.raised_amount is None:
            self.raised_amount = Decimal("0")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("announcements:detail", args=[self.pk])

    def _localized(self, field):
        """Return the field in the active language, falling back to the other."""
        language = (get_language() or settings.LANGUAGE_CODE).split("-")[0]
        value = (getattr(self, f"{field}_{language}", "") or "").strip()
        if not value:
            fallback = "en" if language == "ar" else "ar"
            value = (getattr(self, f"{field}_{fallback}", "") or "").strip()
        return value

    @property
    def title(self):
        return self._localized("title")

    @property
    def description(self):
        return self._localized("description")

    @property
    def has_goal(self):
        return self.goal_amount is not None and self.goal_amount > 0

    @property
    def progress_percent(self):
        if not self.has_goal:
            return 0
        raised = self.raised_amount or Decimal("0")
        percent = int(raised * 100 / self.goal_amount)
        return max(0, min(100, percent))

    @property
    def remaining_amount(self):
        if not self.has_goal:
            return Decimal("0")
        return max(Decimal("0"), self.goal_amount - (self.raised_amount or Decimal("0")))

    @property
    def location(self):
        parts = [part.strip() for part in (self.city, self.country) if part and part.strip()]
        return ", ".join(parts)

    @property
    def is_open(self):
        return self.status == self.Status.OPEN
