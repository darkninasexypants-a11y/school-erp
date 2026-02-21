"""
Management command to clear all data from the database for fresh testing.
IMPORTANT: This will DELETE ALL DATA (records) but PRESERVE the database structure (tables).
Only data will be deleted, NOT the table structure or schema.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from students_app.models import *

# Import CRM models if available
try:
    from students_app.enrollment_crm_models import (
        LeadSource, Lead, LeadActivity, Campaign, 
        CampaignLead, EnrollmentFunnel, Application
    )
    CRM_MODELS_AVAILABLE = True
except ImportError:
    CRM_MODELS_AVAILABLE = False

class Command(BaseCommand):
    help = 'Clear all data (records) from the database. Tables structure will be preserved.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-roles',
            action='store_true',
            help='Keep UserRole data (recommended)',
        )
        parser.add_argument(
            '--keep-superuser',
            action='store_true',
            help='Keep superuser accounts',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                'WARNING: This will delete ALL DATA (records) from the database!'
            ))
            self.stdout.write(self.style.WARNING(
                'NOTE: Table structure will be preserved. Only data will be deleted.'
            ))
            confirm = input('Type "DELETE ALL" to confirm: ')
            if confirm != 'DELETE ALL':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        self.stdout.write(self.style.SUCCESS('Starting data deletion...'))
        
        try:
            # Use a safer approach - delete in try-except blocks
            self.stdout.write('Deleting application data...')
            
            def safe_delete(model_class, model_name):
                """Safely delete all objects from a model"""
                try:
                    count = model_class.objects.count()
                    if count > 0:
                        model_class.objects.all().delete()
                        self.stdout.write(self.style.SUCCESS(f'{model_name}: {count} deleted'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'{model_name}: Could not delete - {str(e)[:100]}'))
            
            # Delete in reverse order of dependencies
            # Note: Not using transaction.atomic() to allow partial deletion if some models fail
            
            # Game and Mock Test related
            safe_delete(StudentGameAchievement, 'StudentGameAchievement')
            safe_delete(GameAchievement, 'GameAchievement')
            safe_delete(GameSession, 'GameSession')
            safe_delete(GameAnswer, 'GameAnswer')
            safe_delete(GameQuestion, 'GameQuestion')
            safe_delete(EducationalGame, 'EducationalGame')
            safe_delete(GameCategory, 'GameCategory')
                
            safe_delete(MockTestAttempt, 'MockTestAttempt')
            safe_delete(MockTestSession, 'MockTestSession')
            safe_delete(MockTestAnswer, 'MockTestAnswer')
            safe_delete(MockTestQuestion, 'MockTestQuestion')
            safe_delete(MockTest, 'MockTest')
            safe_delete(MockTestCategory, 'MockTestCategory')
                
            # ID Card Generator
            safe_delete(IDCardData, 'IDCardData')
            safe_delete(IDCardGenerator, 'IDCardGenerator')
                
            # Fee related
            safe_delete(FeeReconciliation, 'FeeReconciliation')
            safe_delete(FeeNotification, 'FeeNotification')
            safe_delete(StudentFeeConcession, 'StudentFeeConcession')
            safe_delete(FeeConcession, 'FeeConcession')
                
            # Elections
            safe_delete(ElectionResult, 'ElectionResult')
            safe_delete(ElectionVote, 'ElectionVote')
            safe_delete(ElectionNomination, 'ElectionNomination')
            safe_delete(Election, 'Election')
                
            # Leadership
            safe_delete(StudentLeadership, 'StudentLeadership')
            safe_delete(LeadershipPosition, 'LeadershipPosition')
                
            # House system
            safe_delete(HouseEventResult, 'HouseEventResult')
            safe_delete(HouseEvent, 'HouseEvent')
            safe_delete(HouseMembership, 'HouseMembership')
            safe_delete(House, 'House')
                
            # Activities
            safe_delete(ActivityRegistration, 'ActivityRegistration')
            safe_delete(CoCurricularActivity, 'CoCurricularActivity')
            safe_delete(ActivityCategory, 'ActivityCategory')
                
            # Sports
            safe_delete(SportsAchievement, 'SportsAchievement')
            safe_delete(SportsRegistration, 'SportsRegistration')
            safe_delete(Sport, 'Sport')
            safe_delete(SportsCategory, 'SportsCategory')
                
            # Online Exams
            safe_delete(OnlineExamAnswer, 'OnlineExamAnswer')
            safe_delete(OnlineExamAttempt, 'OnlineExamAttempt')
            safe_delete(OnlineExamQuestion, 'OnlineExamQuestion')
            safe_delete(OnlineExam, 'OnlineExam')
                
            # Alumni
            safe_delete(Alumni, 'Alumni')
                
            # Canteen
            safe_delete(OrderItem, 'OrderItem')
            safe_delete(CanteenOrder, 'CanteenOrder')
            safe_delete(CanteenItem, 'CanteenItem')
                
            # Hostel
            safe_delete(HostelAllocation, 'HostelAllocation')
            safe_delete(HostelRoom, 'HostelRoom')
            safe_delete(Hostel, 'Hostel')
                
            # Medical
            safe_delete(MedicalRecord, 'MedicalRecord')
            safe_delete(HealthCheckup, 'HealthCheckup')
                
            # Certificates (handle schema issues)
            safe_delete(Certificate, 'Certificate')
            safe_delete(CertificateTemplate, 'CertificateTemplate')
                
            # Salary
            safe_delete(Salary, 'Salary')
            safe_delete(SalaryComponent, 'SalaryComponent')
                
            # Staff
            safe_delete(Staff, 'Staff')
            safe_delete(StaffCategory, 'StaffCategory')
                
            # Leave
            safe_delete(LeaveApplication, 'LeaveApplication')
            safe_delete(LeaveType, 'LeaveType')
                
            # Inventory
            safe_delete(InventoryTransaction, 'InventoryTransaction')
            safe_delete(InventoryItem, 'InventoryItem')
            safe_delete(InventoryCategory, 'InventoryCategory')
                
            # Homework
            safe_delete(HomeworkSubmission, 'HomeworkSubmission')
            safe_delete(Homework, 'Homework')
                
            # Transport
            safe_delete(StudentTransport, 'StudentTransport')
            safe_delete(Bus, 'Bus')
            safe_delete(TransportRoute, 'TransportRoute')
                
            # Events and Notices
            safe_delete(Event, 'Event')
            safe_delete(Announcement, 'Announcement')
            safe_delete(Notice, 'Notice')
                
            # Library
            safe_delete(BookIssue, 'BookIssue')
            safe_delete(Book, 'Book')
            safe_delete(BookCategory, 'BookCategory')
                
            # Academics
            safe_delete(ClassTestScore, 'ClassTestScore')
            safe_delete(ClassTest, 'ClassTest')
            safe_delete(Marks, 'Marks')
            safe_delete(ExamSchedule, 'ExamSchedule')
            safe_delete(Exam, 'Exam')
            safe_delete(Timetable, 'Timetable')
            safe_delete(TimeSlot, 'TimeSlot')
                
            # Fees
            safe_delete(FeePayment, 'FeePayment')
            safe_delete(FeeStructure, 'FeeStructure')
                
            # Attendance
            safe_delete(Attendance, 'Attendance')
                
            # Class Teacher
            safe_delete(ClassTeacher, 'ClassTeacher')
                
            # Teachers
            safe_delete(Teacher, 'Teacher')
                
            # ID Cards
            safe_delete(StudentIDCard, 'StudentIDCard')
            safe_delete(IDCardTemplate, 'IDCardTemplate')
                
            # Students
            safe_delete(Student, 'Student')
                
            # Parents
            safe_delete(Parent, 'Parent')
                
            # Sections and Classes
            safe_delete(Section, 'Section')
            safe_delete(Class, 'Class')
                
            # Academic Year
            safe_delete(AcademicYear, 'AcademicYear')
                
            # Subjects
            safe_delete(Subject, 'Subject')
                
            # CRM Models (if available)
            if CRM_MODELS_AVAILABLE:
                    self.stdout.write('Deleting CRM data...')
                    safe_delete(Application, 'Application')
                    safe_delete(EnrollmentFunnel, 'EnrollmentFunnel')
                    safe_delete(CampaignLead, 'CampaignLead')
                    safe_delete(Campaign, 'Campaign')
                    safe_delete(LeadActivity, 'LeadActivity')
                    safe_delete(Lead, 'Lead')
                    safe_delete(LeadSource, 'LeadSource')
                
            # School Users and School Settings
            safe_delete(SchoolSettings, 'SchoolSettings')
            safe_delete(SchoolBilling, 'SchoolBilling')
            safe_delete(SchoolUser, 'SchoolUser')
                
            # Schools
            safe_delete(School, 'School')
                
            # User Roles (optional - keep if requested)
            if not options['keep_roles']:
                safe_delete(UserRole, 'UserRole')
            else:
                self.stdout.write(self.style.SUCCESS('UserRole kept (as requested)'))
            
            # Django Users (keep superuser if requested)
            if options['keep_superuser']:
                try:
                    count = User.objects.filter(is_superuser=False).count()
                    if count > 0:
                        User.objects.filter(is_superuser=False).delete()
                        self.stdout.write(self.style.SUCCESS(f'Regular users deleted: {count}'))
                    self.stdout.write(self.style.SUCCESS('Superusers kept'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Could not delete users: {e}'))
            else:
                safe_delete(User, 'User')
                
            # Sessions
            try:
                count = Session.objects.count()
                if count > 0:
                    Session.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS(f'Sessions cleared: {count}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not clear sessions: {e}'))
                
            # Question Papers
            safe_delete(QuestionPaper, 'QuestionPaper')
            
            self.stdout.write(self.style.SUCCESS('\nData deletion process completed!'))
            self.stdout.write(self.style.SUCCESS('Database is now ready for fresh testing.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError deleting data: {str(e)}'))
            import traceback
            traceback.print_exc()
            raise

