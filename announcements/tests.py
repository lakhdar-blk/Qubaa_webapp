from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from .models import Announcement


def make_announcement(**overrides):
    data = {
        "type": Announcement.Type.PERSON,
        "category": Announcement.Category.FOOD,
        "title_ar": "حاجة تجريبية",
        "title_en": "A sample need",
        "description_ar": "وصف تجريبي للحاجة.",
        "description_en": "A sample description of the need.",
        "city": "Rabat",
        "country": "Morocco",
        "goal_amount": Decimal("1000"),
        "raised_amount": Decimal("250"),
        "is_published": True,
    }
    data.update(overrides)
    return Announcement.objects.create(**data)


class AnnouncementModelTests(TestCase):
    def test_localized_fields_fall_back_to_the_other_language(self):
        announcement = make_announcement(title_en="", description_en="")

        with translation.override("en"):
            self.assertEqual(announcement.title, "حاجة تجريبية")
            self.assertEqual(announcement.description, "وصف تجريبي للحاجة.")

        with translation.override("ar"):
            self.assertEqual(announcement.title, "حاجة تجريبية")

    def test_progress_percent_is_capped(self):
        announcement = make_announcement(
            goal_amount=Decimal("100"), raised_amount=Decimal("150")
        )
        self.assertEqual(announcement.progress_percent, 100)

    def test_progress_without_goal(self):
        announcement = make_announcement(goal_amount=None, raised_amount=Decimal("0"))
        self.assertFalse(announcement.has_goal)
        self.assertEqual(announcement.progress_percent, 0)
        self.assertEqual(announcement.remaining_amount, Decimal("0"))

    def test_clean_requires_a_title_in_at_least_one_language(self):
        announcement = Announcement(
            title_ar="",
            title_en="",
            description_ar="وصف",
            description_en="Description",
        )
        with self.assertRaises(ValidationError):
            announcement.full_clean()

    def test_location_joins_city_and_country(self):
        announcement = make_announcement(city="Rabat", country="Morocco")
        self.assertEqual(announcement.location, "Rabat, Morocco")


class PublicViewsTests(TestCase):
    def setUp(self):
        self.published = make_announcement(
            title_ar="مساعدة عائلة",
            title_en="Helping a family",
            city="Casablanca",
        )
        self.draft = make_announcement(
            title_ar="إعلان غير منشور",
            title_en="Unpublished announcement",
            is_published=False,
        )

    def test_root_redirects_to_arabic(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/ar/", fetch_redirect_response=False)

    def test_home_page_is_rendered_in_arabic_and_rtl(self):
        response = self.client.get("/ar/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'dir="rtl"')
        self.assertContains(response, "مساعدة عائلة")
        self.assertNotContains(response, "إعلان غير منشور")

    def test_home_page_is_rendered_in_english_and_ltr(self):
        response = self.client.get("/en/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'dir="ltr"')
        self.assertContains(response, "Helping a family")

    def test_list_excludes_unpublished_announcements(self):
        response = self.client.get("/en/announcements/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Helping a family")
        self.assertNotContains(response, "Unpublished announcement")

    def test_list_filters_by_search_query(self):
        response = self.client.get("/en/announcements/", {"q": "Casablanca"})
        self.assertContains(response, "Helping a family")

        response = self.client.get("/en/announcements/", {"q": "Nowhere"})
        self.assertNotContains(response, "Helping a family")
        self.assertContains(response, "No announcements found")

    def test_list_filters_by_type(self):
        make_announcement(
            title_ar="حاجة المسجد",
            title_en="A mosque need",
            type=Announcement.Type.MOSQUE,
        )
        response = self.client.get(
            "/en/announcements/", {"type": Announcement.Type.MOSQUE}
        )
        self.assertContains(response, "A mosque need")
        self.assertNotContains(response, "Helping a family")

    def test_detail_page_shows_published_announcement(self):
        response = self.client.get(f"/en/announcements/{self.published.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Helping a family")

    def test_detail_page_shows_the_responsible_persons_address(self):
        announcement = make_announcement(
            title_en="Winter clothes",
            contact_name="Sheikh Noureddine",
            contact_address="Rue 12, Mostaganem",
        )
        response = self.client.get(f"/en/announcements/{announcement.pk}/")
        self.assertContains(response, "Rue 12, Mostaganem")

    def test_detail_page_falls_back_to_the_mosque_address(self):
        announcement = make_announcement(title_en="Winter clothes", contact_address="")
        with self.settings(CONTACT_ADDRESS_EN="1 Mosque Road, Rabat"):
            response = self.client.get(f"/en/announcements/{announcement.pk}/")
        self.assertContains(response, "1 Mosque Road, Rabat")

    def test_detail_page_hides_draft(self):
        response = self.client.get(f"/en/announcements/{self.draft.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_about_page(self):
        response = self.client.get("/ar/about/")
        self.assertEqual(response.status_code, 200)

    def test_health_check(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})

    def test_arabic_interface_is_translated(self):
        response = self.client.get("/ar/")
        self.assertContains(response, "آخر الإعلانات")
        self.assertNotContains(response, "Latest announcements")

    def test_admin_requires_authentication(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])


class AdminTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username="admin@example.org",
            email="admin@example.org",
            password="A-strong-password-123",
        )
        self.announcement = make_announcement()

    def test_admin_changelist_is_available(self):
        self.client.force_login(self.admin)
        response = self.client.get("/admin/announcements/announcement/")
        self.assertEqual(response.status_code, 200)

    def test_unpublish_action(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin:announcements_announcement_changelist"),
            {
                "action": "unpublish_selected",
                "_selected_action": [str(self.announcement.pk)],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.announcement.refresh_from_db()
        self.assertFalse(self.announcement.is_published)
