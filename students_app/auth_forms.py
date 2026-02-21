from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserRole, School, SchoolUser


class ParentLoginForm(forms.Form):
    """Login form for parents using admission ID and child name"""
    admission_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Admission ID',
            'required': True
        }),
        label="Admission ID"
    )
    child_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Child Name',
            'required': True
        }),
        label="Child Name"
    )


class TeacherLoginForm(forms.Form):
    """Login form for teachers using mobile number and name"""
    mobile = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Mobile Number',
            'required': True
        }),
        label="Mobile Number"
    )
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Your Name',
            'required': True
        }),
        label="Name"
    )


class SchoolUserCreationForm(UserCreationForm):
    """Form for creating school users with roles"""
    role = forms.ModelChoiceField(
        queryset=UserRole.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Role"
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select School",
        required=False
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    login_id = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Admission ID for parents, Mobile for teachers, Username for others"
    )
    custom_password = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Custom password (leave blank to use default)"
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Extract user from kwargs if provided
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Filter roles and schools based on user permissions
        if user:
            is_superuser = user.is_superuser
            user_school = None
            is_super_admin = False
            
            try:
                school_user = user.school_profile
                is_super_admin = school_user.role.name == 'super_admin'
                user_school = school_user.school
            except:
                pass
            
            # Filter roles: Only superusers or super_admins can create super_admin or school_admin roles
            if not (is_superuser or is_super_admin):
                # Exclude super_admin and school_admin roles for regular school admins
                self.fields['role'].queryset = UserRole.objects.filter(
                    is_active=True
                ).exclude(name__in=['super_admin', 'school_admin'])
            else:
                # Superusers and super_admins can see all roles
                self.fields['role'].queryset = UserRole.objects.filter(is_active=True)
            
            # Filter schools: School admins can only create users for their own school
            if user_school and not (is_superuser or is_super_admin):
                # School admin - restrict to their own school and pre-fill it
                self.fields['school'].queryset = School.objects.filter(id=user_school.id)
                self.fields['school'].initial = user_school.id
                self.fields['school'].required = True
                self.fields['school'].widget.attrs['readonly'] = True
                self.fields['school'].widget.attrs['style'] = 'background-color: #e9ecef; cursor: not-allowed;'
            else:
                # Superuser or super_admin - can select any school
                self.fields['school'].queryset = School.objects.all()
                self.fields['school'].required = False

    def save(self, commit=True, user=None):
        user_obj = super().save(commit=False)
        if commit:
            user_obj.save()
            
            # Get school - if user is provided and is a school admin, use their school
            school = self.cleaned_data.get('school')
            if user and not school:
                try:
                    school_user = user.school_profile
                    if school_user.role.name == 'school_admin' and school_user.school:
                        school = school_user.school
                except:
                    pass
            
            # Create school user profile
            SchoolUser.objects.create(
                user=user_obj,
                role=self.cleaned_data['role'],
                school=school,
                phone=self.cleaned_data.get('phone', ''),
                login_id=self.cleaned_data['login_id'],
                custom_password=self.cleaned_data.get('custom_password', ''),
            )
        return user_obj


class SchoolLogoUpdateForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ['logo']
        widgets = {
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }


