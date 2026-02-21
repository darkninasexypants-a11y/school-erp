#!/usr/bin/env python
"""
LEVEL 3: SCHOOL-SPECIFIC DELETION
Delete all data for a specific school
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
from students_app.models import School, SchoolUser, Student, Teacher, Staff, Parent

def delete_school_data():
    print("=" * 80)
    print("🏫 LEVEL 3: SCHOOL-SPECIFIC DELETION")
    print("=" * 80)
    
    # Show available schools
    schools = School.objects.all()
    if not schools.exists():
        print("No schools found in database!")
        return
    
    print("\nAvailable schools:")
    school_list = list(schools)
    for i, school in enumerate(school_list, 1):
        user_count = SchoolUser.objects.filter(school=school).count()
        print(f"{i}. {school.name} (ID: {school.id}) - {user_count} users")
    
    choice = input(f"\nEnter school number to delete (1-{len(school_list)}): ").strip()
    
    try:
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(school_list):
            print("Invalid school number!")
            return
        
        selected_school = school_list[choice_idx]
        confirm_school_deletion(selected_school)
        
    except ValueError:
        print("Invalid input!")

def confirm_school_deletion(school):
    """Confirm and delete school data"""
    print(f"\n--- Deleting School: {school.name} ---")
    
    # Get comprehensive data counts
    data_summary = get_school_data_summary(school)
    
    print(f"\nData to be deleted for {school.name}:")
    print("=" * 50)
    for category, count in data_summary.items():
        print(f"• {category}: {count}")
    
    total_records = sum(data_summary.values())
    print(f"\nTotal records to delete: {total_records}")
    
    # Warning about superusers
    superusers_in_school = User.objects.filter(
        school_profile__school=school, 
        is_superuser=True
    )
    if superusers_in_school.exists():
        print(f"\n⚠️  WARNING: {superusers_in_school.count()} superuser(s) in this school!")
        for su in superusers_in_school:
            print(f"   • {su.username} ({su.email})")
        print("   These will be PRESERVED (not deleted)")
    
    confirm = input(f"\n⚠️  Delete ALL data for '{school.name}'? (type school name to confirm): ").strip()
    
    if confirm != school.name:
        print("Confirmation failed. Operation cancelled.")
        return
    
    try:
        with transaction.atomic():
            deleted_records = execute_school_deletion(school)
            print(f"\n✅ Successfully deleted school '{school.name}'")
            print(f"Total records deleted: {deleted_records}")
            
    except Exception as e:
        print(f"\n❌ Error during deletion: {e}")
        import traceback
        traceback.print_exc()

def get_school_data_summary(school):
    """Get summary of all data for a school"""
    summary = {}
    
    try:
        # Users
        summary['SchoolUser profiles'] = SchoolUser.objects.filter(school=school).count()
        
        # Students
        students = Student.objects.filter(school=school)
        summary['Students'] = students.count()
        
        # Teachers
        teachers = Teacher.objects.filter(school=school)
        summary['Teachers'] = teachers.count()
        
        # Staff
        try:
            from students_app.models import Staff
            staff = Staff.objects.filter(school=school)
            summary['Staff'] = staff.count()
        except:
            summary['Staff'] = 0
        
        # Parents (linked through students)
        parent_ids = set()
        for student in students:
            if student.father_id:
                parent_ids.add(student.father_id)
            if student.mother_id:
                parent_ids.add(student.mother_id)
        summary['Parents'] = len(parent_ids)
        
        # Academic Structure
        try:
            from students_app.models import Class, Section, AcademicYear
            summary['Classes'] = Class.objects.filter(school=school).count()
            summary['Sections'] = Section.objects.filter(school=school).count()
            summary['Academic Years'] = AcademicYear.objects.filter(school=school).count()
        except:
            summary['Classes'] = 0
            summary['Sections'] = 0
            summary['Academic Years'] = 0
        
        # Attendance
        try:
            from students_app.models import Attendance, TeacherAttendance, StaffAttendance
            student_ids = students.values_list('id', flat=True)
            teacher_ids = teachers.values_list('id', flat=True)
            
            summary['Student Attendance'] = Attendance.objects.filter(student_id__in=student_ids).count()
            summary['Teacher Attendance'] = TeacherAttendance.objects.filter(teacher_id__in=teacher_ids).count()
            summary['Staff Attendance'] = StaffAttendance.objects.filter(school=school).count()
        except:
            summary['Student Attendance'] = 0
            summary['Teacher Attendance'] = 0
            summary['Staff Attendance'] = 0
        
        # Fees
        try:
            from students_app.models import FeePayment, FeeStructure, StudentFeeConcession
            summary['Fee Payments'] = FeePayment.objects.filter(student__school=school).count()
            summary['Fee Structures'] = FeeStructure.objects.filter(school=school).count()
            summary['Fee Concessions'] = StudentFeeConcession.objects.filter(student__school=school).count()
        except:
            summary['Fee Payments'] = 0
            summary['Fee Structures'] = 0
            summary['Fee Concessions'] = 0
        
        # Exams
        try:
            from students_app.models import Exam, ExamSchedule, Marks, ClassTest
            summary['Exams'] = Exam.objects.filter(school=school).count()
            summary['Exam Schedules'] = ExamSchedule.objects.filter(exam__school=school).count()
            summary['Marks'] = Marks.objects.filter(student__school=school).count()
            summary['Class Tests'] = ClassTest.objects.filter(school=school).count()
        except:
            summary['Exams'] = 0
            summary['Exam Schedules'] = 0
            summary['Marks'] = 0
            summary['Class Tests'] = 0
        
        # Library
        try:
            from students_app.models import BookIssue, BookRequest
            summary['Book Issues'] = BookIssue.objects.filter(student__school=school).count()
            summary['Book Requests'] = BookRequest.objects.filter(student__school=school).count()
        except:
            summary['Book Issues'] = 0
            summary['Book Requests'] = 0
        
        # Other modules
        try:
            from students_app.models import Notice, Announcement, Event, Homework, Timetable
            summary['Notices'] = Notice.objects.filter(school=school).count()
            summary['Announcements'] = Announcement.objects.filter(school=school).count()
            summary['Events'] = Event.objects.filter(school=school).count()
            summary['Homework'] = Homework.objects.filter(school=school).count()
            summary['Timetables'] = Timetable.objects.filter(school=school).count()
        except:
            summary['Notices'] = 0
            summary['Announcements'] = 0
            summary['Events'] = 0
            summary['Homework'] = 0
            summary['Timetables'] = 0
        
    except Exception as e:
        print(f"Error getting data summary: {e}")
    
    return summary

def execute_school_deletion(school):
    """Execute the actual deletion of school data"""
    deleted_count = 0
    
    try:
        # Get IDs before deletion
        students = Student.objects.filter(school=school)
        teachers = Teacher.objects.filter(school=school)
        student_ids = students.values_list('id', flat=True)
        teacher_ids = teachers.values_list('id', flat=True)
        
        print("Deleting school data in order of dependencies...")
        
        # Delete student-related data
        print("  • Deleting student records...")
        deleted_count += students.count()
        students.delete()
        
        # Delete teacher-related data
        print("  • Deleting teacher records...")
        deleted_count += teachers.count()
        teachers.delete()
        
        # Delete staff (if exists)
        try:
            from students_app.models import Staff
            staff = Staff.objects.filter(school=school)
            deleted_count += staff.count()
            staff.delete()
            print("  • Deleting staff records...")
        except:
            pass
        
        # Delete academic structure
        try:
            from students_app.models import Section, Class, AcademicYear
            sections = Section.objects.filter(school=school)
            classes = Class.objects.filter(school=school)
            academic_years = AcademicYear.objects.filter(school=school)
            
            deleted_count += sections.count()
            sections.delete()
            print("  • Deleting sections...")
            
            deleted_count += classes.count()
            classes.delete()
            print("  • Deleting classes...")
            
            deleted_count += academic_years.count()
            academic_years.delete()
            print("  • Deleting academic years...")
        except:
            pass
        
        # Delete school-specific data
        try:
            from students_app.models import (
                FeeStructure, Notice, Announcement, Event, 
                Timetable, Exam
            )
            
            for model in [FeeStructure, Notice, Announcement, Event, Timetable, Exam]:
                try:
                    records = model.objects.filter(school=school)
                    deleted_count += records.count()
                    records.delete()
                    print(f"  • Deleting {model.__name__} records...")
                except:
                    pass
        except:
            pass
        
        # Delete SchoolUser profiles (but preserve superusers)
        schoolusers = SchoolUser.objects.filter(school=school)
        superuser_ids = list(User.objects.filter(
            id__in=schoolusers.values('user_id'),
            is_superuser=True
        ).values_list('id', flat=True))
        
        regular_schoolusers = schoolusers.exclude(user_id__in=superuser_ids)
        deleted_count += regular_schoolusers.count()
        regular_schoolusers.delete()
        print("  • Deleting SchoolUser profiles...")
        
        # Delete associated users (but preserve superusers)
        user_ids_to_delete = SchoolUser.objects.filter(
            school=school
        ).exclude(user_id__in=superuser_ids).values_list('user_id', flat=True)
        
        if user_ids_to_delete:
            users_deleted = User.objects.filter(id__in=user_ids_to_delete).count()
            deleted_count += users_deleted
            User.objects.filter(id__in=user_ids_to_delete).delete()
            print("  • Deleting associated user accounts...")
        
        # Finally delete the school
        deleted_count += 1
        school.delete()
        print("  • Deleting school record...")
        
    except Exception as e:
        print(f"Error during deletion: {e}")
        raise
    
    return deleted_count

if __name__ == '__main__':
    delete_school_data()
