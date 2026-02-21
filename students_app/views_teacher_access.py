from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from .models import School, Class, Section, Student, Teacher, ClassTeacher, Timetable, Subject


def get_teacher_info(request):
    """Get current teacher information and their access level"""
    try:
        teacher = Teacher.objects.get(user=request.user)
        
        # Check if teacher is a class teacher
        class_teacher_assignments = ClassTeacher.objects.filter(
            teacher=teacher,
            academic_year__is_current=True
        )
        
        is_class_teacher = class_teacher_assignments.exists()
        assigned_sections = [assignment.section for assignment in class_teacher_assignments]
        
        # For class teachers, prioritize their assigned classes over timetable
        if is_class_teacher:
            # Class teachers get their assigned sections + any additional classes from timetable
            teacher_classes = []
            timetables = Timetable.objects.filter(teacher=teacher)
            for timetable in timetables:
                if timetable.section not in teacher_classes and timetable.section not in assigned_sections:
                    teacher_classes.append(timetable.section)
            
            all_accessible_sections = assigned_sections + teacher_classes
        else:
            # Subject teachers only get classes from timetable
            teacher_classes = []
            timetables = Timetable.objects.filter(teacher=teacher)
            for timetable in timetables:
                if timetable.section not in teacher_classes:
                    teacher_classes.append(timetable.section)
            
            all_accessible_sections = teacher_classes
        
        return {
            'teacher': teacher,
            'is_class_teacher': is_class_teacher,
            'assigned_sections': assigned_sections,
            'teaching_sections': teacher_classes,
            'all_accessible_sections': all_accessible_sections,
            'primary_sections': assigned_sections if is_class_teacher else teacher_classes
        }
    except Teacher.DoesNotExist:
        return None


@login_required
def teacher_dashboard_restricted(request):
    """Teacher dashboard with access control"""
    teacher_info = get_teacher_info(request)
    
    if not teacher_info:
        messages.error(request, "Teacher profile not found.")
        return redirect('students_app:login')
    
    teacher = teacher_info['teacher']
    is_class_teacher = teacher_info['is_class_teacher']
    accessible_sections = teacher_info['all_accessible_sections']
    primary_sections = teacher_info['primary_sections']  # Class teacher assignments or timetable classes
    
    # Get statistics based on access level
    context = {
        'teacher': teacher,
        'is_class_teacher': is_class_teacher,
        'accessible_sections': accessible_sections,
        'primary_sections': primary_sections,  # Add this for template
        'can_import_students': is_class_teacher,
        'total_students': 0,
        'total_classes': len(accessible_sections),
        'today_classes': []
    }
    
    # Count students in accessible sections
    if accessible_sections:
        context['total_students'] = Student.objects.filter(
            section__in=accessible_sections
        ).count()
        
        # Get today's classes from timetable
        today = timezone.now().date()
        today_timetables = Timetable.objects.filter(
            teacher=teacher,
            weekday=today.weekday()  # Monday=0, matching models.py
        ).select_related('section', 'subject')
        
        context['today_classes'] = today_timetables
    
    return render(request, 'students/teacher/teacher_dashboard_restricted.html', context)


@login_required
def teacher_student_list(request):
    """Student list with access control"""
    teacher_info = get_teacher_info(request)
    
    if not teacher_info:
        messages.error(request, "Teacher profile not found.")
        return redirect('students_app:login')
    
    accessible_sections = teacher_info['all_accessible_sections']
    
    if not accessible_sections:
        messages.warning(request, "You are not assigned to any classes.")
        return redirect('students_app:teacher_dashboard_restricted')
    
    # Get students only from accessible sections
    students = Student.objects.filter(
        section__in=accessible_sections
    ).select_related('current_class', 'section').order_by('current_class__numeric_value', 'section__name', 'roll_number')
    
    context = {
        'students': students,
        'teacher_info': teacher_info,
        'can_import_students': teacher_info['is_class_teacher']
    }
    
    return render(request, 'students/teacher/teacher_student_list.html', context)


@login_required
def teacher_timetable(request):
    """Teacher timetable showing only their assigned classes"""
    teacher_info = get_teacher_info(request)
    
    if not teacher_info:
        messages.error(request, "Teacher profile not found.")
        return redirect('students_app:login')
    
    teacher = teacher_info['teacher']
    
    # Get all timetables for this teacher
    timetables = Timetable.objects.filter(teacher=teacher).select_related(
        'section', 'subject', 'section__class_assigned'
    ).order_by('weekday', 'time_slot__start_time')
    
    # Organize by day
    days = {
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 
        3: 'Thursday', 4: 'Friday', 5: 'Saturday'
    }
    
    timetable_by_day = {}
    for day_num, day_name in days.items():
        timetable_by_day[day_num] = {
            'name': day_name,
            'periods': [t for t in timetables if t.weekday == day_num]
        }
    
    context = {
        'teacher_info': teacher_info,
        'timetable_by_day': timetable_by_day,
        'days': days
    }
    
    return render(request, 'students/teacher/teacher_timetable.html', context)


@login_required
def check_import_permission(request):
    """Check if teacher has permission to import students"""
    teacher_info = get_teacher_info(request)
    
    if not teacher_info:
        return JsonResponse({'has_permission': False, 'message': 'Teacher profile not found'})
    
    has_permission = teacher_info['is_class_teacher']
    
    return JsonResponse({
        'has_permission': has_permission,
        'message': 'Only class teachers can import students' if not has_permission else 'Permission granted'
    })


@login_required
def teacher_class_sections(request):
    """Get list of classes and sections this teacher can access"""
    teacher_info = get_teacher_info(request)
    
    if not teacher_info:
        return JsonResponse({'error': 'Teacher profile not found'}, status=400)
    
    accessible_sections = teacher_info['all_accessible_sections']
    
    sections_data = []
    for section in accessible_sections:
        sections_data.append({
            'id': section.id,
            'name': section.name,
            'class_name': section.class_assigned.name,
            'class_id': section.class_assigned.id,
            'is_class_teacher': section in teacher_info['assigned_sections']
        })
    
    return JsonResponse({
        'sections': sections_data,
        'is_class_teacher': teacher_info['is_class_teacher']
    })


def update_teacher_sidebar_permissions(request):
    """Update sidebar menu based on teacher permissions"""
    teacher_info = get_teacher_info(request)
    
    if not teacher_info:
        return {}
    
    return {
        'can_import_students': teacher_info['is_class_teacher'],
        'can_view_all_students': True,  # All teachers can view their assigned students
        'can_take_attendance': True,    # All teachers can take attendance
        'can_view_reports': True,       # All teachers can view reports for their classes
        'accessible_sections': [section.id for section in teacher_info['all_accessible_sections']]
    }
