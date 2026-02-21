"""
Work & Expense Tracking Views for Super Admin
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import WorkEntry, WorkExpense, TeamMember, School


@login_required
def work_tracking_dashboard(request):
    """Main dashboard for work & expense tracking"""
    # Check if user is super admin
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
    
    # Get date range filter
    date_range = request.GET.get('range', '30')  # Default 30 days
    try:
        days = int(date_range)
    except:
        days = 30
    
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Statistics
    total_work_entries = WorkEntry.objects.count()
    recent_work_entries = WorkEntry.objects.filter(work_date__gte=start_date).count()
    total_expenses = WorkExpense.objects.aggregate(total=Sum('amount'))['total'] or 0
    recent_expenses = WorkExpense.objects.filter(expense_date__gte=start_date).aggregate(total=Sum('amount'))['total'] or 0
    
    # Work by status
    work_by_status = WorkEntry.objects.values('status').annotate(count=Count('id'))
    
    # Work by type
    work_by_type = WorkEntry.objects.filter(work_date__gte=start_date).values('work_type').annotate(count=Count('id')).order_by('-count')[:5]
    
    # Top schools by work entries
    top_schools = WorkEntry.objects.values('school__name').annotate(
        work_count=Count('id'),
        total_expense=Sum('expenses__amount')
    ).order_by('-work_count')[:5]
    
    # Recent work entries
    recent_entries = WorkEntry.objects.select_related('school').prefetch_related('team_members').order_by('-created_at')[:10]
    
    # Active team members
    active_team_members = TeamMember.objects.filter(is_active=True).count()
    
    # Expenses by category
    expenses_by_category = WorkExpense.objects.filter(expense_date__gte=start_date).values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Company vs Team Member expenses
    company_expenses = WorkExpense.objects.filter(paid_by='company', expense_date__gte=start_date).aggregate(total=Sum('amount'))['total'] or 0
    team_member_expenses = WorkExpense.objects.filter(paid_by='team_member', expense_date__gte=start_date).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'total_work_entries': total_work_entries,
        'recent_work_entries': recent_work_entries,
        'total_expenses': total_expenses,
        'recent_expenses': recent_expenses,
        'work_by_status': work_by_status,
        'work_by_type': work_by_type,
        'top_schools': top_schools,
        'recent_entries': recent_entries,
        'active_team_members': active_team_members,
        'expenses_by_category': expenses_by_category,
        'company_expenses': company_expenses,
        'team_member_expenses': team_member_expenses,
        'date_range': days,
    }
    
    return render(request, 'work_tracking/dashboard.html', context)


@login_required
def work_entry_list(request):
    """List all work entries with filters"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
    
    # Filters
    school_id = request.GET.get('school')
    work_type = request.GET.get('work_type')
    status = request.GET.get('status')
    team_member_id = request.GET.get('team_member')
    search = request.GET.get('search', '')
    
    work_entries = WorkEntry.objects.select_related('school').prefetch_related('team_members', 'expenses')
    
    if school_id:
        work_entries = work_entries.filter(school_id=school_id)
    if work_type:
        work_entries = work_entries.filter(work_type=work_type)
    if status:
        work_entries = work_entries.filter(status=status)
    if team_member_id:
        work_entries = work_entries.filter(team_members__id=team_member_id)
    if search:
        work_entries = work_entries.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(school__name__icontains=search)
        )
    
    # Add expense totals
    for entry in work_entries:
        entry.expense_total = entry.expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get filter options
    schools = School.objects.all().order_by('name')
    team_members = TeamMember.objects.filter(is_active=True).order_by('name')
    
    context = {
        'work_entries': work_entries,
        'schools': schools,
        'team_members': team_members,
        'current_school': school_id,
        'current_work_type': work_type,
        'current_status': status,
        'current_team_member': team_member_id,
        'current_search': search,
    }
    
    return render(request, 'work_tracking/work_entry_list.html', context)


