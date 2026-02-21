from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db.models import Count, Sum, Q, Avg # All necessary imports are here
from django.utils import timezone
from datetime import date
# ============================================
# Import all models
# ============================================
from .models import *

# Import SystemConfiguration from system_config (this works)
try:
    from .system_config import SystemConfiguration
except ImportError:
    SystemConfiguration = None

# Import CRM Models
try:
    from .enrollment_crm_models import (
        LeadSource, Lead, LeadActivity, Campaign, 
        CampaignLead, EnrollmentFunnel, Application
    )
except ImportError:
    # Models not available yet
    pass

class SchoolAdminSite(AdminSite):
    site_header = "School Management System"
    site_title = "School ERP Portal"
    index_title = "Dashboard"

school_admin_site = SchoolAdminSite(name='school_admin')
# ============================================
# ACADEMIC STRUCTURE
# ============================================

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['year', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current']
    search_fields = ['year']
    ordering = ['-start_date']
    
    actions = ['mark_as_current']
    
    def mark_as_current(self, request, queryset):
        AcademicYear.objects.all().update(is_current=False)
        queryset.update(is_current=True)
        self.message_user(request, f"{queryset.count()} academic year(s) marked as current.")
    mark_as_current.short_description = "Mark selected as Current Year"


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'numeric_value', 'section_count', 'student_count']
    ordering = ['numeric_value']
    search_fields = ['name']
    
    def section_count(self, obj):
        return obj.sections.count()
    section_count.short_description = 'Sections'
    
    def student_count(self, obj):
        return Student.objects.filter(current_class=obj, status='active').count()
    student_count.short_description = 'Active Students'


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_assigned', 'capacity', 'current_strength', 'availability']
    list_filter = ['class_assigned']
    search_fields = ['name']
    ordering = ['class_assigned__numeric_value', 'name']
    
    def current_strength(self, obj):
        count = Student.objects.filter(section=obj, status='active').count()
        return format_html('<strong>{}</strong>', count)
    current_strength.short_description = 'Current Strength'
    
    def availability(self, obj):
        count = Student.objects.filter(section=obj, status='active').count()
        available = obj.capacity - count
        color = 'green' if available > 5 else 'orange' if available > 0 else 'red'
        return format_html('<span style="color: {};">{} seats</span>', color, available)
    availability.short_description = 'Available'


# ============================================
# SUBJECT MANAGEMENT
# ============================================

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'subject_type', 'is_active', 'teacher_count']
    search_fields = ['name', 'code']
    list_filter = ['subject_type', 'is_active']
    
    def teacher_count(self, obj):
        return obj.staff_teachers.count() + obj.teacher_subjects.count()
    teacher_count.short_description = 'Teachers'


# ============================================
# TEACHER MANAGEMENT
# ============================================

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_name', 'phone', 'show_password', 'joining_date', 'is_active', 'photo_preview']
    list_filter = ['is_active', 'gender', 'joining_date']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'phone']
    filter_horizontal = ['subjects']
    date_hierarchy = 'joining_date'
    readonly_fields = ['show_password']
    
    def show_password(self, obj):
        """Display password in admin"""
        if obj.user:
            # Check SchoolUser for custom_password
            try:
                school_user = obj.user.school_profile
                if school_user and school_user.custom_password:
                    return format_html(
                        '<code style="background: #e8f5e9; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px;">{}</code>',
                        school_user.custom_password
                    )
            except:
                pass
            
            # Generate expected password
            password = f"Teacher@{obj.employee_id}"
            return format_html(
                '<code style="background: #fff3cd; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px;">{}</code>',
                password
            )
        return format_html('<span style="color: #999;">No user</span>')
    show_password.short_description = 'Password'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'employee_id', 'photo', 'date_of_birth', 'gender')
        }),
        ('Login Credentials', {
            'fields': ('show_password',),
            'description': 'Password format: Teacher@{EMPLOYEE_ID}'
        }),
        ('Contact Information', {
            'fields': ('phone', 'alternate_phone', 'address', 'city', 'state', 'pincode')
        }),
        ('Professional Information', {
            'fields': ('qualification', 'joining_date', 'salary', 'subjects')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def get_name(self, obj):
        return obj.user.get_full_name()
    get_name.short_description = 'Name'
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.photo.url)
        return '-'
    photo_preview.short_description = 'Photo'


@admin.register(ClassTeacher)
class ClassTeacherAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'section', 'academic_year']
    list_filter = ['academic_year', 'section__class_assigned']
    search_fields = ['teacher__user__first_name', 'teacher__user__last_name']


