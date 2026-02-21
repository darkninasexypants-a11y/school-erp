# Generated migration to add target_status field to Campaign model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0024_create_system_configuration'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='target_status',
            field=models.CharField(
                blank=True,
                choices=[
                    ('new', 'New'),
                    ('contacted', 'Contacted'),
                    ('qualified', 'Qualified'),
                    ('nurturing', 'Nurturing'),
                    ('applied', 'Applied'),
                    ('enrolled', 'Enrolled'),
                    ('rejected', 'Rejected'),
                    ('lost', 'Lost')
                ],
                max_length=20
            ),
        ),
    ]