@login_required
def work_entry_create(request):
    """Create new work entry"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
    
    if request.method == 'POST':
        try:
            school_id = request.POST.get('school')
            work_type = request.POST.get('work_type')
            title = request.POST.get('title')
            description = request.POST.get('description')
            location = request.POST.get('location')
            work_date = request.POST.get('work_date')
            status = request.POST.get('status', 'completed')
            hours_spent = request.POST.get('hours_spent') or None
            notes = request.POST.get('notes', '')
            team_member_ids = request.POST.getlist('team_members')
            
            # Create work entry
            work_entry = WorkEntry.objects.create(
                school_id=school_id,
                work_type=work_type,
                title=title,
                description=description,
                location=location,
                work_date=work_date,
                status=status,
                hours_spent=hours_spent,
                notes=notes,
                created_by=request.user
            )
            
            # Add team members
            if team_member_ids:
                work_entry.team_members.set(team_member_ids)
            
            messages.success(request, f'Work entry "{title}" created successfully!')
            return redirect('students_app:work_detail', work_id=work_entry.id)
            
        except Exception as e:
            messages.error(request, f'Error creating work entry: {str(e)}')
    
    schools = School.objects.all().order_by('name')
    team_members = TeamMember.objects.filter(is_active=True).order_by('name')
    
    context = {
        'schools': schools,
        'team_members': team_members,
    }
    
    return render(request, 'work_tracking/work_entry_form.html', context)


@login_required
def work_entry_detail(request, work_id):
    """View work entry details with expenses"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
    
    work_entry = get_object_or_404(
        WorkEntry.objects.select_related('school', 'created_by').prefetch_related('team_members', 'expenses'),
        id=work_id
    )
    
    # Calculate expense totals
    total_expenses = work_entry.expenses.aggregate(total=Sum('amount'))['total'] or 0
    company_paid = work_entry.expenses.filter(paid_by='company').aggregate(total=Sum('amount'))['total'] or 0
    team_paid = work_entry.expenses.filter(paid_by='team_member').aggregate(total=Sum('amount'))['total'] or 0
    
    # Expenses by category
    expenses_by_category = work_entry.expenses.values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    context = {
        'work_entry': work_entry,
        'total_expenses': total_expenses,
        'company_paid': company_paid,
        'team_paid': team_paid,
        'expenses_by_category': expenses_by_category,
    }
    
    return render(request, 'work_tracking/work_entry_detail.html', context)


@login_required
def work_entry_edit(request, work_id):
    """Edit existing work entry"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
    
    work_entry = get_object_or_404(WorkEntry, id=work_id)
    
    if request.method == 'POST':
        try:
            work_entry.school_id = request.POST.get('school')
            work_entry.work_type = request.POST.get('work_type')
            work_entry.title = request.POST.get('title')
            work_entry.description = request.POST.get('description')
            work_entry.location = request.POST.get('location')
            work_entry.work_date = request.POST.get('work_date')
            work_entry.status = request.POST.get('status', 'completed')
            work_entry.hours_spent = request.POST.get('hours_spent') or None
            work_entry.notes = request.POST.get('notes', '')
            work_entry.save()
            
            # Update team members
            team_member_ids = request.POST.getlist('team_members')
            work_entry.team_members.set(team_member_ids)
            
            messages.success(request, f'Work entry "{work_entry.title}" updated successfully!')
            return redirect('students_app:work_detail', work_id=work_entry.id)
            
        except Exception as e:
            messages.error(request, f'Error updating work entry: {str(e)}')
    
    schools = School.objects.all().order_by('name')
    team_members = TeamMember.objects.filter(is_active=True).order_by('name')
    
    context = {
        'work_entry': work_entry,
        'schools': schools,
        'team_members': team_members,
        'is_edit': True,
    }
    
    return render(request, 'work_tracking/work_entry_form.html', context)


@login_required
def expense_create(request, work_id):
    """Add expense to work entry"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
    
    work_entry = get_object_or_404(WorkEntry, id=work_id)
    
    if request.method == 'POST':
        try:
            category = request.POST.get('category')
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            paid_by = request.POST.get('paid_by')
            team_member_id = request.POST.get('team_member') or None
            expense_date = request.POST.get('expense_date')
            receipt_number = request.POST.get('receipt_number', '')
            notes = request.POST.get('notes', '')
            
            WorkExpense.objects.create(
                work_entry=work_entry,
                category=category,
                description=description,
                amount=amount,
                paid_by=paid_by,
                team_member_id=team_member_id,
                expense_date=expense_date,
                receipt_number=receipt_number,
                notes=notes
            )
            
            messages.success(request, 'Expense added successfully!')
            return redirect('students_app:work_detail', work_id=work_entry.id)
            
        except Exception as e:
            messages.error(request, f'Error adding expense: {str(e)}')
    
    team_members = TeamMember.objects.filter(is_active=True).order_by('name')
    
    context = {
        'work_entry': work_entry,
        'team_members': team_members,
    }
    
    return render(request, 'work_tracking/expense_form.html', context)


