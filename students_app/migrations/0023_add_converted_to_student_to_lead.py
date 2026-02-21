# Generated migration to add converted_to_student field to Lead model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0022_enrollment_crm_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='converted_to_student',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='students_app.student'
            ),
        ),
    ]

