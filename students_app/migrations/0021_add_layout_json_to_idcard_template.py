# Generated manually for ID card system integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0020_auto_20251013_1244'),
    ]

    operations = [
        migrations.AddField(
            model_name='idcardtemplate',
            name='layout_json',
            field=models.JSONField(blank=True, default=dict, help_text='JSON layout definition with elements, background, and positioning', null=True),
        ),
    ]