@login_required
def team_member_list(request):
    """List all team members"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
    
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'active')
    
    team_members = TeamMember.objects.all()
    
    if status == 'active':
        team_members = team_members.filter(is_active=True)
    elif status == 'inactive':
        team_members = team_members.filter(is_active=False)
    
    if search:
        team_members = team_members.filter(
            Q(name__icontains=search) | 
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(role__icontains=search)
        )
    
    # Add work and expense stats
    for member in team_members:
        member.work_count = member.work_entries.count()
        member.expenses_paid = member.workexpense_set.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'team_members': team_members,
        'current_search': search,
        'current_status': status,
    }
    
    return render(request, 'work_tracking/team_member_list.html', context)


@login_required
def team_member_create(request):
    """Create new team member"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            email = request.POST.get('email', '')
            role = request.POST.get('role')
            joining_date = request.POST.get('joining_date')
            is_active = request.POST.get('is_active') == 'on'
            
            TeamMember.objects.create(
                name=name,
                phone=phone,
                email=email or None,
                role=role,
                joining_date=joining_date,
                is_active=is_active
            )
            
            messages.success(request, f'Team member "{name}" added successfully!')
            return redirect('students_app:team_member_list')
            
        except Exception as e:
            messages.error(request, f'Error creating team member: {str(e)}')
    
    context = {}
    return render(request, 'work_tracking/team_member_form.html', context)


@login_required
def reports_work_summary(request):
    """Generate work summary reports"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
    
    # Date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    school_id = request.GET.get('school')
    team_member_id = request.GET.get('team_member')
    
    work_entries = WorkEntry.objects.select_related('school').prefetch_related('team_members', 'expenses')
    
    if start_date:
        work_entries = work_entries.filter(work_date__gte=start_date)
    if end_date:
        work_entries = work_entries.filter(work_date__lte=end_date)
    if school_id:
        work_entries = work_entries.filter(school_id=school_id)
    if team_member_id:
        work_entries = work_entries.filter(team_members__id=team_member_id)
    
    # Calculate totals
    total_work_count = work_entries.count()
    total_expenses = WorkExpense.objects.filter(work_entry__in=work_entries).aggregate(total=Sum('amount'))['total'] or 0
    total_hours = work_entries.aggregate(total=Sum('hours_spent'))['total'] or 0
    
    # Work by type
    work_by_type = work_entries.values('work_type').annotate(count=Count('id')).order_by('-count')
    
    # Work by school
    work_by_school = work_entries.values('school__name').annotate(
        work_count=Count('id'),
        total_expense=Sum('expenses__amount')
    ).order_by('-work_count')
    
    # Work by team member
    work_by_member = TeamMember.objects.filter(work_entries__in=work_entries).annotate(
        work_count=Count('work_entries'),
        total_hours=Sum('work_entries__hours_spent')
    ).order_by('-work_count')
    
    schools = School.objects.all().order_by('name')
    team_members = TeamMember.objects.filter(is_active=True).order_by('name')
    
    context = {
        'work_entries': work_entries,
        'total_work_count': total_work_count,
        'total_expenses': total_expenses,
        'total_hours': total_hours,
        'work_by_type': work_by_type,
        'work_by_school': work_by_school,
        'work_by_member': work_by_member,
        'schools': schools,
        'team_members': team_members,
        'start_date': start_date,
        'end_date': end_date,
        'current_school': school_id,
        'current_team_member': team_member_id,
    }
    
    return render(request, 'work_tracking/reports.html', context)


@login_required
def work_delete(request, work_id):
    """Delete work entry"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
    
    work_entry = get_object_or_404(WorkEntry, id=work_id)
    
    if request.method == 'POST':
        work_entry.delete()
        messages.success(request, 'Work entry deleted successfully!')
        return redirect('students_app:work_list')
        
    return render(request, 'work_tracking/confirm_delete.html', {'obj': work_entry, 'type': 'Work Entry'})


@login_required
def expense_edit(request, expense_id):
    """Edit expense"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
        
    expense = get_object_or_404(WorkExpense, id=expense_id)
    
    if request.method == 'POST':
        try:
            expense.category = request.POST.get('category')
            expense.description = request.POST.get('description')
            expense.amount = request.POST.get('amount')
            expense.paid_by = request.POST.get('paid_by')
            expense.team_member_id = request.POST.get('team_member') or None
            expense.expense_date = request.POST.get('expense_date')
            expense.receipt_number = request.POST.get('receipt_number', '')
            expense.notes = request.POST.get('notes', '')
            expense.save()
            
            messages.success(request, 'Expense updated successfully!')
            return redirect('students_app:work_detail', work_id=expense.work_entry.id)
            
        except Exception as e:
            messages.error(request, f'Error updating expense: {str(e)}')
            
    team_members = TeamMember.objects.filter(is_active=True).order_by('name')
    
    context = {
        'expense': expense,
        'work_entry': expense.work_entry,
        'team_members': team_members,
        'is_edit': True
    }
    return render(request, 'work_tracking/expense_form.html', context)


@login_required
def expense_delete(request, expense_id):
    """Delete expense"""
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'school_profile') and 
             request.user.school_profile.role.name == 'super_admin')):
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('students_app:home')
        
    expense = get_object_or_404(WorkExpense, id=expense_id)
    work_id = expense.work_entry.id
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('students_app:work_detail', work_id=work_id)
        
    return render(request, 'work_tracking/confirm_delete.html', {'obj': expense, 'type': 'Expense'})


