from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

# Import Enrollment CRM Models
try:
    from .enrollment_crm_models import (
        LeadSource, Lead, LeadActivity, Campaign, 
        CampaignLead, EnrollmentFunnel, Application
    )
except ImportError:
    # Models will be imported after enrollment_crm_models is created
    pass

# ============================================
# SUBJECT MANAGEMENT
# ============================================

class Subject(models.Model):
    """Subject Management"""
    SUBJECT_TYPE_CHOICES = [
        ('core', 'Core Subject'),
        ('language', 'Language'),
        ('science', 'Science'),
        ('mathematics', 'Mathematics'),
        ('social', 'Social Studies'),
        ('creative', 'Creative Arts'),
        ('physical', 'Physical Education'),
        ('technology', 'Technology'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    subject_type = models.CharField(max_length=20, choices=SUBJECT_TYPE_CHOICES, default='core')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

# Global Validators
phone_regex = RegexValidator(
    # Regex for international phone numbers, up to 15 digits
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)

# ============================================
# ACADEMIC STRUCTURE
# ============================================

class AcademicYear(models.Model):
    year = models.CharField(max_length=20, unique=True)  # e.g., "2024-2025"
    is_current = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField()
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.year


class Class(models.Model):
    name = models.CharField(max_length=50)  # e.g., "10th", "Class 10"
    numeric_value = models.IntegerField()  # For sorting: 1, 2, 3... 10, 11, 12
    
    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['numeric_value']
    
    def __str__(self):
        return self.name


class Section(models.Model):
    name = models.CharField(max_length=10)  # e.g., "A", "B", "C"
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='sections')
    capacity = models.IntegerField(default=40)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'class_assigned']
    
    def __str__(self):
        return f"{self.class_assigned.name} - {self.name}"


# ============================================
# STUDENT MANAGEMENT
# ============================================

class Student(models.Model):
    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True, blank=True, related_name='students')
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('transferred', 'Transferred'),
        ('graduated', 'Graduated'),
    ]
    
    # Basic Information
    admission_number = models.CharField(max_length=20, unique=True)
    roll_number = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    
    # Contact Information
    email = models.EmailField(blank=True)
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Academic Information
    current_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='students')
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, related_name='students')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True)
    admission_date = models.DateField()
    previous_school = models.CharField(max_length=200, blank=True)
    
    # Parent/Guardian Information
    father_name = models.CharField(max_length=200)
    father_phone = models.CharField(validators=[phone_regex], max_length=17)
    father_occupation = models.CharField(max_length=100, blank=True)
    father_email = models.EmailField(blank=True)
    
    mother_name = models.CharField(max_length=200)
    mother_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    mother_occupation = models.CharField(max_length=100, blank=True)
    mother_email = models.EmailField(blank=True)
    
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    guardian_relation = models.CharField(max_length=50, blank=True)
    
    # Documents and Photos
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    birth_certificate = models.FileField(upload_to='birth_certificates/', blank=True, null=True)
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    designation = models.CharField(max_length=50, default='Student')
    is_transport_required = models.BooleanField(default=False)
    medical_conditions = models.TextField(blank=True, null=True)
    apaar_id = models.CharField(max_length=12, unique=True, blank=True, null=True, help_text="12-digit Automated Permanent Academic Account Registry ID")
    aadhaar_card = models.CharField(max_length=12, blank=True, null=True, help_text="12-digit Aadhaar Card Number")
    samagra_id = models.CharField(max_length=9, blank=True, null=True, help_text="9-digit Samagra ID")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['current_class__numeric_value', 'section__name', 'roll_number', 'first_name']
        indexes = [
            models.Index(fields=['admission_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.admission_number} - {self.get_full_name()}"
    
    def get_full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def get_class_section(self):
        if self.current_class and self.section:
            return f"{self.current_class.name} - {self.section.name}"
        return "Not Assigned"


# ============================================
# ID CARD MANAGEMENT
# ============================================

class IDCardTemplate(models.Model):
    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True, blank=True, related_name='id_card_templates')
    ORIENTATION_CHOICES = [
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
    ]

    name = models.CharField(max_length=100)  # Removed unique=True globally
    description = models.TextField(blank=True, null=True)
    template_image = models.ImageField(upload_to='id_card_templates/', help_text="Background image for the ID card.")
    orientation = models.CharField(max_length=10, choices=ORIENTATION_CHOICES, default='portrait')
    width = models.IntegerField(default=338)
    height = models.IntegerField(default=528)
    is_active = models.BooleanField(default=True)
    
    # Advanced JSON Layout System (from external ID card system)
    layout_json = models.JSONField(default=dict, blank=True, null=True, 
                                   help_text="JSON layout definition with elements, background, and positioning")
    
    # Legacy Text Position Fields (for backward compatibility)
    photo_x = models.IntegerField(default=10, null=True, blank=True); photo_y = models.IntegerField(default=10, null=True, blank=True)
    photo_width = models.IntegerField(default=100, null=True, blank=True); photo_height = models.IntegerField(default=120, null=True, blank=True)

    name_x = models.IntegerField(default=10, null=True, blank=True); name_y = models.IntegerField(default=200, null=True, blank=True); name_font_size = models.IntegerField(default=18, null=True, blank=True)
    
    admission_no_x = models.IntegerField(default=10, null=True, blank=True); admission_no_y = models.IntegerField(default=220, null=True, blank=True)
    
    class_x = models.IntegerField(default=10, null=True, blank=True); class_y = models.IntegerField(default=240, null=True, blank=True)
    
    contact_x = models.IntegerField(default=10, null=True, blank=True); contact_y = models.IntegerField(default=260, null=True, blank=True)
    
    # QR Code Settings
    show_qr_code = models.BooleanField(default=True)
    qr_code_x = models.IntegerField(default=200, null=True, blank=True); qr_code_y = models.IntegerField(default=20, null=True, blank=True); qr_code_size = models.IntegerField(default=50, null=True, blank=True)

    # Additional positions for other fields
    section_x = models.IntegerField(default=10, null=True, blank=True); section_y = models.IntegerField(default=240, null=True, blank=True)
    father_x = models.IntegerField(default=10, null=True, blank=True); father_y = models.IntegerField(default=280, null=True, blank=True)
    mother_x = models.IntegerField(default=10, null=True, blank=True); mother_y = models.IntegerField(default=300, null=True, blank=True)
    guardian_x = models.IntegerField(default=10, null=True, blank=True); guardian_y = models.IntegerField(default=320, null=True, blank=True)
    address_x = models.IntegerField(default=10, null=True, blank=True); address_y = models.IntegerField(default=340, null=True, blank=True)
    dob_x = models.IntegerField(default=10, null=True, blank=True); dob_y = models.IntegerField(default=360, null=True, blank=True)
    blood_group_x = models.IntegerField(default=10, null=True, blank=True); blood_group_y = models.IntegerField(default=380, null=True, blank=True)

    # Display Options - Field Selection
    show_name = models.BooleanField(default=True, help_text="Show student name")
    show_photo = models.BooleanField(default=True, help_text="Show student photo")
    show_admission_no = models.BooleanField(default=True, help_text="Show admission number")
    show_class = models.BooleanField(default=True, help_text="Show class")
    show_section = models.BooleanField(default=True, help_text="Show section")
    show_father_name = models.BooleanField(default=False, help_text="Show father name")
    show_mother_name = models.BooleanField(default=False, help_text="Show mother name")
    show_guardian_name = models.BooleanField(default=False, help_text="Show guardian name")
    show_mobile = models.BooleanField(default=False, help_text="Show mobile number")
    show_address = models.BooleanField(default=False, help_text="Show address")
    show_blood_group = models.BooleanField(default=False, help_text="Show blood group")
    show_dob = models.BooleanField(default=False, help_text="Show date of birth")
    show_qr_code = models.BooleanField(default=True, help_text="Show QR code")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['school', 'name']  # Unique per school

    def __str__(self):
        return self.name
    
    def get_layout(self):
        """Get layout as dictionary"""
        if self.layout_json:
            return self.layout_json
        return {}
    
    def set_layout(self, layout_dict):
        """Set layout from dictionary"""
        self.layout_json = layout_dict


class StudentIDCard(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('lost', 'Lost'),
        ('replaced', 'Replaced'),
    ]

    card_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='id_cards')
    template = models.ForeignKey(IDCardTemplate, on_delete=models.SET_NULL, null=True)
    issue_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    # Generated Output
    generated_image = models.ImageField(upload_to='generated_id_cards/', blank=True, null=True)
    qr_code_data = models.CharField(max_length=255, blank=True, null=True)
    generated_by = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"ID Card - {self.student.get_full_name()} ({self.card_number})"


class StaffIDCard(models.Model):
    """Staff ID Card with QR code for attendance punching"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('lost', 'Lost'),
        ('replaced', 'Replaced'),
    ]

    card_number = models.CharField(max_length=50, unique=True)
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE, related_name='id_cards', null=True, blank=True)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='id_cards', null=True, blank=True)
    template = models.ForeignKey(IDCardTemplate, on_delete=models.SET_NULL, null=True)
    issue_date = models.DateField(auto_now_add=True)
    valid_until = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    # Generated Output
    generated_image = models.ImageField(upload_to='generated_id_cards/staff/', blank=True, null=True)
    qr_code_data = models.TextField(blank=True, null=True, help_text="QR code data for attendance punching")
    qr_code_hash = models.CharField(max_length=64, blank=True, null=True, help_text="Hash for QR code verification")
    generated_by = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Staff ID Card'
        verbose_name_plural = 'Staff ID Cards'
    
    def __str__(self):
        name = self.staff.get_full_name() if self.staff else self.teacher.user.get_full_name()
        return f"Staff ID Card - {name} ({self.card_number})"
    
    def get_staff_member(self):
        """Get the staff member (Staff or Teacher)"""
        return self.staff or self.teacher


# ============================================
# SUBJECT MANAGEMENT
# ============================================



# ============================================
# TEACHER MANAGEMENT
# ============================================

class Teacher(models.Model):
    """Teaching Staff - Only for teachers who teach classes"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True, blank=True, related_name='teachers', help_text="School this teacher belongs to")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20)
    phone = models.CharField(validators=[phone_regex], max_length=17)
    alternate_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField()
    city = models.CharField(max_length=100, default='')
    state = models.CharField(max_length=100, default='')
    pincode = models.CharField(max_length=10, default='')
    qualification = models.CharField(max_length=200)
    designation = models.CharField(max_length=50, default='Teacher')
    joining_date = models.DateField()
    current_salary = models.DecimalField(max_digits=10, decimal_places=2)
    subjects = models.ManyToManyField(Subject, related_name='teacher_subjects', blank=True)
    photo = models.ImageField(upload_to='teachers/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        unique_together = [['school', 'employee_id']]  # Employee ID unique per school
        verbose_name = 'Teaching Staff'
        verbose_name_plural = 'Teaching Staff'
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class ClassTeacher(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['section', 'academic_year']
    
    def __str__(self):
        return f"{self.teacher} - {self.section}"


# ============================================
# ATTENDANCE MANAGEMENT
# ============================================

class Attendance(models.Model):
    """Student Attendance"""
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Late'),
        ('H', 'Half Day'),
        ('E', 'Excused'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', 'student']
        verbose_name_plural = "Student Attendance"
    
    def __str__(self):
        return f"{self.student} - {self.date} - {self.get_status_display()}"


class TeacherAttendance(models.Model):
    """Teacher Attendance"""
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Late'),
        ('H', 'Half Day'),
        ('E', 'Excused'),
        ('L', 'Leave'),
    ]
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    check_in_time = models.TimeField(null=True, blank=True, help_text="Check-in time")
    check_out_time = models.TimeField(null=True, blank=True, help_text="Check-out time")
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Verification fields (OCR and Face Verification)
    verification_photo = models.ImageField(upload_to='attendance_verification/teachers/', blank=True, null=True, help_text="Photo used for verification")
    ocr_extracted_data = models.JSONField(default=dict, blank=True, null=True, help_text="Data extracted from ID card using OCR")
    face_match_result = models.BooleanField(null=True, blank=True, help_text="Face verification result (True if match, False if no match)")
    face_match_confidence = models.FloatField(null=True, blank=True, help_text="Face match confidence score")
    verification_method = models.CharField(max_length=20, choices=[('manual', 'Manual'), ('ocr', 'OCR'), ('face', 'Face Verification'), ('both', 'OCR + Face')], default='manual')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['teacher', 'date']
        ordering = ['-date', 'teacher']
        verbose_name_plural = "Teacher Attendance"
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.date} - {self.get_status_display()}"


class StaffAttendance(models.Model):
    """Non-Teaching Staff Attendance"""
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Late'),
        ('H', 'Half Day'),
        ('E', 'Excused'),
        ('L', 'Leave'),
    ]
    
    staff = models.ForeignKey('Staff', on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    check_in_time = models.TimeField(null=True, blank=True, help_text="Check-in time")
    check_out_time = models.TimeField(null=True, blank=True, help_text="Check-out time")
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Verification fields (OCR and Face Verification)
    verification_photo = models.ImageField(upload_to='attendance_verification/staff/', blank=True, null=True, help_text="Photo used for verification")
    ocr_extracted_data = models.JSONField(default=dict, blank=True, null=True, help_text="Data extracted from ID card using OCR")
    face_match_result = models.BooleanField(null=True, blank=True, help_text="Face verification result (True if match, False if no match)")
    face_match_confidence = models.FloatField(null=True, blank=True, help_text="Face match confidence score")
    verification_method = models.CharField(max_length=20, choices=[('manual', 'Manual'), ('ocr', 'OCR'), ('face', 'Face Verification'), ('both', 'OCR + Face')], default='manual')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['staff', 'date']
        ordering = ['-date', 'staff']
        verbose_name_plural = "Staff Attendance"
    
    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.date} - {self.get_status_display()}"


# ============================================
# FEE MANAGEMENT
# ============================================

class FeeStructure(models.Model):
    STREAM_CHOICES = [
        ('general', 'General (No Stream)'),
        ('science', 'Science'),
        ('commerce', 'Commerce'),
        ('arts', 'Arts'),
        ('math_science', 'Math-Science'),
        ('biology_science', 'Biology-Science'),
    ]
    
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    # Subject/Stream based fee (for classes 9-12)
    stream = models.CharField(max_length=50, choices=STREAM_CHOICES, default='general', blank=True, null=True,
                             help_text="Select stream for classes 9-12 (Science, Commerce, Arts, etc.)")
    subjects = models.ManyToManyField(Subject, blank=True, related_name='fee_structures',
                                     help_text="Select specific subjects for this fee structure (optional)")
    
    # Fee Components
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    library_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lab_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sports_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exam_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    computer_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Optional subject fee (for class 9)
    optional_subject_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                              help_text="Additional fee for optional subjects (Class 9)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['class_assigned', 'academic_year', 'stream']
        verbose_name_plural = "Fee Structures"
    
    def __str__(self):
        stream_text = f" - {self.get_stream_display()}" if self.stream and self.stream != 'general' else ""
        return f"Fee Structure - {self.class_assigned}{stream_text} - {self.academic_year}"
    
    def get_total_fee(self):
        return (self.tuition_fee + self.transport_fee + self.library_fee + 
                self.lab_fee + self.sports_fee + self.exam_fee + 
                self.computer_fee + self.other_fee + self.optional_subject_fee)
    
    def calculate_fee_with_concessions(self, student, academic_year):
        """
        Calculate fee for a student considering all concessions/scholarships
        Returns: (total_fee, total_discount, final_amount)
        """
        from decimal import Decimal
        total_fee = self.get_total_fee()
        total_discount = Decimal('0.00')
        
        # Get active concessions for this student
        try:
            from .fee_enhancements import StudentFeeConcession
            concessions = StudentFeeConcession.objects.filter(
                student=student,
                academic_year=academic_year,
                is_active=True
            ).select_related('concession')
            
            for student_concession in concessions:
                concession = student_concession.concession
                if concession.is_percentage:
                    discount = (total_fee * concession.percentage) / Decimal('100')
                else:
                    discount = concession.fixed_amount
                total_discount += discount
        except ImportError:
            pass
        
        final_amount = total_fee - total_discount
        return (total_fee, total_discount, max(final_amount, Decimal('0.00')))


class FeePayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Debit/Credit Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
        ('cheque', 'Cheque'),
        ('dd', 'Demand Draft'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    receipt_number = models.CharField(max_length=50, unique=True)
    payment_date = models.DateField()
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    
    # Amount Details
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment Details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='completed')
    transaction_id = models.CharField(max_length=100, blank=True)
    cheque_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    remarks = models.TextField(blank=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='fee_collections')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.receipt_number} - {self.student} - ₹{self.amount_paid}"
    
    def get_net_amount(self):
        return self.amount_paid - self.discount + self.late_fee
    
    def generate_receipt_number(self):
        """Generate unique receipt number"""
        import random
        import string
        if not self.receipt_number:
            prefix = "RCP"
            year = self.payment_date.year
            random_part = ''.join(random.choices(string.digits, k=6))
            self.receipt_number = f"{prefix}{year}{random_part}"
        return self.receipt_number