@admin.register(TimetableChangeRequest)
class TimetableChangeRequestAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'academic_year', 'status', 'created_at', 'reviewed_by', 'reviewed_at']
    list_filter = ['status', 'academic_year', 'created_at', 'reviewed_at']
    search_fields = ['teacher__user__first_name', 'teacher__user__last_name', 'teacher__employee_id', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Request Information', {
            'fields': ('teacher', 'academic_year', 'current_timetable_entry', 'reason', 'status')
        }),
        ('Preferred Changes', {
            'fields': ('preferred_day', 'preferred_time_slot', 'preferred_section', 'preferred_subject', 'preferred_room'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('additional_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('teacher', 'teacher__user', 'academic_year', 'current_timetable_entry', 'reviewed_by')


# ============================================
# STUDENT MANAGEMENT
# ============================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'admission_number', 'get_full_name', 'current_class', 
        'section', 'roll_number', 'show_password', 'status', 'father_phone', 'photo_preview'
    ]
    
    list_filter = [
        'status', 'current_class', 'section', 'gender', 
        'academic_year', 'is_transport_required'
    ]
    
    search_fields = [
        'admission_number', 'first_name', 'middle_name', 'last_name',
        'father_name', 'mother_name', 'father_phone', 'email'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'show_password']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'admission_number', 'roll_number', 'first_name', 
                'middle_name', 'last_name', 'date_of_birth', 
                'gender', 'blood_group', 'photo'
            )
        }),
        ('Login Credentials', {
            'fields': ('show_password',),
            'description': 'Password format: Student@{ROLL_NUMBER} or DOB (DDMMYYYY)'
        }),
        ('Contact Information', {
            'fields': (
                'email', 'phone', 'address', 'city', 'state', 'pincode'
            )
        }),
        ('Academic Information', {
            'fields': (
                'current_class', 'section', 'academic_year', 
                'admission_date', 'previous_school'
            )
        }),
        ('Father Information', {
            'fields': (
                'father_name', 'father_phone', 'father_occupation', 'father_email'
            )
        }),
        ('Mother Information', {
            'fields': (
                'mother_name', 'mother_phone', 'mother_occupation', 'mother_email'
            )
        }),
        ('Guardian Information (if applicable)', {
            'fields': (
                'guardian_name', 'guardian_phone', 'guardian_relation'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': (
                'status', 'is_transport_required', 'medical_conditions', 
                'birth_certificate'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def show_password(self, obj):
        """Display password in admin"""
        # Check if student has a user account
        try:
            from django.contrib.auth.models import User
            user = User.objects.filter(username=obj.admission_number).first()
            if user:
                # Check SchoolUser for custom_password
                try:
                    school_user = user.school_profile
                    if school_user and school_user.custom_password:
                        return format_html(
                            '<code style="background: #e8f5e9; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px;">{}</code>',
                            school_user.custom_password
                        )
                except:
                    pass
                
                # Generate expected password (DOB format)
                if obj.date_of_birth:
                    password = str(obj.date_of_birth).replace('-', '')
                    return format_html(
                        '<code style="background: #fff3cd; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px;">{}</code>',
                        password
                    )
        except:
            pass
        
        # Fallback: show expected format
        if obj.roll_number:
            password = f"Student@{obj.roll_number}"
        else:
            password = f"Student@{obj.admission_number}"
        return format_html(
            '<code style="background: #fff3cd; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px;">{}</code>',
            password
        )
    show_password.short_description = 'Password'
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.photo.url)
        return '-'
    photo_preview.short_description = 'Photo'
    
    actions = ['mark_as_active', 'mark_as_inactive']
    
    def mark_as_active(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f"{queryset.count()} students marked as active.")
    mark_as_active.short_description = "Mark selected students as Active"
    
    def mark_as_inactive(self, request, queryset):
        queryset.update(status='inactive')
        self.message_user(request, f"{queryset.count()} students marked as inactive.")
    mark_as_inactive.short_description = "Mark selected students as Inactive"


# ============================================
# ID CARD MANAGEMENT
# ============================================

@admin.register(IDCardTemplate)
class IDCardTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'orientation', 'template_preview', 'is_active', 'created_at']
    list_filter = ['is_active', 'orientation']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'template_image', 'orientation', 'width', 'height', 'is_active')
        }),
        ('Photo Position', {
            'fields': ('photo_x', 'photo_y', 'photo_width', 'photo_height'),
            'classes': ('collapse',)
        }),
        ('Text Positions', {
            'fields': (
                ('name_x', 'name_y', 'name_font_size'),
                ('admission_no_x', 'admission_no_y'),
                ('class_x', 'class_y'),
                ('contact_x', 'contact_y'),
            ),
            'classes': ('collapse',)
        }),
        ('QR Code Settings', {
            'fields': ('show_qr_code', 'qr_code_x', 'qr_code_y', 'qr_code_size'),
            'classes': ('collapse',)
        }),
        ('Display Options', {
            'fields': ('show_blood_group', 'show_dob'),
            'classes': ('collapse',)
        }),
    )
    
    def template_preview(self, obj):
        if obj.template_image:
            return format_html('<img src="{}" width="80" height="100" style="object-fit: cover;" />', obj.template_image.url)
        return "No Image"
    template_preview.short_description = 'Preview'


