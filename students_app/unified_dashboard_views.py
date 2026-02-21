"""
Unified Dashboard View - Combining CRM & ERP Features
Similar to Meritto/Zoho unified platform
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta, date

# Import models
try:
    from .models import (
        Student, Teacher, Parent, Class, Section, 
        Attendance, FeePayment, School
    )
    from .enrollment_crm_models import (
        Lead, LeadSource, Campaign, Application
    )
except ImportError:
    # Fallback if models not available
    pass


@login_required
def unified_dashboard(request):
    """Unified Dashboard showing both CRM and ERP features - Different views for Super Admin vs School Admin"""
    # Check if user is super admin
    is_super_admin = False
    school = None
    
    if request.user.is_superuser:
        is_super_admin = True
    else:
        try:
            school_user = request.user.school_profile
            if school_user.role.name == 'super_admin':
                is_super_admin = True
            else:
                school = school_user.school if hasattr(school_user, 'school') else None
        except:
            pass
    
    # ========== CRM METRICS ==========
    try:
        # Lead Statistics
        total_leads = Lead.objects.filter(is_active=True).count()
        new_leads = Lead.objects.filter(status='new', is_active=True).count()
        qualified_leads = Lead.objects.filter(status='qualified', is_active=True).count()
        enrolled_count = Lead.objects.filter(status='enrolled', is_active=True).count()
        
        # Conversion Rate
        conversion_rate = 0
        if total_leads > 0:
            conversion_rate = (enrolled_count / total_leads) * 100
        
        # Recent Leads (Last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_leads_count = Lead.objects.filter(
            enquiry_date__gte=thirty_days_ago, 
            is_active=True
        ).count()
        recent_enrollments = Lead.objects.filter(
            status='enrolled',
            converted_date__gte=thirty_days_ago,
            is_active=True
        ).count()
        
        # Recent Leads List
        recent_leads = Lead.objects.filter(is_active=True).order_by('-enquiry_date')[:10]
        
        # Overdue Follow-ups
        overdue_followups = Lead.objects.filter(
            is_active=True,
            next_followup__lt=timezone.now(),
            next_followup__isnull=False
        ).order_by('next_followup')[:10]
        
        # Active Campaigns
        active_campaigns = Campaign.objects.filter(status='running').order_by('-start_date')[:5]
        
        # Lead Sources
        lead_sources = LeadSource.objects.annotate(
            lead_count=Count('lead', filter=Q(lead__is_active=True))
        ).order_by('-lead_count')[:10]
    except:
        # If CRM models not available, set defaults
        total_leads = 0
        new_leads = 0
        qualified_leads = 0
        enrolled_count = 0
        conversion_rate = 0
        recent_leads_count = 0
        recent_enrollments = 0
        recent_leads = []
        overdue_followups = []
        active_campaigns = []
        lead_sources = []
    
    # ========== ERP METRICS ==========
    try:
        # Filter ERP data based on user role
        students_query = Student.objects.all()
        teachers_query = Teacher.objects.all()
        parents_query = Parent.objects.all()
        classes_query = Class.objects.all()
        sections_query = Section.objects.all()
        
        if is_super_admin:
            # Super Admin: Show ALL data across ALL schools (system-wide view)
            pass
        elif school:
            # School Admin: Show only data for their school
            if hasattr(Student, 'school'):
                students_query = students_query.filter(school=school)
            if hasattr(Teacher, 'school'):
                teachers_query = teachers_query.filter(school=school)
            if hasattr(Parent, 'school'):
                parents_query = parents_query.filter(school=school)
            if hasattr(Class, 'school'):
                classes_query = classes_query.filter(school=school)
                sections_query = sections_query.filter(class_assigned__school=school)
        
        # Student Statistics
        total_students = students_query.filter(status='active').count()
        total_teachers = teachers_query.filter(is_active=True).count()
        total_parents = parents_query.count()
        total_classes = classes_query.count()
        total_sections = sections_query.count()
        
        # Today's Attendance
        today = timezone.localdate()
        today_attendance = Attendance.objects.filter(date=today).count()
        present_today = Attendance.objects.filter(date=today, status='P').count()
        
        # Today's Fee Collection
        today_fees = FeePayment.objects.filter(
            payment_date=today,
            payment_status='completed'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Pending Tasks (example: students without photos, unpaid fees, etc.)
        students_without_photos = Student.objects.filter(
            status='active',
            photo__isnull=True
        ).count()
        
        pending_tasks = students_without_photos  # Can add more tasks
        
    except:
        total_students = 0
        total_teachers = 0
        total_parents = 0
        total_classes = 0
        total_sections = 0
        today_attendance = 0
        present_today = 0
        today_fees = 0
        pending_tasks = 0
    
    context = {
        # CRM Data
        'total_leads': total_leads,
        'new_leads': new_leads,
        'qualified_leads': qualified_leads,
        'enrolled_count': enrolled_count,
        'conversion_rate': round(conversion_rate, 2),
        'recent_leads_count': recent_leads_count,
        'recent_enrollments': recent_enrollments,
        'recent_leads': recent_leads,
        'overdue_followups': overdue_followups,
        'active_campaigns': active_campaigns,
        'lead_sources': lead_sources,
        
        # ERP Data
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_parents': total_parents,
        'total_classes': total_classes,
        'total_sections': total_sections,
        'today_attendance': today_attendance,
        'present_today': present_today,
        'today_fees': today_fees,
        'pending_tasks': pending_tasks,
    }
    
    return render(request, 'crm/unified_dashboard.html', context)

