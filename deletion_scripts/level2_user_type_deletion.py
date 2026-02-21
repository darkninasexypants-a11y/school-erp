#!/usr/bin/env python
"""
LEVEL 2: USER TYPE DELETION
Delete all users of specific type (Students, Teachers, Staff, Parents)
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from students_app.models import SchoolUser, Student, Teacher, Staff, Parent

def delete_user_type():
    print("=" * 80)
    print("👥 LEVEL 2: USER TYPE DELETION")
    print("=" * 80)
    print("\nSelect user type to delete:")
    print("1. All Students (and related data)")
    print("2. All Teachers (and related data)")
    print("3. All Staff (and related data)")
    print("4. All Parents (and related data)")
    print("5. All non-superuser users (complete cleanup)")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    type_map = {
        '1': ('Students', delete_all_students),
        '2': ('Teachers', delete_all_teachers),
        '3': ('Staff', delete_all_staff),
        '4': ('Parents', delete_all_parents),
        '5': ('All Non-Superusers', delete_all_non_superusers)
    }
    
    if choice not in type_map:
        print("Invalid choice!")
        return
    
    type_name, delete_function = type_map[choice]
    print(f"\n--- Deleting All {type_name} ---")
    delete_function()

def delete_all_students():
    """Delete all students and their related data"""
    try:
        from students_app.models import (
            Attendance, BookIssue, BookRequest, FeePayment, 
            StudentFeeConcession, StudentTransport, Marks,
            ClassTestScore, StudentIDCard, MedicalRecord,
            HomeworkSubmission, SportsRegistration, ActivityRegistration
        )
        
        # Count students
        student_count = Student.objects.count()
        print(f"Students to delete: {student_count}")
        
        if student_count == 0:
            print("No students found!")
            return
        
        # Show sample
        print("Sample students:")
        for student in Student.objects.all()[:5]:
            print(f"  • {student.get_full_name()} - {student.email or 'No email'}")
        if student_count > 5:
            print(f"  ... and {student_count - 5} more")
        
        confirm = input(f"\nDelete ALL {student_count} students and their data? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            deleted_count = 0
            
            # Delete student-related data first
            print("Deleting student-related data...")
            deleted_count += HomeworkSubmission.objects.all().count()
            HomeworkSubmission.objects.all().delete()
            
            deleted_count += ActivityRegistration.objects.all().count()
            ActivityRegistration.objects.all().delete()
            
            deleted_count += SportsRegistration.objects.all().count()
            SportsRegistration.objects.all().delete()
            
            deleted_count += MedicalRecord.objects.all().count()
            MedicalRecord.objects.all().delete()
            
            deleted_count += StudentIDCard.objects.all().count()
            StudentIDCard.objects.all().delete()
            
            deleted_count += ClassTestScore.objects.all().count()
            ClassTestScore.objects.all().delete()
            
            deleted_count += Marks.objects.all().count()
            Marks.objects.all().delete()
            
            deleted_count += StudentTransport.objects.all().count()
            StudentTransport.objects.all().delete()
            
            deleted_count += StudentFeeConcession.objects.all().count()
            StudentFeeConcession.objects.all().delete()
            
            deleted_count += FeePayment.objects.all().count()
            FeePayment.objects.all().delete()
            
            deleted_count += BookRequest.objects.all().count()
            BookRequest.objects.all().delete()
            
            deleted_count += BookIssue.objects.all().count()
            BookIssue.objects.all().delete()
            
            deleted_count += Attendance.objects.all().count()
            Attendance.objects.all().delete()
            
            # Delete students
            print("Deleting students...")
            students = Student.objects.all()
            student_user_ids = [s.user_id for s in students if s.user_id]
            deleted_count += students.count()
            students.delete()
            
            # Delete associated users
            if student_user_ids:
                User.objects.filter(id__in=student_user_ids).delete()
            
            print(f"✅ Successfully deleted {student_count} students and {deleted_count} related records")
            
    except Exception as e:
        print(f"❌ Error deleting students: {e}")

def delete_all_teachers():
    """Delete all teachers and their related data"""
    try:
        from students_app.models import (
            TeacherAttendance, ClassTeacher, Timetable, Homework,
            ClassTest, QuestionPaper
        )
        
        # Count teachers
        teacher_count = Teacher.objects.count()
        print(f"Teachers to delete: {teacher_count}")
        
        if teacher_count == 0:
            print("No teachers found!")
            return
        
        # Show sample
        print("Sample teachers:")
        for teacher in Teacher.objects.all()[:5]:
            print(f"  • {teacher.get_full_name()} - {teacher.employee_id}")
        if teacher_count > 5:
            print(f"  ... and {teacher_count - 5} more")
        
        confirm = input(f"\nDelete ALL {teacher_count} teachers and their data? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            deleted_count = 0
            
            # Delete teacher-related data first
            print("Deleting teacher-related data...")
            deleted_count += QuestionPaper.objects.all().count()
            QuestionPaper.objects.all().delete()
            
            deleted_count += ClassTest.objects.all().count()
            ClassTest.objects.all().delete()
            
            deleted_count += Homework.objects.all().count()
            Homework.objects.all().delete()
            
            deleted_count += Timetable.objects.all().count()
            Timetable.objects.all().delete()
            
            deleted_count += ClassTeacher.objects.all().count()
            ClassTeacher.objects.all().delete()
            
            deleted_count += TeacherAttendance.objects.all().count()
            TeacherAttendance.objects.all().delete()
            
            # Delete teachers
            print("Deleting teachers...")
            teachers = Teacher.objects.all()
            teacher_user_ids = [t.user_id for t in teachers if t.user_id]
            deleted_count += teachers.count()
            teachers.delete()
            
            # Delete associated users
            if teacher_user_ids:
                User.objects.filter(id__in=teacher_user_ids).delete()
            
            print(f"✅ Successfully deleted {teacher_count} teachers and {deleted_count} related records")
            
    except Exception as e:
        print(f"❌ Error deleting teachers: {e}")

def delete_all_staff():
    """Delete all staff and their related data"""
    try:
        from students_app.models import StaffAttendance, LeaveApplication
        
        # Count staff
        staff_count = Staff.objects.count()
        print(f"Staff to delete: {staff_count}")
        
        if staff_count == 0:
            print("No staff found!")
            return
        
        # Show sample
        print("Sample staff:")
        for staff in Staff.objects.all()[:5]:
            print(f"  • {staff.get_full_name()} - {staff.employee_id}")
        if staff_count > 5:
            print(f"  ... and {staff_count - 5} more")
        
        confirm = input(f"\nDelete ALL {staff_count} staff and their data? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            deleted_count = 0
            
            # Delete staff-related data first
            print("Deleting staff-related data...")
            deleted_count += LeaveApplication.objects.all().count()
            LeaveApplication.objects.all().delete()
            
            deleted_count += StaffAttendance.objects.all().count()
            StaffAttendance.objects.all().delete()
            
            # Delete staff
            print("Deleting staff...")
            staff_members = Staff.objects.all()
            staff_user_ids = [s.user_id for s in staff_members if s.user_id]
            deleted_count += staff_members.count()
            staff_members.delete()
            
            # Delete associated users
            if staff_user_ids:
                User.objects.filter(id__in=staff_user_ids).delete()
            
            print(f"✅ Successfully deleted {staff_count} staff and {deleted_count} related records")
            
    except Exception as e:
        print(f"❌ Error deleting staff: {e}")

def delete_all_parents():
    """Delete all parents"""
    try:
        # Count parents
        parent_count = Parent.objects.count()
        print(f"Parents to delete: {parent_count}")
        
        if parent_count == 0:
            print("No parents found!")
            return
        
        # Show sample
        print("Sample parents:")
        for parent in Parent.objects.all()[:5]:
            print(f"  • {parent.get_full_name()} - {parent.email or 'No email'}")
        if parent_count > 5:
            print(f"  ... and {parent_count - 5} more")
        
        confirm = input(f"\nDelete ALL {parent_count} parents? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            # Delete parents
            print("Deleting parents...")
            parents = Parent.objects.all()
            parent_user_ids = [p.user_id for p in parents if p.user_id]
            parents.delete()
            
            # Delete associated users
            if parent_user_ids:
                User.objects.filter(id__in=parent_user_ids).delete()
            
            print(f"✅ Successfully deleted {parent_count} parents")
            
    except Exception as e:
        print(f"❌ Error deleting parents: {e}")

def delete_all_non_superusers():
    """Delete all non-superuser users"""
    try:
        # Count non-superusers
        non_superuser_count = User.objects.filter(is_superuser=False).count()
        print(f"Non-superuser users to delete: {non_superuser_count}")
        
        if non_superuser_count == 0:
            print("No non-superuser users found!")
            return
        
        # Show superusers that will be preserved
        superusers = User.objects.filter(is_superuser=True)
        print(f"\nSuperusers that will be PRESERVED: {superusers.count()}")
        for su in superusers:
            print(f"  ✅ {su.username} ({su.email})")
        
        # Show sample of users to be deleted
        print(f"\nSample users to be deleted:")
        for user in User.objects.filter(is_superuser=False)[:5]:
            print(f"  ❌ {user.username} ({user.email})")
        if non_superuser_count > 5:
            print(f"  ... and {non_superuser_count - 5} more")
        
        confirm = input(f"\nDelete ALL {non_superuser_count} non-superuser users? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            # Delete all non-superuser users
            deleted_count = User.objects.filter(is_superuser=False).count()
            User.objects.filter(is_superuser=False).delete()
            
            print(f"✅ Successfully deleted {deleted_count} non-superuser users")
            
    except Exception as e:
        print(f"❌ Error deleting non-superusers: {e}")

if __name__ == '__main__':
    delete_user_type()
