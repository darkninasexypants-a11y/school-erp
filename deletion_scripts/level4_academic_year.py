#!/usr/bin/env python
"""
LEVEL 4: ACADEMIC YEAR DELETION
Delete data for specific academic year
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
from students_app.models import AcademicYear, School, Class, Section

def delete_academic_year_data():
    print("=" * 80)
    print("🗓️ LEVEL 4: ACADEMIC YEAR DELETION")
    print("=" * 80)
    
    # Show available academic years
    academic_years = AcademicYear.objects.all()
    if not academic_years.exists():
        print("No academic years found in database!")
        return
    
    print("\nAvailable academic years:")
    year_list = list(academic_years)
    for i, year in enumerate(year_list, 1):
        print(f"{i}. {year.name} ({year.start_date} to {year.end_date}) - School: {year.school.name if year.school else 'None'}")
    
    choice = input(f"\nEnter academic year number to delete (1-{len(year_list)}): ").strip()
    
    try:
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(year_list):
            print("Invalid academic year number!")
            return
        
        selected_year = year_list[choice_idx]
        confirm_academic_year_deletion(selected_year)
        
    except ValueError:
        print("Invalid input!")

def confirm_academic_year_deletion(academic_year):
    """Confirm and delete academic year data"""
    print(f"\n--- Deleting Academic Year: {academic_year.name} ---")
    
    # Get comprehensive data counts
    data_summary = get_academic_year_data_summary(academic_year)
    
    print(f"\nData to be deleted for {academic_year.name}:")
    print("=" * 50)
    for category, count in data_summary.items():
        print(f"• {category}: {count}")
    
    total_records = sum(data_summary.values())
    print(f"\nTotal records to delete: {total_records}")
    
    if total_records == 0:
        print("No data found for this academic year.")
        return
    
    confirm = input(f"\n⚠️  Delete ALL data for academic year '{academic_year.name}'? (type year name to confirm): ").strip()
    
    if confirm != academic_year.name:
        print("Confirmation failed. Operation cancelled.")
        return
    
    try:
        with transaction.atomic():
            deleted_records = execute_academic_year_deletion(academic_year)
            print(f"\n✅ Successfully deleted academic year '{academic_year.name}'")
            print(f"Total records deleted: {deleted_records}")
            
    except Exception as e:
        print(f"\n❌ Error during deletion: {e}")
        import traceback
        traceback.print_exc()

def get_academic_year_data_summary(academic_year):
    """Get summary of all data for an academic year"""
    summary = {}
    
    try:
        # Classes and Sections
        classes = Class.objects.filter(academic_year=academic_year)
        sections = Section.objects.filter(academic_year=academic_year)
        
        summary['Classes'] = classes.count()
        summary['Sections'] = sections.count()
        
        # Get student IDs for this academic year
        student_ids = Student.objects.filter(
            current_class__academic_year=academic_year
        ).values_list('id', flat=True)
        
        summary['Students in this year'] = len(student_ids)
        
        # Attendance
        try:
            from students_app.models import Attendance
            summary['Student Attendance'] = Attendance.objects.filter(
                student_id__in=student_ids
            ).count()
        except:
            summary['Student Attendance'] = 0
        
        # Fees
        try:
            from students_app.models import FeePayment, StudentFeeConcession
            summary['Fee Payments'] = FeePayment.objects.filter(
                student__current_class__academic_year=academic_year
            ).count()
            summary['Fee Concessions'] = StudentFeeConcession.objects.filter(
                student__current_class__academic_year=academic_year
            ).count()
        except:
            summary['Fee Payments'] = 0
            summary['Fee Concessions'] = 0
        
        # Exams
        try:
            from students_app.models import Exam, ExamSchedule, Marks, ClassTest
            summary['Exams'] = Exam.objects.filter(academic_year=academic_year).count()
            summary['Exam Schedules'] = ExamSchedule.objects.filter(
                exam__academic_year=academic_year
            ).count()
            summary['Marks'] = Marks.objects.filter(
                student__current_class__academic_year=academic_year
            ).count()
            summary['Class Tests'] = ClassTest.objects.filter(
                academic_year=academic_year
            ).count()
        except:
            summary['Exams'] = 0
            summary['Exam Schedules'] = 0
            summary['Marks'] = 0
            summary['Class Tests'] = 0
        
        # Library
        try:
            from students_app.models import BookIssue, BookRequest
            summary['Book Issues'] = BookIssue.objects.filter(
                student__current_class__academic_year=academic_year
            ).count()
            summary['Book Requests'] = BookRequest.objects.filter(
                student__current_class__academic_year=academic_year
            ).count()
        except:
            summary['Book Issues'] = 0
            summary['Book Requests'] = 0
        
        # Other modules
        try:
            from students_app.models import Homework, Timetable
            summary['Homework'] = Homework.objects.filter(
                academic_year=academic_year
            ).count()
            summary['Timetables'] = Timetable.objects.filter(
                academic_year=academic_year
            ).count()
        except:
            summary['Homework'] = 0
            summary['Timetables'] = 0
        
        # ID Cards
        try:
            from students_app.models import StudentIDCard
            summary['Student ID Cards'] = StudentIDCard.objects.filter(
                student__current_class__academic_year=academic_year
            ).count()
        except:
            summary['Student ID Cards'] = 0
        
        # Medical Records
        try:
            from students_app.models import MedicalRecord
            summary['Medical Records'] = MedicalRecord.objects.filter(
                student__current_class__academic_year=academic_year
            ).count()
        except:
            summary['Medical Records'] = 0
        
        # Transport
        try:
            from students_app.models import StudentTransport
            summary['Student Transport'] = StudentTransport.objects.filter(
                student__current_class__academic_year=academic_year
            ).count()
        except:
            summary['Student Transport'] = 0
        
    except Exception as e:
        print(f"Error getting data summary: {e}")
    
    return summary

def execute_academic_year_deletion(academic_year):
    """Execute the actual deletion of academic year data"""
    deleted_count = 0
    
    try:
        # Get IDs before deletion
        classes = Class.objects.filter(academic_year=academic_year)
        sections = Section.objects.filter(academic_year=academic_year)
        student_ids = Student.objects.filter(
            current_class__academic_year=academic_year
        ).values_list('id', flat=True)
        
        print("Deleting academic year data in order of dependencies...")
        
        # Delete student-related data for this year
        if student_ids:
            print("  • Deleting student-related data...")
            
            try:
                from students_app.models import (
                    BookIssue, BookRequest, FeePayment, StudentFeeConcession,
                    Marks, StudentIDCard, MedicalRecord, StudentTransport
                )
                
                for model in [BookIssue, BookRequest, FeePayment, StudentFeeConcession,
                             Marks, StudentIDCard, MedicalRecord, StudentTransport]:
                    try:
                        records = model.objects.filter(student_id__in=student_ids)
                        deleted_count += records.count()
                        records.delete()
                        print(f"    - Deleted {model.__name__} records")
                    except:
                        pass
            except:
                pass
        
        # Delete class tests for this year
        try:
            from students_app.models import ClassTest
            class_tests = ClassTest.objects.filter(academic_year=academic_year)
            deleted_count += class_tests.count()
            class_tests.delete()
            print("  • Deleting class tests...")
        except:
            pass
        
        # Delete homework for this year
        try:
            from students_app.models import Homework, HomeworkSubmission
            homework = Homework.objects.filter(academic_year=academic_year)
            deleted_count += homework.count()
            homework.delete()
            print("  • Deleting homework...")
            
            # Also delete homework submissions for students in this year
            if student_ids:
                submissions = HomeworkSubmission.objects.filter(
                    student_id__in=student_ids
                )
                deleted_count += submissions.count()
                submissions.delete()
                print("  • Deleting homework submissions...")
        except:
            pass
        
        # Delete timetables for this year
        try:
            from students_app.models import Timetable
            timetables = Timetable.objects.filter(academic_year=academic_year)
            deleted_count += timetables.count()
            timetables.delete()
            print("  • Deleting timetables...")
        except:
            pass
        
        # Delete exams and related data for this year
        try:
            from students_app.models import Exam, ExamSchedule
            exams = Exam.objects.filter(academic_year=academic_year)
            deleted_count += exams.count()
            exams.delete()
            print("  • Deleting exams...")
            
            exam_schedules = ExamSchedule.objects.filter(
                exam__academic_year=academic_year
            )
            deleted_count += exam_schedules.count()
            exam_schedules.delete()
            print("  • Deleting exam schedules...")
        except:
            pass
        
        # Delete sections
        deleted_count += sections.count()
        sections.delete()
        print("  • Deleting sections...")
        
        # Delete classes
        deleted_count += classes.count()
        classes.delete()
        print("  • Deleting classes...")
        
        # Update students who were in this academic year
        if student_ids:
            students_updated = Student.objects.filter(
                id__in=student_ids
            ).update(current_class=None, section=None)
            print(f"  • Updated {students_updated} students (removed class/section references)")
        
        # Finally delete the academic year
        deleted_count += 1
        academic_year.delete()
        print("  • Deleting academic year record...")
        
    except Exception as e:
        print(f"Error during deletion: {e}")
        raise
    
    return deleted_count

if __name__ == '__main__':
    delete_academic_year_data()
