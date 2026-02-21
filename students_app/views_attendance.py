from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from .models import School, Class, Section, Student, Attendance
import json
from datetime import datetime, date


def get_user_school(request):
    """Get school associated with current user"""
    if hasattr(request.user, 'school_profile') and request.user.school_profile:
        return request.user.school_profile.school
    return None


@login_required
def attendance_dashboard(request):
    """Main attendance dashboard with class selector"""
    school = get_user_school(request)
    
    if not school:
        messages.error(request, "Please set up your school first.")
        return redirect('students_app:school_setup_wizard')
    
    # Get today's attendance summary
    today = date.today()
    
    # Get all classes
    classes = Class.objects.all().order_by('numeric_value', 'name')
    
    # Get attendance counts for today
    total_students = Student.objects.filter(school=school).count()
    present_today = Attendance.objects.filter(
        student__school=school,
        date=today,
        status='present'
    ).count()
    absent_today = Attendance.objects.filter(
        student__school=school,
        date=today,
        status='absent'
    ).count()
    
    context = {
        'classes': classes,
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': absent_today,
        'attendance_rate': round((present_today / total_students * 100) if total_students > 0 else 0, 1),
        'today': today
    }
    
    return render(request, 'students/attendance/attendance_dashboard.html', context)


@login_required
def take_attendance(request):
    """Take attendance for selected class and section"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        section_id = request.POST.get('section_id')
        attendance_data = request.POST.get('attendance_data', '{}')
        
        if not class_id or not section_id:
            return JsonResponse({'error': 'Class and section required'}, status=400)
        
        try:
            class_obj = Class.objects.get(id=class_id)
            section_obj = Section.objects.get(id=section_id)
            
            # Get students for this class and section
            students = Student.objects.filter(
                current_class=class_obj,
                section=section_obj,
                school=school
            )
            
            # Parse attendance data
            attendance_json = json.loads(attendance_data)
            today = date.today()
            
            # Save attendance for each student
            for student in students:
                status = attendance_json.get(str(student.id), 'present')
                
                # Update or create attendance record
                attendance, created = Attendance.objects.get_or_create(
                    student=student,
                    date=today,
                    defaults={'status': status}
                )
                
                if not created:
                    attendance.status = status
                    attendance.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Attendance saved for {students.count()} students'
            })
            
        except (Class.DoesNotExist, Section.DoesNotExist):
            return JsonResponse({'error': 'Class or section not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # GET request - show attendance form
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')
    
    if not class_id or not section_id:
        return redirect('students_app:attendance_dashboard')
    
    try:
        class_obj = Class.objects.get(id=class_id)
        section_obj = Section.objects.get(id=section_id)
        
        # Get students for this class and section
        students = Student.objects.filter(
            current_class=class_obj,
            section=section_obj,
            school=school
        ).order_by('roll_number', 'first_name')
        
        # Get today's attendance if exists
        today = date.today()
        existing_attendance = {
            att.student.id: att.status 
            for att in Attendance.objects.filter(
                student__in=students,
                date=today
            )
        }
        
        context = {
            'class_obj': class_obj,
            'section_obj': section_obj,
            'students': students,
            'existing_attendance': existing_attendance,
            'today': today
        }
        
        return render(request, 'students/attendance/take_attendance.html', context)
        
    except (Class.DoesNotExist, Section.DoesNotExist):
        messages.error(request, 'Class or section not found')
        return redirect('students_app:attendance_dashboard')


@login_required
def ajax_get_students_for_attendance(request, class_id, section_id):
    """AJAX endpoint to get students for attendance"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    try:
        class_obj = Class.objects.get(id=class_id)
        section_obj = Section.objects.get(id=section_id)
        
        students = Student.objects.filter(
            current_class=class_obj,
            section=section_obj,
            school=school
        ).order_by('roll_number', 'first_name')
        
        student_data = []
        for student in students:
            student_data.append({
                'id': student.id,
                'name': student.get_full_name(),
                'roll_number': student.roll_number or '',
                'admission_number': student.admission_number,
                'photo_url': student.photo.url if student.photo else '/static/images/default-avatar.png'
            })
        
        return JsonResponse({'students': student_data})
        
    except (Class.DoesNotExist, Section.DoesNotExist):
        return JsonResponse({'error': 'Class or section not found'}, status=404)


@login_required
def attendance_report(request):
    """View attendance reports"""
    school = get_user_school(request)
    
    if not school:
        messages.error(request, "Please set up your school first.")
        return redirect('students_app:school_setup_wizard')
    
    # Get filter parameters
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    # Get classes and sections for filters
    classes = Class.objects.all().order_by('numeric_value', 'name')
    sections = []
    if class_id:
        sections = Section.objects.filter(class_assigned_id=class_id).order_by('name')
    
    # Build query
    attendance_query = Attendance.objects.filter(student__school=school)
    
    if class_id:
        attendance_query = attendance_query.filter(student__current_class_id=class_id)
    if section_id:
        attendance_query = attendance_query.filter(student__section_id=section_id)
    if from_date:
        attendance_query = attendance_query.filter(date__gte=from_date)
    if to_date:
        attendance_query = attendance_query.filter(date__lte=to_date)
    
    # Get attendance records
    attendance_records = attendance_query.select_related('student').order_by('-date', 'student__first_name')
    
    # Calculate statistics
    total_records = attendance_records.count()
    present_count = attendance_records.filter(status='present').count()
    absent_count = attendance_records.filter(status='absent').count()
    late_count = attendance_records.filter(status='late').count()
    
    context = {
        'classes': classes,
        'sections': sections,
        'attendance_records': attendance_records[:100],  # Limit to 100 records
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'selected_class': class_id,
        'selected_section': section_id,
        'from_date': from_date,
        'to_date': to_date
    }
    
    return render(request, 'students/attendance/attendance_report.html', context)
