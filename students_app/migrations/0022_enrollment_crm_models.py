# Generated manually for Enrollment CRM System

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('students_app', '0021_add_layout_json_to_idcard_template'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeadSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Lead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=15)),
                ('alternate_phone', models.CharField(blank=True, max_length=15)),
                ('status', models.CharField(choices=[('new', 'New'), ('contacted', 'Contacted'), ('qualified', 'Qualified'), ('nurturing', 'Nurturing'), ('applied', 'Applied'), ('enrolled', 'Enrolled'), ('rejected', 'Rejected'), ('lost', 'Lost')], default='new', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=10)),
                ('previous_school', models.CharField(blank=True, max_length=200)),
                ('parent_name', models.CharField(blank=True, max_length=200)),
                ('parent_email', models.EmailField(blank=True, max_length=254)),
                ('parent_phone', models.CharField(blank=True, max_length=15)),
                ('relationship', models.CharField(blank=True, max_length=50)),
                ('address', models.TextField(blank=True)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('pincode', models.CharField(blank=True, max_length=10)),
                ('enquiry_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_contacted', models.DateTimeField(blank=True, null=True)),
                ('next_followup', models.DateTimeField(blank=True, null=True)),
                ('converted_date', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('remarks', models.TextField(blank=True)),
                ('conversion_value', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_leads', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_leads', to=settings.AUTH_USER_MODEL)),
                ('interested_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='students_app.class')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='students_app.leadsource')),
            ],
            options={
                'ordering': ['-enquiry_date'],
            },
        ),
        migrations.CreateModel(
            name='LeadActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_type', models.CharField(choices=[('call', 'Phone Call'), ('email', 'Email'), ('whatsapp', 'WhatsApp'), ('meeting', 'Meeting'), ('visit', 'School Visit'), ('note', 'Note'), ('status_change', 'Status Change'), ('campaign', 'Campaign')], max_length=20)),
                ('subject', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField()),
                ('activity_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('duration_minutes', models.IntegerField(blank=True, null=True)),
                ('outcome', models.CharField(blank=True, max_length=100)),
                ('call_direction', models.CharField(blank=True, choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='students_app.lead')),
                ('performed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-activity_date'],
                'verbose_name_plural': 'Lead Activities',
            },
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('campaign_type', models.CharField(choices=[('email', 'Email Campaign'), ('sms', 'SMS Campaign'), ('whatsapp', 'WhatsApp Campaign'), ('social', 'Social Media'), ('advertisement', 'Advertisement'), ('event', 'Event'), ('referral', 'Referral Program')], max_length=20)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('scheduled', 'Scheduled'), ('running', 'Running'), ('paused', 'Paused'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='draft', max_length=20)),
                ('subject', models.CharField(blank=True, max_length=200)),
                ('message', models.TextField()),
                ('template_id', models.CharField(blank=True, max_length=100)),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('scheduled_time', models.TimeField(blank=True, null=True)),
                ('total_sent', models.IntegerField(default=0)),
                ('total_delivered', models.IntegerField(default=0)),
                ('total_opened', models.IntegerField(default=0)),
                ('total_clicked', models.IntegerField(default=0)),
                ('total_converted', models.IntegerField(default=0)),
                ('budget', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('cost_per_lead', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('target_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='students_app.class')),
                ('target_source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='students_app.leadsource')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CampaignLead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('opened_at', models.DateTimeField(blank=True, null=True)),
                ('clicked_at', models.DateTimeField(blank=True, null=True)),
                ('converted', models.BooleanField(default=False)),
                ('converted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='campaign_leads', to='students_app.campaign')),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='campaigns', to='students_app.lead')),
            ],
            options={
                'unique_together': {('campaign', 'lead')},
            },
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('application_number', models.CharField(max_length=50, unique=True)),
                ('application_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('under_review', 'Under Review'), ('shortlisted', 'Shortlisted'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('waitlisted', 'Waitlisted')], default='draft', max_length=20)),
                ('previous_school', models.CharField(blank=True, max_length=200)),
                ('previous_class', models.CharField(blank=True, max_length=50)),
                ('previous_marks', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('documents_uploaded', models.JSONField(blank=True, default=dict)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('review_notes', models.TextField(blank=True)),
                ('decision_date', models.DateTimeField(blank=True, null=True)),
                ('converted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('applied_class', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='students_app.class')),
                ('converted_to_student', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='students_app.student')),
                ('lead', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='students_app.lead')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_applications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-application_date'],
            },
        ),
        migrations.AddField(
            model_name='lead',
            name='interested_subjects',
            field=models.ManyToManyField(blank=True, to='students_app.subject'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['status', 'priority'], name='students_ap_status_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['assigned_to', 'status'], name='students_ap_assigned_status_idx'),
        ),
    ]