# ============================================
# TIMETABLE MANAGEMENT
# ============================================

class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_name = models.CharField(max_length=50)  # e.g., "Period 1", "Break", "Lunch"
    is_break = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        # Format time for clean display
        return f"{self.slot_name} ({self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')})"


class Timetable(models.Model):
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
    ]
    
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='timetables')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    room_number = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['section', 'academic_year', 'weekday', 'time_slot']
        ordering = ['weekday', 'time_slot']
    
    def __str__(self):
        return f"{self.section} - {self.get_weekday_display()} - {self.time_slot}"


class TimetableChangeRequest(models.Model):
    """Model for teachers to request changes to their timetable"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_progress', 'In Progress'),
    ]
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='timetable_change_requests')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    current_timetable_entry = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='change_requests', null=True, blank=True, help_text="The timetable entry that needs to be changed")
    
    # Request details
    reason = models.TextField(help_text="Reason for requesting the change")
    preferred_day = models.IntegerField(choices=Timetable.WEEKDAY_CHOICES, null=True, blank=True, help_text="Preferred day if changing day")
    preferred_time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True, help_text="Preferred time slot if changing time")
    preferred_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, help_text="Preferred section if changing class")
    preferred_subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, help_text="Preferred subject if changing subject")
    preferred_room = models.CharField(max_length=50, blank=True, help_text="Preferred room if changing room")
    
    # Additional notes
    additional_notes = models.TextField(blank=True, help_text="Any additional information or suggestions")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_timetable_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, help_text="Admin's response or notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Timetable Change Request'
        verbose_name_plural = 'Timetable Change Requests'
    
    def get_preferred_day_display_name(self):
        """Get display name for preferred day"""
        if self.preferred_day is not None:
            return dict(Timetable.WEEKDAY_CHOICES).get(self.preferred_day, '')
        return ''
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.get_status_display()} - {self.created_at.strftime('%Y-%m-%d')}"


# ============================================
# EXAMS AND MARKS
# ============================================

class Exam(models.Model):
    TERM_CHOICES = [
        ('unit', 'Unit Test'),
        ('midterm', 'Mid Term'),
        ('final', 'Final Exam'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.CharField(max_length=20, choices=TERM_CHOICES, default='other')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date', 'name']
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'

    def __str__(self):
        return f"{self.name} - {self.academic_year}"


class ExamSchedule(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='schedules')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    exam_date = models.DateField()
    max_marks = models.IntegerField(default=100, validators=[MinValueValidator(1), MaxValueValidator(1000)])

    class Meta:
        unique_together = ['exam', 'subject', 'class_assigned']
        ordering = ['exam_date']
        verbose_name = 'Exam Schedule'
        verbose_name_plural = 'Exam Schedules'

    def __str__(self):
        return f"{self.exam} - {self.class_assigned} - {self.subject}"


class Marks(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE)
    marks_obtained = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_absent = models.BooleanField(default=False)
    remarks = models.CharField(max_length=255, blank=True)
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'exam_schedule']
        ordering = ['student__roll_number']
        verbose_name = 'Mark'
        verbose_name_plural = 'Marks'

    def __str__(self):
        return f"{self.student} - {self.exam_schedule}"


# ============================================
# CLASS TESTS (FOR ONGOING PROGRESS)
# ============================================

class ClassTest(models.Model):
    """Small, frequent classroom tests to track ongoing performance."""
    title = models.CharField(max_length=100)
    date = models.DateField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    max_marks = models.IntegerField(default=20, validators=[MinValueValidator(1), MaxValueValidator(1000)])

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} - {self.class_assigned} - {self.subject}"


class ClassTestScore(models.Model):
    test = models.ForeignKey(ClassTest, on_delete=models.CASCADE, related_name='scores')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='class_test_scores')
    marks_obtained = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    remarks = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['test', 'student']
        ordering = ['student__roll_number']

    def __str__(self):
        return f"{self.student} - {self.test}"

# ============================================
# LIBRARY MANAGEMENT
# ============================================

class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Book Categories"
    
    def __str__(self):
        return self.name


class Book(models.Model):
    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True, blank=True, related_name='books')
    isbn = models.CharField(max_length=13)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    category = models.ForeignKey(BookCategory, on_delete=models.SET_NULL, null=True)
    edition = models.CharField(max_length=50, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    
    total_copies = models.IntegerField()
    available_copies = models.IntegerField()
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rack_number = models.CharField(max_length=50, blank=True)
    
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    
    added_date = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['school', 'isbn']]  # ISBN unique per school
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    def is_available(self):
        return self.available_copies > 0


class BookIssue(models.Model):
    STATUS_CHOICES = [
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issues')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='book_issues')
    
    issue_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fine_paid = models.BooleanField(default=False)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='book_issues')
    returned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='book_returns')
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.book} - {self.student} - {self.status}"
    
    def is_overdue(self):
        if self.status == 'issued' and self.due_date < date.today():
            return True
        return False
    
    def calculate_fine(self, fine_per_day=5):
        """Calculate fine based on overdue days"""
        if self.status == 'issued' and self.due_date < date.today():
            overdue_days = (date.today() - self.due_date).days
            return overdue_days * fine_per_day
        return 0


class BookRequest(models.Model):
    """Book requests from teachers"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('issued', 'Issued'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='book_requests')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='requests')
    
    request_date = models.DateField(auto_now_add=True)
    requested_due_date = models.DateField(help_text="Expected return date")
    purpose = models.TextField(blank=True, help_text="Purpose for borrowing the book")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Approval/Issue details
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_book_requests')
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Issue details (if approved and issued)
    issue_date = models.DateField(null=True, blank=True)
    actual_due_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-request_date']
        verbose_name = "Book Request"
        verbose_name_plural = "Book Requests"
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.book.title} - {self.get_status_display()}"


