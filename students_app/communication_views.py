"""
Communication System Views
Handles all communication features between teachers, parents, and students
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta

from .models import Student, Teacher, Parent, Class, Section, Subject
from .communication_models import (
    Message, Assignment, AssignmentSubmission, CommunicationHomework as Homework, 
    CommunicationHomeworkSubmission as HomeworkSubmission,
    CommunicationTimetable as Timetable, CommunicationEventSchedule as EventSchedule
)


def check_student_access(student):
    """Check if student is in class 7 or above"""
    if student and student.current_class:
        return student.current_class.numeric_value >= 7
    return False


def get_user_role(user):
    """Get user role (teacher, parent, student)"""
    try:
        if hasattr(user, 'teacher'):
            return 'teacher'
        elif hasattr(user, 'parent'):
            return 'parent'
        elif Student.objects.filter(admission_number=user.username).exists():
            return 'student'
    except:
        pass
    return None


# ============================================
# MESSAGING SYSTEM
# ============================================

@login_required
def communication_dashboard(request):
    """Main communication dashboard"""
    user_role = get_user_role(request.user)
    context = {
        'user_role': user_role,
    }
    
    if user_role == 'teacher':
        return render(request, 'communication/teacher_dashboard.html', context)
    elif user_role == 'parent':
        return render(request, 'communication/parent_dashboard.html', context)
    elif user_role == 'student':
        # Check if student can access (class 7+)
        try:
            student = Student.objects.get(admission_number=request.user.username)
            if not check_student_access(student):
                messages.warning(request, 'Communication features are available for class 7 and above only.')
                return redirect('students_app:home')
        except Student.DoesNotExist:
            messages.error(request, 'Student profile not found.')
            return redirect('students_app:home')
        
        return render(request, 'communication/student_dashboard.html', context)
    else:
        messages.error(request, 'Access denied.')
        return redirect('students_app:home')


@login_required
def message_list(request):
    """List all messages for the user"""
    user_role = get_user_role(request.user)
    message_type = request.GET.get('type', 'inbox')  # inbox, sent
    
    if message_type == 'sent':
        message_list = Message.objects.filter(sender=request.user)
    else:
        message_list = Message.objects.filter(recipient=request.user)
    
    # Filter by read/unread
    filter_status = request.GET.get('status', 'all')
    if filter_status == 'unread':
        message_list = message_list.filter(is_read=False)
    elif filter_status == 'read':
        message_list = message_list.filter(is_read=True)
    
    paginator = Paginator(message_list, 20)
    page = request.GET.get('page')
    messages_page = paginator.get_page(page)
    
    context = {
        'messages': messages_page,
        'message_type': message_type,
        'filter_status': filter_status,
        'user_role': user_role,
    }
    return render(request, 'communication/message_list.html', context)


@login_required
def message_detail(request, message_id):
    """View message details"""
    message = get_object_or_404(Message, id=message_id)
    
    # Check access
    if message.recipient != request.user and message.sender != request.user:
        messages.error(request, 'You do not have permission to view this message.')
        return redirect('students_app:message_list')
    
    # Mark as read if recipient
    if message.recipient == request.user and not message.is_read:
        message.mark_as_read()
    
    context = {
        'message': message,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'communication/message_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def message_compose(request):
    """Compose and send a message"""
    user_role = get_user_role(request.user)
    
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        student_id = request.POST.get('related_student', None)
        attachment = request.FILES.get('attachment', None)
        
        try:
            recipient = User.objects.get(id=recipient_id)
            
            # Determine message type
            if user_role == 'teacher':
                recipient_role = get_user_role(recipient)
                if recipient_role == 'parent':
                    msg_type = 'teacher_parent'
                elif recipient_role == 'student':
                    msg_type = 'teacher_student'
                else:
                    messages.error(request, 'Invalid recipient.')
                    return redirect('students_app:message_compose')
            elif user_role == 'parent':
                recipient_role = get_user_role(recipient)
                if recipient_role == 'teacher':
                    msg_type = 'parent_teacher'
                else:
                    messages.error(request, 'Parents can only message teachers.')
                    return redirect('students_app:message_compose')
            elif user_role == 'student':
                recipient_role = get_user_role(recipient)
                if recipient_role == 'teacher':
                    msg_type = 'student_teacher'
                else:
                    messages.error(request, 'Students can only message teachers.')
                    return redirect('students_app:message_compose')
            else:
                messages.error(request, 'Invalid user role.')
                return redirect('students_app:message_compose')
            
            # Create message
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                message_type=msg_type,
                subject=subject,
                message=message_text,
                attachment=attachment,
                related_student_id=student_id if student_id else None
            )
            
            messages.success(request, 'Message sent successfully!')
            return redirect('students_app:message_detail', message_id=message.id)
            
        except User.DoesNotExist:
            messages.error(request, 'Recipient not found.')
    
    # Get available recipients based on user role
    recipients = []
    related_students = []
    
    if user_role == 'teacher':
        # Teachers can message parents and students
        parents = Parent.objects.all()
        students = Student.objects.filter(current_class__numeric_value__gte=7)
        recipients = [{'id': p.user.id, 'name': p.user.get_full_name(), 'type': 'parent'} 
                     for p in parents]
        recipients.extend([{'id': s.admission_number, 'name': s.get_full_name(), 'type': 'student'} 
                          for s in students])
    elif user_role == 'parent':
        # Parents can message teachers
        teachers = Teacher.objects.filter(is_active=True)
        recipients = [{'id': t.user.id, 'name': t.user.get_full_name(), 'type': 'teacher'} 
                     for t in teachers]
        # Get parent's students
        try:
            parent = Parent.objects.get(user=request.user)
            related_students = parent.students.all()
        except Parent.DoesNotExist:
            pass
    elif user_role == 'student':
        # Students can message teachers
        teachers = Teacher.objects.filter(is_active=True)
        recipients = [{'id': t.user.id, 'name': t.user.get_full_name(), 'type': 'teacher'} 
                     for t in teachers]
    
    context = {
        'recipients': recipients,
        'related_students': related_students,
        'user_role': user_role,
    }
    return render(request, 'communication/message_compose.html', context)


# ============================================
# ASSIGNMENT SYSTEM
# ============================================

@login_required
def assignment_list(request):
    """List assignments"""
    user_role = get_user_role(request.user)
    assignments = Assignment.objects.all()
    
    if user_role == 'teacher':
        try:
            teacher = Teacher.objects.get(user=request.user)
            assignments = assignments.filter(teacher=teacher)
        except Teacher.DoesNotExist:
            assignments = Assignment.objects.none()
    elif user_role == 'student':
        try:
            student = Student.objects.get(admission_number=request.user.username)
            if not check_student_access(student):
                messages.warning(request, 'Assignments are available for class 7 and above only.')
                return redirect('students_app:home')
            assignments = assignments.filter(target_class=student.current_class)
            if student.section:
                assignments = assignments.filter(Q(target_section=student.section) | Q(target_section__isnull=True))
        except Student.DoesNotExist:
            assignments = Assignment.objects.none()
    elif user_role == 'parent':
        # Parents see assignments for their children
        try:
            parent = Parent.objects.get(user=request.user)
            student_classes = parent.students.values_list('current_class', flat=True).distinct()
            assignments = assignments.filter(target_class__in=student_classes)
        except Parent.DoesNotExist:
            assignments = Assignment.objects.none()
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        assignments = assignments.filter(status=status_filter)
    
    paginator = Paginator(assignments, 15)
    page = request.GET.get('page')
    assignments_page = paginator.get_page(page)
    
    context = {
        'assignments': assignments_page,
        'status_filter': status_filter,
        'user_role': user_role,
    }
    return render(request, 'communication/assignment_list.html', context)


@login_required
def assignment_detail(request, assignment_id):
    """View assignment details"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    user_role = get_user_role(request.user)
    
    submission = None
    if user_role == 'student':
        try:
            student = Student.objects.get(admission_number=request.user.username)
            submission = AssignmentSubmission.objects.filter(
                assignment=assignment, student=student
            ).first()
        except Student.DoesNotExist:
            pass
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'user_role': user_role,
    }
    return render(request, 'communication/assignment_detail.html', context)


