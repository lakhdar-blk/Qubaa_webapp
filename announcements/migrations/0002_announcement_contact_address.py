from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='contact_address',
            field=models.CharField(blank=True, help_text='Address of the person responsible for this announcement. Leave empty to show the mosque address instead.', max_length=200, verbose_name='contact address'),
        ),
    ]
