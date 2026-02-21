from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
from pathlib import Path

# ============================================
# STUDENT FORMS
# ============================================

class StudentForm(forms.ModelForm):
    """Form for adding/editing students"""
    
    class Meta:
        model = Student
        fields = [
            'admission_number', 'roll_number', 'first_name', 'middle_name', 'last_name',
            'date_of_birth', 'gender', 'blood_group', 'photo',
            'email', 'phone', 'address', 'city', 'state', 'pincode',
            'current_class', 'section', 'academic_year', 'admission_date', 'previous_school',
            'father_name', 'father_phone', 'father_occupation', 'father_email',
            'mother_name', 'mother_phone', 'mother_occupation', 'mother_email',
            'guardian_name', 'guardian_phone', 'guardian_relation',
            'status', 'is_transport_required', 'medical_conditions', 'birth_certificate',
            'aadhaar_card', 'samagra_id'
        ]
        
        widgets = {
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2024001'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 101'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Middle Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
            'current_class': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'admission_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'previous_school': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Previous School Name'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Father's Name"}),
            'father_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
            'father_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Occupation'}),
            'father_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'father@example.com'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Mother's Name"}),
            'mother_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
            'mother_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Occupation'}),
            'mother_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'mother@example.com'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Guardian's Name"}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
            'guardian_relation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relation'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_transport_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any medical conditions or allergies'}),
            'birth_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'aadhaar_card': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12-digit Aadhaar Number'}),
            'samagra_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '9-digit Samagra ID'}),
        }


# ============================================
# ATTENDANCE FORMS
# ============================================

class AttendanceForm(forms.ModelForm):
    """Form for marking attendance"""
    
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status', 'remarks']
        
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class BulkAttendanceForm(forms.Form):
    """Form for bulk attendance marking"""
    section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Section'
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date'
    )


# ============================================
# FEE MANAGEMENT FORMS
# ============================================

class FeeStructureForm(forms.ModelForm):
    """Form for creating/editing fee structure"""
    
    class Meta:
        model = FeeStructure
        fields = '__all__'
        
        widgets = {
            'class_assigned': forms.Select(attrs={'class': 'form-control', 'id': 'id_class_assigned'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'stream': forms.Select(attrs={'class': 'form-control'}),
            'subjects': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
            'tuition_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transport_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'library_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lab_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sports_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'exam_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'computer_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'optional_subject_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class FeePaymentForm(forms.ModelForm):
    """Form for recording fee payment"""
    
    class Meta:
        model = FeePayment
        fields = [
            'student', 'receipt_number', 'payment_date', 'academic_year',
            'amount_paid', 'discount', 'late_fee', 'payment_method',
            'payment_status', 'transaction_id', 'cheque_number', 'bank_name', 'remarks'
        ]
        
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'receipt_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Receipt Number'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'late_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transaction ID'}),
            'cheque_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cheque Number'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Name'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial receipt number
        if not self.instance.pk:
            last_payment = FeePayment.objects.order_by('-id').first()
            if last_payment and last_payment.receipt_number:
                try:
                    # Extract numeric part from receipt number
                    receipt_parts = last_payment.receipt_number.split('-')
                    if len(receipt_parts) > 1:
                        # Get the last part and extract only digits
                        numeric_part = ''.join(filter(str.isdigit, receipt_parts[-1]))
                        if numeric_part:
                            last_number = int(numeric_part)
                            self.fields['receipt_number'].initial = f'REC-{last_number + 1:06d}'
                        else:
                            self.fields['receipt_number'].initial = 'REC-000001'
                    else:
                        self.fields['receipt_number'].initial = 'REC-000001'
                except (ValueError, IndexError):
                    self.fields['receipt_number'].initial = 'REC-000001'
            else:
                self.fields['receipt_number'].initial = 'REC-000001'




# ============================================
# TEACHER FORMS
# ============================================

class TeacherForm(forms.ModelForm):
    """Form for adding/editing teachers"""
    
    # Additional fields for User model
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'})
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        required=False
    )
    
    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'phone', 'alternate_phone', 'date_of_birth', 'gender',
            'address', 'city', 'state', 'pincode', 'qualification',
            'joining_date', 'current_salary', 'subjects', 'photo', 'is_active'
        ]
        
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee ID'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., M.Sc, B.Ed'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'current_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'subjects': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Editing existing teacher
            if self.instance.user:
                self.fields['username'].initial = self.instance.user.username
                self.fields['email'].initial = self.instance.user.email
                self.fields['first_name'].initial = self.instance.user.first_name
                self.fields['last_name'].initial = self.instance.user.last_name
                self.fields['username'].widget.attrs['readonly'] = True
        else:
            # New teacher - username is required
            self.fields['username'].required = True
            self.fields['password'].required = True