# ============================================
# PARENT PORTAL
# ============================================

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Using the globally defined phone_regex
    phone = models.CharField(validators=[phone_regex], max_length=17) 
    alternate_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    address = models.TextField()
    students = models.ManyToManyField(Student, related_name='parents')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Parent"


# ============================================
# COMMUNICATIONS
# ============================================

class Notice(models.Model):
    AUDIENCE_CHOICES = [
        ('all', 'Everyone'),
        ('students', 'Students Only'),
        ('teachers', 'Teachers Only'),
        ('parents', 'Parents Only'),
        ('class', 'Specific Class'),
        ('section', 'Specific Section'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    notice_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    
    target_audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    specific_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True)
    specific_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
    
    attachment = models.FileField(upload_to='notices/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-notice_date']
        verbose_name_plural = "Notices"
    
    def __str__(self):
        return self.title


class Announcement(models.Model):
    """Quick announcements/circulars"""
    title = models.CharField(max_length=200)
    message = models.TextField()
    announcement_date = models.DateTimeField(auto_now_add=True)
    is_urgent = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-announcement_date']
    
    def __str__(self):
        return self.title


# ============================================
# EVENT MANAGEMENT
# ============================================

class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('academic', 'Academic'),
        ('sports', 'Sports'),
        ('cultural', 'Cultural'),
        ('holiday', 'Holiday'),
        ('parent_meeting', 'Parent Meeting'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='other')
    
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=200)
    
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    participants = models.ManyToManyField(Student, blank=True, related_name='events')
    
    # improved publishing options
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    
    AUDIENCE_CHOICES = [
        ('all', 'All Users'),
        ('students', 'Students Only'),
        ('parents', 'Parents Only'),
        ('teachers', 'Teachers Only'),
        ('staff', 'Staff Only'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    target_audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    
    is_holiday = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-event_date']
    
    def __str__(self):
        return f"{self.title} - {self.event_date}"


# ============================================
# TRANSPORT MANAGEMENT
# ============================================

class TransportRoute(models.Model):
    route_name = models.CharField(max_length=100, unique=True)
    route_number = models.CharField(max_length=20, unique=True)
    starting_point = models.CharField(max_length=200)
    ending_point = models.CharField(max_length=200)
    total_distance = models.DecimalField(max_digits=6, decimal_places=2, help_text="Distance in KM")
    estimated_time = models.IntegerField(help_text="Time in minutes")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.route_number} - {self.route_name}"


class Bus(models.Model):
    bus_number = models.CharField(max_length=50, unique=True)
    registration_number = models.CharField(max_length=50, unique=True)
    route = models.ForeignKey(TransportRoute, on_delete=models.SET_NULL, null=True, related_name='buses')
    
    capacity = models.IntegerField()
    driver_name = models.CharField(max_length=100)
    driver_phone = models.CharField(validators=[phone_regex], max_length=17)
    conductor_name = models.CharField(max_length=100, blank=True)
    conductor_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Buses"
    
    def __str__(self):
        return f"{self.bus_number} - {self.registration_number}"


class StudentTransport(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='transport')
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, related_name='students')
    pickup_point = models.CharField(max_length=200)
    drop_point = models.CharField(max_length=200)
    
    pickup_time = models.TimeField()
    drop_time = models.TimeField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student} - {self.bus}"


# ============================================
# HOMEWORK/ASSIGNMENT MANAGEMENT
# ============================================

class Homework(models.Model):
    """Homework/Assignment management system"""
    HOMEWORK_TYPE_CHOICES = [
        ('homework', 'Homework'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
        ('research', 'Research Work'),
        ('practical', 'Practical Work'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    homework_type = models.CharField(max_length=20, choices=HOMEWORK_TYPE_CHOICES, default='homework')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    assigned_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    
    # Dates
    assigned_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    late_submission_allowed = models.BooleanField(default=True)
    late_submission_penalty = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Grading
    max_marks = models.IntegerField(default=10)
    instructions = models.TextField(blank=True)
    attachment = models.FileField(upload_to='homework_attachments/', blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-assigned_date']
        verbose_name = "Homework"
        verbose_name_plural = "Homeworks"
    
    def __str__(self):
        return f"{self.title} - {self.class_assigned} - {self.subject}"
    
    def get_submission_count(self):
        return self.submissions.count()
    
    def get_pending_submissions(self):
        return self.submissions.filter(submission_date__isnull=True).count()


class HomeworkSubmission(models.Model):
    """Student homework submissions"""
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='homework_submissions')
    
    # Submission details
    submission_date = models.DateTimeField(null=True, blank=True)
    attachment = models.FileField(upload_to='homework_submissions/', blank=True, null=True)
    submission_text = models.TextField(blank=True)
    
    # Grading
    marks_obtained = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_submitted = models.BooleanField(default=False)
    is_late = models.BooleanField(default=False)
    is_graded = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['homework', 'student']
        ordering = ['-submission_date']
        verbose_name = "Homework Submission"
        verbose_name_plural = "Homework Submissions"
    
    def __str__(self):
        return f"{self.student} - {self.homework.title}"
    
    def save(self, *args, **kwargs):
        if self.submission_date and self.homework.due_date:
            self.is_late = self.submission_date.date() > self.homework.due_date
        super().save(*args, **kwargs)


# ============================================
# INVENTORY MANAGEMENT
# ============================================

class InventoryCategory(models.Model):
    """Categories for inventory items"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Inventory Category"
        verbose_name_plural = "Inventory Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    """Inventory items/assets management"""
    ITEM_TYPE_CHOICES = [
        ('furniture', 'Furniture'),
        ('equipment', 'Equipment'),
        ('stationery', 'Stationery'),
        ('sports', 'Sports Equipment'),
        ('electronics', 'Electronics'),
        ('books', 'Books'),
        ('uniforms', 'Uniforms'),
        ('other', 'Other'),
    ]
    
    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    ]
    
    item_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(InventoryCategory, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    
    # Quantity and Pricing
    total_quantity = models.IntegerField(default=0)
    available_quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Location and Details
    location = models.CharField(max_length=200)
    room_number = models.CharField(max_length=50, blank=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    
    # Purchase Information
    purchase_date = models.DateField()
    supplier = models.CharField(max_length=200)
    purchase_order_number = models.CharField(max_length=100, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    
    # Additional Details
    brand = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    requires_maintenance = models.BooleanField(default=False)
    last_maintenance_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Inventory Item"
        verbose_name_plural = "Inventory Items"
    
    def __str__(self):
        return f"{self.item_code} - {self.name}"
    
    def save(self, *args, **kwargs):
        self.total_value = self.total_quantity * self.unit_price
        super().save(*args, **kwargs)


class InventoryTransaction(models.Model):
    """Inventory transactions (purchase, issue, return, etc.)"""
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('issue', 'Issue'),
        ('return', 'Return'),
        ('damaged', 'Damaged'),
        ('disposed', 'Disposed'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
    ]
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Transaction Details
    issued_to = models.CharField(max_length=200, blank=True)  # Person/Department
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inventory_issues')
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_receipts')
    
    # Dates
    transaction_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    
    # Additional Information
    reference_number = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    location_from = models.CharField(max_length=200, blank=True)
    location_to = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inventory_created')
    
    class Meta:
        ordering = ['-transaction_date']
        verbose_name = "Inventory Transaction"
        verbose_name_plural = "Inventory Transactions"
    
    def __str__(self):
        return f"{self.item.name} - {self.get_transaction_type_display()} - {self.quantity}"


# ============================================
# LEAVE MANAGEMENT SYSTEM
# ============================================

class LeaveType(models.Model):
    """Types of leave available"""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    max_days_per_year = models.IntegerField(default=30)
    max_days_per_month = models.IntegerField(null=True, blank=True)
    requires_approval = models.BooleanField(default=True)
    is_paid = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Leave Type"
        verbose_name_plural = "Leave Types"
    
    def __str__(self):
        return self.display_name


class LeaveApplication(models.Model):
    """Leave applications from teachers and staff"""
    APPLICANT_TYPE_CHOICES = [
        ('teacher', 'Teacher'),
        ('staff', 'Staff'),
        ('student', 'Student'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Applicant Information
    applicant_type = models.CharField(max_length=20, choices=APPLICANT_TYPE_CHOICES)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    staff_member = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Leave Details
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    total_days = models.IntegerField()
    reason = models.TextField()
    emergency_contact = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=17, blank=True)
    
    # Status and Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Additional Information
    attachment = models.FileField(upload_to='leave_attachments/', blank=True, null=True)
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-applied_date']
        verbose_name = "Leave Application"
        verbose_name_plural = "Leave Applications"
    
    def __str__(self):
        applicant_name = self.get_applicant_name()
        return f"{applicant_name} - {self.leave_type.display_name} - {self.from_date} to {self.to_date}"
    
    def get_applicant_name(self):
        if self.teacher:
            return self.teacher.user.get_full_name()
        elif self.student:
            return self.student.get_full_name()
        elif self.staff_member:
            return self.staff_member.get_full_name()
        return "Unknown"
    
    def save(self, *args, **kwargs):
        if self.from_date and self.to_date:
            self.total_days = (self.to_date - self.from_date).days + 1
        super().save(*args, **kwargs)


# ============================================
# STAFF/EMPLOYEE MANAGEMENT
# ============================================

class StaffCategory(models.Model):
    """Categories for non-teaching staff"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Staff Category"
        verbose_name_plural = "Staff Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Staff(models.Model):
    """Non-Teaching Staff - Administrative, Support, and other non-teaching roles"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    QUALIFICATION_CHOICES = [
        ('bachelor', 'Bachelor Degree'),
        ('master', 'Master Degree'),
        ('phd', 'PhD'),
        ('b_ed', 'B.Ed'),
        ('m_ed', 'M.Ed'),
        ('diploma', 'Diploma'),
        ('certificate', 'Certificate'),
    ]
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True, blank=True, related_name='staff_members', help_text="School this staff member belongs to")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20)
    category = models.ForeignKey(StaffCategory, on_delete=models.CASCADE, help_text="Non-teaching staff category")
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    
    # Personal Information
    phone = models.CharField(validators=[phone_regex], max_length=17)
    alternate_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    
    # Employment Details
    joining_date = models.DateField()
    current_salary = models.DecimalField(max_digits=10, decimal_places=2)
    previous_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    qualification = models.CharField(max_length=20, choices=QUALIFICATION_CHOICES, default='bachelor')
    education_level = models.CharField(max_length=100, default='Bachelor Degree', help_text="Specific degree details")
    experience_years = models.IntegerField(default=0)
    
    # Banking Details
    bank_account = models.CharField(max_length=20, blank=True)
    ifsc_code = models.CharField(max_length=15, blank=True)
    pan_number = models.CharField(max_length=10, blank=True)
    aadhar_number = models.CharField(max_length=12, blank=True)
    pf_number = models.CharField(max_length=20, blank=True)
    
    # Note: Teaching assignments removed - use Teacher model for teaching staff
    # Role Flags
    is_librarian = models.BooleanField(default=False, help_text="Is this staff member a librarian? (Non-teaching role)")
    
    # Additional Information
    photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    emergency_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    class Meta:
        ordering = ['user__first_name', 'user__last_name']
        unique_together = [['school', 'employee_id']]  # Employee ID unique per school
        verbose_name = 'Non-Teaching Staff'
        verbose_name_plural = 'Non-Teaching Staff'
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.employee_id}) - {self.designation}"
    
    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"


# ============================================
# SALARY MANAGEMENT
# ============================================

class SalaryComponent(models.Model):
    """Salary components like basic, allowances, deductions"""
    COMPONENT_TYPE_CHOICES = [
        ('earning', 'Earning'),
        ('deduction', 'Deduction'),
    ]
    
    CALCULATION_TYPE_CHOICES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage of Basic'),
    ]
    
    name = models.CharField(max_length=100)
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPE_CHOICES)
    calculation_type = models.CharField(max_length=20, choices=CALCULATION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_component_type_display()})"

class Salary(models.Model):
    """Monthly salary records for staff"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='salaries')
    month = models.IntegerField(choices=[(i, i) for i in range(1, 13)])
    year = models.IntegerField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['employee', 'month', 'year']
        ordering = ['-year', '-month', 'employee__user__first_name']
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.month}/{self.year}"

# ============================================
# CERTIFICATE GENERATION
# ============================================

class CertificateTemplate(models.Model):
    """Templates for various certificates"""
    CERTIFICATE_TYPE_CHOICES = [
        ('transfer_certificate', 'Transfer Certificate'),
        ('bonafide', 'Bonafide Certificate'),
        ('character', 'Character Certificate'),
        ('migration', 'Migration Certificate'),
        ('achievement', 'Achievement Certificate'),
        ('participation', 'Participation Certificate'),
        ('custom', 'Custom Certificate'),
    ]
    
    name = models.CharField(max_length=100)
    certificate_type = models.CharField(max_length=30, choices=CERTIFICATE_TYPE_CHOICES)
    template_file = models.FileField(upload_to='certificate_templates/')
    description = models.TextField(blank=True)
    
    # Template Settings
    width = models.IntegerField(default=800)
    height = models.IntegerField(default=600)
    background_color = models.CharField(max_length=7, default='#FFFFFF')
    
    # Field Positions (for dynamic text placement)
    student_name_x = models.IntegerField(default=400)
    student_name_y = models.IntegerField(default=200)
    student_name_font_size = models.IntegerField(default=24)
    valid_until = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True)
    
    # Generated File
    generated_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    
    # Approval
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_certificate_templates')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_certificate_templates')
    status = models.CharField(max_length=20, default='issued')
    
    # Additional Information
    remarks = models.TextField(blank=True)
    is_downloaded = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Certificate Template"
        verbose_name_plural = "Certificate Templates"
    
    def __str__(self):
        return f"{self.name} ({self.get_certificate_type_display()})"