@admin.register(StudentIDCard)
class StudentIDCardAdmin(admin.ModelAdmin):
    list_display = [
        'card_number', 'student', 'template', 'issue_date', 
        'valid_until', 'status', 'card_preview'
    ]
    list_filter = ['status', 'template', 'issue_date', 'valid_until']
    search_fields = ['card_number', 'student__first_name', 'student__last_name', 'student__admission_number']
    readonly_fields = ['created_at', 'updated_at', 'issue_date']
    
    fieldsets = (
        ('Card Information', {
            'fields': ('student', 'template', 'card_number', 'status')
        }),
        ('Validity', {
            'fields': ('issue_date', 'valid_until')
        }),
        ('Generated Card', {
            'fields': ('generated_image', 'qr_code_data')
        }),
        ('Additional Info', {
            'fields': ('generated_by', 'notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def card_preview(self, obj):
        if obj.generated_image:
            return format_html('<img src="{}" width="60" height="80" style="object-fit: cover;" />', obj.generated_image.url)
        return "Not Generated"
    card_preview.short_description = 'Preview'
    
    actions = ['mark_as_expired', 'mark_as_active']
    
    def mark_as_expired(self, request, queryset):
        queryset.update(status='expired')
        self.message_user(request, f"{queryset.count()} ID cards marked as expired.")
    mark_as_expired.short_description = "Mark selected cards as Expired"
    
    def mark_as_active(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f"{queryset.count()} ID cards marked as active.")
    mark_as_active.short_description = "Mark selected cards as Active"


# ============================================
# ATTENDANCE
# ============================================

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status_badge', 'marked_by', 'remarks_preview']
    list_filter = ['status', 'date', 'student__section']
    search_fields = ['student__admission_number', 'student__first_name', 'student__last_name']
    date_hierarchy = 'date'
    
    def status_badge(self, obj):
        colors = {'P': 'green', 'A': 'red', 'L': 'orange', 'H': 'blue', 'E': 'gray'}
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def remarks_preview(self, obj):
        if obj.remarks:
            return obj.remarks[:50] + '...' if len(obj.remarks) > 50 else obj.remarks
        return '-'
    remarks_preview.short_description = 'Remarks'


# ============================================
# FEE MANAGEMENT
# ============================================

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['class_assigned', 'academic_year', 'tuition_fee', 'total_fee_display']
    list_filter = ['academic_year', 'class_assigned']
    search_fields = ['class_assigned__name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('class_assigned', 'academic_year')
        }),
        ('Fee Components', {
            'fields': ('tuition_fee', 'transport_fee', 'library_fee', 
                       'lab_fee', 'sports_fee', 'exam_fee', 'computer_fee', 'other_fee')
        }),
    )
    
    def total_fee_display(self, obj):
        return format_html('<strong>₹{:,.2f}</strong>', obj.get_total_fee())
    total_fee_display.short_description = 'Total Fee'


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'student', 'payment_date', 'amount_paid', 
                    'payment_method', 'payment_status', 'received_by']
    list_filter = ['payment_method', 'payment_status', 'payment_date', 'academic_year']
    search_fields = ['receipt_number', 'student__admission_number', 
                     'student__first_name', 'transaction_id']
    date_hierarchy = 'payment_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'academic_year')
        }),
        ('Payment Details', {
            'fields': ('receipt_number', 'payment_date', 'amount_paid', 'discount', 'late_fee')
        }),
        ('Transaction Information', {
            'fields': ('payment_method', 'payment_status', 'transaction_id', 'cheque_number', 'bank_name')
        }),
        ('Additional Information', {
            'fields': ('remarks', 'received_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # --- New Feature: Aggregates for Reporting ---
    def changelist_view(self, request, extra_context=None):
        # 1. Get the standard response from the base class
        response = super().changelist_view(request, extra_context)

        try:
            # 2. Extract the queryset (which respects filters and search terms)
            cl = response.context_data['cl']
            queryset = cl.queryset
        except (AttributeError, KeyError):
            # This handles cases where the view is not the standard changelist
            return response

        # 3. Perform the aggregation on the filtered queryset
        metrics = queryset.aggregate(
            total_paid=Sum('amount_paid'),
            total_discount=Sum('discount'),
            total_late_fee=Sum('late_fee'),
        )

        # 4. Format the metrics nicely (using Indian Rupee symbol and commas)
        formatted_metrics = {
            # Use '0.00' if the sum is None (i.e., no payments found)
            'total_paid_metric': f"₹{metrics['total_paid']:,.2f}" if metrics['total_paid'] is not None else '₹0.00',
            'total_discount_metric': f"₹{metrics['total_discount']:,.2f}" if metrics['total_discount'] is not None else '₹0.00',
            'total_late_fee_metric': f"₹{metrics['total_late_fee']:,.2f}" if metrics['total_late_fee'] is not None else '₹0.00',
            'payment_count_metric': queryset.count(),
        }

        # 5. Add the formatted metrics to the template context
        # These variables can be displayed in a custom change_list.html template.
        response.context_data.update(formatted_metrics)

        return response
    # ---------------------------------------------





# ============================================
# TIMETABLE
# ============================================

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['slot_name', 'start_time', 'end_time', 'is_break']
    list_filter = ['is_break']
    ordering = ['start_time']


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['section', 'weekday', 'time_slot', 'subject', 'teacher', 'room_number']
    list_filter = ['section', 'weekday', 'academic_year']
    search_fields = ['section__name', 'subject__name', 'teacher__user__first_name']
    
    def get_weekday(self, obj):
        return obj.get_weekday_display()
    get_weekday.short_description = 'Day'


# ============================================
# EXAMS & MARKS (NEW)
# ============================================

class ExamScheduleInline(admin.TabularInline):
    model = ExamSchedule
    extra = 1
    fields = ('class_assigned', 'subject', 'exam_date', 'max_marks')
    show_change_link = True


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'term', 'start_date', 'end_date', 'is_published']
    list_filter = ['academic_year', 'term', 'is_published']
    search_fields = ['name']
    inlines = [ExamScheduleInline]
    actions = ['publish_selected', 'unpublish_selected']

    def publish_selected(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"{updated} exam(s) published.")
    publish_selected.short_description = 'Publish selected exams'

    def unpublish_selected(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"{updated} exam(s) unpublished.")
    unpublish_selected.short_description = 'Unpublish selected exams'


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ['exam', 'class_assigned', 'subject', 'exam_date', 'max_marks']
    list_filter = ['exam', 'class_assigned', 'subject']
    search_fields = ['exam__name', 'subject__name', 'class_assigned__name']
    date_hierarchy = 'exam_date'


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ['student', 'get_class', 'get_subject', 'exam_name', 'marks_obtained', 'is_absent']
    list_filter = ['exam_schedule__exam', 'exam_schedule__class_assigned', 'exam_schedule__subject', 'is_absent']
    search_fields = ['student__admission_number', 'student__first_name', 'student__last_name']

    def get_class(self, obj):
        return obj.exam_schedule.class_assigned
    get_class.short_description = 'Class'

    def get_subject(self, obj):
        return obj.exam_schedule.subject
    get_subject.short_description = 'Subject'

    def exam_name(self, obj):
        return obj.exam_schedule.exam.name
    exam_name.short_description = 'Exam'


# ============================================
# CLASS TESTS (NEW)
# ============================================

@admin.register(ClassTest)
class ClassTestAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'class_assigned', 'subject', 'max_marks']
    list_filter = ['class_assigned', 'subject', 'date']
    search_fields = ['title']


@admin.register(ClassTestScore)
class ClassTestScoreAdmin(admin.ModelAdmin):
    list_display = ['test', 'student', 'marks_obtained']
    list_filter = ['test__class_assigned', 'test__subject']
    search_fields = ['student__admission_number', 'student__first_name']

# ============================================
# LIBRARY
# ============================================

@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'isbn', 'category', 'total_copies', 
                    'available_copies', 'availability_status']
    list_filter = ['category', 'added_date']
    search_fields = ['title', 'author', 'isbn']
    
    def availability_status(self, obj):
        if obj.available_copies > 0:
            return format_html('<span style="color: green;">✓ Available</span>')
        return format_html('<span style="color: red;">✗ Not Available</span>')
    availability_status.short_description = 'Status'


@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ['book', 'student', 'issue_date', 'due_date', 'return_date', 
                    'status_display', 'overdue_status']
    list_filter = ['status', 'issue_date', 'due_date']
    search_fields = ['book__title', 'student__admission_number', 'student__first_name']
    date_hierarchy = 'issue_date'
    
    def status_display(self, obj):
        colors = {'issued': 'blue', 'returned': 'green', 'lost': 'red', 'damaged': 'orange'}
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'gray'), obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def overdue_status(self, obj):
        if obj.is_overdue():
            days = (date.today() - obj.due_date).days
            return format_html('<span style="color: red;">Overdue by {} days</span>', days)
        return '-'
    overdue_status.short_description = 'Overdue'


