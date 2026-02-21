from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0032_add_is_active_to_subject'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemconfiguration',
            name='feature_settings',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='schoolfeatureconfiguration',
            name='feature_overrides',
            field=models.JSONField(blank=True, default=dict, help_text='Override flags for extended feature set'),
        ),
    ]


