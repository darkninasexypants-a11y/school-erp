from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import Teacher, Student, Staff, SchoolUser
import json


@login_required
def display_credentials(request):
    """Display login credentials for all users"""
    school = get_user_school(request)
    
    if not school:
        messages.error(request, "Please set up your school first.")
        return redirect('students_app:school_setup_wizard')
    
    # Get all users for this school
    credentials_data = []
    
    # Get Teachers
    teachers = Teacher.objects.filter(school=school).select_related('user')
    for teacher in teachers:
        credentials_data.append({
            'type': 'Teacher',
            'name': f"{teacher.user.first_name} {teacher.user.last_name}",
            'username': teacher.user.username,
            'email': teacher.user.email,
            'employee_id': teacher.employee_id,
            'default_password': "Teacher@123",
            'can_login': True,
            'login_url': '/simple_login/',
            'role': 'Teacher'
        })
    
    # Get Students
    students = Student.objects.filter(school=school).select_related('user')
    for student in students:
        credentials_data.append({
            'type': 'Student',
            'name': f"{student.first_name} {student.last_name}",
            'username': student.user.username,
            'email': student.user.email,
            'admission_number': student.admission_number,
            'default_password': "Student@123",
            'can_login': True,
            'login_url': '/simple_login/',
            'role': 'Student'
        })
    
    # Get Staff
    staff_members = Staff.objects.filter(school=school).select_related('user')
    for staff in staff_members:
        credentials_data.append({
            'type': 'Staff',
            'name': f"{staff.user.first_name} {staff.user.last_name}",
            'username': staff.user.username,
            'email': staff.user.email,
            'employee_id': staff.employee_id,
            'default_password': "Staff@123",
            'can_login': True,
            'login_url': '/simple_login/',
            'role': 'Staff'
        })
    
    context = {
        'credentials_data': credentials_data,
        'total_users': len(credentials_data),
        'teachers_count': teachers.count(),
        'students_count': students.count(),
        'staff_count': staff_members.count(),
        'school_name': school.name
    }
    
    return render(request, 'students/credentials/credentials_display.html', context)


@login_required
def export_credentials(request):
    """Export credentials as JSON/Excel"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    # Get all users for this school
    credentials_data = []
    
    # Get Teachers
    teachers = Teacher.objects.filter(school=school).select_related('user')
    for teacher in teachers:
        credentials_data.append({
            'User Type': 'Teacher',
            'Name': f"{teacher.user.first_name} {teacher.user.last_name}",
            'Username': teacher.user.username,
            'Email': teacher.user.email,
            'Employee ID': teacher.employee_id,
            'Default Password': "Teacher@123",
            'Login URL': '/simple_login/',
            'Role': 'Teacher'
        })
    
    # Get Students
    students = Student.objects.filter(school=school).select_related('user')
    for student in students:
        credentials_data.append({
            'User Type': 'Student',
            'Name': f"{student.first_name} {student.last_name}",
            'Username': student.user.username,
            'Email': student.user.email,
            'Admission Number': student.admission_number,
            'Default Password': "Student@123",
            'Login URL': '/simple_login/',
            'Role': 'Student'
        })
    
    # Get Staff
    staff_members = Staff.objects.filter(school=school).select_related('user')
    for staff in staff_members:
        credentials_data.append({
            'User Type': 'Staff',
            'Name': f"{staff.user.first_name} {staff.user.last_name}",
            'Username': staff.user.username,
            'Email': staff.user.email,
            'Employee ID': staff.employee_id,
            'Default Password': "Staff@123",
            'Login URL': '/simple_login/',
            'Role': 'Staff'
        })
    
    return JsonResponse({
        'success': True,
        'credentials': credentials_data,
        'export_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        'school_name': school.name
    })


@login_required
def reset_passwords(request):
    """Reset all passwords to default"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    if request.method == 'POST':
        try:
            # Reset Teacher passwords
            teachers = Teacher.objects.filter(school=school).select_related('user')
            for teacher in teachers:
                teacher.user.set_password("Teacher@123")
                teacher.user.save()
            
            # Reset Student passwords
            students = Student.objects.filter(school=school).select_related('user')
            for student in students:
                student.user.set_password("Student@123")
                student.user.save()
            
            # Reset Staff passwords
            staff_members = Staff.objects.filter(school=school).select_related('user')
            for staff in staff_members:
                staff.user.set_password("Staff@123")
                staff.user.save()
            
            return JsonResponse({
                'success': True,
                'message': f'All passwords reset to default for {school.name}',
                'teachers_reset': teachers.count(),
                'students_reset': students.count(),
                'staff_reset': staff_members.count()
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error resetting passwords: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=400)


def get_user_school(request):
    """Get school associated with current user"""
    if hasattr(request.user, 'school_profile') and request.user.school_profile:
        return request.user.school_profile.school
    return None