# ============================================
# PARENT PORTAL
# ============================================

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'phone', 'show_password', 'children_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['user__first_name', 'user__last_name', 'phone']
    filter_horizontal = ['students']
    readonly_fields = ['show_password']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'phone', 'alternate_phone', 'address')
        }),
        ('Login Credentials', {
            'fields': ('show_password',),
            'description': 'Password: Child\'s Date of Birth (DDMMYYYY) - Same as student password'
        }),
        ('Children', {
            'fields': ('students',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def get_name(self, obj):
        return obj.user.get_full_name()
    get_name.short_description = 'Name'
    
    def children_count(self, obj):
        return obj.students.count()
    children_count.short_description = 'Children'
    
    def show_password(self, obj):
        """Display password in admin - Same as child's DOB"""
        if obj.user:
            # Check SchoolUser for custom_password
            try:
                school_user = obj.user.school_profile
                if school_user and school_user.custom_password:
                    return format_html(
                        '<code style="background: #e8f5e9; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px;">{}</code>',
                        school_user.custom_password
                    )
            except:
                pass
            
            # Get password from first child's DOB (same as student password)
            if obj.students.exists():
                first_child = obj.students.first()
                if first_child and first_child.date_of_birth:
                    password = str(first_child.date_of_birth).replace('-', '')
                    return format_html(
                        '<code style="background: #e3f2fd; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px;">{}</code> <small style="color: #666;">(Child DOB)</small>',
                        password
                    )
            
            # Fallback
            return format_html('<span style="color: #999;">No child DOB</span>')
        return format_html('<span style="color: #999;">No user</span>')
    show_password.short_description = 'Password (Child DOB)'


# ============================================
# COMMUNICATIONS
# ============================================

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'notice_date', 'target_audience', 'priority_badge', 
                    'is_active', 'created_by']
    list_filter = ['target_audience', 'priority', 'is_active', 'notice_date']
    search_fields = ['title', 'content']
    date_hierarchy = 'notice_date'
    
    def priority_badge(self, obj):
        colors = {'low': 'gray', 'medium': 'blue', 'high': 'orange', 'urgent': 'red'}
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.priority, 'gray'), obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'announcement_date', 'is_urgent', 'created_by']
    list_filter = ['is_urgent', 'announcement_date']
    search_fields = ['title', 'message']
    date_hierarchy = 'announcement_date'


# ============================================
# EVENTS
# ============================================

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'event_date', 'start_time', 'venue', 'is_holiday']
    list_filter = ['event_type', 'is_holiday', 'event_date']
    search_fields = ['title', 'venue']
    filter_horizontal = ['participants']
    date_hierarchy = 'event_date'


# ============================================
# TRANSPORT
# ============================================

@admin.register(TransportRoute)
class TransportRouteAdmin(admin.ModelAdmin):
    list_display = ['route_number', 'route_name', 'starting_point', 'ending_point', 
                    'total_distance', 'is_active']
    list_filter = ['is_active']
    search_fields = ['route_name', 'route_number']


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ['bus_number', 'registration_number', 'route', 'capacity', 
                    'driver_name', 'driver_phone', 'is_active']
    list_filter = ['is_active', 'route']
    search_fields = ['bus_number', 'registration_number', 'driver_name']


@admin.register(StudentTransport)
class StudentTransportAdmin(admin.ModelAdmin):
    list_display = ['student', 'bus', 'pickup_point', 'pickup_time', 'drop_time', 'is_active']
    list_filter = ['bus', 'is_active']
    search_fields = ['student__admission_number', 'student__first_name', 'pickup_point']


@admin.register(QuestionPaper)
class QuestionPaperAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'class_assigned', 'created_by', 'created_at']
    list_filter = ['subject', 'class_assigned', 'created_by']
    search_fields = ['title', 'questions', 'instructions']

# School Settings Admin
class SchoolUserInline(admin.TabularInline):
    model = SchoolUser
    extra = 0
    fields = ['user', 'role', 'login_id', 'is_active']
    readonly_fields = ['created_at']