class Certificate(models.Model):
    """Generated certificates for students"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('cancelled', 'Cancelled'),
    ]
    
    certificate_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certificates')
    template = models.ForeignKey(CertificateTemplate, on_delete=models.CASCADE, related_name='certificates')
    issue_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_certificates')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date', 'student__first_name']
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"
    
    def __str__(self):
        return f"{self.certificate_number} - {self.student.get_full_name()}"


# ============================================
# HEALTH & MEDICAL RECORDS
# ============================================


class HealthCheckup(models.Model):
    """Health checkup records for students"""
    OVERALL_HEALTH_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='health_checkups')
    checkup_date = models.DateField()
    
    # Physical Measurements
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in cm
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in kg
    bmi = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    # Health Assessment
    overall_health = models.CharField(max_length=20, choices=OVERALL_HEALTH_CHOICES)
    vision_status = models.CharField(max_length=50, blank=True)
    hearing_status = models.CharField(max_length=50, blank=True)
    dental_status = models.CharField(max_length=50, blank=True)
    
    # Medical Information
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    
    # Doctor Information
    doctor_name = models.CharField(max_length=100)
    doctor_contact = models.CharField(max_length=20, blank=True)
    clinic_name = models.CharField(max_length=100, blank=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    recommendations = models.TextField(blank=True)
    
    # Additional Notes
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-checkup_date', 'student__first_name']
        verbose_name = "Health Checkup"
        verbose_name_plural = "Health Checkups"
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.checkup_date}"
    
    def save(self, *args, **kwargs):
        # Calculate BMI
        if self.height and self.weight and self.height > 0:
            height_m = self.height / 100
            self.bmi = self.weight / (height_m ** 2)
        super().save(*args, **kwargs)


class MedicalRecord(models.Model):
    """Medical records and treatments"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='medical_records')
    record_date = models.DateField()
    
    # Medical Information
    complaint = models.TextField()
    diagnosis = models.TextField()
    treatment = models.TextField()
    prescription = models.TextField(blank=True)
    
    # Doctor Information
    doctor_name = models.CharField(max_length=100)
    doctor_qualification = models.CharField(max_length=100, blank=True)
    clinic_hospital = models.CharField(max_length=200, blank=True)
    doctor_phone = models.CharField(max_length=17, blank=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    
    # Medication
    medication_prescribed = models.TextField(blank=True)
    dosage = models.CharField(max_length=100, blank=True)
    duration = models.CharField(max_length=100, blank=True)
    
    # Additional Information
    attachment = models.FileField(upload_to='medical_records/', blank=True, null=True)
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-record_date']
        verbose_name = "Medical Record"
        verbose_name_plural = "Medical Records"
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.record_date} - {self.diagnosis[:50]}"


# ============================================
# HOSTEL MANAGEMENT
# ============================================

class Hostel(models.Model):
    """Hostel information and management"""
    HOSTEL_TYPE_CHOICES = [
        ('boys', 'Boys Hostel'),
        ('girls', 'Girls Hostel'),
        ('mixed', 'Mixed Hostel'),
    ]
    
    name = models.CharField(max_length=100)
    hostel_type = models.CharField(max_length=10, choices=HOSTEL_TYPE_CHOICES)
    address = models.TextField()
    total_rooms = models.IntegerField()
    total_capacity = models.IntegerField()
    
    # Management
    warden_name = models.CharField(max_length=100)
    warden_phone = models.CharField(validators=[phone_regex], max_length=17)
    warden_email = models.EmailField(blank=True)
    assistant_warden = models.CharField(max_length=100, blank=True)
    assistant_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Facilities
    facilities = models.TextField(blank=True)
    rules_regulations = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Hostel"
        verbose_name_plural = "Hostels"
    
    def __str__(self):
        return f"{self.name} ({self.get_hostel_type_display()})"


class HostelRoom(models.Model):
    """Individual rooms in hostels"""
    ROOM_TYPE_CHOICES = [
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
        ('dormitory', 'Dormitory'),
    ]
    
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    floor = models.IntegerField()
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    capacity = models.IntegerField()
    current_occupancy = models.IntegerField(default=0)
    
    # Pricing
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Facilities
    amenities = models.TextField(blank=True)
    has_ac = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=False)
    has_attached_bathroom = models.BooleanField(default=False)
    
    # Status
    is_available = models.BooleanField(default=True)
    is_under_maintenance = models.BooleanField(default=False)
    maintenance_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['hostel', 'room_number']
        ordering = ['hostel', 'floor', 'room_number']
        verbose_name = "Hostel Room"
        verbose_name_plural = "Hostel Rooms"
    
    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_number}"
    
    def get_availability_status(self):
        if self.is_under_maintenance:
            return "Under Maintenance"
        elif self.current_occupancy >= self.capacity:
            return "Full"
        elif self.is_available:
            return "Available"
        else:
            return "Not Available"


