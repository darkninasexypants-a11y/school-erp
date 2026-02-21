"""
API Serializers for School ERP Mobile App
Reuses existing Django models and logic
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Student, Class, Section, AcademicYear, Attendance, 
    FeePayment, FeeStructure, StudentIDCard, Teacher, Parent,
    Notice, Event, Timetable, Exam, Marks, IDCardTemplate,
    Book, BookIssue, BookCategory, ExamSchedule, Subject, TimeSlot
)
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
    """User serializer for authentication"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_superuser', 'is_staff', 'is_active']
        read_only_fields = ['id', 'is_superuser', 'is_staff', 'is_active']


class ClassSerializer(serializers.ModelSerializer):
    """Class serializer"""
    class Meta:
        model = Class
        fields = ['id', 'name', 'numeric_value']


class SectionSerializer(serializers.ModelSerializer):
    """Section serializer"""
    class_assigned = ClassSerializer(read_only=True)
    
    class Meta:
        model = Section
        fields = ['id', 'name', 'class_assigned']


class AcademicYearSerializer(serializers.ModelSerializer):
    """Academic Year serializer"""
    class Meta:
        model = AcademicYear
        fields = ['id', 'year', 'start_date', 'end_date', 'is_current']


class StudentListSerializer(serializers.ModelSerializer):
    """Student list serializer (lightweight)"""
    current_class = ClassSerializer(read_only=True)
    section = SectionSerializer(read_only=True)
    photo = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'admission_number', 'roll_number', 'first_name', 
            'middle_name', 'last_name', 'current_class', 'section',
            'gender', 'status', 'photo'
        ]
    
    def get_photo(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class StudentDetailSerializer(serializers.ModelSerializer):
    """Student detail serializer (full information)"""
    current_class = ClassSerializer(read_only=True)
    section = SectionSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True)
    photo = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'admission_number', 'roll_number', 'first_name', 
            'middle_name', 'last_name', 'date_of_birth', 'gender',
            'blood_group', 'email', 'phone', 'address', 'city', 
            'state', 'pincode', 'current_class', 'section', 
            'academic_year', 'admission_date', 'previous_school',
            'father_name', 'father_phone', 'mother_name', 'mother_phone',
            'guardian_name', 'guardian_phone', 'guardian_relation',
            'status', 'photo', 'aadhaar_card', 'samagra_id'
        ]
    
    def get_photo(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class AttendanceSerializer(serializers.ModelSerializer):
    """Attendance serializer"""
    student = StudentListSerializer(read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'student', 'date', 'status', 'remarks', 'created_at']


class FeeStructureSerializer(serializers.ModelSerializer):
    """Fee Structure serializer"""
    class_assigned = ClassSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True)
    
    class Meta:
        model = FeeStructure
        fields = [
            'id', 'class_assigned', 'academic_year', 'tuition_fee',
            'transport_fee', 'library_fee', 'lab_fee', 'sports_fee',
            'exam_fee', 'computer_fee', 'other_fee', 'get_total_fee'
        ]


class FeePaymentSerializer(serializers.ModelSerializer):
    """Fee Payment serializer"""
    student = StudentListSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True, allow_null=True)
    
    class Meta:
        model = FeePayment
        fields = [
            'id', 'student', 'amount_paid', 'payment_date', 'payment_method',
            'receipt_number', 'academic_year', 'remarks', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StudentIDCardSerializer(serializers.ModelSerializer):
    """Student ID Card serializer"""
    student = StudentListSerializer(read_only=True)
    
    class Meta:
        model = StudentIDCard
        fields = [
            'id', 'student', 'template', 'card_number', 'issue_date',
            'expiry_date', 'is_active', 'front_image', 'back_image'
        ]


class NoticeSerializer(serializers.ModelSerializer):
    """Notice serializer"""
    class Meta:
        model = Notice
        fields = [
            'id', 'title', 'content', 'notice_date', 'target_audience',
            'status', 'is_active', 'published_at', 'created_at'
        ]


class EventSerializer(serializers.ModelSerializer):
    """Event serializer"""
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_date', 'event_time',
            'venue', 'is_active', 'created_at'
        ]


