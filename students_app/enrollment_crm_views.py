"""
Enrollment CRM Views - Similar to Meritto/Zoho
Lead Management, Campaign Management, Analytics Dashboard
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal
from .enrollment_crm_models import (
    LeadSource, Lead, LeadActivity, Campaign, 
    CampaignLead, EnrollmentFunnel, Application
)
from .models import Class, Subject, Student


@login_required
def crm_dashboard(request):
    """Main CRM Dashboard - Different views for Super Admin vs School Admin"""
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
    
    # Filter leads based on user role
    leads_query = Lead.objects.filter(is_active=True)
    
    if is_super_admin:
        # Super Admin: Show ALL leads across ALL schools (system-wide view)
        pass
    elif school:
        # School Admin: Show only leads for their school
        if hasattr(Lead, 'school'):
            leads_query = leads_query.filter(school=school)
    
    # Get current user's assigned leads (filtered by role)
    user_leads = leads_query.filter(assigned_to=request.user)
    
    total_leads = leads_query.count()
    new_leads = leads_query.filter(status='new').count()
    qualified_leads = leads_query.filter(status='qualified').count()
    enrolled_count = leads_query.filter(status='enrolled').count()
    
    # Conversion Metrics
    conversion_rate = 0
    if total_leads > 0:
        conversion_rate = (enrolled_count / total_leads) * 100
    
    # Recent Leads
    recent_leads = leads_query.order_by('-enquiry_date')[:10]
    
    # Overdue Follow-ups
    overdue_followups = leads_query.filter(
        next_followup__lt=timezone.now(),
        next_followup__isnull=False
    ).order_by('next_followup')[:10]
    
    # Active Campaigns
    active_campaigns = Campaign.objects.filter(status='running').order_by('-start_date')[:5]
    
    # Funnel Metrics (Last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_leads_count = leads_query.filter(enquiry_date__gte=thirty_days_ago).count()
    recent_enrollments = leads_query.filter(
        status='enrolled',
        converted_date__gte=thirty_days_ago
    ).count()
    
    # Lead Source Distribution
    lead_sources = LeadSource.objects.annotate(
        lead_count=Count('lead', filter=Q(lead__is_active=True))
    ).order_by('-lead_count')[:10]
    
    # Status Distribution
    status_distribution = Lead.objects.filter(is_active=True).values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'is_super_admin': is_super_admin,
        'school': school,
        'total_leads': total_leads,
        'new_leads': new_leads,
        'qualified_leads': qualified_leads,
        'enrolled_count': enrolled_count,
        'conversion_rate': round(conversion_rate, 2),
        'recent_leads': recent_leads,
        'overdue_followups': overdue_followups,
        'active_campaigns': active_campaigns,
        'recent_leads_count': recent_leads_count,
        'recent_enrollments': recent_enrollments,
        'lead_sources': lead_sources,
        'status_distribution': status_distribution,
        'user_leads': user_leads.count(),
    }
    
    return render(request, 'crm/dashboard.html', context)


@login_required
def lead_list(request):
    """List all leads with filters - Available to All Users"""
    # Allow access to all authenticated users
    
    leads = Lead.objects.filter(is_active=True)
    
    # Filters
    status_filter = request.GET.get('status', '')
    source_filter = request.GET.get('source', '')
    assigned_filter = request.GET.get('assigned', '')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    if source_filter:
        leads = leads.filter(source_id=source_filter)
    
    if assigned_filter:
        leads = leads.filter(assigned_to_id=assigned_filter)
    
    if search_query:
        leads = leads.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(leads.order_by('-enquiry_date'), 25)
    page_number = request.GET.get('page')
    leads_page = paginator.get_page(page_number)
    
    # Get filter options
    sources = LeadSource.objects.filter(is_active=True)
    users = User.objects.filter(is_staff=True)
    
    context = {
        'leads': leads_page,
        'sources': sources,
        'users': users,
        'status_filter': status_filter,
        'source_filter': source_filter,
        'assigned_filter': assigned_filter,
        'search_query': search_query,
    }
    
    return render(request, 'crm/lead_list.html', context)


@login_required
def lead_detail(request, lead_id):
    """View and manage individual lead - Available to All Authenticated Users"""
    # Allow access to all authenticated users
    
    lead = get_object_or_404(Lead, id=lead_id)
    activities = lead.activities.all().order_by('-activity_date')[:20]
    campaigns = lead.campaigns.all()
    applications = lead.applications.all()
    
    context = {
        'lead': lead,
        'activities': activities,
        'campaigns': campaigns,
        'applications': applications,
    }
    
    return render(request, 'crm/lead_detail.html', context)


@login_required
def lead_create(request):
    """Create new lead - Available to All Authenticated Users"""
    # Allow access to all authenticated users
    if request.method == 'POST':
        # Create lead from form data
        lead = Lead.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            source_id=request.POST.get('source'),
            interested_class_id=request.POST.get('interested_class'),
            parent_name=request.POST.get('parent_name'),
            parent_phone=request.POST.get('parent_phone'),
            address=request.POST.get('address'),
            notes=request.POST.get('notes'),
            assigned_to_id=request.POST.get('assigned_to') or request.user.id,
            created_by=request.user,
        )
        
        # Create initial activity
        LeadActivity.objects.create(
            lead=lead,
            activity_type='note',
            subject='Lead Created',
            description=f'Lead created by {request.user.get_full_name()}',
            performed_by=request.user,
        )
        
        messages.success(request, f'Lead "{lead.get_full_name()}" created successfully!')
        return redirect('students_app:lead_detail', lead_id=lead.id)
    
    # GET request - show form
    sources = LeadSource.objects.filter(is_active=True)
    classes = Class.objects.all()
    users = User.objects.filter(is_staff=True)
    
    context = {
        'sources': sources,
        'classes': classes,
        'users': users,
    }
    
    return render(request, 'crm/lead_create.html', context)


@login_required
def campaign_list(request):
    """List all campaigns - Available to All Authenticated Users"""
    # Allow access to all authenticated users
    
    campaigns = Campaign.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        campaign_type = request.POST.get('campaign_type') or 'email'
        status_value = request.POST.get('status') or 'draft'
        subject = request.POST.get('subject', '')
        message = (request.POST.get('message') or '').strip()
        target_class = request.POST.get('target_class') or None
        target_source = request.POST.get('target_source') or None
        target_status = request.POST.get('target_status') or ''
        budget_value = request.POST.get('budget') or '0'
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        
        def parse_datetime(value):
            if not value:
                return None
            try:
                naive = datetime.strptime(value, "%Y-%m-%dT%H:%M")
                return timezone.make_aware(naive)
            except ValueError:
                return None
        
        start_date = parse_datetime(start_date_str)
        end_date = parse_datetime(end_date_str)
        
        if not name or not message:
            messages.error(request, 'Campaign name and message are required.')
        else:
            try:
                Campaign.objects.create(
                    name=name,
                    campaign_type=campaign_type,
                    status=status_value,
                    subject=subject,
                    message=message,
                    target_class_id=target_class,
                    target_source_id=target_source,
                    target_status=target_status,
                    budget=Decimal(budget_value or '0'),
                    start_date=start_date,
                    end_date=end_date,
                    created_by=request.user
                )
                messages.success(request, f'Campaign "{name}" created successfully.')
                return redirect('students_app:campaign_list')
            except Exception as exc:
                messages.error(request, f'Unable to create campaign: {exc}')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        campaigns = campaigns.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(campaigns, 20)
    page_number = request.GET.get('page')
    campaigns_page = paginator.get_page(page_number)
    
    context = {
        'campaigns': campaigns_page,
        'status_filter': status_filter,
        'campaign_types': Campaign.CAMPAIGN_TYPES,
        'campaign_statuses': Campaign.STATUS_CHOICES,
        'lead_statuses': Lead.STATUS_CHOICES,
        'classes': Class.objects.all(),
        'lead_sources': LeadSource.objects.filter(is_active=True),
    }
    
    return render(request, 'crm/campaign_list.html', context)


@login_required
def enrollment_analytics(request):
    """Enrollment Analytics Dashboard - Similar to Meritto Analytics - Available to All Authenticated Users"""
    # Allow access to all authenticated users
    
    # Date range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Funnel Metrics
    enquiries = Lead.objects.filter(enquiry_date__gte=start_date, is_active=True).count()
    contacted = Lead.objects.filter(
        enquiry_date__gte=start_date,
        status__in=['contacted', 'qualified', 'nurturing', 'applied', 'enrolled'],
        is_active=True
    ).count()
    qualified = Lead.objects.filter(
        enquiry_date__gte=start_date,
        status__in=['qualified', 'nurturing', 'applied', 'enrolled'],
        is_active=True
    ).count()
    applications = Application.objects.filter(application_date__gte=start_date).count()
    enrolled = Lead.objects.filter(
        status='enrolled',
        converted_date__gte=start_date,
        is_active=True
    ).count()
    
    # Conversion Rates
    enquiry_to_contact = (contacted / enquiries * 100) if enquiries > 0 else 0
    contact_to_qualify = (qualified / contacted * 100) if contacted > 0 else 0
    qualify_to_apply = (applications / qualified * 100) if qualified > 0 else 0
    apply_to_enroll = (enrolled / applications * 100) if applications > 0 else 0
    overall_conversion = (enrolled / enquiries * 100) if enquiries > 0 else 0
    
    # Revenue Metrics
    total_revenue = Lead.objects.filter(
        status='enrolled',
        converted_date__gte=start_date
    ).aggregate(total=Sum('conversion_value'))['total'] or 0
    
    avg_enrollment_value = total_revenue / enrolled if enrolled > 0 else 0
    
    # Lead Source Performance
    source_performance = LeadSource.objects.annotate(
        total_leads=Count('lead', filter=Q(lead__enquiry_date__gte=start_date, lead__is_active=True)),
        enrolled=Count('lead', filter=Q(lead__status='enrolled', lead__converted_date__gte=start_date, lead__is_active=True))
    ).filter(total_leads__gt=0).order_by('-total_leads')
    
    # Calculate conversion rates for each source
    for source in source_performance:
        if source.total_leads > 0:
            source.conversion_rate = round((source.enrolled / source.total_leads) * 100, 2)
        else:
            source.conversion_rate = 0
    
    # Daily Trends
    daily_trends = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        day_enquiries = Lead.objects.filter(
            enquiry_date__date=date.date(),
            is_active=True
        ).count()
        day_enrolled = Lead.objects.filter(
            converted_date__date=date.date(),
            status='enrolled',
            is_active=True
        ).count()
        daily_trends.append({
            'date': date.date(),
            'enquiries': day_enquiries,
            'enrolled': day_enrolled,
        })
    
    context = {
        'days': days,
        'enquiries': enquiries,
        'contacted': contacted,
        'qualified': qualified,
        'applications': applications,
        'enrolled': enrolled,
        'enquiry_to_contact': round(enquiry_to_contact, 2),
        'contact_to_qualify': round(contact_to_qualify, 2),
        'qualify_to_apply': round(qualify_to_apply, 2),
        'apply_to_enroll': round(apply_to_enroll, 2),
        'overall_conversion': round(overall_conversion, 2),
        'total_revenue': total_revenue,
        'avg_enrollment_value': round(avg_enrollment_value, 2),
        'source_performance': source_performance,
        'daily_trends': daily_trends,
    }
    
    return render(request, 'crm/analytics.html', context)

