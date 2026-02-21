"""
SCHOOL SETUP WIZARD VIEW
Complete school configuration system with smart assignment capabilities
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse

def school_setup_wizard(request):
    """Complete school setup wizard with 4 steps"""
    from .models import School, Class, Section, AcademicYear, UserRole, SchoolUser
    
    # Store form data in session
    if request.method == 'POST':
        step = int(request.POST.get('step', 1))
        
        # Save current step data to session
        form_data = request.session.get('school_setup_data', {})
        
        if step == 1:
            # Basic school information
            form_data.update({
                'school_name': request.POST.get('school_name'),
                'school_code': request.POST.get('school_code'),
                'school_address': request.POST.get('school_address'),
                'school_phone': request.POST.get('school_phone'),
                'school_email': request.POST.get('school_email'),
                'school_website': request.POST.get('school_website'),
                'school_type': request.POST.get('school_type'),
            })
            
        elif step == 2:
            # Classes and sections
            form_data.update({
                'total_classes': request.POST.get('total_classes'),
                'sections_per_class': request.POST.get('sections_per_class'),
                'class_naming': request.POST.get('class_naming'),
                'section_naming': request.POST.get('section_naming'),
            })
            
        elif step == 3:
            # Academic years
            form_data.update({
                'current_year_name': request.POST.get('current_year_name'),
                'current_year_start': request.POST.get('current_year_start'),
                'current_year_end': request.POST.get('current_year_end'),
                'previous_years_count': request.POST.get('previous_years_count'),
            })
            
        elif step == 4:
            # Designations - complete setup
            form_data.update({
                'student_designations': request.POST.getlist('student_designations[]'),
                'teacher_designations': request.POST.getlist('teacher_designations[]'),
                'staff_designations': request.POST.getlist('staff_designations[]'),
                'custom_designations': [d for d in request.POST.getlist('custom_designations[]') if d.strip()],
            })
            
            # Complete the setup
            try:
                with transaction.atomic():
                    # Create school
                    school = School.objects.create(
                        name=form_data['school_name'],
                        code=form_data['school_code'],
                        address=form_data.get('school_address', ''),
                        phone=form_data.get('school_phone', ''),
                        email=form_data.get('school_email', ''),
                        website=form_data.get('school_website', ''),
                        school_type=form_data.get('school_type', 'general'),
                        created_by=request.user
                    )
                    
                    # Create classes and sections
                    total_classes = int(form_data['total_classes'])
                    sections_per_class = int(form_data['sections_per_class'])
                    class_naming = form_data.get('class_naming', 'numeric')
                    section_naming = form_data.get('section_naming', 'alphabetical')
                    
                    for class_num in range(1, total_classes + 1):
                        class_name = get_class_name(class_num, class_naming)
                        
                        # Create class
                        school_class = Class.objects.create(
                            name=class_name,
                            numeric_value=class_num,
                            school=school
                        )
                        
                        # Create sections for this class
                        for section_num in range(1, sections_per_class + 1):
                            section_name = get_section_name(section_num, section_naming)
                            
                            Section.objects.create(
                                name=section_name,
                                class_assigned=school_class,
                                capacity=40  # Default capacity
                            )
                    
                    # Create academic years
                    current_year_name = form_data['current_year_name']
                    current_year_start = form_data['current_year_start']
                    current_year_end = form_data['current_year_end']
                    previous_years_count = int(form_data.get('previous_years_count', 2))
                    
                    # Create previous years
                    start_year = int(current_year_name.split('-')[0])
                    for i in range(previous_years_count, 0, -1):
                        year_num = start_year - i
                        prev_year_name = f"{year_num}-{year_num + 1}"
                        
                        AcademicYear.objects.create(
                            name=prev_year_name,
                            start_date=f"{year_num}-04-01",
                            end_date=f"{year_num + 1}-03-31",
                            is_current=False,
                            school=school
                        )
                    
                    # Create current year
                    AcademicYear.objects.create(
                        name=current_year_name,
                        start_date=current_year_start,
                        end_date=current_year_end,
                        is_current=True,
                        school=school
                    )
                    
                    # Create designations
                    all_designations = []
                    
                    # Student designations
                    for designation in form_data.get('student_designations', []):
                        all_designations.append({
                            'name': designation,
                            'user_type': 'student',
                            'is_active': True
                        })
                    
                    # Teacher designations
                    for designation in form_data.get('teacher_designations', []):
                        all_designations.append({
                            'name': designation,
                            'user_type': 'teacher',
                            'is_active': True
                        })
                    
                    # Staff designations
                    for designation in form_data.get('staff_designations', []):
                        all_designations.append({
                            'name': designation,
                            'user_type': 'staff',
                            'is_active': True
                        })
                    
                    # Custom designations
                    for designation in form_data.get('custom_designations', []):
                        all_designations.append({
                            'name': designation,
                            'user_type': 'custom',
                            'is_active': True
                        })
                    
                    # Save designations to session for later use
                    request.session['school_designations'] = all_designations
                    
                    # Create SchoolUser for the admin
                    try:
                        admin_role = UserRole.objects.filter(name__icontains='admin').first()
                        if admin_role:
                            SchoolUser.objects.create(
                                user=request.user,
                                role=admin_role,
                                school=school,
                                login_id=request.user.username,
                                custom_password='Admin@123',
                                phone=form_data.get('school_phone', '')
                            )
                    except Exception as e:
                        print(f"Error creating SchoolUser: {e}")
                    
                    # Clear session data
                    request.session.pop('school_setup_data', None)
                    
                    messages.success(request, f"School '{school.name}' has been successfully set up with {total_classes} classes and {total_classes * sections_per_class} sections!")
                    return redirect('students_app:dashboard')
                    
            except Exception as e:
                messages.error(request, f"Error setting up school: {str(e)}")
                return redirect('students_app:school_setup_wizard')
        
        # Check for previous button
        if 'previous' in request.POST:
            step = max(1, step - 1)
        else:
            step = min(4, step + 1)
        
        request.session['school_setup_data'] = form_data
        return redirect(f'/school-setup/?step={step}')
    
    # GET request
    step = int(request.GET.get('step', 1))
    form_data = request.session.get('school_setup_data', {})
    
    context = {
        'current_step': step,
        'form_data': form_data,
    }
    
    return render(request, 'students/school_setup_wizard.html', context)

def get_class_name(num, pattern):
    """Generate class name based on pattern"""
    if pattern == 'grade':
        return f"Grade {num}"
    elif pattern == 'standard':
        return f"Std {num}"
    elif pattern == 'class':
        return f"Class {num}"
    else:
        return str(num)

def get_section_name(num, pattern):
    """Generate section name based on pattern"""
    if pattern == 'numeric':
        return str(num)
    elif pattern == 'flower':
        flowers = ['Rose', 'Lily', 'Tulip', 'Daisy', 'Sunflower', 'Jasmine', 'Lotus', 'Orchid']
        return flowers[num - 1] if num <= len(flowers) else f"Section {num}"
    elif pattern == 'color':
        colors = ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange', 'Pink', 'Brown']
        return colors[num - 1] if num <= len(colors) else f"Section {num}"
    else:
        return chr(64 + num)  # A, B, C...

def check_school_setup_status(request):
    """API endpoint to check if school is set up"""
    from .models import School, Class, Section
    
    user_school = None
    if hasattr(request.user, 'school_profile'):
        user_school = request.user.school_profile.school
    
    if not user_school:
        return JsonResponse({'setup_required': True, 'message': 'No school found'})
    
    classes_count = Class.objects.filter(school=user_school).count()
    sections_count = Section.objects.filter(class_assigned__school=user_school).count()
    
    if classes_count == 0 or sections_count == 0:
        return JsonResponse({
            'setup_required': True, 
            'message': f'School found but no classes/sections configured ({classes_count} classes, {sections_count} sections)'
        })
    
    return JsonResponse({
        'setup_required': False,
        'school_name': user_school.name,
        'classes_count': classes_count,
        'sections_count': sections_count
    })

def get_school_designations(request):
    """API endpoint to get available designations for the school"""
    from .models import School
    
    user_school = None
    if hasattr(request.user, 'school_profile'):
        user_school = request.user.school_profile.school
    
    if not user_school:
        return JsonResponse({'designations': []})
    
    # Get designations from session or database
    designations = request.session.get('school_designations', [])
    
    # If not in session, return default designations
    if not designations:
        designations = [
            {'name': 'Student', 'user_type': 'student'},
            {'name': 'Class Monitor', 'user_type': 'student'},
            {'name': 'Teacher', 'user_type': 'teacher'},
            {'name': 'Librarian', 'user_type': 'teacher'},
            {'name': 'Principal', 'user_type': 'teacher'},
            {'name': 'Accountant', 'user_type': 'staff'},
            {'name': 'Clerk', 'user_type': 'staff'},
        ]
    
    return JsonResponse({'designations': designations})