class HostelAllocation(models.Model):
    """Student hostel room allocations"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='hostel_allocation')
    room = models.ForeignKey(HostelRoom, on_delete=models.CASCADE, related_name='allocations')
    
    # Allocation Details
    allocation_date = models.DateField()
    checkout_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Fees
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit_paid = models.BooleanField(default=False)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17)
    emergency_contact_relation = models.CharField(max_length=50)
    
    # Additional Information
    special_requirements = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    dietary_restrictions = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('checked_out', 'Checked Out'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ], default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-allocation_date']
        verbose_name = "Hostel Allocation"
        verbose_name_plural = "Hostel Allocations"
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.room}"


# ============================================
# CANTEEN MANAGEMENT
# ============================================

class CanteenItem(models.Model):
    """Canteen menu items"""
    CATEGORY_CHOICES = [
        ('snacks', 'Snacks'),
        ('meals', 'Meals'),
        ('beverages', 'Beverages'),
        ('desserts', 'Desserts'),
        ('healthy', 'Healthy Options'),
    ]
    
    item_name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Nutritional Information
    calories = models.IntegerField(null=True, blank=True)
    is_vegetarian = models.BooleanField(default=True)
    is_healthy = models.BooleanField(default=False)
    allergens = models.TextField(blank=True)
    
    # Availability
    is_available = models.BooleanField(default=True)
    preparation_time = models.IntegerField(default=10, help_text="Preparation time in minutes")
    
    # Images
    image = models.ImageField(upload_to='canteen_items/', blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'item_name']
        verbose_name = "Canteen Item"
        verbose_name_plural = "Canteen Items"
    
    def __str__(self):
        return f"{self.item_name} - ₹{self.price}"


class CanteenOrder(models.Model):
    """Canteen orders from students"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='canteen_orders')
    
    # Order Details
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_time = models.DateTimeField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Payment
    payment_method = models.CharField(max_length=20, choices=[
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('wallet', 'Wallet'),
    ], blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # Additional Information
    special_instructions = models.TextField(blank=True)
    delivery_location = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order_date']
        verbose_name = "Canteen Order"
        verbose_name_plural = "Canteen Orders"
    
    def __str__(self):
        return f"Order {self.order_number} - {self.student.get_full_name()}"


class OrderItem(models.Model):
    """Individual items in canteen orders"""
    order = models.ForeignKey(CanteenOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(CanteenItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Special Instructions
    special_instructions = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
    
    def __str__(self):
        return f"{self.item.item_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ============================================
# ALUMNI MANAGEMENT
# ============================================

class Alumni(models.Model):
    """Alumni information and management"""
    OCCUPATION_CHOICES = [
        ('student', 'Student'),
        ('employed', 'Employed'),
        ('self_employed', 'Self Employed'),
        ('unemployed', 'Unemployed'),
        ('retired', 'Retired'),
    ]
    
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='alumni_profile')
    graduation_year = models.IntegerField()
    graduation_class = models.CharField(max_length=50)
    
    # Current Information
    current_occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES)
    job_title = models.CharField(max_length=200, blank=True)
    company_organization = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    current_address = models.TextField()
    current_city = models.CharField(max_length=100)
    current_state = models.CharField(max_length=100)
    current_country = models.CharField(max_length=100, default='India')
    current_pincode = models.CharField(max_length=10)
    email = models.EmailField()
    phone = models.CharField(validators=[phone_regex], max_length=17)
    alternate_email = models.EmailField(blank=True)
    alternate_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Social Media
    linkedin_profile = models.URLField(blank=True)
    facebook_profile = models.URLField(blank=True)
    twitter_profile = models.URLField(blank=True)
    instagram_profile = models.URLField(blank=True)
    
    # Alumni Activities
    is_willing_to_mentor = models.BooleanField(default=False)
    is_willing_to_volunteer = models.BooleanField(default=False)
    is_willing_to_donate = models.BooleanField(default=False)
    areas_of_expertise = models.TextField(blank=True)
    
    # Achievements
    achievements = models.TextField(blank=True)
    awards_honors = models.TextField(blank=True)
    publications = models.TextField(blank=True)
    
    # Additional Information
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='alumni_photos/', blank=True, null=True)
    is_public_profile = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-graduation_year', 'student__first_name']
        verbose_name = "Alumni"
        verbose_name_plural = "Alumni"
    
    def __str__(self):
        return f"{self.student.get_full_name()} ({self.graduation_year})"


# ============================================
# ONLINE EXAMINATION SYSTEM
# ============================================

class OnlineExam(models.Model):
    """Online examinations"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    
    # Exam Settings
    total_marks = models.IntegerField()
    passing_marks = models.IntegerField()
    duration_minutes = models.IntegerField(help_text="Exam duration in minutes")
    
    # Timing
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    late_submission_allowed = models.BooleanField(default=False)
    late_submission_penalty = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Security Settings
    shuffle_questions = models.BooleanField(default=True)
    shuffle_options = models.BooleanField(default=True)
    allow_review = models.BooleanField(default=True)
    show_correct_answers = models.BooleanField(default=False)
    show_answers_after = models.DateTimeField(null=True, blank=True)
    
    # Instructions
    instructions = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = "Online Exam"
        verbose_name_plural = "Online Exams"
    
    def __str__(self):
        return f"{self.title} - {self.class_assigned} - {self.subject}"


class OnlineExamQuestion(models.Model):
    """Questions for online exams"""
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    ]
    
    exam = models.ForeignKey(OnlineExam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    marks = models.IntegerField(default=1)
    order = models.IntegerField(default=0)
    
    # For multiple choice questions
    option_a = models.TextField(blank=True)
    option_b = models.TextField(blank=True)
    option_c = models.TextField(blank=True)
    option_d = models.TextField(blank=True)
    correct_answer = models.CharField(max_length=10, blank=True)  # A, B, C, D, etc.
    
    # For other question types
    correct_answer_text = models.TextField(blank=True)
    sample_answer = models.TextField(blank=True)
    
    # Additional Information
    explanation = models.TextField(blank=True)
    difficulty_level = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ], default='medium')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Exam Question"
        verbose_name_plural = "Exam Questions"
    
    def __str__(self):
        return f"{self.exam.title} - Q{self.order}"


class OnlineExamAttempt(models.Model):
    """Student attempts for online exams"""
    exam = models.ForeignKey(OnlineExam, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_attempts')
    
    # Attempt Details
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    total_marks = models.IntegerField(default=0)
    obtained_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_passed = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('auto_submitted', 'Auto Submitted'),
        ('graded', 'Graded'),
    ], default='in_progress')
    
    # Additional Information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    warnings_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['exam', 'student']
        ordering = ['-start_time']
        verbose_name = "Exam Attempt"
        verbose_name_plural = "Exam Attempts"
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.exam.title}"


class OnlineExamAnswer(models.Model):
    """Student answers for exam questions"""
    attempt = models.ForeignKey(OnlineExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(OnlineExamQuestion, on_delete=models.CASCADE)
    
    # Answer Details
    answer_text = models.TextField(blank=True)
    selected_option = models.CharField(max_length=10, blank=True)  # A, B, C, D, etc.
    
    # Grading
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_correct = models.BooleanField(default=False)
    is_graded = models.BooleanField(default=False)
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    # Timing
    time_spent = models.IntegerField(default=0, help_text="Time spent in seconds")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['attempt', 'question']
        verbose_name = "Exam Answer"
        verbose_name_plural = "Exam Answers"
    
    def __str__(self):
        return f"{self.attempt.student.get_full_name()} - {self.question.question_text[:50]}"


# ============================================
# SPORTS CLUB MANAGEMENT
# ============================================

class SportsCategory(models.Model):
    """Categories of sports activities"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For UI icons
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Sports Category"
        verbose_name_plural = "Sports Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Sport(models.Model):
    """Individual sports activities"""
    DIFFICULTY_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('professional', 'Professional'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.ForeignKey(SportsCategory, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVEL_CHOICES, default='beginner')
    
    # Requirements
    min_age = models.IntegerField(default=6)
    max_age = models.IntegerField(default=18)
    equipment_required = models.TextField(blank=True)
    venue_required = models.CharField(max_length=200, blank=True)
    
    # Coaching
    coach_name = models.CharField(max_length=100, blank=True)
    coach_qualification = models.CharField(max_length=200, blank=True)
    coach_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Schedule
    practice_days = models.CharField(max_length=100, blank=True)  # e.g., "Mon,Wed,Fri"
    practice_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=60)
    
    # Fees and Requirements
    monthly_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    equipment_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    uniform_required = models.BooleanField(default=False)
    medical_certificate_required = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    max_participants = models.IntegerField(default=30)
    current_participants = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = "Sport"
        verbose_name_plural = "Sports"
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"


class SportsRegistration(models.Model):
    """Student registrations for sports"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sports_registrations')
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='registrations')
    
    # Registration Details
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Medical Information
    medical_certificate = models.FileField(upload_to='sports_medical/', blank=True, null=True)
    medical_validity = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    emergency_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Additional Information
    previous_experience = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)
    parent_consent = models.BooleanField(default=False)
    parent_signature = models.CharField(max_length=200, blank=True)
    
    # Payment
    fee_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'sport']
        ordering = ['-registration_date']
        verbose_name = "Sports Registration"
        verbose_name_plural = "Sports Registrations"
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.sport.name}"


class SportsAchievement(models.Model):
    """Student achievements in sports"""
    ACHIEVEMENT_TYPE_CHOICES = [
        ('medal', 'Medal'),
        ('trophy', 'Trophy'),
        ('certificate', 'Certificate'),
        ('badge', 'Badge'),
        ('recognition', 'Recognition'),
    ]
    
    LEVEL_CHOICES = [
        ('school', 'School Level'),
        ('district', 'District Level'),
        ('state', 'State Level'),
        ('national', 'National Level'),
        ('international', 'International Level'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sports_achievements')
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='achievements')
    
    # Achievement Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPE_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    position = models.CharField(max_length=50)  # e.g., "1st Place", "Gold Medal"
    
    # Event Information
    event_name = models.CharField(max_length=200)
    event_date = models.DateField()
    venue = models.CharField(max_length=200, blank=True)
    organizer = models.CharField(max_length=200, blank=True)
    
    # Recognition
    points_awarded = models.IntegerField(default=0)
    certificate = models.FileField(upload_to='sports_certificates/', blank=True, null=True)
    photo = models.ImageField(upload_to='sports_photos/', blank=True, null=True)
    
    # Verification
    verified_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    verified_date = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-event_date']
        verbose_name = "Sports Achievement"
        verbose_name_plural = "Sports Achievements"
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.title}"


# ============================================
# CO-CURRICULAR ACTIVITIES
# ============================================

class ActivityCategory(models.Model):
    """Categories of co-curricular activities"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#6366f1')  # Hex color code
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Activity Category"
        verbose_name_plural = "Activity Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CoCurricularActivity(models.Model):
    """Co-curricular activities like music, dance, drama, etc."""
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ActivityCategory, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    
    # Requirements
    min_age = models.IntegerField(default=6)
    max_age = models.IntegerField(default=18)
    equipment_required = models.TextField(blank=True)
    venue_required = models.CharField(max_length=200, blank=True)
    
    # Instructor
    instructor_name = models.CharField(max_length=100, blank=True)
    instructor_qualification = models.CharField(max_length=200, blank=True)
    instructor_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Schedule
    practice_days = models.CharField(max_length=100, blank=True)
    practice_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=60)
    
    # Fees
    monthly_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    equipment_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    max_participants = models.IntegerField(default=25)
    current_participants = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = "Co-curricular Activity"
        verbose_name_plural = "Co-curricular Activities"
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"


