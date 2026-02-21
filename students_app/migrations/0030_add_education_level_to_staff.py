# Generated migration to add education_level field to Staff model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0029_add_assistant_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='education_level',
            field=models.CharField(default='Bachelor Degree', help_text='Specific degree details', max_length=100),
        ),
    ]

