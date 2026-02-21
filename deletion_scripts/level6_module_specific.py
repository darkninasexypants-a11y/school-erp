#!/usr/bin/env python
"""
LEVEL 6: MODULE-SPECIFIC DELETION
Delete specific module data only
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

def module_specific_deletion():
    print("=" * 80)
    print("🧹 LEVEL 6: MODULE-SPECIFIC DELETION")
    print("=" * 80)
    print("\nSelect module to delete:")
    print("1. Attendance Data (Student, Teacher, Staff)")
    print("2. Fee Data (Structures, Payments, Concessions)")
    print("3. Exam Data (Exams, Schedules, Marks, Tests)")
    print("4. Library Data (Books, Issues, Requests)")
    print("5. Timetable Data (Timetables, Time Slots, Change Requests)")
    print("6. ID Card Data (Templates, Generated Cards)")
    print("7. Notice & Event Data")
    print("8. Homework Data")
    print("9. Transport Data")
    print("10. Inventory Data")
    print("11. Hostel Data")
    print("12. Canteen Data")
    print("13. Medical & Health Data")
    print("14. Certificate Data")
    print("15. Sports & Activities Data")
    print("16. Election Data")
    print("17. All Academic Data (Exams + Attendance + Marks)")
    
    choice = input("\nEnter module number (1-17): ").strip()
    
    module_map = {
        '1': ('Attendance Data', delete_attendance_data),
        '2': ('Fee Data', delete_fee_data),
        '3': ('Exam Data', delete_exam_data),
        '4': ('Library Data', delete_library_data),
        '5': ('Timetable Data', delete_timetable_data),
        '6': ('ID Card Data', delete_idcard_data),
        '7': ('Notice & Event Data', delete_notice_event_data),
        '8': ('Homework Data', delete_homework_data),
        '9': ('Transport Data', delete_transport_data),
        '10': ('Inventory Data', delete_inventory_data),
        '11': ('Hostel Data', delete_hostel_data),
        '12': ('Canteen Data', delete_canteen_data),
        '13': ('Medical & Health Data', delete_medical_data),
        '14': ('Certificate Data', delete_certificate_data),
        '15': ('Sports & Activities Data', delete_sports_activities_data),
        '16': ('Election Data', delete_election_data),
        '17': ('All Academic Data', delete_all_academic_data)
    }
    
    if choice not in module_map:
        print("Invalid choice!")
        return
    
    module_name, delete_function = module_map[choice]
    print(f"\n--- Deleting {module_name} ---")
    delete_function()

def delete_attendance_data():
    """Delete all attendance data"""
    try:
        from students_app.models import Attendance, TeacherAttendance, StaffAttendance
        
        summary = {
            'Student Attendance': Attendance.objects.count(),
            'Teacher Attendance': TeacherAttendance.objects.count(),
            'Staff Attendance': StaffAttendance.objects.count()
        }
        
        print(f"\nAttendance data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No attendance data found!")
            return
        
        confirm = input(f"\nDelete all {total} attendance records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            Attendance.objects.all().delete()
            TeacherAttendance.objects.all().delete()
            StaffAttendance.objects.all().delete()
            print(f"✅ Successfully deleted {total} attendance records")
            
    except Exception as e:
        print(f"❌ Error deleting attendance data: {e}")

def delete_fee_data():
    """Delete all fee-related data"""
    try:
        from students_app.models import FeePayment, FeeStructure, FeeConcession, StudentFeeConcession, FeeNotification, FeeReconciliation
        
        summary = {
            'Fee Payments': FeePayment.objects.count(),
            'Fee Structures': FeeStructure.objects.count(),
            'Fee Concessions': FeeConcession.objects.count(),
            'Student Fee Concessions': StudentFeeConcession.objects.count(),
            'Fee Notifications': FeeNotification.objects.count(),
            'Fee Reconciliations': FeeReconciliation.objects.count()
        }
        
        print(f"\nFee data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No fee data found!")
            return
        
        confirm = input(f"\nDelete all {total} fee records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            FeePayment.objects.all().delete()
            StudentFeeConcession.objects.all().delete()
            FeeNotification.objects.all().delete()
            FeeReconciliation.objects.all().delete()
            FeeConcession.objects.all().delete()
            FeeStructure.objects.all().delete()
            print(f"✅ Successfully deleted {total} fee records")
            
    except Exception as e:
        print(f"❌ Error deleting fee data: {e}")

def delete_exam_data():
    """Delete all exam-related data"""
    try:
        from students_app.models import Exam, ExamSchedule, Marks, ClassTest, ClassTestScore, QuestionPaper
        
        summary = {
            'Exams': Exam.objects.count(),
            'Exam Schedules': ExamSchedule.objects.count(),
            'Marks': Marks.objects.count(),
            'Class Tests': ClassTest.objects.count(),
            'Class Test Scores': ClassTestScore.objects.count(),
            'Question Papers': QuestionPaper.objects.count()
        }
        
        print(f"\nExam data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No exam data found!")
            return
        
        confirm = input(f"\nDelete all {total} exam records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            ClassTestScore.objects.all().delete()
            Marks.objects.all().delete()
            QuestionPaper.objects.all().delete()
            ExamSchedule.objects.all().delete()
            ClassTest.objects.all().delete()
            Exam.objects.all().delete()
            print(f"✅ Successfully deleted {total} exam records")
            
    except Exception as e:
        print(f"❌ Error deleting exam data: {e}")

def delete_library_data():
    """Delete all library data"""
    try:
        from students_app.models import Book, BookCategory, BookIssue, BookRequest
        
        summary = {
            'Books': Book.objects.count(),
            'Book Categories': BookCategory.objects.count(),
            'Book Issues': BookIssue.objects.count(),
            'Book Requests': BookRequest.objects.count()
        }
        
        print(f"\nLibrary data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No library data found!")
            return
        
        confirm = input(f"\nDelete all {total} library records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            BookIssue.objects.all().delete()
            BookRequest.objects.all().delete()
            Book.objects.all().delete()
            BookCategory.objects.all().delete()
            print(f"✅ Successfully deleted {total} library records")
            
    except Exception as e:
        print(f"❌ Error deleting library data: {e}")

def delete_timetable_data():
    """Delete all timetable data"""
    try:
        from students_app.models import Timetable, TimeSlot, TimetableChangeRequest, ClassTeacher
        
        summary = {
            'Timetables': Timetable.objects.count(),
            'Time Slots': TimeSlot.objects.count(),
            'Timetable Change Requests': TimetableChangeRequest.objects.count(),
            'Class Teachers': ClassTeacher.objects.count()
        }
        
        print(f"\nTimetable data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No timetable data found!")
            return
        
        confirm = input(f"\nDelete all {total} timetable records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            TimetableChangeRequest.objects.all().delete()
            ClassTeacher.objects.all().delete()
            Timetable.objects.all().delete()
            TimeSlot.objects.all().delete()
            print(f"✅ Successfully deleted {total} timetable records")
            
    except Exception as e:
        print(f"❌ Error deleting timetable data: {e}")

def delete_idcard_data():
    """Delete all ID card data"""
    try:
        from students_app.models import IDCardTemplate, StudentIDCard, StaffIDCard, IDCardGenerator, IDCardData
        
        summary = {
            'ID Card Templates': IDCardTemplate.objects.count(),
            'Student ID Cards': StudentIDCard.objects.count(),
            'Staff ID Cards': StaffIDCard.objects.count(),
            'ID Card Generators': IDCardGenerator.objects.count(),
            'ID Card Data': IDCardData.objects.count()
        }
        
        print(f"\nID card data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No ID card data found!")
            return
        
        confirm = input(f"\nDelete all {total} ID card records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            StudentIDCard.objects.all().delete()
            StaffIDCard.objects.all().delete()
            IDCardData.objects.all().delete()
            IDCardGenerator.objects.all().delete()
            IDCardTemplate.objects.all().delete()
            print(f"✅ Successfully deleted {total} ID card records")
            
    except Exception as e:
        print(f"❌ Error deleting ID card data: {e}")

def delete_notice_event_data():
    """Delete all notice and event data"""
    try:
        from students_app.models import Notice, Announcement, Event
        
        summary = {
            'Notices': Notice.objects.count(),
            'Announcements': Announcement.objects.count(),
            'Events': Event.objects.count()
        }
        
        print(f"\nNotice & Event data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No notice/event data found!")
            return
        
        confirm = input(f"\nDelete all {total} notice/event records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            Notice.objects.all().delete()
            Announcement.objects.all().delete()
            Event.objects.all().delete()
            print(f"✅ Successfully deleted {total} notice/event records")
            
    except Exception as e:
        print(f"❌ Error deleting notice/event data: {e}")

def delete_homework_data():
    """Delete all homework data"""
    try:
        from students_app.models import Homework, HomeworkSubmission
        
        summary = {
            'Homework': Homework.objects.count(),
            'Homework Submissions': HomeworkSubmission.objects.count()
        }
        
        print(f"\nHomework data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No homework data found!")
            return
        
        confirm = input(f"\nDelete all {total} homework records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            HomeworkSubmission.objects.all().delete()
            Homework.objects.all().delete()
            print(f"✅ Successfully deleted {total} homework records")
            
    except Exception as e:
        print(f"❌ Error deleting homework data: {e}")

def delete_transport_data():
    """Delete all transport data"""
    try:
        from students_app.models import TransportRoute, Bus, StudentTransport
        
        summary = {
            'Transport Routes': TransportRoute.objects.count(),
            'Buses': Bus.objects.count(),
            'Student Transport': StudentTransport.objects.count()
        }
        
        print(f"\nTransport data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No transport data found!")
            return
        
        confirm = input(f"\nDelete all {total} transport records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            StudentTransport.objects.all().delete()
            Bus.objects.all().delete()
            TransportRoute.objects.all().delete()
            print(f"✅ Successfully deleted {total} transport records")
            
    except Exception as e:
        print(f"❌ Error deleting transport data: {e}")

def delete_inventory_data():
    """Delete all inventory data"""
    try:
        from students_app.models import InventoryItem, InventoryCategory, InventoryTransaction
        
        summary = {
            'Inventory Items': InventoryItem.objects.count(),
            'Inventory Categories': InventoryCategory.objects.count(),
            'Inventory Transactions': InventoryTransaction.objects.count()
        }
        
        print(f"\nInventory data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No inventory data found!")
            return
        
        confirm = input(f"\nDelete all {total} inventory records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            InventoryTransaction.objects.all().delete()
            InventoryItem.objects.all().delete()
            InventoryCategory.objects.all().delete()
            print(f"✅ Successfully deleted {total} inventory records")
            
    except Exception as e:
        print(f"❌ Error deleting inventory data: {e}")

def delete_hostel_data():
    """Delete all hostel data"""
    try:
        from students_app.models import Hostel, HostelRoom, HostelAllocation
        
        summary = {
            'Hostels': Hostel.objects.count(),
            'Hostel Rooms': HostelRoom.objects.count(),
            'Hostel Allocations': HostelAllocation.objects.count()
        }
        
        print(f"\nHostel data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No hostel data found!")
            return
        
        confirm = input(f"\nDelete all {total} hostel records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            HostelAllocation.objects.all().delete()
            HostelRoom.objects.all().delete()
            Hostel.objects.all().delete()
            print(f"✅ Successfully deleted {total} hostel records")
            
    except Exception as e:
        print(f"❌ Error deleting hostel data: {e}")

def delete_canteen_data():
    """Delete all canteen data"""
    try:
        from students_app.models import CanteenItem, CanteenOrder, OrderItem
        
        summary = {
            'Canteen Items': CanteenItem.objects.count(),
            'Canteen Orders': CanteenOrder.objects.count(),
            'Order Items': OrderItem.objects.count()
        }
        
        print(f"\nCanteen data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No canteen data found!")
            return
        
        confirm = input(f"\nDelete all {total} canteen records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            OrderItem.objects.all().delete()
            CanteenOrder.objects.all().delete()
            CanteenItem.objects.all().delete()
            print(f"✅ Successfully deleted {total} canteen records")
            
    except Exception as e:
        print(f"❌ Error deleting canteen data: {e}")

def delete_medical_data():
    """Delete all medical and health data"""
    try:
        from students_app.models import HealthCheckup, MedicalRecord
        
        summary = {
            'Health Checkups': HealthCheckup.objects.count(),
            'Medical Records': MedicalRecord.objects.count()
        }
        
        print(f"\nMedical data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No medical data found!")
            return
        
        confirm = input(f"\nDelete all {total} medical records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            MedicalRecord.objects.all().delete()
            HealthCheckup.objects.all().delete()
            print(f"✅ Successfully deleted {total} medical records")
            
    except Exception as e:
        print(f"❌ Error deleting medical data: {e}")

def delete_certificate_data():
    """Delete all certificate data"""
    try:
        from students_app.models import CertificateTemplate, Certificate
        
        summary = {
            'Certificate Templates': CertificateTemplate.objects.count(),
            'Certificates': Certificate.objects.count()
        }
        
        print(f"\nCertificate data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No certificate data found!")
            return
        
        confirm = input(f"\nDelete all {total} certificate records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            Certificate.objects.all().delete()
            CertificateTemplate.objects.all().delete()
            print(f"✅ Successfully deleted {total} certificate records")
            
    except Exception as e:
        print(f"❌ Error deleting certificate data: {e}")

def delete_sports_activities_data():
    """Delete all sports and activities data"""
    try:
        from students_app.models import (
            SportsCategory, Sport, SportsRegistration, SportsAchievement,
            ActivityCategory, CoCurricularActivity, ActivityRegistration
        )
        
        summary = {
            'Sports Categories': SportsCategory.objects.count(),
            'Sports': Sport.objects.count(),
            'Sports Registrations': SportsRegistration.objects.count(),
            'Sports Achievements': SportsAchievement.objects.count(),
            'Activity Categories': ActivityCategory.objects.count(),
            'Co-curricular Activities': CoCurricularActivity.objects.count(),
            'Activity Registrations': ActivityRegistration.objects.count()
        }
        
        print(f"\nSports & Activities data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No sports/activities data found!")
            return
        
        confirm = input(f"\nDelete all {total} sports/activities records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            SportsRegistration.objects.all().delete()
            SportsAchievement.objects.all().delete()
            Sport.objects.all().delete()
            SportsCategory.objects.all().delete()
            ActivityRegistration.objects.all().delete()
            CoCurricularActivity.objects.all().delete()
            ActivityCategory.objects.all().delete()
            print(f"✅ Successfully deleted {total} sports/activities records")
            
    except Exception as e:
        print(f"❌ Error deleting sports/activities data: {e}")

def delete_election_data():
    """Delete all election data"""
    try:
        from students_app.models import (
            Election, ElectionNomination, ElectionVote, ElectionResult
        )
        
        summary = {
            'Elections': Election.objects.count(),
            'Election Nominations': ElectionNomination.objects.count(),
            'Election Votes': ElectionVote.objects.count(),
            'Election Results': ElectionResult.objects.count()
        }
        
        print(f"\nElection data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No election data found!")
            return
        
        confirm = input(f"\nDelete all {total} election records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            ElectionResult.objects.all().delete()
            ElectionVote.objects.all().delete()
            ElectionNomination.objects.all().delete()
            Election.objects.all().delete()
            print(f"✅ Successfully deleted {total} election records")
            
    except Exception as e:
        print(f"❌ Error deleting election data: {e}")

def delete_all_academic_data():
    """Delete all academic data (exams + attendance + marks)"""
    try:
        from students_app.models import (
            Attendance, TeacherAttendance, StaffAttendance,
            Exam, ExamSchedule, Marks, ClassTest, ClassTestScore, QuestionPaper
        )
        
        summary = {
            'Student Attendance': Attendance.objects.count(),
            'Teacher Attendance': TeacherAttendance.objects.count(),
            'Staff Attendance': StaffAttendance.objects.count(),
            'Exams': Exam.objects.count(),
            'Exam Schedules': ExamSchedule.objects.count(),
            'Marks': Marks.objects.count(),
            'Class Tests': ClassTest.objects.count(),
            'Class Test Scores': ClassTestScore.objects.count(),
            'Question Papers': QuestionPaper.objects.count()
        }
        
        print(f"\nAll Academic data to delete:")
        for category, count in summary.items():
            print(f"• {category}: {count}")
        
        total = sum(summary.values())
        if total == 0:
            print("No academic data found!")
            return
        
        confirm = input(f"\nDelete all {total} academic records? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Operation cancelled.")
            return
        
        with transaction.atomic():
            ClassTestScore.objects.all().delete()
            Marks.objects.all().delete()
            QuestionPaper.objects.all().delete()
            ExamSchedule.objects.all().delete()
            ClassTest.objects.all().delete()
            Exam.objects.all().delete()
            Attendance.objects.all().delete()
            TeacherAttendance.objects.all().delete()
            StaffAttendance.objects.all().delete()
            print(f"✅ Successfully deleted {total} academic records")
            
    except Exception as e:
        print(f"❌ Error deleting academic data: {e}")

if __name__ == '__main__':
    module_specific_deletion()