@login_required
def assignment_create(request):
    """Create new assignment (teachers only)"""
    user_role = get_user_role(request.user)
    if user_role != 'teacher':
        messages.error(request, 'Only teachers can create assignments.')
        return redirect('students_app:assignment_list')
    
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('students_app:assignment_list')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        subject_id = request.POST.get('subject')
        class_id = request.POST.get('target_class')
        section_id = request.POST.get('target_section', None)
        submission_type = request.POST.get('submission_type', 'digital')
        due_date_str = request.POST.get('due_date')
        max_marks = request.POST.get('max_marks', 100)
        instructions = request.POST.get('instructions', '')
        attachment = request.FILES.get('attachment', None)
        
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            assignment = Assignment.objects.create(
                title=title,
                description=description,
                subject_id=subject_id,
                teacher=teacher,
                target_class_id=class_id,
                target_section_id=section_id if section_id else None,
                submission_type=submission_type,
                due_date=due_date,
                max_marks=max_marks,
                instructions=instructions,
                attachment=attachment,
                status='published'
            )
            messages.success(request, 'Assignment created successfully!')
            return redirect('students_app:assignment_detail', assignment_id=assignment.id)
        except Exception as e:
            messages.error(request, f'Error creating assignment: {str(e)}')
    
    subjects = Subject.objects.filter(is_active=True)
    classes = Class.objects.all()
    sections = Section.objects.all()
    
    context = {
        'subjects': subjects,
        'classes': classes,
        'sections': sections,
    }
    return render(request, 'communication/assignment_create.html', context)


