# Generated manually to create BookRequest table
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0047_remove_staff_subjects_expertise_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BookRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_date', models.DateField(auto_now_add=True)),
                ('requested_due_date', models.DateField(help_text='Expected return date')),
                ('purpose', models.TextField(blank=True, help_text='Purpose for borrowing the book')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('issued', 'Issued'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('approved_date', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('issue_date', models.DateField(blank=True, null=True)),
                ('actual_due_date', models.DateField(blank=True, null=True)),
                ('return_date', models.DateField(blank=True, null=True)),
                ('remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_book_requests', to=settings.AUTH_USER_MODEL)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to='students_app.book')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='book_requests', to='students_app.teacher')),
            ],
            options={
                'verbose_name': 'Book Request',
                'verbose_name_plural': 'Book Requests',
                'ordering': ['-request_date'],
            },
        ),
    ]







