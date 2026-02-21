#!/usr/bin/env python
"""
LEVEL 5: COMPLETE DATA RESET
Delete ALL school data (enhanced version of delete_all_data.py)
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
from students_app.models import *

def complete_data_reset():
    print("=" * 80)
    print("💥 LEVEL 5: COMPLETE DATA RESET")
    print("=" * 80)
    print("\n⚠️  WARNING: This will delete ALL school data!")
    print("   • All schools, users (except superusers)")
    print("   • All academic data, fees, exams, etc.")
    print("   • All modules: library, transport, hostel, etc.")
    print("\n✅ WILL BE PRESERVED:")
    print("   • Superuser accounts")
    print("   • Database structure")
    print("   • System configurations")
    
    # Show current superusers
    superusers = User.objects.filter(is_superuser=True)
    print(f"\nSuperusers that will be PRESERVED ({superusers.count()}):")
    for su in superusers:
        print(f"  ✅ {su.username} ({su.email})")
    
    # Show current data summary
    print(f"\nCurrent data summary:")
    print("=" * 50)
    summary = get_complete_data_summary()
    for category, count in summary.items():
        print(f"• {category}: {count}")
    
    total_records = sum(summary.values())
    print(f"\nTotal records to delete: {total_records}")
    
    # Double confirmation
    print("\n" + "=" * 80)
    print("🚨 FINAL CONFIRMATION REQUIRED")
    print("=" * 80)
    
    confirm1 = input("Type 'DELETE ALL' to proceed: ").strip()
    if confirm1 != 'DELETE ALL':
        print("❌ Operation cancelled.")
        return
    
    confirm2 = input("Type 'I UNDERSTAND' to confirm you understand this will delete everything: ").strip()
    if confirm2 != 'I UNDERSTAND':
        print("❌ Operation cancelled.")
        return
    
    try:
        with transaction.atomic():
            deleted_records = execute_complete_reset()
            print(f"\n✅ COMPLETE RESET SUCCESSFUL!")
            print(f"Total records deleted: {deleted_records}")
            print("\n🎯 System is now ready for fresh data!")
            
    except Exception as e:
        print(f"\n❌ Error during reset: {e}")
        import traceback
        traceback.print_exc()

def get_complete_data_summary():
    """Get summary of all data in the system"""
    summary = {}
    
    try:
        # Schools
        summary['Schools'] = School.objects.count()
        
        # Users
        summary['Total Users'] = User.objects.count()
        summary['Non-Superusers'] = User.objects.filter(is_superuser=False).count()
        summary['SchoolUser profiles'] = SchoolUser.objects.count()
        
        # User Types
        summary['Students'] = Student.objects.count()
        summary['Teachers'] = Teacher.objects.count()
        
        try:
            summary['Staff'] = Staff.objects.count()
        except:
            summary['Staff'] = 0
        
        try:
            summary['Parents'] = Parent.objects.count()
        except:
            summary['Parents'] = 0
        
        # Academic Structure
        summary['Academic Years'] = AcademicYear.objects.count()
        summary['Classes'] = Class.objects.count()
        summary['Sections'] = Section.objects.count()
        summary['Subjects'] = Subject.objects.count()
        
        # Attendance
        try:
            summary['Student Attendance'] = Attendance.objects.count()
            summary['Teacher Attendance'] = TeacherAttendance.objects.count()
            summary['Staff Attendance'] = StaffAttendance.objects.count()
        except:
            summary['Student Attendance'] = 0
            summary['Teacher Attendance'] = 0
            summary['Staff Attendance'] = 0
        
        # Fees
        try:
            summary['Fee Structures'] = FeeStructure.objects.count()
            summary['Fee Payments'] = FeePayment.objects.count()
            summary['Fee Concessions'] = FeeConcession.objects.count()
            summary['Student Fee Concessions'] = StudentFeeConcession.objects.count()
            summary['Fee Notifications'] = FeeNotification.objects.count()
            summary['Fee Reconciliations'] = FeeReconciliation.objects.count()
        except:
            summary['Fee Structures'] = 0
            summary['Fee Payments'] = 0
            summary['Fee Concessions'] = 0
            summary['Student Fee Concessions'] = 0
            summary['Fee Notifications'] = 0
            summary['Fee Reconciliations'] = 0
        
        # Exams
        try:
            summary['Exams'] = Exam.objects.count()
            summary['Exam Schedules'] = ExamSchedule.objects.count()
            summary['Marks'] = Marks.objects.count()
            summary['Class Tests'] = ClassTest.objects.count()
            summary['Class Test Scores'] = ClassTestScore.objects.count()
            summary['Question Papers'] = QuestionPaper.objects.count()
        except:
            summary['Exams'] = 0
            summary['Exam Schedules'] = 0
            summary['Marks'] = 0
            summary['Class Tests'] = 0
            summary['Class Test Scores'] = 0
            summary['Question Papers'] = 0
        
        # Timetable
        try:
            summary['Time Slots'] = TimeSlot.objects.count()
            summary['Timetables'] = Timetable.objects.count()
            summary['Timetable Change Requests'] = TimetableChangeRequest.objects.count()
            summary['Class Teachers'] = ClassTeacher.objects.count()
        except:
            summary['Time Slots'] = 0
            summary['Timetables'] = 0
            summary['Timetable Change Requests'] = 0
            summary['Class Teachers'] = 0
        
        # Library
        try:
            summary['Books'] = Book.objects.count()
            summary['Book Categories'] = BookCategory.objects.count()
            summary['Book Issues'] = BookIssue.objects.count()
            summary['Book Requests'] = BookRequest.objects.count()
        except:
            summary['Books'] = 0
            summary['Book Categories'] = 0
            summary['Book Issues'] = 0
            summary['Book Requests'] = 0
        
        # ID Cards
        try:
            summary['ID Card Templates'] = IDCardTemplate.objects.count()
            summary['Student ID Cards'] = StudentIDCard.objects.count()
            summary['Staff ID Cards'] = StaffIDCard.objects.count()
        except:
            summary['ID Card Templates'] = 0
            summary['Student ID Cards'] = 0
            summary['Staff ID Cards'] = 0
        
        # Notices & Events
        try:
            summary['Notices'] = Notice.objects.count()
            summary['Announcements'] = Announcement.objects.count()
            summary['Events'] = Event.objects.count()
        except:
            summary['Notices'] = 0
            summary['Announcements'] = 0
            summary['Events'] = 0
        
        # Other modules
        try:
            summary['Inventory Items'] = InventoryItem.objects.count()
            summary['Homework'] = Homework.objects.count()
            summary['Homework Submissions'] = HomeworkSubmission.objects.count()
            summary['Transport Routes'] = TransportRoute.objects.count()
            summary['Buses'] = Bus.objects.count()
            summary['Leave Applications'] = LeaveApplication.objects.count()
            summary['Certificates'] = Certificate.objects.count()
            summary['Health Checkups'] = HealthCheckup.objects.count()
            summary['Hostels'] = Hostel.objects.count()
            summary['Canteen Items'] = CanteenItem.objects.count()
        except:
            summary['Inventory Items'] = 0
            summary['Homework'] = 0
            summary['Homework Submissions'] = 0
            summary['Transport Routes'] = 0
            summary['Buses'] = 0
            summary['Leave Applications'] = 0
            summary['Certificates'] = 0
            summary['Health Checkups'] = 0
            summary['Hostels'] = 0
            summary['Canteen Items'] = 0
        
    except Exception as e:
        print(f"Error getting data summary: {e}")
    
    return summary

def execute_complete_reset():
    """Execute complete data reset"""
    deleted_count = 0
    
    try:
        print("Executing complete data reset...")
        print("This may take a few minutes...")
        
        # Import all models to ensure they're available
        model_classes = [
            # Student-related data
            HomeworkSubmission, ClassTestScore, Marks, StudentIDCard, Attendance,
            BookIssue, BookRequest, FeePayment, StudentFeeConcession, StudentTransport,
            MedicalRecord, HealthCheckup, SportsRegistration, ActivityRegistration,
            StudentLeadership, StudentGameAchievement,
            
            # Teacher-related data
            TeacherAttendance, StaffAttendance, TimetableChangeRequest, ClassTeacher,
            Timetable, Homework, ClassTest, QuestionPaper,
            
            # Academic structure
            ExamSchedule, Exam, OnlineExamQuestion, OnlineExamAnswer, OnlineExamAttempt,
            MockTestQuestion, MockTestAnswer, MockTestSession, MockTestAttempt,
            Section, Class, AcademicYear, TimeSlot,
            
            # User profiles (delete before users)
            Student, Teacher, Staff, Parent, SchoolUser,
            
            # Schools and settings
            SchoolSettings, SchoolBilling, School,
            
            # Library
            Book, BookCategory,
            
            # Fees
            FeeStructure, FeeConcession, FeeNotification, FeeReconciliation,
            
            # ID Cards
            IDCardTemplate, StaffIDCard, IDCardGenerator, IDCardData,
            
            # Notices & Events
            Notice, Announcement, Event,
            
            # Other modules
            InventoryTransaction, InventoryItem, InventoryCategory,
            OrderItem, CanteenOrder, CanteenItem,
            HostelRoom, HostelAllocation, Hostel,
            Bus, TransportRoute,
            LeaveType, LeaveApplication,
            Salary, SalaryComponent,
            CertificateTemplate, Certificate,
            Alumni,
            Sport, SportsCategory, SportsAchievement,
            CoCurricularActivity, ActivityCategory,
            House, HouseMembership, HouseEvent, HouseEventResult,
            LeadershipPosition, Election, ElectionNomination, ElectionVote, ElectionResult,
            GameAchievement, GameSession, GameAnswer, GameQuestion,
            EducationalGame, GameCategory,
            MobileDevice, TeamMember, WorkEntry, WorkExpense,
            
            # Subjects
            Subject,
        ]
        
        # Delete in order (most dependent first)
        for model_class in model_classes:
            try:
                count = model_class.objects.count()
                if count > 0:
                    model_class.objects.all().delete()
                    deleted_count += count
                    print(f"  ✅ Deleted {count} {model_class.__name__} records")
            except Exception as e:
                print(f"  ⚠️  Skipped {model_class.__name__}: {e}")
        
        # Delete non-superuser users last
        non_superusers = User.objects.filter(is_superuser=False)
        user_count = non_superusers.count()
        if user_count > 0:
            non_superusers.delete()
            deleted_count += user_count
            print(f"  ✅ Deleted {user_count} non-superuser users")
        
        # Clear sessions
        try:
            from django.contrib.sessions.models import Session
            session_count = Session.objects.count()
            if session_count > 0:
                Session.objects.all().delete()
                deleted_count += session_count
                print(f"  ✅ Deleted {session_count} sessions")
        except:
            pass
        
    except Exception as e:
        print(f"Error during reset: {e}")
        raise
    
    return deleted_count

if __name__ == '__main__':
    complete_data_reset()