@admin.register(SchoolSettings)
class SchoolSettingsAdmin(admin.ModelAdmin):
    list_display = ['school_name', 'school_phone', 'school_email', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('School Information', {
            'fields': ('school_name', 'school_address', 'school_phone', 'school_email', 'school_website')
        }),
        ('School Details', {
            'fields': ('principal_name', 'established_year', 'affiliation_number', 'board')
        }),
        ('Logo & Branding', {
            'fields': ('school_logo',)
        }),
        ('Receipt Settings', {
            'fields': ('receipt_footer_text',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not SchoolSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the only instance
        return False

# ============================================
# USER MANAGEMENT ADMIN
# ============================================

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Role Information', {
            'fields': ('name', 'display_name', 'description', 'is_active')
        }),
        ('Permissions', {
            'fields': ('permissions',),
            'description': 'List of permission codes for this role'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'principal_name', 'phone', 'subscription_active', 'created_at']
    list_filter = ['subscription_active', 'board', 'created_at']
    search_fields = ['name', 'principal_name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SchoolUserInline]
    
    fieldsets = (
        ('School Information', {
            'fields': ('name', 'address', 'phone', 'email', 'website', 'logo')
        }),
        ('School Details', {
            'fields': ('principal_name', 'established_year', 'affiliation_number', 'board')
        }),
        ('Subscription', {
            'fields': ('subscription_active', 'subscription_expires', 'max_users')
        }),
        ('Settings', {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SchoolBilling)
class SchoolBillingAdmin(admin.ModelAdmin):
    list_display = ['school', 'billing_period', 'amount', 'payment_status', 'due_date', 'payment_date']
    list_filter = ['payment_status', 'due_date', 'created_at']
    search_fields = ['school__name', 'billing_period', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Billing Information', {
            'fields': ('school', 'billing_period', 'amount', 'due_date')
        }),
        ('Payment Details', {
            'fields': ('payment_status', 'payment_date', 'payment_method', 'transaction_id')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SchoolUser)
class SchoolUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'school', 'login_id', 'show_password', 'is_active', 'created_at']
    list_filter = ['role', 'school', 'is_active', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'login_id', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'show_password']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'school')
        }),
        ('Login Credentials', {
            'fields': ('login_id', 'custom_password', 'show_password'),
            'description': 'Password format: Staff@{EMPLOYEE_ID} or Teacher@{EMPLOYEE_ID} or Student@{ROLL_NUMBER}'
        }),
        ('Profile', {
            'fields': ('phone', 'address', 'profile_picture')
        }),
        ('Status', {
            'fields': ('is_active', 'last_login')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def show_password(self, obj):
        """Display password in admin"""
        if obj.custom_password:
            return format_html(
                '<code style="background: #f0f0f0; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</code>',
                obj.custom_password
            )
        # Try to get password from related staff/teacher/student
        password = None
        if hasattr(obj, 'staff') and obj.staff:
            emp_id = obj.staff.employee_id
            password = f"Staff@{emp_id}"
        elif hasattr(obj, 'teacher') and obj.teacher:
            emp_id = obj.teacher.employee_id
            password = f"Teacher@{emp_id}"
        elif hasattr(obj, 'student') and obj.student:
            roll = obj.student.roll_number or obj.student.admission_number
            password = f"Student@{roll}"
        
        if password:
            return format_html(
                '<code style="background: #e8f5e9; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</code>',
                password
            )
        return format_html('<span style="color: #999;">Not set</span>')
    show_password.short_description = 'Password'


# Inline for SchoolUser in User admin
class SchoolUserInline(admin.StackedInline):
    model = SchoolUser
    can_delete = False
    verbose_name_plural = 'School Profile'


# Extend User admin
class CustomUserAdmin(UserAdmin):
    inlines = (SchoolUserInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_school_role')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    
    def get_school_role(self, obj):
        try:
            return obj.school_profile.role.display_name
        except:
            return 'No Role'
    get_school_role.short_description = 'School Role'


# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Hide all other models from super admin panel - only show school management
admin.site.unregister(Student)
admin.site.unregister(Class)
admin.site.unregister(Section)
admin.site.unregister(Subject)
admin.site.unregister(Teacher)
admin.site.unregister(ClassTeacher)
admin.site.unregister(Attendance)
admin.site.unregister(FeeStructure)
admin.site.unregister(FeePayment)
admin.site.unregister(AcademicYear)
admin.site.unregister(IDCardTemplate)
admin.site.unregister(StudentIDCard)
admin.site.unregister(TimeSlot)
admin.site.unregister(Timetable)
admin.site.unregister(Exam)
admin.site.unregister(ExamSchedule)
admin.site.unregister(Marks)
admin.site.unregister(ClassTest)
admin.site.unregister(ClassTestScore)
admin.site.unregister(BookCategory)
admin.site.unregister(Book)
admin.site.unregister(BookIssue)
admin.site.unregister(Parent)
admin.site.unregister(Notice)
admin.site.unregister(Announcement)
admin.site.unregister(Event)
admin.site.unregister(TransportRoute)
admin.site.unregister(Bus)
admin.site.unregister(StudentTransport)
admin.site.unregister(QuestionPaper)
admin.site.unregister(SchoolUser)

# ============================================
# NEW MODELS ADMIN REGISTRATION
# ============================================

# Homework Management
@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'class_assigned', 'assigned_by', 'due_date', 'is_active']
    list_filter = ['homework_type', 'subject', 'class_assigned', 'is_active', 'assigned_date']
    search_fields = ['title', 'description', 'assigned_by__user__first_name']
    date_hierarchy = 'assigned_date'
    ordering = ['-assigned_date']

@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'homework', 'submission_date', 'is_submitted', 'is_late', 'marks_obtained']
    list_filter = ['is_submitted', 'is_late', 'is_graded', 'homework__subject']
    search_fields = ['student__first_name', 'student__last_name', 'homework__title']
    date_hierarchy = 'submission_date'

# Inventory Management
@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_category', 'is_active']
    list_filter = ['is_active', 'parent_category']
    search_fields = ['name', 'description']

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['item_code', 'name', 'category', 'item_type', 'total_quantity', 'available_quantity', 'unit_price', 'is_active']
    list_filter = ['item_type', 'category', 'condition', 'is_active']
    search_fields = ['item_code', 'name', 'brand', 'model_number']
    ordering = ['name']

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['item', 'transaction_type', 'quantity', 'issued_to', 'transaction_date']
    list_filter = ['transaction_type', 'transaction_date']
    search_fields = ['item__name', 'issued_to', 'reference_number']
    date_hierarchy = 'transaction_date'

# Leave Management
@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'max_days_per_year', 'requires_approval', 'is_paid', 'is_active']
    list_filter = ['requires_approval', 'is_paid', 'is_active']

@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ['get_applicant_name', 'leave_type', 'from_date', 'to_date', 'total_days', 'status', 'applied_date']
    list_filter = ['applicant_type', 'leave_type', 'status', 'applied_date']
    search_fields = ['teacher__user__first_name', 'student__first_name', 'staff_member__first_name']
    date_hierarchy = 'applied_date'

# Staff Management
@admin.register(StaffCategory)
class StaffCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'category', 'designation', 'department', 'show_password', 'joining_date']
    list_filter = ['category', 'department', 'joining_date']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id', 'designation']
    readonly_fields = ['show_password']
    
    def show_password(self, obj):
        """Display password in admin"""
        if obj.user:
            # Check SchoolUser for custom_password
            try:
                school_user = obj.user.school_profile
                if school_user and school_user.custom_password:
                    return format_html(
                        '<code style="background: #e8f5e9; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px;">{}</code>',
                        school_user.custom_password
                    )
            except:
                pass
            
            # Generate expected password
            password = f"Staff@{obj.employee_id}"
            return format_html(
                '<code style="background: #fff3cd; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px;">{}</code>',
                password
            )
        return format_html('<span style="color: #999;">No user</span>')
    show_password.short_description = 'Password'

# Payroll Management
@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'component_type', 'calculation_type', 'is_taxable', 'is_active']
    list_filter = ['component_type', 'calculation_type', 'is_taxable', 'is_active']