class StaffForm(forms.ModelForm):
    """Form for adding/editing non-teaching staff"""
    
    # Additional fields for User model
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'})
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        required=False
    )
    
    class Meta:
        from .models import Staff
        model = Staff
        fields = [
            'employee_id', 'category', 'designation', 'department',
            'phone', 'alternate_phone', 'date_of_birth', 'gender',
            'address', 'city', 'state', 'pincode',
            'joining_date', 'current_salary', 'qualification', 'education_level',
            'experience_years', 'bank_account', 'ifsc_code', 'pan_number',
            'aadhar_number', 'pf_number', 'is_librarian', 'photo',
            'emergency_contact', 'emergency_phone'
        ]
        # Note: Teaching-related fields removed - Staff is for non-teaching only
        
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee ID'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Designation'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'current_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'qualification': forms.Select(attrs={'class': 'form-control'}),
            'education_level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specific degree details'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'bank_account': forms.TextInput(attrs={'class': 'form-control'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control'}),
            'aadhar_number': forms.TextInput(attrs={'class': 'form-control'}),
            'pf_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_librarian': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Editing existing staff
            if self.instance.user:
                self.fields['username'].initial = self.instance.user.username
                self.fields['email'].initial = self.instance.user.email
                self.fields['first_name'].initial = self.instance.user.first_name
                self.fields['last_name'].initial = self.instance.user.last_name
                self.fields['username'].widget.attrs['readonly'] = True
        else:
            # New staff - username is required
            self.fields['username'].required = True
            self.fields['password'].required = True


# ============================================
# LIBRARY FORMS
# ============================================

class BookForm(forms.ModelForm):
    """Form for adding/editing books"""
    
    class Meta:
        model = Book
        fields = [
            'isbn', 'title', 'author', 'publisher', 'category',
            'edition', 'publication_year', 'total_copies', 'available_copies',
            'price', 'rack_number', 'description', 'cover_image'
        ]
        
        widgets = {
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ISBN'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Book Title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author Name'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Publisher'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'edition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Edition'}),
            'publication_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'rack_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rack Number'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class BookIssueForm(forms.ModelForm):
    """Form for issuing books"""
    
    class Meta:
        model = BookIssue
        fields = ['book', 'student', 'issue_date', 'due_date', 'remarks']
        
        widgets = {
            'book': forms.Select(attrs={'class': 'form-control'}),
            'student': forms.Select(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter only available books
        self.fields['book'].queryset = Book.objects.filter(available_copies__gt=0)


# ============================================
# TIMETABLE FORMS
# ============================================

class TimetableForm(forms.ModelForm):
    """Form for creating timetable"""
    
    class Meta:
        model = Timetable
        fields = [
            'section', 'academic_year', 'weekday', 'time_slot', 
            'subject', 'teacher', 'room_number'
        ]
        
        widgets = {
            'section': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'weekday': forms.Select(attrs={'class': 'form-control'}),
            'time_slot': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Room Number'}),
        }


class TimeSlotForm(forms.ModelForm):
    """Form for creating time slots"""
    
    class Meta:
        model = TimeSlot
        fields = ['start_time', 'end_time', 'slot_name', 'is_break']
        
        widgets = {
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'slot_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Period 1'}),
            'is_break': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AssignClassTeacherForm(forms.Form):
    """Form to assign class teacher"""
    teacher = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Teacher"
    )
    section = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Section"
    )
    academic_year = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Academic Year"
    )
    
    def __init__(self, *args, **kwargs):
        from .models import Teacher, Section, AcademicYear
        super().__init__(*args, **kwargs)
        
        self.fields['teacher'].queryset = Teacher.objects.filter(is_active=True).select_related('user').order_by('user__first_name')
        self.fields['section'].queryset = Section.objects.select_related('class_assigned').order_by('class_assigned__numeric_value', 'name')
        self.fields['academic_year'].queryset = AcademicYear.objects.all().order_by('-year')
        
        # Set default to current academic year
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            self.fields['academic_year'].initial = current_year.id


class TimetableChangeRequestForm(forms.ModelForm):
    """Form for teachers to request timetable changes"""
    
    class Meta:
        from .models import TimetableChangeRequest
        model = TimetableChangeRequest
        fields = [
            'current_timetable_entry', 'reason', 'preferred_day', 
            'preferred_time_slot', 'preferred_section', 'preferred_subject', 
            'preferred_room', 'additional_notes'
        ]
        
        widgets = {
            'current_timetable_entry': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Please explain why you need this change (e.g., personal reasons, conflict, etc.)'
            }),
            'preferred_day': forms.Select(attrs={'class': 'form-select'}),
            'preferred_time_slot': forms.Select(attrs={'class': 'form-select'}),
            'preferred_section': forms.Select(attrs={'class': 'form-select'}),
            'preferred_subject': forms.Select(attrs={'class': 'form-select'}),
            'preferred_room': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Room 101'
            }),
            'additional_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional information or suggestions'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        academic_year = kwargs.pop('academic_year', None)
        super().__init__(*args, **kwargs)
        
        from .models import Timetable, TimeSlot, Section, Subject
        
        # Filter timetable entries for this teacher
        if teacher and academic_year:
            self.fields['current_timetable_entry'].queryset = Timetable.objects.filter(
                teacher=teacher,
                academic_year=academic_year
            ).select_related('section', 'subject', 'time_slot')
        else:
            self.fields['current_timetable_entry'].queryset = Timetable.objects.none()
        
        # Make current_timetable_entry required
        self.fields['current_timetable_entry'].required = True
        
        # Make preferred fields optional
        self.fields['preferred_day'].required = False
        self.fields['preferred_time_slot'].required = False
        self.fields['preferred_section'].required = False
        self.fields['preferred_subject'].required = False
        self.fields['preferred_room'].required = False
        self.fields['additional_notes'].required = False
        
        # Add empty option
        self.fields['preferred_day'].choices = [('', '---------')] + list(self.fields['preferred_day'].choices)[1:]
        self.fields['preferred_time_slot'].queryset = TimeSlot.objects.filter(is_break=False).order_by('start_time')
        self.fields['preferred_section'].queryset = Section.objects.select_related('class_assigned').order_by('class_assigned__numeric_value', 'name')
        self.fields['preferred_subject'].queryset = Subject.objects.all().order_by('name')


