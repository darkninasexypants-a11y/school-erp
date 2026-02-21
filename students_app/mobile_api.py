"""
Simple Mobile API Endpoints (No Authentication Required for Testing)
For production, add authentication decorators
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from django.db import transaction
from django.utils import timezone
from students_app.models import Student, Attendance, Class, Section, Timetable, TimeSlot, Teacher, Exam, ExamSchedule, Marks, AcademicYear, Subject
from datetime import datetime, timedelta
import json


@csrf_exempt
@require_POST
def mobile_mark_attendance(request):
    """
    Mobile API: Mark attendance for students
    POST /api/mobile/attendance/mark/
    Body: {
        "class_id": 15,
        "date": "2025-12-07",
        "attendance": [
            {"student_id": 1, "status": "P"},
            {"student_id": 2, "status": "A"}
        ]
    }
    """
    try:
        data = json.loads(request.body)
        class_id = data.get('class_id')
        date_str = data.get('date')
        attendance_data = data.get('attendance', [])
        
        if not class_id or not date_str:
            return JsonResponse({
                'success': False,
                'error': 'class_id and date are required'
            }, status=400)
        
        attendance_date = parse_date(date_str)
        if not attendance_date:
            return JsonResponse({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=400)
        
        try:
            class_obj = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Class not found'
            }, status=404)
        
        marked_count = 0
        with transaction.atomic():
            for record in attendance_data:
                student_id = record.get('student_id')
                status = record.get('status')
                
                if not student_id or not status:
                    continue
                
                try:
                    student = Student.objects.get(id=student_id)
                    Attendance.objects.update_or_create(
                        student=student,
                        date=attendance_date,
                        defaults={'status': status}
                    )
                    marked_count += 1
                except Student.DoesNotExist:
                    continue
        
        return JsonResponse({
            'success': True,
            'marked_count': marked_count,
            'message': f'Attendance marked for {marked_count} students',
            'date': str(attendance_date),
            'class': class_obj.name
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
def mobile_get_students(request):
    """
    Mobile API: Get students by class
    GET /api/mobile/students/?class_id=15
    """
    class_id = request.GET.get('class_id')
    
    if not class_id:
        return JsonResponse({
            'success': False,
            'error': 'class_id parameter is required'
        }, status=400)
    
    try:
        class_obj = Class.objects.get(id=class_id)
        students = Student.objects.filter(
            current_class=class_obj,
            status='active'
        ).select_related('section').order_by('section__name', 'roll_number')
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'name': student.get_full_name(),
                'roll_number': student.roll_number,
                'section': student.section.name if student.section else None,
                'admission_number': student.admission_number,
                'photo_url': student.photo.url if student.photo else None
            })
        
        return JsonResponse({
            'success': True,
            'class': class_obj.name,
            'students': students_data,
            'count': len(students_data)
        })
    
    except Class.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Class not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
def mobile_get_classes(request):
    """
    Mobile API: Get all classes
    GET /api/mobile/classes/
    """
    try:
        classes = Class.objects.all().order_by('name')
        
        classes_data = []
        for cls in classes:
            classes_data.append({
                'id': cls.id,
                'name': cls.name
            })
        
        return JsonResponse({
            'success': True,
            'classes': classes_data,
            'count': len(classes_data)
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
def mobile_attendance_summary(request):
    """
    Mobile API: Get attendance summary for a student
    GET /api/mobile/attendance/summary/?student_id=1&month=12&year=2025
    """
    student_id = request.GET.get('student_id')
    month = request.GET.get('month', datetime.now().month)
    year = request.GET.get('year', datetime.now().year)
    
    if not student_id:
        return JsonResponse({
            'success': False,
            'error': 'student_id parameter is required'
        }, status=400)
    
    try:
        student = Student.objects.get(id=student_id)
        
        attendance_records = Attendance.objects.filter(
            student=student,
            date__month=int(month),
            date__year=int(year)
        ).order_by('date')
        
        total_days = attendance_records.count()
        present_count = attendance_records.filter(status='P').count()
        absent_count = attendance_records.filter(status='A').count()
        percentage = (present_count / total_days * 100) if total_days > 0 else 0
        
        records = []
        for record in attendance_records:
            records.append({
                'date': str(record.date),
                'day': record.date.strftime('%A'),
                'status': record.status,
                'status_display': 'Present' if record.status == 'P' else 'Absent'
            })
        
        return JsonResponse({
            'success': True,
            'student': {
                'id': student.id,
                'name': student.get_full_name(),
                'class': student.current_class.name if student.current_class else None,
                'section': student.section.name if student.section else None
            },
            'month': datetime(int(year), int(month), 1).strftime('%B %Y'),
            'summary': {
                'total_days': total_days,
                'present': present_count,
                'absent': absent_count,
                'percentage': round(percentage, 2)
            },
            'records': records
        })
    
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_GET
@csrf_exempt
@require_GET
def mobile_get_timetable(request):
    """
    Mobile API: Get timetable with role-based access
    GET /api/mobile/timetable/?section_id=1 (for student/parent)
    GET /api/mobile/timetable/?teacher_id=1 (for teacher - shows only their subjects)
    GET /api/mobile/timetable/?user_id=username (auto-detect based on user role)
    """
    from students_app.models import Parent, AcademicYear
    
    section_id = request.GET.get('section_id')
    teacher_id = request.GET.get('teacher_id')
    user_id = request.GET.get('user_id')  # Optional: for identifying user
    
    try:
        # Get current academic year
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return JsonResponse({
                'success': False,
                'error': 'No active academic year found'
            }, status=400)
        
        timetables = Timetable.objects.filter(academic_year=current_year).select_related(
            'time_slot', 'subject', 'teacher', 'section', 'section__class_assigned'
        )
        
        # Role-based filtering
        if teacher_id:
            # Teacher timetable - show only their subjects
            try:
                teacher = Teacher.objects.get(id=teacher_id)
                timetables = timetables.filter(teacher=teacher).order_by('weekday', 'time_slot__start_time')
                timetable_list = []
                
                for tt in timetables:
                    timetable_list.append({
                        'id': tt.id,
                        'weekday': tt.weekday,
                        'weekday_name': tt.get_weekday_display(),
                        'time_slot': {
                            'id': tt.time_slot.id if tt.time_slot else None,
                            'start_time': tt.time_slot.start_time.strftime('%H:%M:%S') if tt.time_slot else None,
                            'end_time': tt.time_slot.end_time.strftime('%H:%M:%S') if tt.time_slot else None,
                            'slot_name': tt.time_slot.slot_name if tt.time_slot else None,
                        },
                        'subject': {
                            'id': tt.subject.id if tt.subject else None,
                            'name': tt.subject.name if tt.subject else None,
                        },
                        'section': {
                            'id': tt.section.id,
                            'name': tt.section.name,
                            'class': tt.section.class_assigned.name if tt.section.class_assigned else None,
                        },
                        'room_number': tt.room_number,
                    })
                
                return JsonResponse({
                    'success': True,
                    'type': 'teacher',
                    'teacher': {
                        'id': teacher.id,
                        'name': teacher.user.get_full_name() if teacher.user else teacher.user.username,
                    },
                    'timetable': timetable_list
                })
            except Teacher.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Teacher not found'
                }, status=404)
        
        elif section_id:
            # Student/Parent timetable - specific section
            try:
                section = Section.objects.get(id=section_id)
                timetables = timetables.filter(section=section).order_by('weekday', 'time_slot__start_time')
                timetable_list = []
                
                for tt in timetables:
                    timetable_list.append({
                        'id': tt.id,
                        'weekday': tt.weekday,
                        'weekday_name': tt.get_weekday_display(),
                        'time_slot': {
                            'id': tt.time_slot.id if tt.time_slot else None,
                            'start_time': tt.time_slot.start_time.strftime('%H:%M:%S') if tt.time_slot else None,
                            'end_time': tt.time_slot.end_time.strftime('%H:%M:%S') if tt.time_slot else None,
                            'slot_name': tt.time_slot.slot_name if tt.time_slot else None,
                        },
                        'subject': {
                            'id': tt.subject.id if tt.subject else None,
                            'name': tt.subject.name if tt.subject else None,
                        },
                        'teacher': {
                            'id': tt.teacher.id if tt.teacher else None,
                            'name': tt.teacher.user.get_full_name() if tt.teacher and tt.teacher.user else None,
                            'first_name': tt.teacher.user.first_name if tt.teacher and tt.teacher.user else None,
                            'last_name': tt.teacher.user.last_name if tt.teacher and tt.teacher.user else None,
                        },
                        'room_number': tt.room_number,
                    })
                
                return JsonResponse({
                    'success': True,
                    'type': 'section',
                    'section': {
                        'id': section.id,
                        'name': section.name,
                        'class': section.class_assigned.name if section.class_assigned else None,
                    },
                    'timetable': timetable_list
                })
            except Section.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Section not found'
                }, status=404)
        
        elif user_id:
            # Auto-detect based on user_id
            # Try to find student
            try:
                student = Student.objects.filter(admission_number=user_id).first()
                if student and student.section:
                    # Recursively call with section_id
                    from django.http import QueryDict
                    new_request = request.__class__(request.META)
                    new_request.GET = QueryDict(f'section_id={student.section.id}')
                    return mobile_get_timetable(new_request)
            except:
                pass
            
            # Try to find parent
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(username=user_id)
                parent = Parent.objects.filter(user=user).first()
                if parent:
                    child = parent.students.first()
                    if child and child.section:
                        from django.http import QueryDict
                        new_request = request.__class__(request.META)
                        new_request.GET = QueryDict(f'section_id={child.section.id}')
                        return mobile_get_timetable(new_request)
            except:
                pass
            
            return JsonResponse({
                'success': False,
                'error': 'Could not auto-detect section for user'
            }, status=400)
        
        else:
            return JsonResponse({
                'success': False,
                'error': 'section_id, teacher_id, or user_id parameter is required'
            }, status=400)
    
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_POST
def mobile_edit_timetable(request):
    """
    Mobile API: Edit timetable entry
    POST /api/mobile/timetable/edit/
    Body: {
        "timetable_id": 1,  # Optional: for updating existing
        "section_id": 1,
        "weekday": 0,  # 0=Monday, 1=Tuesday, etc.
        "time_slot_id": 1,
        "subject_id": 1,
        "teacher_id": 1,  # Optional
        "room_number": "101"  # Optional
    }
    """
    from students_app.models import AcademicYear, Subject
    
    try:
        data = json.loads(request.body)
        
        # Get current academic year
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            return JsonResponse({
                'success': False,
                'error': 'No active academic year found'
            }, status=400)
        
        section_id = data.get('section_id')
        weekday = data.get('weekday')
        time_slot_id = data.get('time_slot_id')
        subject_id = data.get('subject_id')
        teacher_id = data.get('teacher_id')
        room_number = data.get('room_number', '')
        timetable_id = data.get('timetable_id')
        
        if not all([section_id, weekday is not None, time_slot_id, subject_id]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: section_id, weekday, time_slot_id, subject_id'
            }, status=400)
        
        section = Section.objects.get(id=section_id)
        time_slot = TimeSlot.objects.get(id=time_slot_id)
        subject = Subject.objects.get(id=subject_id)
        teacher = Teacher.objects.get(id=teacher_id) if teacher_id else None
        
        # Get or create timetable entry
        timetable_entry, created = Timetable.objects.get_or_create(
            section=section,
            academic_year=current_year,
            weekday=weekday,
            time_slot=time_slot,
            defaults={
                'subject': subject,
                'teacher': teacher,
                'room_number': room_number
            }
        )
        
        if not created:
            # Update existing entry
            timetable_entry.subject = subject
            timetable_entry.teacher = teacher
            timetable_entry.room_number = room_number
            timetable_entry.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Timetable updated successfully',
            'timetable': {
                'id': timetable_entry.id,
                'weekday': timetable_entry.weekday,
                'weekday_name': timetable_entry.get_weekday_display(),
            }
        })
    
    except (Section.DoesNotExist, TimeSlot.DoesNotExist, Subject.DoesNotExist) as e:
        return JsonResponse({
            'success': False,
            'error': f'Resource not found: {str(e)}'
        }, status=404)
    except Teacher.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Teacher not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@require_GET
def mobile_get_exams(request):
    """
    Mobile API: Get all exams
    GET /api/mobile/exams/?is_published=true (optional filter)
    """
    try:
        is_published = request.GET.get('is_published')
        
        exams_query = Exam.objects.all().select_related('academic_year')
        
        # Filter by is_published if provided
        if is_published is not None:
            is_published_bool = is_published.lower() == 'true'
            exams_query = exams_query.filter(is_published=is_published_bool)
        
        exams = exams_query.order_by('-start_date', 'name')
        
        exams_data = []
        for exam in exams:
            exams_data.append({
                'id': exam.id,
                'name': exam.name,
                'term': exam.term,
                'term_display': exam.get_term_display(),
                'start_date': str(exam.start_date) if exam.start_date else None,
                'end_date': str(exam.end_date) if exam.end_date else None,
                'is_published': exam.is_published,
                'academic_year': {
                    'id': exam.academic_year.id,
                    'name': str(exam.academic_year)
                } if exam.academic_year else None,
                'created_at': exam.created_at.isoformat() if exam.created_at else None
            })
        
        return JsonResponse({
            'success': True,
            'exams': exams_data,
            'count': len(exams_data)
        })
    
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@require_GET
def mobile_get_marks(request):
    """
    Mobile API: Get marks for a student
    GET /api/mobile/marks/?student_id=1&exam_id=1 (optional exam_id)
    GET /api/mobile/marks/?user_id=username (auto-detect student)
    """
    try:
        student_id = request.GET.get('student_id')
        exam_id = request.GET.get('exam_id')
        user_id = request.GET.get('user_id')  # Optional: for auto-detection
        
        # Auto-detect student from user_id if provided
        if user_id and not student_id:
            try:
                from django.contrib.auth.models import User
                user = User.objects.get(username=user_id)
                student = Student.objects.filter(user=user).first()
                if student:
                    student_id = student.id
                else:
                    # Try to find by admission_number
                    student = Student.objects.filter(admission_number=user_id).first()
                    if student:
                        student_id = student.id
            except:
                pass
        
        if not student_id:
            return JsonResponse({
                'success': False,
                'error': 'student_id or user_id parameter is required'
            }, status=400)
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Student not found'
            }, status=404)
        
        # Get marks for the student
        marks_query = Marks.objects.filter(student=student).select_related(
            'exam_schedule', 'exam_schedule__exam', 'exam_schedule__subject', 
            'exam_schedule__class_assigned', 'entered_by'
        )
        
        # Filter by exam if provided
        if exam_id:
            marks_query = marks_query.filter(exam_schedule__exam_id=exam_id)
        
        marks = marks_query.order_by('-exam_schedule__exam_date', 'exam_schedule__subject__name')
        
        marks_data = []
        for mark in marks:
            marks_data.append({
                'id': mark.id,
                'marks_obtained': mark.marks_obtained,
                'is_absent': mark.is_absent,
                'remarks': mark.remarks,
                'exam_schedule': {
                    'id': mark.exam_schedule.id,
                    'exam': {
                        'id': mark.exam_schedule.exam.id,
                        'name': mark.exam_schedule.exam.name,
                        'term': mark.exam_schedule.exam.term
                    },
                    'subject': {
                        'id': mark.exam_schedule.subject.id,
                        'name': mark.exam_schedule.subject.name
                    },
                    'class': {
                        'id': mark.exam_schedule.class_assigned.id,
                        'name': mark.exam_schedule.class_assigned.name
                    },
                    'exam_date': str(mark.exam_schedule.exam_date),
                    'max_marks': mark.exam_schedule.max_marks
                },
                'entered_by': mark.entered_by.username if mark.entered_by else None,
                'created_at': mark.created_at.isoformat() if mark.created_at else None,
                'updated_at': mark.updated_at.isoformat() if mark.updated_at else None
            })
        
        return JsonResponse({
            'success': True,
            'student': {
                'id': student.id,
                'name': student.get_full_name(),
                'admission_number': student.admission_number,
                'class': student.current_class.name if student.current_class else None,
                'section': student.section.name if student.section else None
            },
            'marks': marks_data,
            'count': len(marks_data)
        })
    
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@csrf_exempt
@require_POST
def mobile_enter_marks(request):
    """
    Mobile API: Enter marks for students
    POST /api/mobile/marks/enter/
    Body: {
        "exam_schedule_id": 1,
        "marks": [
            {"student_id": 1, "marks_obtained": 85, "is_absent": false, "remarks": ""},
            {"student_id": 2, "marks_obtained": 0, "is_absent": true, "remarks": "Absent"}
        ]
    }
    """
    try:
        from django.contrib.auth.models import User
        
        data = json.loads(request.body)
        exam_schedule_id = data.get('exam_schedule_id')
        marks_data = data.get('marks', [])
        
        if not exam_schedule_id:
            return JsonResponse({
                'success': False,
                'error': 'exam_schedule_id is required'
            }, status=400)
        
        if not marks_data:
            return JsonResponse({
                'success': False,
                'error': 'marks array is required'
            }, status=400)
        
        try:
            exam_schedule = ExamSchedule.objects.get(id=exam_schedule_id)
        except ExamSchedule.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Exam schedule not found'
            }, status=404)
        
        # Get the user who is entering marks (if authenticated)
        entered_by = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            entered_by = request.user
        
        entered_count = 0
        errors = []
        
        with transaction.atomic():
            for mark_record in marks_data:
                student_id = mark_record.get('student_id')
                marks_obtained = mark_record.get('marks_obtained', 0)
                is_absent = mark_record.get('is_absent', False)
                remarks = mark_record.get('remarks', '')
                
                if not student_id:
                    errors.append('Missing student_id in marks record')
                    continue
                
                try:
                    student = Student.objects.get(id=student_id)
                    
                    # Validate marks
                    if marks_obtained < 0:
                        marks_obtained = 0
                    if marks_obtained > exam_schedule.max_marks:
                        marks_obtained = exam_schedule.max_marks
                    
                    # If absent, set marks to 0
                    if is_absent:
                        marks_obtained = 0
                    
                    Marks.objects.update_or_create(
                        student=student,
                        exam_schedule=exam_schedule,
                        defaults={
                            'marks_obtained': marks_obtained,
                            'is_absent': is_absent,
                            'remarks': remarks,
                            'entered_by': entered_by
                        }
                    )
                    entered_count += 1
                    
                except Student.DoesNotExist:
                    errors.append(f'Student with id {student_id} not found')
                    continue
                except Exception as e:
                    errors.append(f'Error processing student {student_id}: {str(e)}')
                    continue
        
        return JsonResponse({
            'success': True,
            'message': f'Marks entered for {entered_count} students',
            'entered_count': entered_count,
            'total_records': len(marks_data),
            'errors': errors if errors else None
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@require_GET
def mobile_get_events(request):
    """
    Mobile API: Get all events
    GET /api/mobile/events/?type=academic&date=upcoming (optional filters)
    """
    try:
        from students_app.models import Event
        
        filter_type = request.GET.get('type', 'all')
        filter_date = request.GET.get('date', 'upcoming')  # all, upcoming, past, today
        
        # Base query
        events_query = Event.objects.all()
        
        # Filter by date
        today = timezone.localdate()
        if filter_date == 'upcoming':
            events_query = events_query.filter(event_date__gte=today)
        elif filter_date == 'past':
            events_query = events_query.filter(event_date__lt=today)
        elif filter_date == 'today':
            events_query = events_query.filter(event_date=today)
        # 'all' shows everything
        
        # Filter by event type
        if filter_type != 'all':
            events_query = events_query.filter(event_type=filter_type)
        
        # Order by date
        events = events_query.order_by('event_date', 'start_time')
        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'event_type': event.event_type,
                'event_type_display': event.get_event_type_display(),
                'event_date': str(event.event_date),
                'start_time': event.start_time.strftime('%H:%M:%S') if event.start_time else None,
                'end_time': event.end_time.strftime('%H:%M:%S') if event.end_time else None,
                'venue': event.venue,
                'is_holiday': event.is_holiday,
                'organizer': {
                    'id': event.organizer.id if event.organizer else None,
                    'name': event.organizer.get_full_name() if event.organizer and hasattr(event.organizer, 'get_full_name') else (event.organizer.username if event.organizer else None)
                } if event.organizer else None,
                'participants_count': event.participants.count(),
                'created_at': event.created_at.isoformat() if event.created_at else None,
            })
        
        return JsonResponse({
            'success': True,
            'events': events_data,
            'count': len(events_data),
            'filters': {
                'type': filter_type,
                'date': filter_date
            }
        })
    
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
