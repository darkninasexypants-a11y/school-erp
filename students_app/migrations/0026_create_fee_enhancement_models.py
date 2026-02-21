# Generated manually - Fee Enhancement Models Migration
from django.db import migrations, models
import django.core.validators
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0025_add_target_status_to_campaign'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeeConcession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('concession_type', models.CharField(choices=[('merit', 'Merit-based'), ('scholarship', 'Scholarship'), ('category', 'Category-based (SC/ST/OBC)'), ('religion', 'Religion-based'), ('sibling', 'Sibling Discount'), ('staff_child', 'Staff Child'), ('sports', 'Sports Achievement'), ('academic', 'Academic Excellence'), ('financial', 'Financial Aid'), ('other', 'Other')], max_length=20)),
                ('percentage', models.DecimalField(decimal_places=2, default=0, help_text='Percentage discount (0-100)', max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('fixed_amount', models.DecimalField(decimal_places=2, default=0, help_text='Fixed amount discount (if not percentage)', max_digits=10)),
                ('is_percentage', models.BooleanField(default=True, help_text='True for percentage, False for fixed amount')),
                ('applicable_to', models.CharField(blank=True, help_text='Category/Class/Other criteria', max_length=50)),
                ('min_marks_required', models.DecimalField(blank=True, decimal_places=2, help_text='Minimum marks required for merit-based', max_digits=5, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Fee Concession',
                'verbose_name_plural': 'Fee Concessions',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='StudentFeeConcession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('approved_date', models.DateField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('remarks', models.TextField(blank=True)),
                ('academic_year', models.ForeignKey(on_delete=models.deletion.CASCADE, to='students_app.academicyear')),
                ('approved_by', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('concession', models.ForeignKey(on_delete=models.deletion.CASCADE, to='students_app.feeconcession')),
                ('student', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='fee_concessions', to='students_app.student')),
            ],
            options={
                'ordering': ['-approved_date'],
                'unique_together': {('student', 'concession', 'academic_year')},
            },
        ),
        migrations.CreateModel(
            name='FeeNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('pending', 'Pending Fee Reminder'), ('overdue', 'Overdue Fee Alert'), ('receipt', 'Payment Receipt'), ('reminder', 'General Reminder')], max_length=20)),
                ('subject', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('sent_via', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS'), ('whatsapp', 'WhatsApp'), ('both', 'Both'), ('all', 'All')], max_length=20)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('is_sent', models.BooleanField(default=False)),
                ('sent_to_email', models.EmailField(blank=True, max_length=254)),
                ('sent_to_phone', models.CharField(blank=True, max_length=15)),
                ('student', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='fee_notifications', to='students_app.student')),
            ],
            options={
                'ordering': ['-sent_at'],
            },
        ),
        migrations.CreateModel(
            name='FeeReconciliation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reconciliation_date', models.DateField()),
                ('bank_name', models.CharField(max_length=100)),
                ('bank_statement_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('system_recorded_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('difference', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('matched', 'Matched'), ('mismatch', 'Mismatch'), ('resolved', 'Resolved')], default='pending', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reconciled_by', models.ForeignKey(null=True, on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Fee Reconciliation',
                'verbose_name_plural': 'Fee Reconciliations',
                'ordering': ['-reconciliation_date'],
            },
        ),
    ]

