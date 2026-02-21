"""
Enrollment CRM Models - Similar to Meritto/Zoho
Lead Management, Campaign Management, Enrollment Tracking
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta

# Import related models - using string references to avoid circular imports
# These will be resolved at runtime


class LeadSource(models.Model):
    """Lead source tracking (Website, Referral, Advertisement, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Lead(models.Model):
    """Student Lead/Enquiry Management - Similar to Meritto CRM"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('nurturing', 'Nurturing'),
        ('applied', 'Applied'),
        ('enrolled', 'Enrolled'),
        ('rejected', 'Rejected'),
        ('lost', 'Lost'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)
    
    # Lead Details
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Academic Interest
    interested_class = models.ForeignKey('students_app.Class', on_delete=models.SET_NULL, null=True, blank=True)
    interested_subjects = models.ManyToManyField('students_app.Subject', blank=True)
    previous_school = models.CharField(max_length=200, blank=True)
    
    # Parent/Guardian Information
    parent_name = models.CharField(max_length=200, blank=True)
    parent_email = models.EmailField(blank=True)
    parent_phone = models.CharField(max_length=15, blank=True)
    relationship = models.CharField(max_length=50, blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    
    # Assignment & Tracking
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='assigned_leads')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                related_name='created_leads')
    
    # Dates
    enquiry_date = models.DateTimeField(default=timezone.now)
    last_contacted = models.DateTimeField(null=True, blank=True)
    next_followup = models.DateTimeField(null=True, blank=True)
    converted_date = models.DateTimeField(null=True, blank=True)
    
    # Notes & Remarks
    notes = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    
    # Conversion Tracking
    converted_to_student = models.ForeignKey('students_app.Student', on_delete=models.SET_NULL, null=True, blank=True)
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-enquiry_date']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_status_display()}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def days_since_enquiry(self):
        return (timezone.now() - self.enquiry_date).days
    
    def is_overdue_followup(self):
        if self.next_followup:
            return timezone.now() > self.next_followup
        return False


class LeadActivity(models.Model):
    """Track all activities/interactions with a lead"""
    ACTIVITY_TYPES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('meeting', 'Meeting'),
        ('visit', 'School Visit'),
        ('note', 'Note'),
        ('status_change', 'Status Change'),
        ('campaign', 'Campaign'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    subject = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    activity_date = models.DateTimeField(default=timezone.now)
    duration_minutes = models.IntegerField(null=True, blank=True)
    outcome = models.CharField(max_length=100, blank=True)
    
    # For calls/meetings
    call_direction = models.CharField(max_length=10, choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')], blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-activity_date']
        verbose_name_plural = "Lead Activities"
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.lead.get_full_name()}"


class Campaign(models.Model):
    """Marketing Campaigns - Similar to Meritto Campaign Management"""
    CAMPAIGN_TYPES = [
        ('email', 'Email Campaign'),
        ('sms', 'SMS Campaign'),
        ('whatsapp', 'WhatsApp Campaign'),
        ('social', 'Social Media'),
        ('advertisement', 'Advertisement'),
        ('event', 'Event'),
        ('referral', 'Referral Program'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Targeting
    target_class = models.ForeignKey('students_app.Class', on_delete=models.SET_NULL, null=True, blank=True)
    target_source = models.ForeignKey('LeadSource', on_delete=models.SET_NULL, null=True, blank=True)
    target_status = models.CharField(max_length=20, choices=[('new', 'New'), ('contacted', 'Contacted'), ('qualified', 'Qualified'), ('nurturing', 'Nurturing'), ('applied', 'Applied'), ('enrolled', 'Enrolled'), ('rejected', 'Rejected'), ('lost', 'Lost')], blank=True)
    
    # Content
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    template_id = models.CharField(max_length=100, blank=True)
    
    # Scheduling
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    
    # Tracking
    total_sent = models.IntegerField(default=0)
    total_delivered = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_converted = models.IntegerField(default=0)
    
    # Budget & Cost
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_lead = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_campaign_type_display()}"
    
    def get_conversion_rate(self):
        if self.total_sent > 0:
            return (self.total_converted / self.total_sent) * 100
        return 0
    
    def get_roi(self):
        if self.budget > 0 and self.total_converted > 0:
            # Assuming average conversion value
            revenue = self.total_converted * 50000  # Example: 50k per enrollment
            return ((revenue - self.budget) / self.budget) * 100
        return 0


class CampaignLead(models.Model):
    """Link leads to campaigns for tracking"""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_leads')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='campaigns')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    converted = models.BooleanField(default=False)
    converted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['campaign', 'lead']
    
    def __str__(self):
        return f"{self.campaign.name} - {self.lead.get_full_name()}"


class EnrollmentFunnel(models.Model):
    """Track enrollment funnel metrics - Similar to Meritto Analytics"""
    date = models.DateField(default=timezone.now)
    
    # Funnel Stages
    enquiries = models.IntegerField(default=0)  # New leads
    contacted = models.IntegerField(default=0)  # Leads contacted
    qualified = models.IntegerField(default=0)  # Qualified leads
    applications = models.IntegerField(default=0)  # Applications received
    enrolled = models.IntegerField(default=0)  # Final enrollments
    
    # Conversion Metrics
    enquiry_to_contact_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    contact_to_qualify_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    qualify_to_apply_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    apply_to_enroll_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Revenue Metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_enrollment_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['date']
    
    def __str__(self):
        return f"Funnel Metrics - {self.date}"
    
    def calculate_rates(self):
        """Calculate conversion rates"""
        if self.enquiries > 0:
            self.enquiry_to_contact_rate = (self.contacted / self.enquiries) * 100
        if self.contacted > 0:
            self.contact_to_qualify_rate = (self.qualified / self.contacted) * 100
        if self.qualified > 0:
            self.qualify_to_apply_rate = (self.applications / self.qualified) * 100
        if self.applications > 0:
            self.apply_to_enroll_rate = (self.enrolled / self.applications) * 100
        if self.enquiries > 0:
            self.overall_conversion_rate = (self.enrolled / self.enquiries) * 100
        self.save()


class Application(models.Model):
    """Student Application/Admission Form - Similar to Meritto Application Platform"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('waitlisted', 'Waitlisted'),
    ]
    
    # Link to Lead
    lead = models.ForeignKey('Lead', on_delete=models.CASCADE, related_name='applications', null=True, blank=True)
    
    # Application Details
    application_number = models.CharField(max_length=50, unique=True)
    application_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Academic Details
    applied_class = models.ForeignKey('students_app.Class', on_delete=models.SET_NULL, null=True)
    previous_school = models.CharField(max_length=200, blank=True)
    previous_class = models.CharField(max_length=50, blank=True)
    previous_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Documents
    documents_uploaded = models.JSONField(default=dict, blank=True)  # Store document URLs
    
    # Review & Decision
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    decision_date = models.DateTimeField(null=True, blank=True)
    
    # Conversion
    converted_to_student = models.ForeignKey('students_app.Student', on_delete=models.SET_NULL, null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-application_date']
    
    def __str__(self):
        return f"Application {self.application_number} - {self.get_status_display()}"
    
    def generate_application_number(self):
        """Auto-generate application number"""
        if not self.application_number:
            year = timezone.now().year
            count = Application.objects.filter(application_date__year=year).count() + 1
            self.application_number = f"APP{year}{count:04d}"
        return self.application_number