class SchoolCreationForm(forms.ModelForm):
    """Form for creating new schools"""
    admin_username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter admin username',
            'id': 'id_admin_username'
        }),
        required=True,
        label="Admin Username",
        help_text="Choose a unique username for the school admin user"
    )
    admin_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter admin email',
            'id': 'admin_email'
        }),
        required=False,
        label="Admin Email",
        help_text="Will default to school email. You can change it if needed."
    )
    admin_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter strong password',
            'id': 'id_admin_password'
        }),
        required=True,
        label="Admin Password",
        help_text="Password must be at least 8 characters and contain letters and numbers"
    )
    admin_password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'id': 'id_admin_password_confirm'
        }),
        required=True,
        label="Confirm Password"
    )
    
    class Meta:
        model = School
        fields = [
            'name', 'address', 'phone', 'email', 'website', 'logo',
            'principal_name', 'established_year', 'affiliation_number', 'board',
            'max_users'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '10',
                'pattern': '[0-9]{10}',
                'id': 'id_phone'
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'principal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'established_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'affiliation_number': forms.TextInput(attrs={'class': 'form-control'}),
            'board': forms.TextInput(attrs={'class': 'form-control'}),
            'max_users': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove any non-digit characters
            phone = ''.join(filter(str.isdigit, phone))
            # Check if exactly 10 digits
            if len(phone) != 10:
                raise forms.ValidationError("Phone number must be exactly 10 digits.")
            # Check if it starts with a valid digit (not 0)
            if phone[0] == '0':
                raise forms.ValidationError("Phone number cannot start with 0.")
        return phone
    
    def clean_admin_username(self):
        username = self.cleaned_data.get('admin_username')
        if username:
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("This username is already taken. Please choose another.")
            # Validate username format (alphanumeric and underscore only)
            if not username.replace('_', '').replace('-', '').isalnum():
                raise forms.ValidationError("Username can only contain letters, numbers, underscores, and hyphens.")
            if len(username) < 3:
                raise forms.ValidationError("Username must be at least 3 characters long.")
        return username
    
    def clean_admin_password(self):
        password = self.cleaned_data.get('admin_password')
        if password:
            # Check minimum length
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            # Check for at least one letter and one number
            has_letter = any(c.isalpha() for c in password)
            has_number = any(c.isdigit() for c in password)
            if not has_letter:
                raise forms.ValidationError("Password must contain at least one letter.")
            if not has_number:
                raise forms.ValidationError("Password must contain at least one number.")
            # Use Django's password validators
            try:
                validate_password(password)
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
        return password
    
    def clean_admin_password_confirm(self):
        password = self.cleaned_data.get('admin_password')
        password_confirm = self.cleaned_data.get('admin_password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return password_confirm
    
    def clean_admin_email(self):
        admin_email = self.cleaned_data.get('admin_email')
        school_email = self.cleaned_data.get('email')
        
        # If admin email is not provided, use school email
        if not admin_email:
            admin_email = school_email
        
        # Validate that email is provided
        if not admin_email:
            raise forms.ValidationError("Admin email is required.")
        
        return admin_email


class SchoolUserEditForm(forms.ModelForm):
    """Form for editing school users with password change option"""
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Leave blank to keep current password. Enter new password to change it."
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Confirm new password"
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.school_user = kwargs.pop('school_user', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-populate school user fields if instance exists
        if self.school_user:
            self.fields['phone'] = forms.CharField(
                max_length=15,
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                required=False,
                initial=self.school_user.phone
            )
            self.fields['login_id'] = forms.CharField(
                max_length=100,
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                initial=self.school_user.login_id,
                help_text="Admission ID for parents, Mobile for teachers, Username for others"
            )
            self.fields['custom_password'] = forms.CharField(
                max_length=100,
                widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'text'}),
                required=False,
                initial=self.school_user.custom_password if self.school_user.custom_password else '',
                help_text="Custom password for mobile app/alternative login (visible for admin)"
            )
            
            # Role field
            role_queryset = UserRole.objects.filter(is_active=True)
            if user:
                is_superuser = user.is_superuser
                is_super_admin = False
                try:
                    user_school_user = user.school_profile
                    is_super_admin = user_school_user.role.name == 'super_admin'
                except:
                    pass
                
                if not (is_superuser or is_super_admin):
                    role_queryset = role_queryset.exclude(name__in=['super_admin', 'school_admin'])
            
            self.fields['role'] = forms.ModelChoiceField(
                queryset=role_queryset,
                widget=forms.Select(attrs={'class': 'form-control'}),
                initial=self.school_user.role,
                required=True
            )
            
            # School field
            school_queryset = School.objects.all()
            if user:
                try:
                    user_school_user = user.school_profile
                    user_school = user_school_user.school
                    if user_school and not (user.is_superuser or user_school_user.role.name == 'super_admin'):
                        school_queryset = School.objects.filter(id=user_school.id)
                except:
                    pass
            
            self.fields['school'] = forms.ModelChoiceField(
                queryset=school_queryset,
                widget=forms.Select(attrs={'class': 'form-control'}),
                required=False,
                initial=self.school_user.school
            )
        else:
            # If no school_user, create empty fields
            self.fields['phone'] = forms.CharField(
                max_length=15,
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                required=False
            )
            self.fields['login_id'] = forms.CharField(
                max_length=100,
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                help_text="Admission ID for parents, Mobile for teachers, Username for others"
            )
            self.fields['custom_password'] = forms.CharField(
                max_length=100,
                widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'text'}),
                required=False,
                help_text="Custom password for mobile app/alternative login (visible for admin)"
            )
            self.fields['role'] = forms.ModelChoiceField(
                queryset=UserRole.objects.filter(is_active=True),
                widget=forms.Select(attrs={'class': 'form-control'}),
                required=True
            )
            self.fields['school'] = forms.ModelChoiceField(
                queryset=School.objects.all(),
                widget=forms.Select(attrs={'class': 'form-control'}),
                required=False
            )
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match.")
            if password1:
                try:
                    validate_password(password1)
                except ValidationError as e:
                    raise forms.ValidationError(e.messages)
        
        return password2
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and self.instance:
            # Check if username is being changed and if it already exists
            if username != self.instance.username:
                if User.objects.filter(username=username).exists():
                    raise forms.ValidationError("This username is already taken.")
        return username
    
    def save(self, commit=True):
        user_obj = super().save(commit=False)
        
        # Update password if provided
        password1 = self.cleaned_data.get('password1')
        if password1:
            user_obj.set_password(password1)
        
        if commit:
            user_obj.save()
            
            # Update school user profile
            if self.school_user:
                self.school_user.role = self.cleaned_data.get('role')
                self.school_user.school = self.cleaned_data.get('school')
                self.school_user.phone = self.cleaned_data.get('phone', '')
                self.school_user.login_id = self.cleaned_data.get('login_id', '')
                
                custom_password = self.cleaned_data.get('custom_password')
                if custom_password:
                    self.school_user.custom_password = custom_password
                
                self.school_user.save()
        
        return user_obj