class ActivityRegistration(models.Model):
    """Student registrations for co-curricular activities"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='activity_registrations')
    activity = models.ForeignKey(CoCurricularActivity, on_delete=models.CASCADE, related_name='registrations')
    
    # Registration Details
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Additional Information
    previous_experience = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)
    parent_consent = models.BooleanField(default=False)
    
    # Payment
    fee_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'activity']
        ordering = ['-registration_date']
        verbose_name = "Activity Registration"
        verbose_name_plural = "Activity Registrations"
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.activity.name}"


# ============================================
# HOUSE SYSTEM
# ============================================

class House(models.Model):
    """School houses (Green, Red, Blue, Yellow, etc.)"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7)  # Hex color code
    motto = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # House Management
    house_master = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='house_master')
    vice_house_master = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='vice_house_master')
    
    # House Statistics
    total_students = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "House"
        verbose_name_plural = "Houses"
    
    def __str__(self):
        return f"{self.name} House"


class HouseMembership(models.Model):
    """Student house memberships"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='house_membership')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='members')
    
    # Membership Details
    joined_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Student's Contribution
    points_earned = models.IntegerField(default=0)
    achievements_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['house', 'student__first_name']
        verbose_name = "House Membership"
        verbose_name_plural = "House Memberships"
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.house.name} House"


class HouseEvent(models.Model):
    """House events and competitions"""
    EVENT_TYPE_CHOICES = [
        ('sports', 'Sports'),
        ('academic', 'Academic'),
        ('cultural', 'Cultural'),
        ('debate', 'Debate'),
        ('quiz', 'Quiz'),
        ('drama', 'Drama'),
        ('music', 'Music'),
        ('dance', 'Dance'),
        ('art', 'Art'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    
    # Event Details
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=200)
    
    # Points and Prizes
    first_place_points = models.IntegerField(default=10)
    second_place_points = models.IntegerField(default=7)
    third_place_points = models.IntegerField(default=5)
    participation_points = models.IntegerField(default=2)
    
    # Management
    organized_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    judges = models.ManyToManyField(Teacher, related_name='judged_events', blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-event_date']
        verbose_name = "House Event"
        verbose_name_plural = "House Events"
    
    def __str__(self):
        return f"{self.name} - {self.event_date}"


class HouseEventResult(models.Model):
    """Results of house events"""
    event = models.ForeignKey(HouseEvent, on_delete=models.CASCADE, related_name='results')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='event_results')
    
    # Result Details
    position = models.IntegerField()  # 1, 2, 3, etc.
    points_earned = models.IntegerField()
    participants = models.ManyToManyField(Student, related_name='event_participations')
    
    # Additional Information
    remarks = models.TextField(blank=True)
    certificate_issued = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['event', 'house']
        ordering = ['position']
        verbose_name = "House Event Result"
        verbose_name_plural = "House Event Results"
    
    def __str__(self):
        return f"{self.event.name} - {self.house.name} House - Position {self.position}"


# ============================================
# STUDENT LEADERSHIP POSITIONS
# ============================================

class LeadershipPosition(models.Model):
    """Student leadership positions"""
    POSITION_TYPE_CHOICES = [
        ('school_captain', 'School Captain'),
        ('vice_captain', 'Vice Captain'),
        ('sports_captain', 'Sports Captain'),
        ('cultural_captain', 'Cultural Captain'),
        ('house_captain', 'House Captain'),
        ('vice_house_captain', 'Vice House Captain'),
        ('class_monitor', 'Class Monitor'),
        ('vice_monitor', 'Vice Monitor'),
        ('prefect', 'Prefect'),
        ('librarian', 'Student Librarian'),
        ('environmental_monitor', 'Environmental Monitor'),
        ('discipline_monitor', 'Discipline Monitor'),
    ]
    
    name = models.CharField(max_length=100)
    position_type = models.CharField(max_length=30, choices=POSITION_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    # Requirements
    min_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='min_leadership_positions')
    max_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='max_leadership_positions')
    min_age = models.IntegerField(default=12)
    min_academic_performance = models.DecimalField(max_digits=5, decimal_places=2, default=70.00)
    
    # Responsibilities
    responsibilities = models.TextField(blank=True)
    privileges = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_elected = models.BooleanField(default=False)  # True for elected positions
    term_duration_months = models.IntegerField(default=12)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position_type', 'name']
        verbose_name = "Leadership Position"
        verbose_name_plural = "Leadership Positions"
    
    def __str__(self):
        return f"{self.name} ({self.get_position_type_display()})"


class StudentLeadership(models.Model):
    """Student leadership appointments"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('resigned', 'Resigned'),
        ('removed', 'Removed'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='leadership_positions')
    position = models.ForeignKey(LeadershipPosition, on_delete=models.CASCADE, related_name='appointments')
    house = models.ForeignKey(House, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Appointment Details
    appointment_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Appointment Process
    appointed_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    appointment_reason = models.TextField(blank=True)
    resignation_reason = models.TextField(blank=True)
    
    # Performance
    performance_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    achievements = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-appointment_date']
        verbose_name = "Student Leadership"
        verbose_name_plural = "Student Leadership"
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.position.name}"


# ============================================
# STUDENT ELECTIONS
# ============================================

class Election(models.Model):
    """Student elections for leadership positions"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('announced', 'Announced'),
        ('nomination_open', 'Nomination Open'),
        ('nomination_closed', 'Nomination Closed'),
        ('voting_open', 'Voting Open'),
        ('voting_closed', 'Voting Closed'),
        ('results_published', 'Results Published'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    position = models.ForeignKey(LeadershipPosition, on_delete=models.CASCADE, related_name='elections')
    house = models.ForeignKey(House, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Election Timeline
    nomination_start_date = models.DateTimeField()
    nomination_end_date = models.DateTimeField()
    voting_start_date = models.DateTimeField()
    voting_end_date = models.DateTimeField()
    results_announcement_date = models.DateTimeField()
    
    # Eligibility
    eligible_classes = models.ManyToManyField(Class, related_name='elections')
    min_academic_performance = models.DecimalField(max_digits=5, decimal_places=2, default=70.00)
    min_attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=80.00)
    
    # Election Rules
    max_candidates = models.IntegerField(default=5)
    voting_method = models.CharField(max_length=20, choices=[
        ('first_past_post', 'First Past the Post'),
        ('preferential', 'Preferential Voting'),
        ('approval', 'Approval Voting'),
    ], default='first_past_post')
    
    # Management
    conducted_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    election_committee = models.ManyToManyField(Teacher, related_name='election_committees', blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Election"
        verbose_name_plural = "Elections"
    
    def __str__(self):
        return f"{self.title} - {self.position.name}"


class ElectionNomination(models.Model):
    """Student nominations for elections"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='nominations')
    candidate = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='election_nominations')
    nominator = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='nominations_made')
    
    # Nomination Details
    nomination_date = models.DateTimeField(auto_now_add=True)
    manifesto = models.TextField(blank=True)
    qualifications = models.TextField(blank=True)
    goals = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Campaign
    campaign_photo = models.ImageField(upload_to='election_campaigns/', blank=True, null=True)
    campaign_video = models.FileField(upload_to='election_videos/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['election', 'candidate']
        ordering = ['-nomination_date']
        verbose_name = "Election Nomination"
        verbose_name_plural = "Election Nominations"
    
    def __str__(self):
        return f"{self.candidate.get_full_name()} - {self.election.title}"


class ElectionVote(models.Model):
    """Student votes in elections"""
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='votes_cast')
    candidate = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='votes_received')
    
    # Vote Details
    vote_date = models.DateTimeField(auto_now_add=True)
    preference_order = models.IntegerField(default=1)  # For preferential voting
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        unique_together = ['election', 'voter', 'candidate']
        ordering = ['-vote_date']
        verbose_name = "Election Vote"
        verbose_name_plural = "Election Votes"
    
    def __str__(self):
        return f"{self.voter.get_full_name()} voted for {self.candidate.get_full_name()}"


class ElectionResult(models.Model):
    """Election results"""
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='results')
    candidate = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='election_results')
    
    # Result Details
    total_votes = models.IntegerField(default=0)
    position = models.IntegerField(null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_winner = models.BooleanField(default=False)
    
    # Announcement
    announced_date = models.DateTimeField(null=True, blank=True)
    announced_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['election', 'candidate']
        ordering = ['-total_votes']
        verbose_name = "Election Result"
        verbose_name_plural = "Election Results"
    
    def __str__(self):
        return f"{self.candidate.get_full_name()} - {self.election.title} - {self.total_votes} votes"


# ============================================
# TEACHER PORTAL - QUESTION PAPERS
# ============================================

class QuestionPaper(models.Model):
    """Teacher-authored question paper for class tests/exams."""
    QUESTION_TYPE_CHOICES = [
        ('mcq', 'Multiple Choice Question (MCQ)'),
        ('fill_blank', 'Fill in the Blanks'),
        ('match_columns', 'Match the Columns'),
        ('one_word', 'One Word Answer'),
        ('single_line', 'Single Line Answer'),
        ('multiple_line', 'Multiple Line Answer'),
        ('true_false', 'True/False'),
        ('numerical', 'Numerical Problem'),
    ]
    
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    instructions = models.TextField(blank=True)
    questions = models.TextField(help_text="Store as plain text or lightweight markup", blank=True)
    structured_questions = models.JSONField(default=list, blank=True, help_text="Structured questions with types and templates")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.class_assigned} - {self.subject}"


