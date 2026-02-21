from django import forms
from .models import IDCardGenerator, IDCardData

class IDCardGeneratorForm(forms.ModelForm):
    """Form for ID Card Generator"""
    
    class Meta:
        model = IDCardGenerator
        fields = [
            'card_type', 'page_size', 'orientation',
            'school_name', 'school_address', 'school_phone', 'school_email',
            'card_width', 'card_height', 'border_color', 'background_color',
            'is_active'
        ]
        
        widgets = {
            'card_type': forms.Select(attrs={'class': 'form-control'}),
            'page_size': forms.Select(attrs={'class': 'form-control'}),
            'orientation': forms.Select(attrs={'class': 'form-control'}),
            'school_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School Name'}),
            'school_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'School Address'}),
            'school_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91-XXXXXXXXXX'}),
            'school_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'school@example.com'}),
            'card_width': forms.NumberInput(attrs={'class': 'form-control', 'min': '50', 'max': '200'}),
            'card_height': forms.NumberInput(attrs={'class': 'form-control', 'min': '50', 'max': '300'}),
            'border_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'background_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['card_type'].widget.attrs.update({'onchange': 'updatePageSize()'})
        self.fields['page_size'].widget.attrs.update({'onchange': 'updateCardsPerPage()'})

class IDCardDataForm(forms.ModelForm):
    """Form for ID Card Data Entry"""
    
    class Meta:
        model = IDCardData
        fields = [
            'name', 'father_name', 'mother_name', 'address', 'mobile', 'admission_no',
            'date_of_birth', 'class_name', 'section', 'roll_number', 'photo',
            'blood_group', 'emergency_contact', 'valid_until'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student Full Name'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Father\'s Name'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mother\'s Name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Complete Address'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91-XXXXXXXXXX'}),
            'admission_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Admission Number'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'class_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Class (e.g., 10th, 12th)'}),
            'section': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Section (e.g., A, B)'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Roll Number'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Blood Group (e.g., A+, B-, O+)'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91-XXXXXXXXXX'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields required
        self.fields['name'].required = True
        self.fields['father_name'].required = True
        self.fields['admission_no'].required = True
        self.fields['date_of_birth'].required = True
        self.fields['class_name'].required = True
        self.fields['mobile'].required = True
        self.fields['address'].required = True
