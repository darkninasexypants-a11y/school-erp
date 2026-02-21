"""
Auto User Creation Signals
Creates login accounts automatically when Student/Teacher/Staff are created
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Student, Teacher, Staff, Parent, SchoolUser, UserRole
import string
import random


def generate_password(length=8):
    """Generate random password"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


@receiver(post_save, sender=Student)
def create_student_user(sender, instance, created, **kwargs):
    """
    Auto-create User account when Student is created
    Username format: Admission Number
    Password format: DOB (DDMMYYYY) or default
    """
    if created:
        try:
            # Check if user already exists for this student
            # Since Student doesn't have a user field, we check by username (admission_number)
            username = instance.admission_number
            
            if User.objects.filter(username=username).exists():
                return
            
            # Generate password from DOB in DDMMYYYY format (same as parent will use)
            if instance.date_of_birth:
                dob = instance.date_of_birth
                password = f"{dob.day:02d}{dob.month:02d}{dob.year}"
            else:
                password = 'student123'  # Fallback if DOB not set
            
            # Create Django User
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=instance.first_name,
                last_name=instance.last_name,
                email=instance.email or f"{username}@school.com"
            )
            
            # Get or create student role
            student_role, _ = UserRole.objects.get_or_create(
                name='student',
                defaults={'description': 'Student role with limited access'}
            )
            
            # Get school (Student has foreign key to Class, which doesn't directly link to School in some models, 
            # but usually there's a way. Based on previous inspection, Student DOES NOT have a direct school field?
            # Let's check the model again. 
            # Wait, I checked Student model and it DOES NOT have a 'school' field in the lines I saw.
            # But 'Class' might. Let's assume for now we might need to fetch it or leave it None if not directly available.
            # However, the sync script used 'School.objects.first()'. 
            # If Student has no school field, we can't easily assign it unless we infer it.
            # For now, let's try to find a school if possible, or leave it blank.
            # actually, usually systems have a school field. 
            # Let's look at Class model.
            
            school = None
            if hasattr(instance, 'school'):
                school = instance.school
            elif hasattr(instance, 'current_class') and instance.current_class and hasattr(instance.current_class, 'school'):
                school = instance.current_class.school
            
            # If we still don't have a school, and there's only one school in DB, use it.
            if not school:
                from .models import School
                if School.objects.count() == 1:
                    school = School.objects.first()

            # Create SchoolUser profile
            SchoolUser.objects.create(
                user=user,
                school=school,
                role=student_role,
                login_id=username,
                custom_password=password,
                phone=instance.phone,
                is_active=True
            )
            
            print(f"✅ Auto-created user for Student: {username}")
            
        except Exception as e:
            print(f"❌ Error creating user for student {instance.admission_number}: {e}")


@receiver(post_save, sender=Teacher)
def create_teacher_user(sender, instance, created, **kwargs):
    """
    Auto-create SchoolUser profile when Teacher is created
    Teacher already has a OneToOne to User, so we just need SchoolUser.
    """
    if created:
        try:
            user = instance.user
            
            # Check if SchoolUser already exists
            if SchoolUser.objects.filter(user=user).exists():
                return
            
            # Get or create teacher role
            teacher_role, _ = UserRole.objects.get_or_create(
                name='teacher',
                defaults={'description': 'Teacher role with teaching access'}
            )
            
            # Determine School
            school = None
            # Teacher doesn't have a direct school field in the lines I saw, 
            # but let's check if we can find it.
            # If not, we might default to the first school or leave None.
            if hasattr(instance, 'school'):
                school = instance.school
            
            if not school:
                from .models import School
                if School.objects.count() == 1:
                    school = School.objects.first()

            # Generate password: Teacher@{EMPLOYEE_ID}
            password = f"Teacher@{instance.employee_id}"
            
            # Update user password if it's the default one
            if not user.has_usable_password() or user.check_password('teacher123'):
                user.set_password(password)
                user.save()
            
            # Create SchoolUser profile
            SchoolUser.objects.create(
                user=user,
                school=school,
                role=teacher_role,
                login_id=instance.phone, # Use phone as login ID
                custom_password=password, # Teacher@{EMPLOYEE_ID}
                phone=instance.phone,
                is_active=True
            )
            
            print(f"✅ Auto-created SchoolUser for Teacher: {user.username}")
            
        except Exception as e:
            print(f"❌ Error creating SchoolUser for teacher: {e}")


