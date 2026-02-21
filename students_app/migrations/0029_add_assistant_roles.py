from django.db import migrations


def create_assistant_roles(apps, schema_editor):
    UserRole = apps.get_model('students_app', 'UserRole')
    roles_to_create = [
        ('assistant_viewer', 'Assistant - View Only', 'Can view dashboards and data; no write actions'),
        ('assistant_creator', 'Assistant - Create School + View', 'Can create schools and view data; no other writes'),
    ]
    for name, display_name, description in roles_to_create:
        UserRole.objects.get_or_create(
            name=name,
            defaults={
                'display_name': display_name,
                'description': description,
                'is_active': True
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0028_create_security_settings'),
    ]

    operations = [
        migrations.RunPython(create_assistant_roles, migrations.RunPython.noop),
    ]


