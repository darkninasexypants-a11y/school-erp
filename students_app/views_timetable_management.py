from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import School, Class, Section, Teacher, Timetable, Subject, TimeSlot, AcademicYear
import json


@login_required
def timetable_management(request):
    """Timetable management for school admin"""
    school = get_user_school(request)
    
    if not school:
        messages.error(request, "Please set up your school first.")
        return redirect('students_app:school_setup_wizard')
    
    # Get current academic year
    current_year = AcademicYear.objects.filter(is_current=True).first()
    if not current_year:
        messages.warning(request, "No current academic year found. Please set up academic year first.")
        return redirect('students_app:school_setup_wizard')
    
    # Get all data for dropdowns
    classes = Class.objects.all().order_by('numeric_value', 'name')
    teachers = Teacher.objects.filter(school=school).select_related('user').order_by('user__first_name')
    subjects = Subject.objects.all().order_by('name')
    time_slots = TimeSlot.objects.all().order_by('start_time')
    
    # Get existing timetables
    timetables = Timetable.objects.filter(
        academic_year=current_year
    ).select_related('section', 'subject', 'teacher', 'time_slot').order_by(
        'section__class_assigned__numeric_value', 'section__name', 'weekday', 'time_slot__start_time'
    )
    
    context = {
        'classes': classes,
        'teachers': teachers,
        'subjects': subjects,
        'time_slots': time_slots,
        'timetables': timetables,
        'current_year': current_year,
        'weekday_choices': Timetable.WEEKDAY_CHOICES
    }
    
    return render(request, 'students/timetable/timetable_management.html', context)


