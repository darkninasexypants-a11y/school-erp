# Generated migration to add is_active field to Subject model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0031_add_subject_type_to_subject'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]