# User Roles and Permissions
class UserRole(models.Model):
    """Different user roles in the system"""
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('school_admin', 'School Admin'),
        ('teacher', 'Teacher'),
        ('librarian', 'Librarian'),
        ('accountant', 'Accountant'),
        ('parent', 'Parent'),
        ('student', 'Student'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, help_text="List of permission codes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
    
    def __str__(self):
        return self.display_name


class SchoolUser(models.Model):
    """Extended user model for school-specific users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='school_profile')
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True, blank=True)
    
    # User-specific data
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='user_profiles/', blank=True, null=True)
    
    # Login credentials for different user types
    login_id = models.CharField(max_length=100, help_text="Admission ID for parents, Mobile for teachers")
    custom_password = models.CharField(max_length=100, blank=True, help_text="Custom password for non-Django auth")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "School User"
        verbose_name_plural = "School Users"
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role.display_name})"


class School(models.Model):
    """School information for multi-tenant system"""
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    
    # School details
    principal_name = models.CharField(max_length=100, blank=True)
    established_year = models.IntegerField(blank=True, null=True)
    affiliation_number = models.CharField(max_length=50, blank=True)
    board = models.CharField(max_length=100, default="CBSE")
    
    # Subscription details
    subscription_active = models.BooleanField(default=True)
    subscription_expires = models.DateField(null=True, blank=True)
    max_users = models.IntegerField(default=100)
    
    # Settings
    settings = models.JSONField(default=dict, help_text="School-specific settings")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"
    
    def __str__(self):
        return self.name


class SchoolBilling(models.Model):
    """Billing information for schools"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    BILLING_TYPE_CHOICES = [
        ('fixed', 'Fixed Amount'),
        ('per_student', 'Per Student'),
    ]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='billing')
    billing_period = models.CharField(max_length=50, help_text="e.g., Jan 2024")
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES, default='per_student', help_text="Fixed amount or per student")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    rate_per_student = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Rate per student (e.g., ₹5, ₹10)")
    student_count = models.IntegerField(null=True, blank=True, help_text="Number of active students at billing time")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "School Billing"
        verbose_name_plural = "School Billing"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.school.name} - {self.billing_period} - {self.payment_status}"


# School Settings Model
class SchoolSettings(models.Model):
    """School configuration settings including logo and basic info"""
    school_name = models.CharField(max_length=200, default="Gyanodaya School")
    school_address = models.TextField(default="123 Education Street, Learning City")
    school_phone = models.CharField(max_length=20, default="+91-1234567890")
    school_email = models.EmailField(default="info@gyanodaya.edu")
    school_website = models.URLField(blank=True, null=True)
    school_logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    principal_name = models.CharField(max_length=100, blank=True, null=True)
    established_year = models.IntegerField(blank=True, null=True)
    affiliation_number = models.CharField(max_length=50, blank=True, null=True)
    board = models.CharField(max_length=100, default="CBSE")
    
    # Receipt settings
    receipt_footer_text = models.TextField(
        default="This is a computer generated receipt and does not require signature.\nFor any queries, please contact the school office.",
        help_text="Text to display at the bottom of receipts"
    )
    
    # Twilio/WhatsApp Configuration (School's Account)
    twilio_account_sid = models.CharField(max_length=100, blank=True, help_text="Twilio Account SID from https://www.twilio.com/console")
    twilio_auth_token = models.CharField(max_length=100, blank=True, help_text="Twilio Auth Token (keep secure)")
    twilio_phone_number = models.CharField(max_length=20, blank=True, help_text="Twilio phone number (e.g., +1234567890)")
    twilio_whatsapp_number = models.CharField(max_length=50, blank=True, default='whatsapp:+14155238886', help_text="Twilio WhatsApp number (sandbox or approved)")
    twilio_enabled = models.BooleanField(default=False, help_text="Enable WhatsApp/SMS messaging via Twilio")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "School Settings"
        verbose_name_plural = "School Settings"
    
    def __str__(self):
        return f"Settings for {self.school_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SchoolSettings.objects.exists():
            # If this is a new instance and one already exists, don't create another
            return
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get the school settings instance, create if doesn't exist"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'school_name': 'Gyanodaya School',
                'school_address': '123 Education Street, Learning City',
                'school_phone': '+91-1234567890',
                'school_email': 'info@gyanodaya.edu',
            }
        )
        return settings


# ============================================
# EDUCATIONAL GAMES SYSTEM
# ============================================

class GameCategory(models.Model):
    name = models.CharField(max_length=100)  # Maths, Science, Hindi, English
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='🎮')  # Emoji icon
    color = models.CharField(max_length=20, default='#6366f1')  # Hex color
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Game Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class EducationalGame(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    GAME_TYPE_CHOICES = [
        ('quiz', 'Quiz'),
        ('puzzle', 'Puzzle'),
        ('memory', 'Memory Game'),
        ('word', 'Word Game'),
        ('number', 'Number Game'),
        ('science', 'Science Experiment'),
        ('story', 'Story Game'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(GameCategory, on_delete=models.CASCADE, related_name='games')
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='games')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    game_type = models.CharField(max_length=20, choices=GAME_TYPE_CHOICES, default='quiz')
    instructions = models.TextField(help_text="How to play the game")
    learning_objectives = models.TextField(help_text="What students will learn")
    time_limit = models.IntegerField(default=300, help_text="Time limit in seconds")
    max_score = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['class_level__numeric_value', 'difficulty', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.class_level.name}"


class GameQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
        ('drag_drop', 'Drag and Drop'),
        ('matching', 'Matching'),
        ('sequence', 'Sequence'),
    ]
    
    game = models.ForeignKey(EducationalGame, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')
    points = models.IntegerField(default=10)
    time_limit = models.IntegerField(default=30, help_text="Time limit in seconds")
    explanation = models.TextField(blank=True, help_text="Explanation for the answer")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.game.title} - Q{self.order + 1}"


class GameAnswer(models.Model):
    question = models.ForeignKey(GameQuestion, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.question.game.title} - Answer {self.order + 1}"


class GameSession(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='game_sessions')
    game = models.ForeignKey(EducationalGame, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    time_taken = models.IntegerField(default=0, help_text="Time taken in seconds")
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.game.title}"
    
    @property
    def percentage(self):
        if self.total_questions > 0:
            return round((self.correct_answers / self.total_questions) * 100, 2)
        return 0


class GameAchievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='🏆')
    condition_type = models.CharField(max_length=50, help_text="e.g., score_100, complete_5_games")
    condition_value = models.IntegerField(help_text="Value needed to unlock achievement")
    points_reward = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class StudentGameAchievement(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='game_achievements')
    achievement = models.ForeignKey(GameAchievement, on_delete=models.CASCADE, related_name='student_achievements')
    unlocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'achievement']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.achievement.name}"


# ============================================
# MOCK TESTS SYSTEM (9th-12th Class)
# ============================================

class MockTestCategory(models.Model):
    name = models.CharField(max_length=100)  # Mathematics, Physics, Chemistry, Biology
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='📚')  # Emoji icon
    color = models.CharField(max_length=20, default='#10b981')  # Hex color
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Mock Test Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class MockTest(models.Model):
    DIFFICULTY_CHOICES = [
        ('hard', 'Hard'),
        ('very_hard', 'Very Hard'),
        ('expert', 'Expert'),
    ]
    
    EXAM_TYPE_CHOICES = [
        ('board', 'Board Exam'),
        ('competitive', 'Competitive Exam'),
        ('entrance', 'Entrance Exam'),
        ('final', 'Final Exam'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(MockTestCategory, on_delete=models.CASCADE, related_name='mock_tests')
    class_level = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='mock_tests')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='hard')
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES, default='board')
    instructions = models.TextField(help_text="Instructions for the mock test")
    syllabus_topics = models.TextField(help_text="Topics covered in this mock test")
    time_limit = models.IntegerField(default=10800, help_text="Time limit in seconds (3 hours)")
    total_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=33)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['class_level__numeric_value', 'difficulty', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.class_level.name}"


class MockTestQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
        ('short_answer', 'Short Answer'),
        ('long_answer', 'Long Answer'),
        ('numerical', 'Numerical'),
    ]
    
    mock_test = models.ForeignKey(MockTest, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')
    marks = models.IntegerField(default=1)
    negative_marks = models.FloatField(default=0.25, help_text="Negative marks for wrong answer")
    explanation = models.TextField(blank=True, help_text="Explanation for the answer")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.mock_test.title} - Q{self.order + 1}"


class MockTestAnswer(models.Model):
    question = models.ForeignKey(MockTestQuestion, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.mock_test.title} - Answer {self.order + 1}"


