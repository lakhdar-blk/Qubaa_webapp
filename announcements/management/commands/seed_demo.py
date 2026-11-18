"""Add a few bilingual demo announcements for local previews or a fresh site."""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from announcements.models import Announcement

DEMO = [
    {
        "type": Announcement.Type.PERSON,
        "category": Announcement.Category.FOOD,
        "title_ar": "سلال غذائية لخمس عائلات محتاجة",
        "title_en": "Food baskets for five families in need",
        "description_ar": (
            "يعمل المسجد مع متطوعين لتجهيز سلال غذائية شهرية لخمس عائلات "
            "تعيش ظروفًا صعبة. تحتوي كل سلة على المواد الأساسية للشهر: "
            "دقيق، زيت، أرز، سكر، وبعض المواد الغذائية الأخرى. نسأل الله "
            "أن يجعل هذه المساعدة في ميزان حسناتكم."
        ),
        "description_en": (
            "The mosque is preparing monthly food baskets for five families "
            "going through difficult times. Each basket contains the essentials "
            "for a month: flour, oil, rice, sugar and other basic goods. "
            "May Allah reward everyone who contributes."
        ),
        "beneficiary_name": "Five families in the neighbourhood",
        "city": "Casablanca",
        "country": "Morocco",
        "goal_amount": Decimal("2500"),
        "raised_amount": Decimal("1300"),
        "status": Announcement.Status.OPEN,
        "contact_name": "Mosque social committee",
        "contact_address": "Rue 42, Hay Mohammadi, Casablanca",
        "contact_phone": "+212 600 000 000",
    },
    {
        "type": Announcement.Type.MOSQUE,
        "category": Announcement.Category.MOSQUE_MAINTENANCE,
        "title_ar": "ترميم سقف قاعة الصلاة",
        "title_en": "Repairing the roof of the prayer hall",
        "description_ar": (
            "بعد الأمطار الأخيرة، ظهرت تشققات في سقف قاعة الصلاة الرئيسية. "
            "نحتاج إلى إصلاح السقف وعزل الماء قبل فصل الشتاء القادم. "
            "المساهمة في هذا المشروع صدقة جارية بإذن الله."
        ),
        "description_en": (
            "After the recent rains, cracks appeared in the roof of the main "
            "prayer hall. We need to repair and waterproof it before the next "
            "winter. Contributing to this project is an ongoing charity, "
            "by the will of Allah."
        ),
        "city": "Rabat",
        "country": "Morocco",
        "goal_amount": Decimal("8000"),
        "raised_amount": Decimal("3200"),
        "status": Announcement.Status.OPEN,
        "contact_name": "Mosque maintenance team",
        "contact_address": "Hay Ennour, Rabat",
        "contact_email": "maintenance@example.org",
    },
    {
        "type": Announcement.Type.PERSON,
        "category": Announcement.Category.ORPHANS,
        "title_ar": "محافظ ولوازم مدرسية لعشرين يتيمًا",
        "title_en": "School supplies for twenty orphaned children",
        "description_ar": (
            "مع بداية العام الدراسي، يحتاج عشرون طفلًا يتيمًا إلى حافظات "
            "ودفاتر ولوازم مدرسية. الهدف هو تجهيز كل طفل بحقيبة كاملة "
            "حتى يتمكن من متابعة دراسته بكرامة. تم بفضل الله جمع المبلغ "
            "الكامل وتم توزيع اللوازم."
        ),
        "description_en": (
            "At the start of the school year, twenty orphaned children need "
            "school bags, notebooks and supplies. The goal was to equip every "
            "child with a complete kit so they can study with dignity. Thanks "
            "to Allah, the full amount was raised and the supplies distributed."
        ),
        "beneficiary_name": "Twenty orphaned children",
        "city": "Tangier",
        "country": "Morocco",
        "goal_amount": Decimal("1800"),
        "raised_amount": Decimal("1800"),
        "status": Announcement.Status.FULFILLED,
    },
    {
        "type": Announcement.Type.PERSON,
        "category": Announcement.Category.MEDICAL,
        "title_ar": "مساعدة طبية لرجل مسن",
        "title_en": "Medical help for an elderly man",
        "description_ar": (
            "رجل مسن يعيش وحده يحتاج إلى علاج طبي ومواد دوائية شهرية "
            "لا يستطيع تحمل تكاليفها. نساعد في تغطية تكاليف العلاج "
            "والمواعيد الطبية. كل مساهمة، مهما كانت صغيرة، تفرق كثيرًا."
        ),
        "description_en": (
            "An elderly man living alone needs monthly medical treatment and "
            "medicines he cannot afford. We are helping cover the cost of "
            "treatment and medical appointments. Every contribution, however "
            "small, makes a difference."
        ),
        "beneficiary_name": "An elderly member of the community",
        "city": "Fes",
        "country": "Morocco",
        "goal_amount": Decimal("1200"),
        "raised_amount": Decimal("450"),
        "status": Announcement.Status.OPEN,
        "contact_address": "Rue 8, Fes",
        "contact_phone": "+212 600 000 000",
    },
    {
        "type": Announcement.Type.MOSQUE,
        "category": Announcement.Category.MOSQUE_MAINTENANCE,
        "title_ar": "سجاد جديد لقاعة الصلاة",
        "title_en": "New carpets for the prayer hall",
        "description_ar": (
            "بعد سنوات من الاستعمال، أصبح سجاد قاعة الصلاة متآكلًا في "
            "بعض الأماكن. تم بفضل الله جمع المبلغ اللازم وشراء سجاد جديد، "
            "وسيتم تركيبه قبل شهر رمضان. شكرًا لكل من ساهم."
        ),
        "description_en": (
            "After years of use, the prayer hall carpets have worn out in "
            "several places. Thanks to Allah, the needed amount was collected "
            "and new carpets purchased. They will be installed before Ramadan. "
            "Thank you to everyone who contributed."
        ),
        "city": "Rabat",
        "country": "Morocco",
        "goal_amount": Decimal("3000"),
        "raised_amount": Decimal("3000"),
        "status": Announcement.Status.FULFILLED,
    },
    {
        "type": Announcement.Type.MOSQUE,
        "category": Announcement.Category.QURAN,
        "title_ar": "دروس تحفيظ القرآن للأطفال",
        "title_en": "Quran memorisation classes for children",
        "description_ar": (
            "يفتح المسجد باب التسجيل في حلقات تحفيظ القرآن الكريم للأطفال "
            "من سن السادسة إلى الثانية عشرة، كل يوم سبت بعد صلاة العصر. "
            "الحلقات مجانية ويشرف عليها معلمون متطوعون. نرحب بكل الأطفال "
            "الراغبين في حفظ كتاب الله."
        ),
        "description_en": (
            "The mosque is opening registration for Quran memorisation "
            "classes for children aged six to twelve, every Saturday after "
            "the afternoon prayer. Classes are free and led by volunteer "
            "teachers. All children are welcome to memorise the Book of Allah."
        ),
        "city": "Rabat",
        "country": "Morocco",
        "status": Announcement.Status.OPEN,
        "contact_email": "quran@example.org",
    },
]


class Command(BaseCommand):
    help = "Create demo announcements (skipped if announcements already exist)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing announcements before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Announcement.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} record(s)."))

        if Announcement.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Announcements already exist — nothing was added. "
                    "Use --clear to replace them."
                )
            )
            return

        now = timezone.now()
        created = 0
        for index, data in enumerate(DEMO):
            announcement = Announcement(**data)
            announcement.is_published = True
            announcement.save()
            # Slightly vary dates so the list looks natural.
            Announcement.objects.filter(pk=announcement.pk).update(
                created_at=now - timezone.timedelta(days=index * 2)
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Created {created} demo announcements.")
        )