@login_required
def upload_timetable(request):
    """Upload timetable via Excel/CSV"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=400)
    
    try:
        # Get current academic year
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return JsonResponse({'error': 'No current academic year found'}, status=400)
        
        # Get uploaded file
        file = request.FILES.get('timetable_file')
        if not file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        # Process file based on type
        import pandas as pd
        
        if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            df = pd.read_excel(file)
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return JsonResponse({'error': 'Invalid file format. Please upload Excel or CSV file.'}, status=400)
        
        # Expected columns
        required_columns = ['class_name', 'section_name', 'weekday', 'time_slot', 'subject', 'teacher_employee_id', 'room_number']
        
        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return JsonResponse({'error': f'Missing columns: {", ".join(missing_columns)}'}, status=400)
        
        # Process each row
        success_count = 0
        error_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Get class and section info
                class_name = str(row['class_name'])
                section_name = str(row.get('section_name', ''))
                
                # Get class object
                class_obj = Class.objects.get(name=class_name)
                
                # Handle section
                if section_name:
                    # Class has sections
                    section_obj = Section.objects.get(class_assigned=class_obj, name=section_name)
                else:
                    # Class without sections - create default section
                    section_obj, created = Section.objects.get_or_create(
                        class_assigned=class_obj,
                        name='Default',
                        defaults={'capacity': 50}
                    )
                
                # Get other objects
                teacher_obj = Teacher.objects.get(employee_id=str(row['teacher_employee_id']))
                subject_obj = Subject.objects.get(name=str(row['subject']))
                time_slot_obj = TimeSlot.objects.get(slot_name=str(row['time_slot']))
                
                # Create or update timetable
                timetable, created = Timetable.objects.get_or_create(
                    section=section_obj,
                    academic_year=current_year,
                    weekday=int(row['weekday']),
                    time_slot=time_slot_obj,
                    defaults={
                        'subject': subject_obj,
                        'teacher': teacher_obj,
                        'room_number': str(row.get('room_number', ''))
                    }
                )
                
                if created:
                    success_count += 1
                else:
                    # Update existing
                    timetable.subject = subject_obj
                    timetable.teacher = teacher_obj
                    timetable.room_number = str(row.get('room_number', ''))
                    timetable.save()
                    success_count += 1
                    
            except Exception as e:
                error_count += 1
                errors.append(f"Row {index + 1}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': f'Timetable uploaded successfully! {success_count} entries processed, {error_count} errors.',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]  # Show first 10 errors
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Error processing file: {str(e)}'}, status=500)


@login_required
def download_sample_timetable(request):
    """Download sample timetable Excel file"""
    import pandas as pd
    from django.http import HttpResponse
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    
    # Sample data
    sample_data = [
        {
            'class_name': 'Class 10',
            'section_name': 'A',
            'weekday': '0',  # Monday
            'time_slot': 'Period 1',
            'subject': 'Mathematics',
            'teacher_employee_id': 'EMP001',
            'room_number': 'Room 101'
        },
        {
            'class_name': 'Class 9',
            'section_name': '',  # No sections
            'weekday': '1',  # Tuesday
            'time_slot': 'Period 2',
            'subject': 'Physics',
            'teacher_employee_id': 'EMP002',
            'room_number': 'Room 201'
        },
        {
            'class_name': 'Class 8',
            'section_name': 'B',
            'weekday': '2',  # Wednesday
            'time_slot': 'Period 3',
            'subject': 'Chemistry',
            'teacher_employee_id': 'EMP003',
            'room_number': 'Room 301'
        },
        {
            'class_name': 'Nursery',
            'section_name': '',  # No sections
            'weekday': '3',  # Thursday
            'time_slot': 'Period 1',
            'subject': 'Art & Craft',
            'teacher_employee_id': 'EMP004',
            'room_number': 'Room 401'
        }
    ]
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=sample_timetable.xlsx'
    
    # Save to Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sample Timetable', index=False)
    
    return response


@login_required
def add_timetable_entry(request):
    """Add single timetable entry"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    if request.method == 'POST':
        try:
            # Get form data
            class_id = request.POST.get('class_id')
            section_id = request.POST.get('section_id')
            class_only_id = request.POST.get('class_only_id')
            weekday = request.POST.get('weekday')
            time_slot_id = request.POST.get('time_slot_id')
            subject_id = request.POST.get('subject_id')
            teacher_id = request.POST.get('teacher_id')
            room_number = request.POST.get('room_number', '')
            
            # Get current academic year
            current_year = AcademicYear.objects.filter(is_current=True).first()
            if not current_year:
                return JsonResponse({'error': 'No current academic year found'}, status=400)
            
            # Handle both scenarios
            if section_id:
                # Class with sections scenario
                section_obj = get_object_or_404(Section, id=section_id)
                class_obj = section_obj.class_assigned
            elif class_only_id:
                # Class without sections scenario
                class_obj = get_object_or_404(Class, id=class_only_id)
                # Create a default section or use existing
                section_obj, created = Section.objects.get_or_create(
                    class_assigned=class_obj,
                    name='Default',
                    defaults={'capacity': 50}
                )
            else:
                return JsonResponse({'error': 'Either section_id or class_only_id is required'}, status=400)
            
            # Get other objects
            time_slot_obj = get_object_or_404(TimeSlot, id=time_slot_id)
            subject_obj = get_object_or_404(Subject, id=subject_id)
            teacher_obj = get_object_or_404(Teacher, id=teacher_id)
            
            # Create or update timetable
            timetable, created = Timetable.objects.get_or_create(
                section=section_obj,
                academic_year=current_year,
                weekday=int(weekday),
                time_slot=time_slot_obj,
                defaults={
                    'subject': subject_obj,
                    'teacher': teacher_obj,
                    'room_number': room_number
                }
            )
            
            if not created:
                # Update existing
                timetable.subject = subject_obj
                timetable.teacher = teacher_obj
                timetable.room_number = room_number
                timetable.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Timetable entry saved successfully!',
                'created': created,
                'section_info': f'{section_obj.class_assigned.name} - {section_obj.name}'
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error saving timetable entry: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=400)


@login_required
def delete_timetable_entry(request, timetable_id):
    """Delete timetable entry"""
    school = get_user_school(request)
    
    if not school:
        return JsonResponse({'error': 'School not found'}, status=400)
    
    if request.method == 'DELETE':
        try:
            timetable = get_object_or_404(Timetable, id=timetable_id)
            timetable.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Timetable entry deleted successfully!'
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error deleting timetable entry: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Only DELETE method allowed'}, status=400)


def get_user_school(request):
    """Get school associated with current user"""
    if hasattr(request.user, 'school_profile') and request.user.school_profile:
        return request.user.school_profile.school
    return None