class MockTestSession(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mock_test_sessions')
    mock_test = models.ForeignKey(MockTest, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_marks = models.IntegerField(default=0)
    obtained_marks = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    time_taken = models.IntegerField(default=0, help_text="Time taken in seconds")
    is_completed = models.BooleanField(default=False)
    is_passed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.mock_test.title}"
    
    @property
    def percentage(self):
        if self.total_marks > 0:
            return round((self.obtained_marks / self.total_marks) * 100, 2)
        return 0
    
    @property
    def grade(self):
        percentage = self.percentage
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C+'
        elif percentage >= 40:
            return 'C'
        elif percentage >= 33:
            return 'D'
        else:
            return 'F'


class MockTestAttempt(models.Model):
    session = models.ForeignKey(MockTestSession, on_delete=models.CASCADE, related_name='attempts')
    question = models.ForeignKey(MockTestQuestion, on_delete=models.CASCADE, related_name='attempts')
    selected_answer = models.ForeignKey(MockTestAnswer, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(blank=True, help_text="For text-based answers")
    is_correct = models.BooleanField(default=False)
    marks_obtained = models.FloatField(default=0)
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session', 'question']
    
    def __str__(self):
        return f"{self.session.student.get_full_name()} - {self.question.mock_test.title} - Q{self.question.order + 1}"


# ============================================
# ID CARD GENERATOR FOR SUPER USER
# ============================================

class IDCardGenerator(models.Model):
    """ID Card Generator for Super User - Offline Data Entry"""
    PAGE_SIZE_CHOICES = [
        ('A4', 'A4 (10 cards per page)'),
        ('12x18', '12x18 (25 cards per page)'),
    ]
    
    ORIENTATION_CHOICES = [
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
    ]
    
    CARD_TYPE_CHOICES = [
        ('single', 'Single Card'),
        ('multi', 'Multi Card'),
    ]
    
    # Generator Settings
    card_type = models.CharField(max_length=10, choices=CARD_TYPE_CHOICES, default='multi')
    page_size = models.CharField(max_length=10, choices=PAGE_SIZE_CHOICES, default='A4')
    orientation = models.CharField(max_length=10, choices=ORIENTATION_CHOICES, default='portrait')
    
    # School Information
    school_name = models.CharField(max_length=200, default='ABC School')
    school_address = models.TextField(blank=True)
    school_phone = models.CharField(max_length=20, blank=True)
    school_email = models.EmailField(blank=True)
    
    # Card Design Settings
    card_width = models.IntegerField(default=90, help_text="Width in mm")
    card_height = models.IntegerField(default=120, help_text="Height in mm")
    border_color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    background_color = models.CharField(max_length=7, default='#ffffff', help_text="Hex color code")
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"ID Card Generator - {self.get_card_type_display()}"
    
    def get_cards_per_page(self):
        """Get number of cards per page based on page size"""
        if self.page_size == 'A4':
            return 10
        elif self.page_size == '12x18':
            return 25
        return 10


class IDCardData(models.Model):
    """Individual ID Card Data Entry"""
    generator = models.ForeignKey(IDCardGenerator, on_delete=models.CASCADE, related_name='card_data')
    
    # Student Information
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100, blank=True)
    address = models.TextField()
    mobile = models.CharField(max_length=15)
    admission_no = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    class_name = models.CharField(max_length=20)
    section = models.CharField(max_length=10, blank=True)
    roll_number = models.CharField(max_length=10, blank=True)
    
    # Photo
    photo = models.ImageField(upload_to='id_card_photos/', blank=True, null=True)
    
    # Additional Information
    blood_group = models.CharField(max_length=5, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    valid_until = models.DateField(blank=True, null=True)
    
    # Status
    is_generated = models.BooleanField(default=False)
    generated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.admission_no}"
    
    def get_full_name(self):
        return f"{self.name}"
    
    def get_age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

# Import SystemConfiguration from system_config at the end to avoid circular imports
from .system_config import SystemConfiguration


# ============================================
# ENHANCED FEE MANAGEMENT MODELS
# (Moved from fee_enhancements.py for Django auto-detection)
# ============================================

class FeeConcession(models.Model):
    """Fee concessions based on category, merit, scholarship, etc."""
    CONCESSION_TYPE_CHOICES = [
        ('merit', 'Merit-based'),
        ('scholarship', 'Scholarship'),
        ('category', 'Category-based (SC/ST/OBC)'),
        ('religion', 'Religion-based'),
        ('sibling', 'Sibling Discount'),
        ('staff_child', 'Staff Child'),
        ('sports', 'Sports Achievement'),
        ('academic', 'Academic Excellence'),
        ('financial', 'Financial Aid'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    concession_type = models.CharField(max_length=20, choices=CONCESSION_TYPE_CHOICES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                    validators=[MinValueValidator(0), MaxValueValidator(100)],
                                    help_text="Percentage discount (0-100)")
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                      help_text="Fixed amount discount (if not percentage)")
    is_percentage = models.BooleanField(default=True, help_text="True for percentage, False for fixed amount")
    applicable_to = models.CharField(max_length=50, blank=True, 
                                    help_text="Category/Class/Other criteria")
    min_marks_required = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                            help_text="Minimum marks required for merit-based")
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Fee Concession"
        verbose_name_plural = "Fee Concessions"
    
    def __str__(self):
        return f"{self.name} - {self.get_concession_type_display()}"


class StudentFeeConcession(models.Model):
    """Link students to fee concessions"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_concessions')
    concession = models.ForeignKey(FeeConcession, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    approved_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'concession', 'academic_year']
        ordering = ['-approved_date']
    
    def __str__(self):
        return f"{self.student} - {self.concession}"


class FeeNotification(models.Model):
    """Fee payment notifications and reminders"""
    NOTIFICATION_TYPE_CHOICES = [
        ('pending', 'Pending Fee Reminder'),
        ('overdue', 'Overdue Fee Alert'),
        ('receipt', 'Payment Receipt'),
        ('reminder', 'General Reminder'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sent_via = models.CharField(max_length=20, choices=[('email', 'Email'), ('sms', 'SMS'), ('whatsapp', 'WhatsApp'), ('both', 'Both'), ('all', 'All')])
    sent_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
    sent_to_email = models.EmailField(blank=True)
    sent_to_phone = models.CharField(max_length=15, blank=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.student} - {self.get_notification_type_display()}"


class FeeReconciliation(models.Model):
    """Payment reconciliation - cross-check bank statements with payments"""
    reconciliation_date = models.DateField()
    bank_name = models.CharField(max_length=100)
    bank_statement_amount = models.DecimalField(max_digits=12, decimal_places=2)
    system_recorded_amount = models.DecimalField(max_digits=12, decimal_places=2)
    difference = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('matched', 'Matched'),
        ('mismatch', 'Mismatch'),
        ('resolved', 'Resolved'),
    ], default='pending')
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reconciliation_date']
        verbose_name = "Fee Reconciliation"
        verbose_name_plural = "Fee Reconciliations"
    
    def __str__(self):
        return f"Reconciliation - {self.reconciliation_date} - {self.bank_name}"
    
    def calculate_difference(self):
        """Calculate difference between bank and system amounts"""
        self.difference = self.bank_statement_amount - self.system_recorded_amount
        return self.difference


# ============================================
# MOBILE APP DEVICE TRACKING
# ============================================

class MobileDevice(models.Model):
    """Track mobile devices where app is installed"""
    device_id = models.CharField(max_length=255, unique=True, help_text="Unique device identifier")
    device_name = models.CharField(max_length=200, blank=True, help_text="Device name/model")
    device_type = models.CharField(max_length=50, default='android', choices=[('android', 'Android'), ('ios', 'iOS')])
    os_version = models.CharField(max_length=50, blank=True, help_text="OS version")
    app_version = models.CharField(max_length=50, blank=True, help_text="App version installed")
    
    # User association (optional - if user logged in)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    
    # Installation info
    first_installed = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Device is currently active")
    
    # Network info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional device info")
    
    class Meta:
        verbose_name = "Mobile Device"
        verbose_name_plural = "Mobile Devices"
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['device_id']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        user_info = f" - {self.user.username}" if self.user else ""
        return f"{self.device_name or self.device_id}{user_info} ({self.device_type})"
    
    def update_last_seen(self, ip_address=None):
        """Update last seen timestamp and IP"""
        self.last_seen = timezone.now()
        if ip_address:
            self.last_ip_address = ip_address
        self.is_active = True
        self.save(update_fields=['last_seen', 'last_ip_address', 'is_active'])


class VerifiedDevice(models.Model):
    """Track devices that have been OTP verified for a user"""
    device_id = models.CharField(max_length=255, help_text="Unique device identifier")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verified_devices')
    phone = models.CharField(max_length=15, blank=True, help_text="Phone number used for verification")
    
    # Verification info
    verified_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Device info
    device_name = models.CharField(max_length=200, blank=True)
    device_type = models.CharField(max_length=50, default='android', choices=[('android', 'Android'), ('ios', 'iOS')])
    
    class Meta:
        verbose_name = "Verified Device"
        verbose_name_plural = "Verified Devices"
        unique_together = [['device_id', 'user']]  # One device can be verified for one user
        ordering = ['-last_used']
        indexes = [
            models.Index(fields=['device_id', 'user']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.device_name or self.device_id} - {self.user.username} (Verified)"
    
    def update_last_used(self):
        """Update last used timestamp"""
        self.last_used = timezone.now()
        self.is_active = True
        self.save(update_fields=['last_used', 'is_active'])


# ============================================
# WORK & EXPENSE TRACKING (Super Admin)
# ============================================

class TeamMember(models.Model):
    """Team members who can be assigned to work tasks"""
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, validators=[phone_regex])
    email = models.EmailField(blank=True, null=True)
    role = models.CharField(max_length=100, help_text="e.g., Technician, Sales Executive, Support Staff")
    is_active = models.BooleanField(default=True)
    joining_date = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.role})"


class WorkEntry(models.Model):
    """Track operational work done for schools"""
    WORK_TYPE_CHOICES = [
        ('erp_setup', 'ERP Setup & Configuration'),
        ('id_card', 'ID Card Generation'),
        ('camera_installation', 'Camera Installation'),
        ('system_installation', 'System/Hardware Installation'),
        ('printing_material', 'Printing Material Supply'),
        ('training', 'Staff Training'),
        ('maintenance', 'System Maintenance'),
        ('troubleshooting', 'Troubleshooting & Support'),
        ('data_migration', 'Data Migration'),
        ('customization', 'Software Customization'),
        ('other', 'Other Work'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='work_entries')
    work_type = models.CharField(max_length=50, choices=WORK_TYPE_CHOICES)
    title = models.CharField(max_length=200, help_text="Brief title of the work")
    description = models.TextField(help_text="Detailed description of work done")
    location = models.CharField(max_length=200, help_text="Work location/address")
    work_date = models.DateField(help_text="Date when work was done")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    
    # Team members assigned to this work
    team_members = models.ManyToManyField('TeamMember', related_name='work_entries', blank=True)
    
    # Additional details
    hours_spent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                       help_text="Number of hours spent on this work")
    notes = models.TextField(blank=True, help_text="Additional notes or observations")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_work_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-work_date', '-created_at']
        verbose_name = 'Work Entry'
        verbose_name_plural = 'Work Entries'
    
    def __str__(self):
        return f"{self.school.name} - {self.get_work_type_display()} ({self.work_date})"
    
    def total_expenses(self):
        """Calculate total expenses for this work entry"""
        return self.expenses.aggregate(total=models.Sum('amount'))['total'] or 0


class WorkExpense(models.Model):
    """Track expenses for each work entry"""
    PAID_BY_CHOICES = [
        ('company', 'Company'),
        ('team_member', 'Team Member'),
    ]
    
    EXPENSE_CATEGORY_CHOICES = [
        ('travel', 'Travel & Transportation'),
        ('material', 'Material/Hardware Purchase'),
        ('printing', 'Printing & Stationery'),
        ('food', 'Food & Accommodation'),
        ('software', 'Software/License'),
        ('installation', 'Installation Charges'),
        ('labor', 'Labor Charges'),
        ('misc', 'Miscellaneous'),
    ]
    
    work_entry = models.ForeignKey('WorkEntry', on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORY_CHOICES)
    description = models.CharField(max_length=200, help_text="What was this expense for?")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    paid_by = models.CharField(max_length=20, choices=PAID_BY_CHOICES, default='company')
    
    # If paid by team member, track who paid
    team_member = models.ForeignKey('TeamMember', on_delete=models.SET_NULL, null=True, blank=True,
                                     help_text="If paid by team member, select who paid")
    
    expense_date = models.DateField(help_text="Date of expense")
    receipt_number = models.CharField(max_length=100, blank=True, help_text="Receipt/bill number")
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"{self.work_entry.school.name} - {self.get_category_display()} - ₹{self.amount}"
