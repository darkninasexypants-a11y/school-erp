from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import School, Class, Section, AcademicYear, Student
import json


def get_user_school(request):
    """Get school associated with current user"""
    if hasattr(request.user, 'school_profile') and request.user.school_profile:
        return request.user.school_profile.school
    return None


@login_required
def class_list_management(request):
    """Class list management for school admin"""
    school = get_user_school(request)
    
    if not school:
        messages.error(request, "Please set up your school first.")
        return redirect('students_app:school_setup_wizard')
    
    # Get current academic year
    current_year = AcademicYear.objects.filter(is_current=True).first()
    if not current_year:
        messages.warning(request, "No current academic year found. Please set up academic year first.")
        return redirect('students_app:school_setup_wizard')
    
    # Get all classes with their sections
    classes = Class.objects.all().order_by('numeric_value', 'name')
    
    # Add section counts to each class
    class_data = []
    for class_obj in classes:
        sections = Section.objects.filter(class_assigned=class_obj).order_by('name')
        class_data.append({
            'id': class_obj.id,
            'name': class_obj.name,
            'numeric_value': class_obj.numeric_value,
            'sections': [
                {
                    'id': section.id,
                    'name': section.name,
                    'student_count': section.students.count()
                }
                for section in sections
            ],
            'total_sections': sections.count(),
            'total_students': sum(section.students.count() for section in sections)
        })
    
    context = {
        'classes': class_data,
        'current_year': current_year,
        'total_classes': classes.count(),
        'total_sections': Section.objects.count(),
        'total_students': Student.objects.filter(school=school).count()
    }
    
    return render(request, 'students/class_management/class_list_management.html', context)


