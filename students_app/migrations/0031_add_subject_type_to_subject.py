# Generated migration to add subject_type field to Subject model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0030_add_education_level_to_staff'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='subject_type',
            field=models.CharField(choices=[('core', 'Core Subject'), ('language', 'Language'), ('science', 'Science'), ('mathematics', 'Mathematics'), ('social', 'Social Studies'), ('creative', 'Creative Arts'), ('physical', 'Physical Education'), ('technology', 'Technology')], default='core', max_length=20),
        ),
    ]