@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'month', 'year', 'gross_salary', 'net_salary', 'status', 'payment_date']
    list_filter = ['status', 'year', 'month', 'payment_date']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    date_hierarchy = 'payment_date'

# Certificate Management
@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'certificate_type', 'description']
    list_filter = ['certificate_type']

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'student', 'template', 'issue_date', 'status', 'issued_by']
    list_filter = ['template__certificate_type', 'status', 'issue_date']
    search_fields = ['certificate_number', 'student__first_name', 'student__last_name']
    date_hierarchy = 'issue_date'

# Health Records
@admin.register(HealthCheckup)
class HealthCheckupAdmin(admin.ModelAdmin):
    list_display = ['student', 'checkup_date', 'height', 'weight', 'bmi', 'overall_health', 'doctor_name']
    list_filter = ['overall_health', 'follow_up_required', 'checkup_date']
    search_fields = ['student__first_name', 'student__last_name', 'doctor_name']
    date_hierarchy = 'checkup_date'

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'record_date', 'diagnosis', 'doctor_name', 'follow_up_required']
    list_filter = ['follow_up_required', 'record_date']
    search_fields = ['student__first_name', 'student__last_name', 'diagnosis', 'doctor_name']
    date_hierarchy = 'record_date'

# Hostel Management
@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ['name', 'hostel_type', 'total_rooms', 'total_capacity', 'warden_name', 'is_active']
    list_filter = ['hostel_type', 'is_active']

@admin.register(HostelRoom)
class HostelRoomAdmin(admin.ModelAdmin):
    list_display = ['hostel', 'room_number', 'floor', 'room_type', 'capacity', 'current_occupancy', 'is_available']
    list_filter = ['hostel', 'room_type', 'floor', 'is_available', 'is_under_maintenance']
    search_fields = ['room_number', 'hostel__name']

@admin.register(HostelAllocation)
class HostelAllocationAdmin(admin.ModelAdmin):
    list_display = ['student', 'room', 'allocation_date', 'status', 'is_active']
    list_filter = ['status', 'is_active', 'allocation_date']
    search_fields = ['student__first_name', 'student__last_name', 'room__room_number']

# Canteen Management
@admin.register(CanteenItem)
class CanteenItemAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'category', 'price', 'is_available', 'is_vegetarian', 'is_healthy']
    list_filter = ['category', 'is_available', 'is_vegetarian', 'is_healthy']
    search_fields = ['item_name', 'description']

@admin.register(CanteenOrder)
class CanteenOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'student', 'order_date', 'total_amount', 'status', 'payment_status']
    list_filter = ['status', 'payment_status', 'order_date']
    search_fields = ['order_number', 'student__first_name', 'student__last_name']
    date_hierarchy = 'order_date'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'item', 'quantity', 'unit_price', 'total_price']
    list_filter = ['item__category']

# Alumni Management
@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = ['student', 'graduation_year', 'current_occupation', 'company_organization', 'is_active']
    list_filter = ['graduation_year', 'current_occupation', 'is_active']
    search_fields = ['student__first_name', 'student__last_name', 'company_organization']

# Online Examination
@admin.register(OnlineExam)
class OnlineExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'class_assigned', 'total_marks', 'duration_minutes', 'status', 'start_date']
    list_filter = ['status', 'subject', 'class_assigned', 'start_date']
    search_fields = ['title', 'description']
    date_hierarchy = 'start_date'

@admin.register(OnlineExamQuestion)
class OnlineExamQuestionAdmin(admin.ModelAdmin):
    list_display = ['exam', 'question_text', 'question_type', 'marks', 'difficulty_level', 'order']
    list_filter = ['question_type', 'difficulty_level', 'exam__subject']
    search_fields = ['question_text', 'exam__title']

@admin.register(OnlineExamAttempt)
class OnlineExamAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'start_time', 'status', 'obtained_marks', 'percentage', 'is_passed']
    list_filter = ['status', 'is_passed', 'start_time']
    search_fields = ['student__first_name', 'student__last_name', 'exam__title']
    date_hierarchy = 'start_time'

@admin.register(OnlineExamAnswer)
class OnlineExamAnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'selected_option', 'is_correct', 'marks_obtained', 'is_graded']
    list_filter = ['is_correct', 'is_graded']

# ============================================
# SPORTS & CO-CURRICULAR ADMIN REGISTRATION
# ============================================

# Sports Management
@admin.register(SportsCategory)
class SportsCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']

@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'difficulty_level', 'coach_name', 'monthly_fee', 'is_active']
    list_filter = ['category', 'difficulty_level', 'is_active']
    search_fields = ['name', 'coach_name']

@admin.register(SportsRegistration)
class SportsRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student', 'sport', 'status', 'registration_date', 'fee_paid']
    list_filter = ['status', 'fee_paid', 'sport__category']
    search_fields = ['student__first_name', 'student__last_name', 'sport__name']
    date_hierarchy = 'registration_date'

@admin.register(SportsAchievement)
class SportsAchievementAdmin(admin.ModelAdmin):
    list_display = ['student', 'sport', 'title', 'level', 'position', 'event_date', 'is_verified']
    list_filter = ['achievement_type', 'level', 'is_verified', 'sport__category']
    search_fields = ['student__first_name', 'student__last_name', 'title']
    date_hierarchy = 'event_date'

# Co-curricular Activities
@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'is_active']
    list_filter = ['is_active']

@admin.register(CoCurricularActivity)
class CoCurricularActivityAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'instructor_name', 'monthly_fee', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'instructor_name']

@admin.register(ActivityRegistration)
class ActivityRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student', 'activity', 'status', 'registration_date', 'fee_paid']
    list_filter = ['status', 'fee_paid', 'activity__category']
    search_fields = ['student__first_name', 'student__last_name', 'activity__name']
    date_hierarchy = 'registration_date'

# House System
@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'house_master', 'total_students', 'total_points', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'house_master__user__first_name']

@admin.register(HouseMembership)
class HouseMembershipAdmin(admin.ModelAdmin):
    list_display = ['student', 'house', 'joined_date', 'points_earned', 'is_active']
    list_filter = ['house', 'is_active']
    search_fields = ['student__first_name', 'student__last_name', 'house__name']
    date_hierarchy = 'joined_date'