@login_required
def add_class(request):
    """Add new class"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            numeric_value = request.POST.get('numeric_value')
            
            if not name or not numeric_value:
                return JsonResponse({'error': 'Class name and numeric value are required'}, status=400)
            
            # Check if class already exists
            if Class.objects.filter(name=name, school=school).exists():
                return JsonResponse({'error': 'Class with this name already exists'}, status=400)
            
            # Create new class
            class_obj = Class.objects.create(
                name=name,
                numeric_value=int(numeric_value),
                school=school
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Class "{name}" created successfully!',
                'class': {
                    'id': class_obj.id,
                    'name': class_obj.name,
                    'numeric_value': class_obj.numeric_value
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error creating class: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=400)


@login_required
def add_section(request):
    """Add new section to a class"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    if request.method == 'POST':
        try:
            class_id = request.POST.get('class_id')
            name = request.POST.get('name')
            capacity = request.POST.get('capacity', 50)
            
            if not class_id or not name:
                return JsonResponse({'error': 'Class ID and section name are required'}, status=400)
            
            # Get class object
            class_obj = get_object_or_404(Class, id=class_id)
            
            # Check if section already exists for this class
            if Section.objects.filter(class_assigned=class_obj, name=name).exists():
                return JsonResponse({'error': 'Section with this name already exists for this class'}, status=400)
            
            # Create new section
            section_obj = Section.objects.create(
                class_assigned=class_obj,
                name=name,
                capacity=int(capacity)
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Section "{name}" created successfully!',
                'section': {
                    'id': section_obj.id,
                    'name': section_obj.name,
                    'capacity': section_obj.capacity,
                    'class_name': class_obj.name
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error creating section: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=400)


@login_required
def edit_class(request, class_id):
    """Edit existing class"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    class_obj = get_object_or_404(Class, id=class_id)
    
    if class_obj.school != school:
        return JsonResponse({'error': 'Class not found in your school'}, status=400)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            numeric_value = request.POST.get('numeric_value')
            
            if not name or not numeric_value:
                return JsonResponse({'error': 'Class name and numeric value are required'}, status=400)
            
            # Check if name conflicts with another class
            if Class.objects.filter(name=name, school=school).exclude(id=class_id).exists():
                return JsonResponse({'error': 'Class with this name already exists'}, status=400)
            
            # Update class
            class_obj.name = name
            class_obj.numeric_value = int(numeric_value)
            class_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Class "{name}" updated successfully!',
                'class': {
                    'id': class_obj.id,
                    'name': class_obj.name,
                    'numeric_value': class_obj.numeric_value
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error updating class: {str(e)}'}, status=500)
    
    return JsonResponse({
        'success': True,
        'class': {
            'id': class_obj.id,
            'name': class_obj.name,
            'numeric_value': class_obj.numeric_value
        }
    })


@login_required
def edit_section(request, section_id):
    """Edit existing section"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    section_obj = get_object_or_404(Section, id=section_id)
    
    if section_obj.class_assigned.school != school:
        return JsonResponse({'error': 'Section not found in your school'}, status=400)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            capacity = request.POST.get('capacity', 50)
            
            if not name:
                return JsonResponse({'error': 'Section name is required'}, status=400)
            
            # Check if name conflicts with another section in same class
            if Section.objects.filter(class_assigned=section_obj.class_assigned, name=name).exclude(id=section_id).exists():
                return JsonResponse({'error': 'Section with this name already exists for this class'}, status=400)
            
            # Update section
            section_obj.name = name
            section_obj.capacity = int(capacity)
            section_obj.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Section "{name}" updated successfully!',
                'section': {
                    'id': section_obj.id,
                    'name': section_obj.name,
                    'capacity': section_obj.capacity,
                    'class_name': section_obj.class_assigned.name
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error updating section: {str(e)}'}, status=500)
    
    return JsonResponse({
        'success': True,
        'section': {
            'id': section_obj.id,
            'name': section_obj.name,
            'capacity': section_obj.capacity,
            'class_name': section_obj.class_assigned.name
        }
    })


@login_required
def delete_class(request, class_id):
    """Delete class"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    class_obj = get_object_or_404(Class, id=class_id)
    
    if class_obj.school != school:
        return JsonResponse({'error': 'Class not found in your school'}, status=400)
    
    if request.method == 'DELETE':
        try:
            # Check if class has sections
            sections_count = Section.objects.filter(class_assigned=class_obj).count()
            if sections_count > 0:
                return JsonResponse({'error': 'Cannot delete class with existing sections. Delete sections first.'}, status=400)
            
            # Check if class has students
            students_count = Student.objects.filter(current_class=class_obj).count()
            if students_count > 0:
                return JsonResponse({'error': 'Cannot delete class with enrolled students. Transfer students first.'}, status=400)
            
            class_name = class_obj.name
            class_obj.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Class "{class_name}" deleted successfully!'
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error deleting class: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Only DELETE method allowed'}, status=400)


@login_required
def delete_section(request, section_id):
    """Delete section"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    section_obj = get_object_or_404(Section, id=section_id)
    
    if section_obj.class_assigned.school != school:
        return JsonResponse({'error': 'Section not found in your school'}, status=400)
    
    if request.method == 'DELETE':
        try:
            # Check if section has students
            students_count = Student.objects.filter(section=section_obj).count()
            if students_count > 0:
                return JsonResponse({'error': 'Cannot delete section with enrolled students. Transfer students first.'}, status=400)
            
            section_name = f"{section_obj.class_assigned.name} - {section_obj.name}"
            section_obj.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Section "{section_name}" deleted successfully!'
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error deleting section: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Only DELETE method allowed'}, status=400)


@login_required
def export_class_data(request):
    """Export class data as JSON"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    try:
        classes = Class.objects.filter(school=school).values('name', 'numeric_value').order_by('numeric_value', 'name')
        return JsonResponse({
            'success': True,
            'classes': list(classes),
            'export_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return JsonResponse({'error': f'Error exporting data: {str(e)}'}, status=500)


@login_required
def get_class_sections(request, class_id):
    """Get sections for a specific class - JSON response for AJAX"""
    school = get_user_school(request)
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    try:
        class_obj = Class.objects.get(id=class_id)
        sections = Section.objects.filter(class_assigned=class_obj).order_by('name')
        
        section_data = [
            {
                'id': section.id,
                'name': section.name,
                'student_count': section.students.count()
            }
            for section in sections
        ]
        
        return JsonResponse({'sections': section_data})
    except Class.DoesNotExist:
        return JsonResponse({'error': 'Class not found'}, status=404)