@receiver(post_save, sender=Staff)
def create_staff_user(sender, instance, created, **kwargs):
    """
    Auto-create User account and SchoolUser profile when Staff is created
    Username format: STF_{SCHOOL_CODE}_{EMPLOYEE_ID}
    Password format: Staff@{EMPLOYEE_ID}
    """
    if created:
        try:
            # Check if user already exists
            user = None
            if hasattr(instance, 'user') and instance.user:
                user = instance.user
            else:
                # Generate username and password
                emp_id = getattr(instance, 'employee_id', None) or f"S{instance.id}"
                
                # Get school code
                school = None
                if hasattr(instance, 'school') and instance.school:
                    school = instance.school
                else:
                    from .models import School
                    if School.objects.count() == 1:
                        school = School.objects.first()
                
                school_code = school.school_code if school and hasattr(school, 'school_code') else 'SCH'
                username = f"STF_{school_code}_{emp_id}"
                
                # Check if username already exists
                if User.objects.filter(username=username).exists():
                    username = f"{username}_{generate_password(4)}"
                
                # Generate password
                password = f"Staff@{emp_id}"
                
                # Get staff name
                first_name = getattr(instance, 'first_name', '') or getattr(instance, 'name', '').split()[0] if hasattr(instance, 'name') and instance.name else ''
                last_name = getattr(instance, 'last_name', '') or ' '.join(getattr(instance, 'name', '').split()[1:]) if hasattr(instance, 'name') and len(instance.name.split()) > 1 else ''
                email = getattr(instance, 'email', '') or f"{username}@school.com"
                
                # Create Django User
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )
                
                # Link user to staff if field exists
                if hasattr(instance, 'user'):
                    instance.user = user
                    instance.save(update_fields=['user'])
                
                print(f"✅ Auto-created User for Staff: {username} / {password}")
            
            # Check if SchoolUser already exists
            if SchoolUser.objects.filter(user=user).exists():
                return
            
            # Get or create staff role
            staff_role, _ = UserRole.objects.get_or_create(
                name='staff',
                defaults={'description': 'Staff role'}
            )
            
            # Get school if not already set
            if not school:
                if hasattr(instance, 'school') and instance.school:
                    school = instance.school
                else:
                    from .models import School
                    if School.objects.count() == 1:
                        school = School.objects.first()
            
            # Generate password for SchoolUser
            emp_id = getattr(instance, 'employee_id', None) or f"S{instance.id}"
            staff_password = f"Staff@{emp_id}"
            
            # Create SchoolUser profile
            SchoolUser.objects.create(
                user=user,
                school=school,
                role=staff_role,
                staff=instance,
                login_id=getattr(instance, 'phone', '') or user.username,
                custom_password=staff_password,
                phone=getattr(instance, 'phone', ''),
                is_active=True
            )
            
            print(f"✅ Auto-created SchoolUser for Staff: {user.username}")
            
        except Exception as e:
            print(f"❌ Error creating user for staff {getattr(instance, 'employee_id', instance.id)}: {e}")
            import traceback
            traceback.print_exc()


@receiver(post_save, sender=Parent)
def create_parent_user(sender, instance, created, **kwargs):
    """
    Auto-create User account and SchoolUser profile when Parent is created
    Password format: Child's DOB (DDMMYYYY) - same as student password
    """
    if created:
        try:
            # Check if user already exists
            user = None
            if hasattr(instance, 'user') and instance.user:
                user = instance.user
            else:
                # Get first child's admission number for username
                first_child = instance.students.first()
                if not first_child:
                    print(f"⚠️  Parent {instance.user.get_full_name() if hasattr(instance, 'user') else 'Unknown'} has no children. Cannot create user.")
                    return
                
                # Use child's admission number as username
                username = f"parent_{first_child.admission_number}"
                
                # Check if username already exists
                if User.objects.filter(username=username).exists():
                    username = f"{username}_{generate_password(4)}"
                
                # Generate password from child's DOB in DDMMYYYY format (same as student password)
                if first_child.date_of_birth:
                    dob = first_child.date_of_birth
                    password = f"{dob.day:02d}{dob.month:02d}{dob.year}"
                else:
                    password = 'parent123'  # Fallback if DOB not set
                
                # Get parent name from user if exists, otherwise from student
                first_name = instance.user.first_name if hasattr(instance, 'user') and instance.user else first_child.father_name.split()[0] if first_child.father_name else 'Parent'
                last_name = instance.user.last_name if hasattr(instance, 'user') and instance.user else ' '.join(first_child.father_name.split()[1:]) if first_child.father_name and len(first_child.father_name.split()) > 1 else ''
                email = instance.user.email if hasattr(instance, 'user') and instance.user else first_child.father_email or f"{username}@school.com"
                
                # Create Django User
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )
                
                # Link user to parent if field exists
                if hasattr(instance, 'user'):
                    instance.user = user
                    instance.save(update_fields=['user'])
                
                print(f"✅ Auto-created User for Parent: {username} / {password} (Child DOB)")
            
            # Check if SchoolUser already exists
            if SchoolUser.objects.filter(user=user).exists():
                return
            
            # Get or create parent role
            parent_role, _ = UserRole.objects.get_or_create(
                name='parent',
                defaults={'description': 'Parent role with child access'}
            )
            
            # Get school from first child
            school = None
            first_child = instance.students.first()
            if first_child:
                if hasattr(first_child, 'school') and first_child.school:
                    school = first_child.school
                elif hasattr(first_child, 'current_class') and first_child.current_class and hasattr(first_child.current_class, 'school'):
                    school = first_child.current_class.school
            
            if not school:
                from .models import School
                if School.objects.count() == 1:
                    school = School.objects.first()
            
            # Get password from first child's DOB in DDMMYYYY format (same as student password)
            if first_child and first_child.date_of_birth:
                dob = first_child.date_of_birth
                password = f"{dob.day:02d}{dob.month:02d}{dob.year}"
            else:
                password = 'parent123'  # Fallback if DOB not set
            
            # Create SchoolUser profile
            SchoolUser.objects.create(
                user=user,
                school=school,
                role=parent_role,
                login_id=first_child.admission_number if first_child else instance.phone,
                custom_password=password,
                phone=instance.phone,
                is_active=True
            )
            
            print(f"✅ Auto-created SchoolUser for Parent: {user.username} with password: {password} (Child DOB)")
            
        except Exception as e:
            print(f"❌ Error creating user for parent: {e}")
            import traceback
            traceback.print_exc()