@admin.register(HouseEvent)
class HouseEventAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_type', 'event_date', 'venue', 'organized_by', 'is_completed']
    list_filter = ['event_type', 'is_completed', 'event_date']
    search_fields = ['name', 'venue', 'organized_by__user__first_name']
    date_hierarchy = 'event_date'

@admin.register(HouseEventResult)
class HouseEventResultAdmin(admin.ModelAdmin):
    list_display = ['event', 'house', 'position', 'points_earned', 'certificate_issued']
    list_filter = ['event__event_type', 'certificate_issued']
    search_fields = ['event__name', 'house__name']

# Student Leadership
@admin.register(LeadershipPosition)
class LeadershipPositionAdmin(admin.ModelAdmin):
    list_display = ['name', 'position_type', 'min_class', 'max_class', 'is_elected', 'is_active']
    list_filter = ['position_type', 'is_elected', 'is_active']
    search_fields = ['name']

@admin.register(StudentLeadership)
class StudentLeadershipAdmin(admin.ModelAdmin):
    list_display = ['student', 'position', 'house', 'appointment_date', 'status', 'performance_rating']
    list_filter = ['position__position_type', 'status', 'house']
    search_fields = ['student__first_name', 'student__last_name', 'position__name']
    date_hierarchy = 'appointment_date'

# Elections
@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'position', 'house', 'status', 'voting_start_date', 'voting_end_date']
    list_filter = ['status', 'position__position_type', 'house']
    search_fields = ['title', 'position__name']
    date_hierarchy = 'voting_start_date'

@admin.register(ElectionNomination)
class ElectionNominationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'election', 'status', 'nomination_date']
    list_filter = ['status', 'election__position__position_type']
    search_fields = ['candidate__first_name', 'candidate__last_name', 'election__title']
    date_hierarchy = 'nomination_date'

@admin.register(ElectionVote)
class ElectionVoteAdmin(admin.ModelAdmin):
    list_display = ['voter', 'candidate', 'election', 'vote_date']
    list_filter = ['election__position__position_type']
    search_fields = ['voter__first_name', 'voter__last_name', 'candidate__first_name']
    date_hierarchy = 'vote_date'

@admin.register(ElectionResult)
class ElectionResultAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'election', 'total_votes', 'position', 'percentage', 'is_winner']
    list_filter = ['is_winner', 'election__position__position_type']
    search_fields = ['candidate__first_name', 'candidate__last_name', 'election__title']


# ============================================
# EDUCATIONAL GAMES ADMIN
# ============================================

@admin.register(GameCategory)
class GameCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_active', 'game_count']
    list_filter = ['is_active']
    search_fields = ['name']
    
    def game_count(self, obj):
        return obj.games.count()
    game_count.short_description = 'Games Count'


@admin.register(EducationalGame)
class EducationalGameAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'class_level', 'difficulty', 'game_type', 'max_score', 'is_active']
    list_filter = ['category', 'class_level', 'difficulty', 'game_type', 'is_active']
    search_fields = ['title', 'description']
    filter_horizontal = []
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'class_level')
        }),
        ('Game Settings', {
            'fields': ('difficulty', 'game_type', 'time_limit', 'max_score', 'is_active')
        }),
        ('Learning Content', {
            'fields': ('instructions', 'learning_objectives')
        }),
    )


@admin.register(GameQuestion)
class GameQuestionAdmin(admin.ModelAdmin):
    list_display = ['game', 'question_text_short', 'question_type', 'points', 'order', 'is_active']
    list_filter = ['game__category', 'game__class_level', 'question_type', 'is_active']
    search_fields = ['question_text', 'game__title']
    ordering = ['game', 'order']
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(GameAnswer)
class GameAnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'answer_text_short', 'is_correct', 'order']
    list_filter = ['is_correct', 'question__game__category']
    search_fields = ['answer_text', 'question__question_text']
    
    def answer_text_short(self, obj):
        return obj.answer_text[:30] + "..." if len(obj.answer_text) > 30 else obj.answer_text
    answer_text_short.short_description = 'Answer'


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['student', 'game', 'score', 'percentage', 'time_taken', 'is_completed', 'started_at']
    list_filter = ['is_completed', 'game__category', 'game__class_level', 'started_at']
    search_fields = ['student__first_name', 'student__last_name', 'game__title']
    readonly_fields = ['started_at', 'completed_at']
    ordering = ['-started_at']


@admin.register(GameAchievement)
class GameAchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'condition_type', 'condition_value', 'points_reward', 'is_active']
    list_filter = ['is_active', 'condition_type']
    search_fields = ['name', 'description']


@admin.register(StudentGameAchievement)
class StudentGameAchievementAdmin(admin.ModelAdmin):
    list_display = ['student', 'achievement', 'unlocked_at']
    list_filter = ['achievement', 'unlocked_at']
    search_fields = ['student__first_name', 'student__last_name', 'achievement__name']
    readonly_fields = ['unlocked_at']


# ============================================
# MOCK TESTS ADMIN
# ============================================

@admin.register(MockTestCategory)
class MockTestCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_active', 'mock_test_count']
    list_filter = ['is_active']
    search_fields = ['name']
    
    def mock_test_count(self, obj):
        return obj.mock_tests.count()
    mock_test_count.short_description = 'Mock Tests Count'


@admin.register(MockTest)
class MockTestAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'class_level', 'difficulty', 'exam_type', 'total_marks', 'is_active']
    list_filter = ['category', 'class_level', 'difficulty', 'exam_type', 'is_active']
    search_fields = ['title', 'description']
    filter_horizontal = []
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'class_level')
        }),
        ('Test Settings', {
            'fields': ('difficulty', 'exam_type', 'time_limit', 'total_marks', 'passing_marks', 'is_active')
        }),
        ('Content', {
            'fields': ('instructions', 'syllabus_topics')
        }),
    )


