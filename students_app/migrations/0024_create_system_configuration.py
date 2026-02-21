# Generated migration for SystemConfiguration model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0023_add_converted_to_student_to_lead'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('crm_enabled', models.BooleanField(default=True, help_text='Enable CRM Module')),
                ('erp_enabled', models.BooleanField(default=True, help_text='Enable ERP Module')),
                ('id_card_generator', models.BooleanField(default=True, help_text='Enable ID Card Generator')),
                ('fee_payment_online', models.BooleanField(default=True, help_text='Enable Online Fee Payment')),
                ('attendance_tracking', models.BooleanField(default=True, help_text='Enable Attendance Tracking')),
                ('marks_entry', models.BooleanField(default=True, help_text='Enable Marks Entry')),
                ('library_management', models.BooleanField(default=True, help_text='Enable Library Management')),
                ('transport_management', models.BooleanField(default=False, help_text='Enable Transport Management')),
                ('hostel_management', models.BooleanField(default=False, help_text='Enable Hostel Management')),
                ('canteen_management', models.BooleanField(default=False, help_text='Enable Canteen Management')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'System Configuration',
                'verbose_name_plural': 'System Configuration',
                'db_table': 'students_app_systemconfiguration',
            },
        ),
    ]