@login_required
def assignment_submit(request, assignment_id):
    """Submit assignment (students only)"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    user_role = get_user_role(request.user)
    
    if user_role != 'student':
        messages.error(request, 'Only students can submit assignments.')
        return redirect('students_app:assignment_detail', assignment_id=assignment_id)
    
    try:
        student = Student.objects.get(admission_number=request.user.username)
        if not check_student_access(student):
            messages.warning(request, 'Assignment submission is available for class 7 and above only.')
            return redirect('students_app:assignment_detail', assignment_id=assignment_id)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('students_app:assignment_list')
    
    if request.method == 'POST':
        digital_file = request.FILES.get('digital_file', None)
        digital_text = request.POST.get('digital_text', '')
        physical_submitted = request.POST.get('physical_submitted') == 'on'
        physical_remarks = request.POST.get('physical_remarks', '')
        
        submission, created = AssignmentSubmission.objects.get_or_create(
            assignment=assignment,
            student=student,
            defaults={
                'digital_file': digital_file if digital_file else None,
                'digital_text': digital_text,
                'digital_submitted_at': timezone.now() if (digital_file or digital_text) else None,
                'physical_submitted': physical_submitted,
                'physical_submitted_at': timezone.now() if physical_submitted else None,
                'physical_remarks': physical_remarks,
                'status': 'submitted'
            }
        )
        
        if not created:
            # Update existing submission
            if digital_file:
                submission.digital_file = digital_file
            if digital_text:
                submission.digital_text = digital_text
            if digital_file or digital_text:
                submission.digital_submitted_at = timezone.now()
            if physical_submitted:
                submission.physical_submitted = True
                submission.physical_submitted_at = timezone.now()
                submission.physical_remarks = physical_remarks
            submission.save()
        
        # Check if late
        if submission.digital_submitted_at and submission.digital_submitted_at > assignment.due_date:
            submission.status = 'late'
            submission.save()
        
        messages.success(request, 'Assignment submitted successfully!')
        return redirect('students_app:assignment_detail', assignment_id=assignment_id)
    
    # Get existing submission if any
    submission = AssignmentSubmission.objects.filter(
        assignment=assignment, student=student
    ).first()
    
    context = {
        'assignment': assignment,
        'submission': submission,
    }
    return render(request, 'communication/assignment_submit.html', context)


# ============================================
# HOMEWORK SYSTEM
# ============================================

@login_required
def homework_list(request):
    """List homework"""
    user_role = get_user_role(request.user)
    homework_list = Homework.objects.filter(is_active=True)
    
    if user_role == 'teacher':
        try:
            teacher = Teacher.objects.get(user=request.user)
            homework_list = homework_list.filter(teacher=teacher)
        except Teacher.DoesNotExist:
            homework_list = Homework.objects.none()
    elif user_role == 'student':
        try:
            student = Student.objects.get(admission_number=request.user.username)
            if not check_student_access(student):
                messages.warning(request, 'Homework is available for class 7 and above only.')
                return redirect('students_app:home')
            homework_list = homework_list.filter(target_class=student.current_class)
            if student.section:
                homework_list = homework_list.filter(Q(target_section=student.section) | Q(target_section__isnull=True))
        except Student.DoesNotExist:
            homework_list = Homework.objects.none()
    elif user_role == 'parent':
        try:
            parent = Parent.objects.get(user=request.user)
            student_classes = parent.students.values_list('current_class', flat=True).distinct()
            homework_list = homework_list.filter(target_class__in=student_classes)
        except Parent.DoesNotExist:
            homework_list = Homework.objects.none()
    
    # Filter by due date
    filter_due = request.GET.get('due', 'all')
    today = timezone.now().date()
    if filter_due == 'today':
        homework_list = homework_list.filter(due_date=today)
    elif filter_due == 'upcoming':
        homework_list = homework_list.filter(due_date__gt=today)
    elif filter_due == 'overdue':
        homework_list = homework_list.filter(due_date__lt=today)
    
    paginator = Paginator(homework_list, 15)
    page = request.GET.get('page')
    homework_page = paginator.get_page(page)
    
    context = {
        'homework_list': homework_page,
        'filter_due': filter_due,
        'user_role': user_role,
    }
    return render(request, 'communication/homework_list.html', context)


@login_required
def homework_create(request):
    """Create homework (teachers only)"""
    user_role = get_user_role(request.user)
    if user_role != 'teacher':
        messages.error(request, 'Only teachers can create homework.')
        return redirect('students_app:homework_list')
    
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('students_app:homework_list')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        subject_id = request.POST.get('subject')
        class_id = request.POST.get('target_class')
        section_id = request.POST.get('target_section', None)
        due_date_str = request.POST.get('due_date')
        priority = request.POST.get('priority', 'medium')
        instructions = request.POST.get('instructions', '')
        attachment = request.FILES.get('attachment', None)
        
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            homework = Homework.objects.create(
                title=title,
                description=description,
                subject_id=subject_id,
                teacher=teacher,
                target_class_id=class_id,
                target_section_id=section_id if section_id else None,
                due_date=due_date,
                priority=priority,
                instructions=instructions,
                attachment=attachment
            )
            messages.success(request, 'Homework created successfully!')
            return redirect('students_app:homework_list')
        except Exception as e:
            messages.error(request, f'Error creating homework: {str(e)}')
    
    subjects = Subject.objects.filter(is_active=True)
    classes = Class.objects.all()
    sections = Section.objects.all()
    
    context = {
        'subjects': subjects,
        'classes': classes,
        'sections': sections,
    }
    return render(request, 'communication/homework_create.html', context)


@login_required
def homework_submit(request, homework_id):
    """Submit homework (students only)"""
    homework = get_object_or_404(Homework, id=homework_id)
    user_role = get_user_role(request.user)
    
    if user_role != 'student':
        messages.error(request, 'Only students can submit homework.')
        return redirect('students_app:homework_list')
    
    try:
        student = Student.objects.get(admission_number=request.user.username)
        if not check_student_access(student):
            messages.warning(request, 'Homework submission is available for class 7 and above only.')
            return redirect('students_app:homework_list')
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('students_app:homework_list')
    
    if request.method == 'POST':
        submission_file = request.FILES.get('submission_file', None)
        submission_text = request.POST.get('submission_text', '')
        
        submission, created = HomeworkSubmission.objects.get_or_create(
            homework=homework,
            student=student,
            defaults={
                'submission_file': submission_file,
                'submission_text': submission_text,
                'submission_date': timezone.now(),
                'status': 'submitted'
            }
        )
        
        if not created:
            if submission_file:
                submission.submission_file = submission_file
            if submission_text:
                submission.submission_text = submission_text
            submission.submission_date = timezone.now()
            submission.status = 'submitted'
            submission.save()
        
        # Check if late
        if submission.submission_date.date() > homework.due_date:
            submission.status = 'late'
            submission.save()
        
        messages.success(request, 'Homework submitted successfully!')
        return redirect('students_app:homework_list')
    
    submission = HomeworkSubmission.objects.filter(
        homework=homework, student=student
    ).first()
    
    context = {
        'homework': homework,
        'submission': submission,
    }
    return render(request, 'communication/homework_submit.html', context)


# ============================================
# TIMETABLE SYSTEM
# ============================================

@login_required
def timetable_view(request):
    """View timetable"""
    user_role = get_user_role(request.user)
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')
    
    timetable_data = {}
    
    if user_role == 'student':
        try:
            student = Student.objects.get(admission_number=request.user.username)
            if not check_student_access(student):
                messages.warning(request, 'Timetable is available for class 7 and above only.')
                return redirect('students_app:home')
            class_id = student.current_class.id if student.current_class else None
            section_id = student.section.id if student.section else None
        except Student.DoesNotExist:
            pass
    elif user_role == 'parent':
        try:
            parent = Parent.objects.get(user=request.user)
            # Get first student's class
            first_student = parent.students.first()
            if first_student:
                class_id = first_student.current_class.id if first_student.current_class else None
                section_id = first_student.section.id if first_student.section else None
        except Parent.DoesNotExist:
            pass
    
    if class_id:
        timetables = Timetable.objects.filter(
            class_assigned_id=class_id,
            is_active=True
        )
        if section_id:
            timetables = timetables.filter(Q(section_id=section_id) | Q(section__isnull=True))
        
        # Organize by day
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            day_timetable = timetables.filter(day=day).order_by('period_number')
            if day_timetable.exists():
                timetable_data[day] = day_timetable
    
    classes = Class.objects.all()
    sections = Section.objects.filter(class_assigned_id=class_id) if class_id else Section.objects.none()
    
    context = {
        'timetable_data': timetable_data,
        'classes': classes,
        'sections': sections,
        'selected_class_id': int(class_id) if class_id else None,
        'selected_section_id': int(section_id) if section_id else None,
        'user_role': user_role,
    }
    return render(request, 'communication/timetable_view.html', context)


@login_required
def timetable_upload(request):
    """Upload/create timetable (teachers/admin only)"""
    user_role = get_user_role(request.user)
    if user_role not in ['teacher', 'admin']:
        messages.error(request, 'Only teachers and admins can upload timetables.')
        return redirect('students_app:timetable_view')
    
    if request.method == 'POST':
        class_id = request.POST.get('class_assigned')
        section_id = request.POST.get('section', None)
        day = request.POST.get('day')
        period_number = request.POST.get('period_number')
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher', None)
        room_number = request.POST.get('room_number', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        try:
            timetable = Timetable.objects.create(
                class_assigned_id=class_id,
                section_id=section_id if section_id else None,
                day=day,
                period_number=period_number,
                subject_id=subject_id,
                teacher_id=teacher_id if teacher_id else None,
                room_number=room_number,
                start_time=start_time,
                end_time=end_time
            )
            messages.success(request, 'Timetable entry created successfully!')
            return redirect('students_app:timetable_view')
        except Exception as e:
            messages.error(request, f'Error creating timetable: {str(e)}')
    
    classes = Class.objects.all()
    sections = Section.objects.all()
    subjects = Subject.objects.filter(is_active=True)
    teachers = Teacher.objects.filter(is_active=True)
    
    context = {
        'classes': classes,
        'sections': sections,
        'subjects': subjects,
        'teachers': teachers,
    }
    return render(request, 'communication/timetable_upload.html', context)


# ============================================
# EVENT SCHEDULING SYSTEM
# ============================================

@login_required
def event_list(request):
    """List events"""
    events = EventSchedule.objects.filter(is_active=True)
    
    # Filter by date
    filter_date = request.GET.get('date', 'all')
    today = timezone.now().date()
    if filter_date == 'today':
        events = events.filter(start_date=today)
    elif filter_date == 'upcoming':
        events = events.filter(start_date__gte=today)
    elif filter_date == 'past':
        events = events.filter(start_date__lt=today)
    
    # Filter by type
    event_type = request.GET.get('type', 'all')
    if event_type != 'all':
        events = events.filter(event_type=event_type)
    
    paginator = Paginator(events, 20)
    page = request.GET.get('page')
    events_page = paginator.get_page(page)
    
    context = {
        'events': events_page,
        'filter_date': filter_date,
        'event_type': event_type,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'communication/event_list.html', context)


@login_required
def event_create(request):
    """Create event"""
    user_role = get_user_role(request.user)
    if user_role not in ['teacher', 'admin']:
        messages.error(request, 'Only teachers and admins can create events.')
        return redirect('students_app:event_list')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        event_type = request.POST.get('event_type')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date', None)
        start_time = request.POST.get('start_time', None)
        end_time = request.POST.get('end_time', None)
        venue = request.POST.get('venue', '')
        target_audience = request.POST.get('target_audience', 'all')
        target_class_id = request.POST.get('target_class', None)
        target_section_id = request.POST.get('target_section', None)
        is_all_day = request.POST.get('is_all_day') == 'on'
        attachment = request.FILES.get('attachment', None)
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
            
            event = EventSchedule.objects.create(
                title=title,
                description=description,
                event_type=event_type,
                start_date=start_date,
                end_date=end_date,
                start_time=start_time if not is_all_day else None,
                end_time=end_time if not is_all_day else None,
                venue=venue,
                target_audience=target_audience,
                target_class_id=target_class_id if target_class_id else None,
                target_section_id=target_section_id if target_section_id else None,
                is_all_day=is_all_day,
                attachment=attachment,
                created_by=request.user
            )
            messages.success(request, 'Event created successfully!')
            return redirect('students_app:event_list')
        except Exception as e:
            messages.error(request, f'Error creating event: {str(e)}')
    
    classes = Class.objects.all()
    sections = Section.objects.all()
    
    context = {
        'classes': classes,
        'sections': sections,
    }
    return render(request, 'communication/event_create.html', context)

