from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q
from .models import SchoolUser, Student, Teacher, Parent
import hashlib


class MultiUserAuthBackend(ModelBackend):
    """
    Custom authentication backend for different user types:
    - Parents: Login with admission ID + child name
    - Teachers: Login with mobile number + name
    - Others: Standard username/password
    """
    
    def authenticate(self, request, username=None, password=None, user_type=None, **kwargs):
        if not username or not password:
            return None
            
        try:
            if user_type == 'parent':
                return self.authenticate_parent(username, password)
            elif user_type == 'teacher':
                return self.authenticate_teacher(username, password)
            else:
                return self.authenticate_standard(username, password)
        except Exception:
            return None
    
    def authenticate_parent(self, admission_id, child_name):
        """Authenticate parent using admission ID and child name"""
        try:
            # Find student by admission ID
            student = Student.objects.get(admission_number=admission_id)
            
            # Find parent linked to this student
            parent = Parent.objects.get(student=student)
            
            # Check if child name matches (case insensitive)
            if child_name.lower() == student.name.lower():
                # Get or create Django user for parent
                user, created = User.objects.get_or_create(
                    username=f"parent_{admission_id}",
                    defaults={
                        'first_name': parent.name,
                        'last_name': '',
                        'email': parent.email or '',
                        'is_active': True,
                    }
                )
                
                # Create or update school user profile
                school_user, created = SchoolUser.objects.get_or_create(
                    user=user,
                    defaults={
                        'role_id': 6,  # Parent role
                        'login_id': admission_id,
                        'custom_password': child_name,
                        'phone': parent.phone or '',
                    }
                )
                
                return user
        except (Student.DoesNotExist, Parent.DoesNotExist):
            pass
        return None
    
    def authenticate_teacher(self, mobile, name):
        """Authenticate teacher using mobile number and name"""
        try:
            # Find teacher by mobile number
            teacher = Teacher.objects.get(phone=mobile)
            
            # Check if name matches (case insensitive)
            if name.lower() == teacher.name.lower():
                # Get or create Django user for teacher
                user, created = User.objects.get_or_create(
                    username=f"teacher_{mobile}",
                    defaults={
                        'first_name': teacher.name,
                        'last_name': '',
                        'email': teacher.email or '',
                        'is_active': True,
                    }
                )
                
                # Create or update school user profile
                school_user, created = SchoolUser.objects.get_or_create(
                    user=user,
                    defaults={
                        'role_id': 3,  # Teacher role
                        'login_id': mobile,
                        'custom_password': name,
                        'phone': mobile,
                    }
                )
                
                return user
        except Teacher.DoesNotExist:
            pass
        return None
    
    def authenticate_standard(self, username, password):
        """Standard Django authentication"""
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


def create_default_roles():
    """Create default user roles if they don't exist"""
    from .models import UserRole
    
    default_roles = [
        {
            'name': 'super_admin',
            'display_name': 'Super Admin',
            'description': 'Full system access',
            'permissions': ['all']
        },
        {
            'name': 'school_admin',
            'display_name': 'School Admin',
            'description': 'School administration access',
            'permissions': ['manage_users', 'manage_students', 'manage_teachers', 'manage_fees', 'view_reports']
        },
        {
            'name': 'teacher',
            'display_name': 'Teacher',
            'description': 'Teacher access',
            'permissions': ['manage_attendance', 'manage_marks', 'view_students', 'create_question_papers']
        },
        {
            'name': 'librarian',
            'display_name': 'Librarian',
            'description': 'Library management access',
            'permissions': ['manage_books', 'manage_issues', 'view_library_reports']
        },
        {
            'name': 'accountant',
            'display_name': 'Accountant',
            'description': 'Financial management access',
            'permissions': ['manage_fees', 'view_financial_reports', 'manage_receipts']
        },
        {
            'name': 'parent',
            'display_name': 'Parent',
            'description': 'Parent portal access',
            'permissions': ['view_child_progress', 'view_attendance', 'view_fees']
        },
        {
            'name': 'student',
            'display_name': 'Student',
            'description': 'Student portal access',
            'permissions': ['view_own_data', 'view_attendance', 'view_marks']
        }
    ]
    
    for role_data in default_roles:
        UserRole.objects.get_or_create(
            name=role_data['name'],
            defaults=role_data
        )
