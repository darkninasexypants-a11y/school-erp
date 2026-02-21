"""
SMART TEACHER BULK UPLOAD VIEW
Clean implementation with smart class/section assignment functionality
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
import pandas as pd

def teacher_bulk_upload(request):
    """Smart bulk upload for teachers with automatic class/section assignment"""
    from .models import Teacher, School, Class, Section
    
    context = {}
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'save_bulk':
            import os
            from django.core.files.base import ContentFile
            from django.conf import settings
            
            # Get form data
            first_names = request.POST.getlist('first_name[]')
            last_names = request.POST.getlist('last_name[]')
            employee_ids = request.POST.getlist('employee_id[]')
            emails = request.POST.getlist('email[]')
            phones = request.POST.getlist('phone[]')
            dobs = request.POST.getlist('dob[]')
            genders = request.POST.getlist('gender[]')
            qualifications = request.POST.getlist('qualification[]')
            salaries = request.POST.getlist('salary[]')
            addresses = request.POST.getlist('address[]')
            joining_dates = request.POST.getlist('joining_date[]')
            image_filenames = request.POST.getlist('image_filename[]')
            designations = request.POST.getlist('designation[]')
            assigned_classes = request.POST.getlist('assigned_class[]')
            assigned_sections = request.POST.getlist('assigned_section[]')
            auto_assign_classes = request.POST.get('auto_assign_classes', 'no')
            auto_assign_sections = request.POST.get('auto_assign_sections', 'no')
            images_path = request.session.get('teacher_import_images_path')
            
            success_count = 0
            error_count = 0
            skipped_details = []
            teachers_data = []

            # Get available classes and sections for smart assignment
            school_obj = request.user.school_profile.school if hasattr(request.user, 'school_profile') and request.user.school_profile else None
            available_classes = Class.objects.filter(school=school_obj).prefetch_related('section_set')
            available_sections = Section.objects.filter(class_assigned__in=available_classes).select_related('class_assigned')
            
            # Smart assignment logic
            if auto_assign_classes == 'yes' and available_classes.exists():
                # Auto-assign classes to teachers
                class_index = 0
                for i in range(len(first_names)):
                    if class_index < len(available_classes):
                        assigned_class = available_classes[class_index]
                    else:
                        assigned_class = None
                    
                    # Update teacher data with assigned class
                    teachers_data.append({
                        'first_name': first_names[i],
                        'last_name': last_names[i],
                        'employee_id': employee_ids[i],
                        'email': emails[i],
                        'phone': phones[i],
                        'dob': dobs[i],
                        'gender': genders[i],
                        'qualification': qualifications[i],
                        'designation': designations[i] if i < len(designations) and designations[i] else 'Teacher',
                        'joining_date': joining_dates[i],
                        'salary': salaries[i] if salaries[i] else 0,
                        'address': addresses[i] if addresses[i] else "Not Provided",
                        'assigned_class': assigned_class,
                        'assigned_section': None  # Will be auto-assigned if needed
                    })
                    class_index = (class_index + 1) % len(available_classes)
            
            elif auto_assign_sections == 'yes' and available_sections.exists():
                # Auto-assign sections to teachers with classes
                section_index = 0
                for i in range(len(first_names)):
                    if section_index < len(available_sections):
                        # Find a class for this teacher (use first available class)
                        assigned_class = None
                        for cls in available_classes:
                            if section_index < len(cls.section_set.all()):
                                assigned_class = cls
                                break
                        
                        # Find a section for this class
                        assigned_section = None
                        if assigned_class:
                            available_sections_for_class = assigned_class.section_set.all()
                            if section_index < len(available_sections_for_class):
                                assigned_section = available_sections_for_class[section_index]
                                break
                    
                    # Update teacher data with assigned class and section
                    teachers_data.append({
                        'first_name': first_names[i],
                        'last_name': last_names[i],
                        'employee_id': employee_ids[i],
                        'email': emails[i],
                        'phone': phones[i],
                        'dob': dobs[i],
                        'gender': genders[i],
                        'qualification': qualifications[i],
                        'designation': designations[i] if i < len(designations) and designations[i] else 'Teacher',
                        'joining_date': joining_dates[i],
                        'salary': salaries[i] if salaries[i] else 0,
                        'address': addresses[i] if addresses[i] else "Not Provided",
                        'assigned_class': assigned_class,
                        'assigned_section': assigned_section
                    })
                    section_index = (section_index + 1) % len(available_sections)
            else:
                # Manual assignment - use provided class/section values
                for i in range(len(first_names)):
                    teachers_data.append({
                        'first_name': first_names[i],
                        'last_name': last_names[i],
                        'employee_id': employee_ids[i],
                        'email': emails[i],
                        'phone': phones[i],
                        'dob': dobs[i],
                        'gender': genders[i],
                        'qualification': qualifications[i],
                        'designation': designations[i] if i < len(designations) and designations[i] else 'Teacher',
                        'joining_date': joining_dates[i],
                        'salary': salaries[i] if salaries[i] else 0,
                        'address': addresses[i] if addresses[i] else "Not Provided",
                        'assigned_class_id': assigned_classes[i] if i < len(assigned_classes) else '',
                        'assigned_section_id': assigned_sections[i] if i < len(assigned_sections) else '',
                        'assigned_class': None,
                        'assigned_section': None
                    })
            
            # Process each teacher
            for i in range(len(first_names)):
                try:
                    if not emails[i] or not employee_ids[i]:
                        error_count += 1
                        skipped_details.append(f"Row {i+1}: Missing required fields (Email / Employee ID)")
                        continue

                    # Check for duplicates within same school only
                    if User.objects.filter(username=emails[i]).exists():
                        su = SchoolUser.objects.filter(user__username=emails[i], school=school_obj).first()
                        if su:
                            error_count += 1
                            skipped_details.append(f"Row {i+1}: Duplicate email/username '{emails[i]}' within this school (SchoolUser found)")
                            continue

                    if Teacher.objects.filter(employee_id=employee_ids[i], school=school_obj).exists():
                        error_count += 1
                        skipped_details.append(f"Row {i+1}: Duplicate Employee ID '{employee_ids[i]}' within this school")
                        continue

                    # Create user
                    user = User.objects.create_user(
                        username=emails[i],
                        email=emails[i],
                        password="Teacher@123",
                        first_name=first_names[i],
                        last_name=last_names[i]
                    )

                    # Create teacher with smart assignment
                    assigned_class_id = teachers_data[i].get('assigned_class_id')
                    assigned_section_id = teachers_data[i].get('assigned_section_id')
                    
                    teacher = Teacher(
                        user=user,
                        employee_id=employee_ids[i],
                        phone=phones[i],
                        date_of_birth=dobs[i],
                        gender=genders[i],
                        qualification=qualifications[i],
                        current_salary=salaries[i] if salaries[i] else 0,
                        address=addresses[i] if addresses[i] else "Not Provided",
                        joining_date=joining_dates[i],
                        designation=designations[i] if i < len(designations) and designations[i] else 'Teacher'
                    )
                    
                    # Assign class if provided
                    if assigned_class_id:
                        try:
                            assigned_class = Class.objects.get(id=assigned_class_id)
                            teacher.assigned_class = assigned_class
                            print(f"Assigned class {assigned_class.name} to teacher {first_names[i]} {last_names[i]}")
                        except Class.DoesNotExist:
                            print(f"Class {assigned_class_id} not found for teacher {first_names[i]}")
                    
                    # Assign section if provided
                    if assigned_section_id:
                        try:
                            assigned_section = Section.objects.get(id=assigned_section_id)
                            teacher.assigned_section = assigned_section
                            print(f"Assigned section {assigned_section.name} to teacher {first_names[i]} {last_names[i]}")
                        except Section.DoesNotExist:
                            print(f"Section {assigned_section_id} not found for teacher {first_names[i]}")
                    
                    # Assign school if user has school profile
                    if hasattr(request.user, 'school_profile') and request.user.school_profile:
                        teacher.school = request.user.school_profile.school

                    teacher.save()
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error adding teacher {first_names[i]}: {e}")
                    skipped_details.append(f"Row {i+1}: {str(e)}")
            
            # Clean up
            if images_path and os.path.isdir(images_path):
                try:
                    import shutil
                    shutil.rmtree(images_path, ignore_errors=True)
                except Exception:
                    pass
            request.session.pop('teacher_import_images_path', None)
            
            if success_count > 0:
                messages.success(request, f"Successfully added {success_count} teachers.")
            if error_count > 0:
                msg = f"Skipped {error_count} teachers (duplicates or errors)."
                if skipped_details:
                    sample = skipped_details[:5]
                    msg += f" Sample: {'; '.join(sample)}"
                messages.warning(request, msg)
            return redirect('students_app:teacher_list')
        
        elif 'excel_file' in request.FILES:
            # Handle Excel file upload
            try:
                import os
                import uuid
                from django.core.files.base import ContentFile
                from django.conf import settings
                
                excel_file = request.FILES['excel_file']
                images_zip = request.FILES.get('images_zip')
                images_path = None
                
                if images_zip and images_zip.name.endswith('.zip'):
                    try:
                        images_dict = extract_images_from_zip(images_zip)
                        if images_dict:
                            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_teacher_import', str(uuid.uuid4()))
                            os.makedirs(temp_dir, exist_ok=True)
                            for fn, data in images_dict.items():
                                with open(os.path.join(temp_dir, fn), 'wb') as f:
                                    f.write(data)
                            request.session['teacher_import_images_path'] = temp_dir
                    except Exception:
                        request.session.pop('teacher_import_images_path', None)
                else:
                    request.session.pop('teacher_import_images_path', None)
                
                df = pd.read_excel(excel_file)
                df.columns = [str(c).strip().lower().replace(' ', ' ') for c in df.columns]
                
                def get_photo(row):
                    for col in ['image filename', 'image_filename', 'photo', 'photo filename']:
                        if col in df.columns and pd.notna(row.get(col)):
                            return str(row[col]).strip()
                    return ''
                
                teachers_data = []
                for index, row in df.iterrows():
                    def format_date(val, default):
                        if pd.isna(val) or str(val).strip() == '': return default
                        try: return pd.to_datetime(val).strftime('%Y-%m-%d')
                        except: return default
                    
                    dob = format_date(row.get('date of birth (yyyy-mm-dd)') or row.get('dob'), '2000-01-01')
                    joining = format_date(row.get('joining date (yyyy-mm-dd)') or row.get('joining date'), timezone.now().date().strftime('%Y-%m-%d'))
                    
                    teachers_data.append({
                        'first_name': row.get('first name', ''),
                        'last_name': row.get('last name', ''),
                        'employee_id': row.get('employee id', ''),
                        'email': row.get('email', ''),
                        'phone': row.get('phone', ''),
                        'dob': dob,
                        'gender': str(row.get('gender (m/f/o)') or row.get('gender') or 'O')[0].upper(),
                        'address': row.get('address', ''),
                        'designation': row.get('designation', 'Teacher'),
                        'qualification': row.get('qualification', ''),
                        'joining_date': joining,
                        'salary': row.get('current salary') or row.get('salary') or 0,
                        'image_filename': get_photo(row),
                    })
                
                context['teachers_data'] = teachers_data
                context['available_classes'] = Class.objects.filter(school=school_obj).prefetch_related('section_set')
                context['available_sections'] = Section.objects.filter(class_assigned__in=context['available_classes']).select_related('class_assigned')
                
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
                
            return render(request, 'students/teacher_bulk_upload.html', context)
    
    else:
        # GET request - show upload form
        context = {}
        return render(request, 'students/teacher_bulk_upload.html', context)

def extract_images_from_zip(zip_file):
    """Extract images from ZIP file and return dictionary"""
    import zipfile
    images_dict = {}
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if not file_info.is_dir():
                    with zip_ref.open(file_info.filename) as file:
                        images_dict[file_info.filename] = file.read()
    except Exception as e:
        print(f"Error extracting ZIP: {e}")
    
    return images_dict
