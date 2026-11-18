"""Tests for the private staff dashboard."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext

from announcements.models import Announcement


def make_announcement(**overrides):
    data = {
        "type": Announcement.Type.PERSON,
        "category": Announcement.Category.FOOD,
        "title_ar": "حاجة إلى مساعدة",
        "title_en": "A need for help",
        "description_ar": "وصف الحاجة.",
        "description_en": "Description of the need.",
        "city": "Rabat",
        "country": "Morocco",
        "goal_amount": Decimal("1000"),
        "raised_amount": Decimal("250"),
        "is_published": True,
    }
    data.update(overrides)
    return Announcement.objects.create(**data)


class DashboardAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="staff@example.org",
            email="staff@example.org",
            password="StaffPass-12345!",
            is_staff=True,
        )
        self.superuser = user_model.objects.create_superuser(
            username="admin@example.org",
            email="admin@example.org",
            password="AdminPass-12345!",
        )
        self.visitor = user_model.objects.create_user(
            username="visitor@example.org",
            email="visitor@example.org",
            password="VisitorPass-12345!",
        )

    def test_anonymous_users_are_sent_to_the_dashboard_login(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertRedirects(
            response,
            f"{reverse('dashboard:login')}?next={reverse('dashboard:home')}",
        )

    def test_non_staff_users_get_a_forbidden_page(self):
        self.client.force_login(self.visitor)

        for name in ("home", "list", "create"):
            with self.subTest(view=name):
                self.assertEqual(self.client.get(reverse(f"dashboard:{name}")).status_code, 403)

    def test_login_page_is_available_in_both_languages(self):
        for language in ("ar", "en"):
            with self.subTest(language=language):
                with translation.override(language):
                    response = self.client.get(reverse("dashboard:login"))

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'name="username"')
                self.assertContains(response, 'name="password"')

    def test_login_uses_the_email_as_the_username(self):
        response = self.client.post(
            reverse("dashboard:login"),
            {"username": "staff@example.org", "password": "StaffPass-12345!"},
        )

        self.assertRedirects(response, reverse("dashboard:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.staff.pk)

    def test_login_rejects_a_bad_password(self):
        response = self.client.post(
            reverse("dashboard:login"),
            {"username": "staff@example.org", "password": "wrong"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_only_accepts_post(self):
        self.client.force_login(self.staff)

        self.assertEqual(self.client.get(reverse("dashboard:logout")).status_code, 405)

        response = self.client.post(reverse("dashboard:logout"))

        self.assertRedirects(response, reverse("dashboard:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_can_change_their_password(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("dashboard:password_change"),
            {
                "old_password": "StaffPass-12345!",
                "new_password1": "BrandNew-12345!",
                "new_password2": "BrandNew-12345!",
            },
        )

        self.assertRedirects(response, reverse("dashboard:home"))
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.check_password("BrandNew-12345!"))


class DashboardPagesTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="staff@example.org",
            email="staff@example.org",
            password="StaffPass-12345!",
            is_staff=True,
        )
        self.announcement = make_announcement(created_by=self.staff)
        self.client.force_login(self.staff)

    def test_dashboard_pages_are_not_cached_by_the_browser(self):
        # A cached copy would hide confirmation messages and show deleted rows
        # on a phone that keeps the tab open.
        response = self.client.get(reverse("dashboard:list"))

        self.assertIn("no-store", response["Cache-Control"])

    def test_pages_render_in_arabic_and_english(self):
        for language in ("ar", "en"):
            with self.subTest(language=language):
                with translation.override(language):
                    urls = [
                        reverse("dashboard:home"),
                        reverse("dashboard:list"),
                        reverse("dashboard:create"),
                        reverse("dashboard:edit", args=[self.announcement.pk]),
                        reverse("dashboard:password_change"),
                    ]

                for url in urls:
                    with self.subTest(url=url):
                        self.assertEqual(self.client.get(url).status_code, 200)

    def test_home_shows_summary_numbers(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["stats"]["total"], 1)
        self.assertEqual(response.context["stats"]["published"], 1)
        self.assertEqual(response.context["stats"]["drafts"], 0)

    def test_list_filters_by_search_and_visibility(self):
        make_announcement(title_en="Winter coats", is_published=False)

        response = self.client.get(reverse("dashboard:list"), {"q": "winter"})
        self.assertEqual(response.context["total"], 1)
        self.assertEqual(response.context["page_obj"].object_list[0].title_en, "Winter coats")

        response = self.client.get(reverse("dashboard:list"), {"visibility": "draft"})
        self.assertEqual(response.context["total"], 1)
        self.assertFalse(response.context["page_obj"].object_list[0].is_published)

    def test_create_stores_the_author_and_keeps_drafts_private(self):
        response = self.client.post(
            reverse("dashboard:create"),
            {
                "type": Announcement.Type.MOSQUE,
                "category": Announcement.Category.QURAN,
                "status": Announcement.Status.OPEN,
                "title_ar": "إصلاح سقف المسجد",
                "title_en": "Repairing the mosque roof",
                "description_ar": "نحتاج إلى إصلاح السقف قبل الشتاء.",
                "description_en": "We need to repair the roof before winter.",
                "goal_amount": "5000",
                "raised_amount": "0",
                "currency": Announcement.Currency.EUR,
            },
        )

        created = Announcement.objects.get(title_en="Repairing the mosque roof")
        self.assertRedirects(response, reverse("dashboard:edit", args=[created.pk]))
        self.assertEqual(created.created_by, self.staff)
        self.assertFalse(created.is_published)

        with translation.override("en"):
            public = self.client.get(reverse("announcements:list"))
        self.assertNotContains(public, "Repairing the mosque roof")

    def test_edit_updates_the_announcement(self):
        response = self.client.post(
            reverse("dashboard:edit", args=[self.announcement.pk]),
            {
                "type": self.announcement.type,
                "category": self.announcement.category,
                "status": Announcement.Status.FULFILLED,
                "is_published": "on",
                "title_ar": "عنوان محدَّث",
                "title_en": "An updated title",
                "description_ar": "وصف محدَّث.",
                "description_en": "An updated description.",
                "raised_amount": "1000",
                "goal_amount": "1000",
                "currency": self.announcement.currency,
            },
        )

        self.assertRedirects(
            response, reverse("dashboard:edit", args=[self.announcement.pk])
        )
        self.announcement.refresh_from_db()
        self.assertEqual(self.announcement.title_en, "An updated title")
        self.assertEqual(self.announcement.status, Announcement.Status.FULFILLED)
        self.assertTrue(self.announcement.is_published)

    def test_contact_address_is_saved_from_the_form(self):
        response = self.client.post(
            reverse("dashboard:edit", args=[self.announcement.pk]),
            {
                "type": self.announcement.type,
                "category": self.announcement.category,
                "status": self.announcement.status,
                "is_published": "on",
                "title_ar": self.announcement.title_ar,
                "title_en": self.announcement.title_en,
                "description_ar": self.announcement.description_ar,
                "description_en": self.announcement.description_en,
                "goal_amount": "",
                "raised_amount": "0",
                "currency": self.announcement.currency,
                "contact_name": "Sheikh Noureddine",
                "contact_address": "Rue 12, Mostaganem",
            },
        )

        self.assertRedirects(
            response, reverse("dashboard:edit", args=[self.announcement.pk])
        )
        self.announcement.refresh_from_db()
        self.assertEqual(self.announcement.contact_address, "Rue 12, Mostaganem")

    def test_toggle_publish_hides_and_shows_again(self):
        url = reverse("dashboard:toggle_publish", args=[self.announcement.pk])

        self.client.post(url, {"next": reverse("dashboard:list")})
        self.announcement.refresh_from_db()
        self.assertFalse(self.announcement.is_published)

        self.client.post(url)
        self.announcement.refresh_from_db()
        self.assertTrue(self.announcement.is_published)

    def test_toggle_publish_ignores_an_external_next_url(self):
        response = self.client.post(
            reverse("dashboard:toggle_publish", args=[self.announcement.pk]),
            {"next": "https://evil.example.org/steal"},
        )

        self.assertRedirects(response, reverse("dashboard:list"))

    def test_bulk_publish_and_fulfil(self):
        drafts = [
            make_announcement(title_en=f"Draft {index}", is_published=False)
            for index in range(2)
        ]

        response = self.client.post(
            reverse("dashboard:bulk_action"),
            {
                "action": "publish",
                "selected": [announcement.pk for announcement in drafts],
            },
        )

        self.assertRedirects(response, reverse("dashboard:list"))
        self.assertEqual(
            Announcement.objects.filter(pk__in=[item.pk for item in drafts], is_published=True).count(),
            2,
        )

        self.client.post(
            reverse("dashboard:bulk_action"),
            {
                "action": "fulfil",
                "selected": [announcement.pk for announcement in drafts],
            },
        )
        self.assertEqual(
            Announcement.objects.filter(
                pk__in=[item.pk for item in drafts], status=Announcement.Status.FULFILLED
            ).count(),
            2,
        )

    def test_bulk_action_without_a_selection_warns(self):
        response = self.client.post(
            reverse("dashboard:bulk_action"), {"action": "publish"}, follow=True
        )

        self.assertRedirects(response, reverse("dashboard:list"))
        rendered = [str(message) for message in response.context["messages"]]
        with translation.override("ar"):
            expected = str(gettext("Select at least one announcement."))
        self.assertIn(expected, rendered)

    def test_regular_staff_cannot_delete_an_announcement(self):
        response = self.client.post(
            reverse("dashboard:delete", args=[self.announcement.pk])
        )

        self.assertRedirects(
            response, reverse("dashboard:edit", args=[self.announcement.pk])
        )
        self.assertTrue(Announcement.objects.filter(pk=self.announcement.pk).exists())

    def test_superuser_can_delete_an_announcement(self):
        self.staff.is_superuser = True
        self.staff.save(update_fields=["is_superuser"])

        response = self.client.post(
            reverse("dashboard:delete", args=[self.announcement.pk])
        )

        self.assertRedirects(response, reverse("dashboard:list"))
        self.assertFalse(Announcement.objects.filter(pk=self.announcement.pk).exists())

    def test_deleting_an_already_deleted_announcement_does_not_404(self):
        # A stale list or the Back button can resend an old delete form.
        pk = self.announcement.pk
        Announcement.objects.filter(pk=pk).delete()

        response = self.client.post(
            reverse("dashboard:delete", args=[pk]), follow=True
        )

        self.assertRedirects(response, reverse("dashboard:list"))
        rendered = [str(message) for message in response.context["messages"]]
        with translation.override("ar"):
            expected = str(gettext("This announcement no longer exists."))
        self.assertIn(expected, rendered)

    def test_opening_the_editor_of_a_deleted_announcement_does_not_404(self):
        # Phones keep the editor URL around (history, restored tabs): do not
        # answer with Django's unstyled debug page.
        pk = self.announcement.pk
        Announcement.objects.filter(pk=pk).delete()

        response = self.client.get(
            reverse("dashboard:edit", args=[pk]), follow=True
        )

        self.assertRedirects(response, reverse("dashboard:list"))
        rendered = [str(message) for message in response.context["messages"]]
        with translation.override("ar"):
            expected = str(gettext("This announcement no longer exists."))
        self.assertIn(expected, rendered)

    def test_toggling_an_already_deleted_announcement_does_not_404(self):
        pk = self.announcement.pk
        Announcement.objects.filter(pk=pk).delete()

        response = self.client.post(
            reverse("dashboard:toggle_publish", args=[pk]), follow=True
        )

        self.assertRedirects(response, reverse("dashboard:list"))
