"""Forms used by the mosque dashboard."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils.translation import gettext_lazy as _

from announcements.models import Announcement


class DashboardAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label=_("Email or username"),
        widget=forms.TextInput(
            attrs={
                "autofocus": True,
                "autocomplete": "username",
                "class": "input",
                "placeholder": "admin@example.org",
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "class": "input"}
        ),
    )

    error_messages = {
        "invalid_login": _(
            "The email or password is incorrect. Please try again."
        ),
        "inactive": _("This account is disabled."),
    }


class DashboardPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class AnnouncementForm(forms.ModelForm):
    """Bilingual announcement form with a comfortable admin layout."""

    class Meta:
        model = Announcement
        fields = (
            "type",
            "category",
            "status",
            "is_published",
            "title_ar",
            "title_en",
            "description_ar",
            "description_en",
            "beneficiary_name",
            "city",
            "country",
            "goal_amount",
            "raised_amount",
            "currency",
            "image_url",
            "contact_name",
            "contact_address",
            "contact_phone",
            "contact_email",
        )
        widgets = {
            "type": forms.Select(attrs={"class": "input"}),
            "category": forms.Select(attrs={"class": "input"}),
            "status": forms.Select(attrs={"class": "input"}),
            "is_published": forms.CheckboxInput(attrs={"class": "checkbox"}),
            "title_ar": forms.TextInput(
                attrs={
                    "class": "input",
                    "dir": "rtl",
                    "lang": "ar",
                    "maxlength": 200,
                    "data-counter": "200",
                }
            ),
            "title_en": forms.TextInput(
                attrs={
                    "class": "input",
                    "dir": "ltr",
                    "lang": "en",
                    "maxlength": 200,
                    "data-counter": "200",
                }
            ),
            "description_ar": forms.Textarea(
                attrs={"class": "input textarea", "rows": 6, "dir": "rtl", "lang": "ar"}
            ),
            "description_en": forms.Textarea(
                attrs={"class": "input textarea", "rows": 6, "dir": "ltr", "lang": "en"}
            ),
            "beneficiary_name": forms.TextInput(attrs={"class": "input"}),
            "city": forms.TextInput(attrs={"class": "input"}),
            "country": forms.TextInput(attrs={"class": "input"}),
            "goal_amount": forms.NumberInput(
                attrs={
                    "class": "input",
                    "step": "0.01",
                    "min": "0",
                    "inputmode": "decimal",
                }
            ),
            "raised_amount": forms.NumberInput(
                attrs={
                    "class": "input",
                    "step": "0.01",
                    "min": "0",
                    "inputmode": "decimal",
                }
            ),
            "currency": forms.Select(attrs={"class": "input"}),
            "image_url": forms.URLInput(
                attrs={
                    "class": "input",
                    "placeholder": "https://…",
                    "data-image-input": "",
                }
            ),
            "contact_name": forms.TextInput(attrs={"class": "input"}),
            "contact_address": forms.TextInput(
                attrs={"class": "input", "autocomplete": "street-address"}
            ),
            "contact_phone": forms.TextInput(
                attrs={"class": "input", "dir": "ltr", "inputmode": "tel"}
            ),
            "contact_email": forms.EmailInput(
                attrs={"class": "input", "dir": "ltr"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title_en"].help_text = _(
            "Leave empty to show the Arabic title on the English site too."
        )
        self.fields["description_en"].help_text = _(
            "Leave empty to show the Arabic description on the English site too."
        )
        self.fields["title_ar"].help_text = _(
            "Leave empty to show the English title on the Arabic site too."
        )
        self.fields["description_ar"].help_text = _(
            "Leave empty to show the English description on the Arabic site too."
        )
        self.fields["raised_amount"].help_text = _(
            "Update this amount to keep the progress bar accurate."
        )
