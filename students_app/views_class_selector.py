from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import School, Class, Section


@login_required
def class_selector_view(request):
    """Simple class and section selector for forms"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    # Get all classes with their sections
    classes = Class.objects.all().order_by('numeric_value', 'name')
    
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
                    'capacity': section.capacity
                }
                for section in sections
            ]
        })
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'classes': class_data})
    
    context = {
        'classes': class_data,
        'school': school
    }
    
    return render(request, 'students/class_selector/class_selector.html', context)


@login_required
def ajax_get_sections(request, class_id):
    """AJAX endpoint to get sections for a specific class"""
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
                'capacity': section.capacity
            }
            for section in sections
        ]
        
        return JsonResponse({'sections': section_data})
        
    except Class.DoesNotExist:
        return JsonResponse({'error': 'Class not found'}, status=404)


@login_required
def ajax_get_classes_by_school(request, school_id):
    """AJAX endpoint to get classes for a specific school"""
    try:
        # Check if user is super admin or has permission for this school
        user_is_super_admin = request.user.is_superuser or getattr(request.user, 'user_type', '') == 'super_admin'
        
        if not user_is_super_admin:
            # For school users, check if they belong to this school
            user_school = get_user_school(request)
            if not user_school or user_school.id != int(school_id):
                return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get classes for the specified school
        classes = Class.objects.filter(
            school_id=school_id
        ).order_by('numeric_value', 'name')
        
        class_data = [
            {
                'id': class_obj.id,
                'name': class_obj.name,
                'numeric_value': class_obj.numeric_value
            }
            for class_obj in classes
        ]
        
        return JsonResponse({'classes': class_data})
        
    except (ValueError, Class.DoesNotExist):
        return JsonResponse({'error': 'Invalid school ID'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_user_school(request):
    """Get school associated with current user"""
    if hasattr(request.user, 'school_profile') and request.user.school_profile:
        return request.user.school_profile.school
    return None