class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistics serializer - supports both super admin and school admin"""
    user_type = serializers.CharField(required=False)
    
    # Super Admin fields
    total_schools = serializers.IntegerField(required=False)
    active_schools = serializers.IntegerField(required=False)
    total_users = serializers.IntegerField(required=False)
    system_health = serializers.IntegerField(required=False)
    
    # School Admin fields
    total_students = serializers.IntegerField()
    total_teachers = serializers.IntegerField()
    total_classes = serializers.IntegerField()
    present_today = serializers.IntegerField()
    absent_today = serializers.IntegerField()
    total_fee_collected = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_fees = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_fee_structures = serializers.IntegerField(required=False)
    monthly_fee_collection = serializers.ListField(
        child=serializers.FloatField(),
        required=False,
        allow_null=True
    )


class BookCategorySerializer(serializers.ModelSerializer):
    """Book Category serializer"""
    class Meta:
        model = BookCategory
        fields = ['id', 'name', 'description']


class BookSerializer(serializers.ModelSerializer):
    """Book serializer"""
    category = BookCategorySerializer(read_only=True, allow_null=True)
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'isbn', 'title', 'author', 'publisher', 'category',
            'edition', 'publication_year', 'total_copies', 'available_copies',
            'price', 'rack_number', 'description', 'cover_image', 'is_available'
        ]
    
    def get_is_available(self, obj):
        """Get availability status"""
        return obj.available_copies > 0


class BookIssueSerializer(serializers.ModelSerializer):
    """Book Issue serializer"""
    book = BookSerializer(read_only=True)
    student = StudentListSerializer(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = BookIssue
        fields = [
            'id', 'book', 'student', 'issue_date', 'due_date', 'return_date',
            'fine_amount', 'fine_paid', 'status', 'remarks', 'is_overdue'
        ]


class SubjectSerializer(serializers.ModelSerializer):
    """Subject serializer"""
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code']


class TimeSlotSerializer(serializers.ModelSerializer):
    """Time Slot serializer"""
    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time', 'period_number']


class TimetableSerializer(serializers.ModelSerializer):
    """Timetable serializer"""
    section = SectionSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    time_slot = TimeSlotSerializer(read_only=True)
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    
    class Meta:
        model = Timetable
        fields = [
            'id', 'section', 'academic_year', 'weekday', 'weekday_display',
            'time_slot', 'subject', 'teacher', 'room_number'
        ]


class ExamSerializer(serializers.ModelSerializer):
    """Exam serializer"""
    academic_year = AcademicYearSerializer(read_only=True)
    term_display = serializers.CharField(source='get_term_display', read_only=True)
    
    class Meta:
        model = Exam
        fields = [
            'id', 'name', 'academic_year', 'term', 'term_display',
            'start_date', 'end_date', 'is_published', 'created_at'
        ]


class ExamScheduleSerializer(serializers.ModelSerializer):
    """Exam Schedule serializer"""
    exam = ExamSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    class_assigned = ClassSerializer(read_only=True)
    
    class Meta:
        model = ExamSchedule
        fields = [
            'id', 'exam', 'subject', 'class_assigned', 'exam_date', 'max_marks'
        ]


class MarksSerializer(serializers.ModelSerializer):
    """Marks serializer"""
    student = StudentListSerializer(read_only=True)
    exam_schedule = ExamScheduleSerializer(read_only=True)
    
    class Meta:
        model = Marks
        fields = [
            'id', 'student', 'exam_schedule', 'marks_obtained',
            'is_absent', 'remarks', 'created_at'
        ]


class IDCardTemplateSerializer(serializers.ModelSerializer):
    """ID Card Template serializer"""
    template_file = serializers.SerializerMethodField()
    
    class Meta:
        model = IDCardTemplate
        fields = [
            'id', 'name', 'description', 'template_image', 'template_file',
            'orientation', 'width', 'height', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_template_file(self, obj):
        if obj.template_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.template_image.url)
            return obj.template_image.url
        return None