# ============================================
# NOTICE & EVENT FORMS
# ============================================

class NoticeForm(forms.ModelForm):
    """Form for creating notices"""
    
    class Meta:
        model = Notice
        fields = [
            'title', 'content', 'notice_date', 'expiry_date',
            'target_audience', 'priority', 'status',
            'specific_class', 'specific_section', 'attachment',
            'is_active'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notice Title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'notice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'target_audience': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'specific_class': forms.Select(attrs={'class': 'form-control'}),
            'specific_section': forms.Select(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EventForm(forms.ModelForm):
    """Form for creating events"""
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'event_date',
            'start_time', 'end_time', 'venue', 'participants', 
            'status', 'target_audience', 'is_holiday'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'event_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'venue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Venue'}),
            'participants': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'target_audience': forms.Select(attrs={'class': 'form-control'}),
            'is_holiday': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



# ============================================
# IMPORT FORMS
# ============================================

class StudentImportForm(forms.Form):
    """Upload Excel with folder-based photo lookup for bulk student import.
    
    Enhanced photo matching supports:
    - Multiple column names: photo_filename, Photo No, photo, Photo, photo_name, Photo Name, etc.
    - Photo numbers (e.g., 1, 2, 3) or photo filenames (e.g., student_name.jpg)
    - Multiple naming patterns in folder: photo_1.jpg, 1.jpg, photo1.jpg, etc.
    """
    excel_file = forms.FileField(
        label='Excel (.xlsx)',
        help_text='Required columns: admission_number, first_name, last_name, date_of_birth, gender, class_name, section_name, academic_year. Optional: roll_number, father_name, father_phone, city, state, pincode. Photo column: photo_filename, Photo No, photo, Photo, photo_name, Photo Name, etc.'
    )
    photo_folder = forms.CharField(
        required=False,
        label='Photo folder path',
        help_text='Path to folder containing student photos. Photos will be matched by name/number from Excel photo column. Supports multiple naming patterns: photo_1.jpg, 1.jpg, photo1.jpg, etc. Default: students_app/photo'
    )
    images_zip = forms.FileField(
        required=False,
        label='Images ZIP (optional - not required)',
        help_text='Optional: ZIP file containing photos as alternative to folder. Photos will be matched by name from Excel photo column. If not provided, photos will be loaded from the folder path above.'
    )

    def clean_excel_file(self):
        f = self.cleaned_data['excel_file']
        if not f.name.lower().endswith('.xlsx'):
            raise ValidationError('Only .xlsx files are supported')
        return f


# ============================================
# TEACHER PORTAL FORMS
# ============================================

class QuestionPaperForm(forms.ModelForm):
    class Meta:
        model = QuestionPaper
        fields = ['title', 'subject', 'class_assigned', 'instructions']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'class_assigned': forms.Select(attrs={'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class WhatsAppMessageForm(forms.Form):
    audience = forms.ChoiceField(choices=[('individual', 'Individual'), ('section', 'Section'), ('class', 'Class'), ('all', 'All Students')], widget=forms.Select(attrs={'class': 'form-control'}))
    student = forms.ModelChoiceField(queryset=Student.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    section = forms.ModelChoiceField(queryset=Section.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    class_assigned = forms.ModelChoiceField(queryset=Class.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

    def clean_images_zip(self):
        f = self.cleaned_data.get('images_zip')
        if f and not (f.name.lower().endswith('.zip')):
            raise ValidationError('Only .zip is supported for bulk images')
        return f



# ============================================
# TRANSPORT FORMS
# ============================================

class TransportRouteForm(forms.ModelForm):
    """Form for creating transport routes"""
    
    class Meta:
        model = TransportRoute
        fields = [
            'route_name', 'route_number', 'starting_point',
            'ending_point', 'total_distance', 'estimated_time', 'is_active'
        ]
        
        widgets = {
            'route_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Route Name'}),
            'route_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Route Number'}),
            'starting_point': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Starting Point'}),
            'ending_point': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ending Point'}),
            'total_distance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_time': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BusForm(forms.ModelForm):
    """Form for managing buses"""
    
    class Meta:
        model = Bus
        fields = [
            'bus_number', 'registration_number', 'route', 'capacity',
            'driver_name', 'driver_phone', 'conductor_name',
            'conductor_phone', 'is_active'
        ]
        
        widgets = {
            'bus_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bus Number'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Registration Number'}),
            'route': forms.Select(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Driver Name'}),
            'driver_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
            'conductor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Conductor Name'}),
            'conductor_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91XXXXXXXXXX'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ============================================
# EXAM FORMS
# ============================================

class ExamForm(forms.ModelForm):
    """Form for creating exams"""
    
    class Meta:
        model = Exam
        fields = ['name', 'academic_year', 'term', 'start_date', 'end_date', 'is_published']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Exam Name (e.g. Mid Term 2025)'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'term': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ExamScheduleForm(forms.ModelForm):
    """Form for scheduling exams"""
    
    class Meta:
        model = ExamSchedule
        fields = ['exam', 'subject', 'class_assigned', 'exam_date', 'max_marks']
        
        widgets = {
            'exam': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'class_assigned': forms.Select(attrs={'class': 'form-select'}),
            'exam_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# ============================================
# ACADEMIC & TIMETABLE FORMS
# ============================================

class AcademicYearForm(forms.ModelForm):
    """Form for managing academic years"""
    class Meta:
        model = AcademicYear
        fields = ['year', 'start_date', 'end_date', 'is_current']
        widgets = {
            'year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2025-2026'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TimeSlotForm(forms.ModelForm):
    """Form for managing time slots"""
    class Meta:
        model = TimeSlot
        fields = ['slot_name', 'start_time', 'end_time', 'is_break']
        widgets = {
            'slot_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Period 1'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_break': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