@admin.register(MockTestQuestion)
class MockTestQuestionAdmin(admin.ModelAdmin):
    list_display = ['mock_test', 'question_text_short', 'question_type', 'marks', 'order', 'is_active']
    list_filter = ['mock_test__category', 'mock_test__class_level', 'question_type', 'is_active']
    search_fields = ['question_text', 'mock_test__title']
    ordering = ['mock_test', 'order']
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(MockTestAnswer)
class MockTestAnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'answer_text_short', 'is_correct', 'order']
    list_filter = ['is_correct', 'question__mock_test__category']
    search_fields = ['answer_text', 'question__question_text']
    
    def answer_text_short(self, obj):
        return obj.answer_text[:30] + "..." if len(obj.answer_text) > 30 else obj.answer_text
    answer_text_short.short_description = 'Answer'


@admin.register(MockTestSession)
class MockTestSessionAdmin(admin.ModelAdmin):
    list_display = ['student', 'mock_test', 'percentage', 'grade', 'is_passed', 'is_completed', 'started_at']
    list_filter = ['is_completed', 'is_passed', 'mock_test__category', 'mock_test__class_level', 'started_at']
    search_fields = ['student__first_name', 'student__last_name', 'mock_test__title']
    readonly_fields = ['started_at', 'completed_at']
    ordering = ['-started_at']


@admin.register(MockTestAttempt)
class MockTestAttemptAdmin(admin.ModelAdmin):
    list_display = ['session', 'question', 'is_correct', 'marks_obtained', 'attempted_at']
    list_filter = ['is_correct', 'attempted_at', 'session__mock_test__category']
    search_fields = ['session__student__first_name', 'session__student__last_name', 'question__question_text']
    readonly_fields = ['attempted_at']


# ============================================
# ID CARD GENERATOR ADMIN
# ============================================

@admin.register(IDCardGenerator)
class IDCardGeneratorAdmin(admin.ModelAdmin):
    list_display = ['card_type', 'page_size', 'orientation', 'school_name', 'is_active', 'created_at']
    list_filter = ['card_type', 'page_size', 'orientation', 'is_active']
    search_fields = ['school_name', 'school_address']
    fieldsets = (
        ('Generator Settings', {
            'fields': ('card_type', 'page_size', 'orientation', 'is_active')
        }),
        ('School Information', {
            'fields': ('school_name', 'school_address', 'school_phone', 'school_email')
        }),
        ('Card Design', {
            'fields': ('card_width', 'card_height', 'border_color', 'background_color')
        }),
    )


@admin.register(IDCardData)
class IDCardDataAdmin(admin.ModelAdmin):
    list_display = ['name', 'admission_no', 'class_name', 'section', 'is_generated', 'created_at']
    list_filter = ['is_generated', 'class_name', 'section', 'created_at']
    search_fields = ['name', 'admission_no', 'father_name', 'mobile']
    fieldsets = (
        ('Student Information', {
            'fields': ('name', 'father_name', 'mother_name', 'admission_no', 'date_of_birth')
        }),
        ('Academic Details', {
            'fields': ('class_name', 'section', 'roll_number')
        }),
        ('Contact Information', {
            'fields': ('address', 'mobile', 'emergency_contact')
        }),
        ('Additional Information', {
            'fields': ('photo', 'blood_group', 'valid_until')
        }),
        ('Status', {
            'fields': ('is_generated', 'generated_at')
        }),
    )
    readonly_fields = ['generated_at', 'created_at']

# ============================================
# CRM MODELS ADMIN REGISTRATION
# ============================================

try:
    @admin.register(LeadSource)
    class LeadSourceAdmin(admin.ModelAdmin):
        list_display = ['name', 'is_active', 'created_at']
        list_filter = ['is_active']
        search_fields = ['name', 'description']
    
    @admin.register(Lead)
    class LeadAdmin(admin.ModelAdmin):
        list_display = ['get_full_name', 'phone', 'email', 'status', 'priority', 'source', 'assigned_to', 'enquiry_date']
        list_filter = ['status', 'priority', 'source', 'assigned_to', 'enquiry_date']
        search_fields = ['first_name', 'last_name', 'email', 'phone', 'admission_number']
        readonly_fields = ['created_at', 'updated_at']
        fieldsets = (
            ('Basic Information', {
                'fields': ('first_name', 'last_name', 'email', 'phone', 'alternate_phone')
            }),
            ('Lead Details', {
                'fields': ('source', 'status', 'priority', 'assigned_to')
            }),
            ('Academic Interest', {
                'fields': ('interested_class', 'interested_subjects', 'previous_school')
            }),
            ('Parent Information', {
                'fields': ('parent_name', 'parent_email', 'parent_phone', 'relationship')
            }),
            ('Address', {
                'fields': ('address', 'city', 'state', 'pincode')
            }),
            ('Tracking', {
                'fields': ('enquiry_date', 'last_contacted', 'next_followup', 'converted_date')
            }),
            ('Notes', {
                'fields': ('notes', 'remarks')
            }),
            ('Conversion', {
                'fields': ('converted_to_student', 'conversion_value')
            }),
        )
    
    @admin.register(LeadActivity)
    class LeadActivityAdmin(admin.ModelAdmin):
        list_display = ['lead', 'activity_type', 'performed_by', 'activity_date']
        list_filter = ['activity_type', 'activity_date']
        search_fields = ['lead__first_name', 'lead__last_name', 'subject', 'description']
        readonly_fields = ['created_at']
    
    @admin.register(Campaign)
    class CampaignAdmin(admin.ModelAdmin):
        list_display = ['name', 'campaign_type', 'status', 'start_date', 'total_sent', 'total_converted']
        list_filter = ['campaign_type', 'status', 'start_date']
        search_fields = ['name', 'description']
        readonly_fields = ['created_at', 'updated_at']
    
    @admin.register(Application)
    class ApplicationAdmin(admin.ModelAdmin):
        list_display = ['application_number', 'lead', 'applied_class', 'status', 'application_date']
        list_filter = ['status', 'applied_class', 'application_date']
        search_fields = ['application_number', 'lead__first_name', 'lead__last_name']
        readonly_fields = ['application_number', 'created_at', 'updated_at']
except:
    pass

# At the end of admin.py file
admin.site.site_header = "School ERP - Super Admin Panel"
admin.site.site_title = "Super Admin Portal"
admin.site.index_title = "Manage Schools & System"







