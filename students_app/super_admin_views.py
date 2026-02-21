"""
Super Admin Views - Advanced Management Features
User Management, Analytics, Configuration, Security Controls
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import School, SchoolUser, UserRole, Student, Teacher, Parent
from .enrollment_crm_models import Lead, Campaign
from .feature_registry import FEATURE_GROUPS, iter_all_features
from .system_config import SchoolFeatureConfiguration, SystemConfiguration


@login_required
def super_admin_user_management(request):
    """Advanced User Management with Access Level Controls"""
    # Check super admin permission
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name != 'super_admin':
                messages.error(request, 'Access denied. Super admin only.')
                return redirect('students_app:admin_dashboard')
        except:
            messages.error(request, 'Access denied.')
            return redirect('students_app:admin_dashboard')
    
    # Get all users with filters
    users = SchoolUser.objects.select_related('user', 'role', 'school').all()
    
    # Filters
    role_filter = request.GET.get('role', '')
    school_filter = request.GET.get('school', '')
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Super admin: School selection is mandatory - show no users if school not selected
    if not school_filter:
        users = SchoolUser.objects.none()  # Return empty queryset
    else:
        users = users.filter(school_id=school_filter)
    
    if role_filter:
        users = users.filter(role__name=role_filter)
    if search:
        users = users.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(login_id__icontains=search)
        )
    if status_filter:
        users = users.filter(user__is_active=(status_filter == 'active'))
    
    # Access level statistics
    access_stats = {
        'total': users.count(),
        'by_role': SchoolUser.objects.values('role__name').annotate(count=Count('id')),
        'by_school': SchoolUser.objects.values('school__name').annotate(count=Count('id')),
        'active': users.filter(user__is_active=True).count(),
        'inactive': users.filter(user__is_active=False).count(),
    }
    
    # All schools and roles for filters
    schools = School.objects.all()
    roles = UserRole.objects.all()
    
    context = {
        'users': users[:100],  # Limit for performance
        'schools': schools,
        'roles': roles,
        'access_stats': access_stats,
        'current_filters': {
            'role': role_filter,
            'school': school_filter,
            'search': search,
            'status': status_filter,
        }
    }
    
    return render(request, 'super_admin/user_management.html', context)


@login_required
def super_admin_analytics(request):
    """Analytics & Reporting Dashboard - School Performance Monitoring"""
    # Check super admin permission
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name != 'super_admin':
                messages.error(request, 'Access denied. Super admin only.')
                return redirect('students_app:admin_dashboard')
        except:
            messages.error(request, 'Access denied.')
            return redirect('students_app:admin_dashboard')
    
    # Date range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # School Performance Metrics
    # Note: Student model may not have direct school relationship
    # Adjust based on your actual model structure
    school_performance = School.objects.annotate(
        total_users=Count('schooluser'),
    ).order_by('-created_at')
    
    # Add student and teacher counts manually if needed
    for school in school_performance:
        # You can add custom logic here if Student has school relationship
        school.total_students = 0  # Placeholder
        school.total_teachers = 0  # Placeholder
    
    # System-wide Analytics
    total_schools = School.objects.count()
    active_schools = School.objects.filter(subscription_active=True).count()
    total_users = SchoolUser.objects.count()
    
    try:
        total_students = Student.objects.filter(status='active').count()
    except:
        total_students = 0
    
    try:
        total_teachers = Teacher.objects.filter(is_active=True).count()
    except:
        total_teachers = 0
    
    # Growth Metrics (Last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_schools = School.objects.filter(created_at__gte=thirty_days_ago).count()
    new_users = SchoolUser.objects.filter(created_at__gte=thirty_days_ago).count()
    
    try:
        new_students = Student.objects.filter(admission_date__gte=thirty_days_ago).count()
    except:
        new_students = 0
    
    # Error Monitoring (Placeholder - can be enhanced with error logging)
    system_health = {
        'status': 'healthy',
        'active_schools_percentage': (active_schools / total_schools * 100) if total_schools > 0 else 0,
        'avg_users_per_school': (total_users / total_schools) if total_schools > 0 else 0,
        'avg_students_per_school': (total_students / total_schools) if total_schools > 0 else 0,
    }
    
    # Role Distribution
    role_distribution = SchoolUser.objects.values('role__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # CRM Analytics
    try:
        total_leads = Lead.objects.filter(is_active=True).count()
        enrolled_leads = Lead.objects.filter(status='enrolled', is_active=True).count()
        conversion_rate = (enrolled_leads / total_leads * 100) if total_leads > 0 else 0
    except:
        total_leads = 0
        enrolled_leads = 0
        conversion_rate = 0
    
    context = {
        'school_performance': school_performance,
        'total_schools': total_schools,
        'active_schools': active_schools,
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'new_schools': new_schools,
        'new_users': new_users,
        'new_students': new_students,
        'system_health': system_health,
        'role_distribution': role_distribution,
        'total_leads': total_leads,
        'enrolled_leads': enrolled_leads,
        'conversion_rate': conversion_rate,
        'days': days,
    }
    
    return render(request, 'super_admin/analytics.html', context)


@login_required
def super_admin_analytics_export(request):
    """Export analytics summary CSV (per-school metrics and role distribution)"""
    # Only super admin can export
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name != 'super_admin':
                messages.error(request, 'Access denied. Super admin only.')
                return redirect('students_app:super_admin_analytics')
        except:
            messages.error(request, 'Access denied.')
            return redirect('students_app:super_admin_analytics')
    
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="analytics_export.csv"'
    writer = csv.writer(response)
    
    # Per-school metrics
    writer.writerow(['Per-School Metrics'])
    writer.writerow(['School', 'Total Users', 'Created At'])
    schools = School.objects.annotate(total_users=Count('schooluser')).order_by('name')
    for s in schools:
        writer.writerow([s.name, s.total_users, getattr(s, 'created_at', '')])
    
    writer.writerow([])
    # Role distribution
    writer.writerow(['Role Distribution'])
    writer.writerow(['Role', 'Count'])
    roles = SchoolUser.objects.values('role__name').annotate(count=Count('id')).order_by('-count')
    for r in roles:
        writer.writerow([r['role__name'], r['count']])
    
    return response


@login_required
def edit_school_features(request, school_id):
    """Edit per-school feature toggles (tri-state: inherit/enable/disable)"""
    # Only super admin can edit features
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Super admin only.')
        return redirect('students_app:super_admin_analytics')
    
    school = get_object_or_404(School, id=school_id)
    config = SchoolFeatureConfiguration.get_or_create_for_school(school)
    feature_definitions = list(iter_all_features())
    
    if request.method == 'POST':
        for definition in feature_definitions:
            state = request.POST.get(definition.key, 'inherit')
            if state == 'inherit':
                override_value = None
            elif state == 'enabled':
                override_value = True
            elif state == 'disabled':
                override_value = False
            else:
                override_value = None

            config.set_feature_state(definition.key, override_value, definition)

        config.save()
        messages.success(request, f'Features updated for "{school.name}".')
        return redirect('students_app:edit_school_features', school_id=school.id)
    
    # Build grouped context with effective values
    global_config = SystemConfiguration.get_config()
    grouped_features = []
    for group in FEATURE_GROUPS:
        entries = []
        for definition in group["features"]:
            override_value = config.get_feature_state(definition.key, definition)
            global_value = global_config.get_feature_state(definition.key, definition)

            if override_value is None:
                state = 'inherit'
                effective = global_value
            else:
                state = 'enabled' if override_value else 'disabled'
                effective = override_value

            entries.append({
                "definition": definition,
                "state": state,
                "effective": effective,
                "global": global_value,
            })

        grouped_features.append({
            "id": group["id"],
            "label": group["label"],
            "features": entries,
        })
    
    context = {
        'school': school,
        'grouped_features': grouped_features,
    }
    return render(request, 'super_admin/edit_school_features.html', context)

@login_required
def super_admin_configuration(request):
    """Configuration Settings - Feature Toggles & Customization"""
    # Check super admin permission
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name != 'super_admin':
                messages.error(request, 'Access denied. Super admin only.')
                return redirect('students_app:admin_dashboard')
        except:
            messages.error(request, 'Access denied.')
            return redirect('students_app:admin_dashboard')
    
    # Import SystemConfiguration
    try:
        from .system_config import SystemConfiguration
    except ImportError:
        # Fallback if model not available
        messages.error(request, 'Configuration model not available. Please run migrations.')
        return redirect('students_app:admin_dashboard')
    
    # Get or create configuration
    config = SystemConfiguration.get_config()
    
    feature_definitions = list(iter_all_features())
    
    if request.method == 'POST':
        for definition in feature_definitions:
            enabled = request.POST.get(definition.key) == 'on'
            config.set_feature_state(definition.key, enabled, definition)
        
        config.save()
        messages.success(request, 'Configuration updated successfully!')
        return redirect('students_app:super_admin_configuration')
    
    # Convert config to dictionary for template
    grouped_features = []
    for group in FEATURE_GROUPS:
        entries = []
        for definition in group["features"]:
            entries.append({
                "definition": definition,
                "enabled": config.get_feature_state(definition.key, definition),
            })
        grouped_features.append({
            "id": group["id"],
            "label": group["label"],
            "features": entries,
        })
    
    context = {
        'grouped_features': grouped_features,
    }
    
    return render(request, 'super_admin/configuration.html', context)


@login_required
def super_admin_security(request):
    """Security Controls - Data Protection & Access Management"""
    # Check super admin permission
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name != 'super_admin':
                messages.error(request, 'Access denied. Super admin only.')
                return redirect('students_app:admin_dashboard')
        except:
            messages.error(request, 'Access denied.')
            return redirect('students_app:admin_dashboard')
    
    # Import SecuritySettings
    try:
        from .system_config import SecuritySettings
    except ImportError:
        messages.error(request, 'Security settings model not available. Please run migrations.')
        return redirect('students_app:admin_dashboard')
    
    # Get or create security settings
    security_settings = SecuritySettings.get_settings()
    
    # Security statistics
    security_stats = {
        'total_active_sessions': 0,  # Can be implemented with session tracking
        'failed_login_attempts': 0,  # Can be implemented with login tracking
        'password_resets_24h': 0,  # Can be implemented
        'data_backup_status': 'up_to_date',  # Can be implemented
    }
    
    if request.method == 'POST':
        # Update security settings from form data
        security_settings.require_2fa = request.POST.get('require_2fa') == 'on'
        security_settings.password_min_length = int(request.POST.get('password_min_length', 8))
        security_settings.password_complexity = request.POST.get('password_complexity') == 'on'
        security_settings.session_timeout = int(request.POST.get('session_timeout', 30))
        security_settings.ip_whitelist_enabled = request.POST.get('ip_whitelist_enabled') == 'on'
        security_settings.audit_logging = request.POST.get('audit_logging') == 'on'
        security_settings.save()
        messages.success(request, 'Security settings updated successfully!')
        return redirect('students_app:super_admin_security')
    
    # Convert settings to dictionary for template
    access_settings = {
        'require_2fa': security_settings.require_2fa,
        'password_min_length': security_settings.password_min_length,
        'password_complexity': security_settings.password_complexity,
        'session_timeout': security_settings.session_timeout,
        'ip_whitelist_enabled': security_settings.ip_whitelist_enabled,
        'audit_logging': security_settings.audit_logging,
    }
    
    context = {
        'security_stats': security_stats,
        'access_settings': access_settings,
    }
    
    return render(request, 'super_admin/security.html', context)


# ---------------- Notifications (lightweight, no DB) ----------------
def _compute_notifications():
    """Build a lightweight notifications list without new DB tables."""
    notifications = []
    # Recent schools
    try:
        recent_schools = School.objects.order_by('-created_at')[:5]
        for s in recent_schools:
            notifications.append({
                'type': 'school',
                'icon': 'fa-school',
                'title': f'New school: {s.name}',
                'message': 'School was created recently',
                'time': s.created_at.isoformat() if hasattr(s, 'created_at') else ''
            })
    except Exception:
        pass
    # Recent users
    try:
        recent_users = SchoolUser.objects.select_related('user', 'role').order_by('-created_at')[:5]
        for su in recent_users:
            display = su.user.get_full_name() or su.user.username
            role_name = getattr(su.role, "display_name", None) or getattr(su.role, "name", "")
            notifications.append({
                'type': 'user',
                'icon': 'fa-user-plus',
                'title': f'New user: {display}',
                'message': f'Role: {role_name}',
                'time': su.created_at.isoformat() if hasattr(su, 'created_at') else ''
            })
    except Exception:
        pass
    # Inactive schools as alerts
    try:
        inactive_schools = School.objects.filter(subscription_active=False)[:5]
        for s in inactive_schools:
            notifications.append({
                'type': 'alert',
                'icon': 'fa-exclamation-triangle',
                'title': f'Inactive subscription: {s.name}',
                'message': 'Subscription inactive',
                'time': s.created_at.isoformat() if hasattr(s, 'created_at') else ''
            })
    except Exception:
        pass
    return notifications[:10]


@login_required
def notifications_json(request):
    """Return latest notifications as JSON with a count."""
    items = _compute_notifications()
    return JsonResponse({'count': len(items), 'items': items})


@login_required
def notifications_feed(request):
    """HTML feed of notifications."""
    # Access: super admin, assistants, school admin
    try:
        role = request.user.school_profile.role.name
        if role not in ['super_admin', 'assistant_viewer', 'assistant_creator', 'school_admin']:
            messages.error(request, 'Access denied.')
            return redirect('students_app:admin_dashboard')
    except Exception:
        if not request.user.is_superuser:
            messages.error(request, 'Access denied.')
            return redirect('students_app:admin_dashboard')
    items = _compute_notifications()
    return render(request, 'super_admin/notifications.html', {'notifications': items})

@login_required
@require_http_methods(["POST"])
def update_user_access_level(request, user_id):
    """Update user access level (AJAX)"""
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name != 'super_admin':
                return JsonResponse({'success': False, 'error': 'Access denied'})
        except:
            return JsonResponse({'success': False, 'error': 'Access denied'})
    
    user = get_object_or_404(SchoolUser, id=user_id)
    new_role_id = request.POST.get('role_id')
    
    try:
        new_role = UserRole.objects.get(id=new_role_id)
        user.role = new_role
        user.save()
        return JsonResponse({'success': True, 'message': 'Access level updated'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def delete_user(request, user_id):
    """Delete a user (with confirmation)"""
    # Check super admin permission
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name != 'super_admin':
                messages.error(request, 'Access denied. Super admin only.')
                return redirect('students_app:super_admin_user_management')
        except:
            messages.error(request, 'Access denied.')
            return redirect('students_app:super_admin_user_management')
    
    # Get the user
    school_user = get_object_or_404(SchoolUser, id=user_id)
    user = school_user.user
    user_name = user.get_full_name() or user.username
    
    # Prevent deleting yourself
    if user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('students_app:super_admin_user_management')
    
    if request.method == 'POST':
        try:
            # Delete the SchoolUser (this will cascade to User if CASCADE is set)
            # But we'll delete User explicitly to be safe
            user.delete()  # This will also delete SchoolUser due to CASCADE
            messages.success(request, f'User "{user_name}" has been deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
        
        return redirect('students_app:super_admin_user_management')
    
    # GET request - show confirmation page
    context = {
        'school_user': school_user,
        'user': user,
        'user_name': user_name,
    }
    return render(request, 'super_admin/delete_user_confirm.html', context)

