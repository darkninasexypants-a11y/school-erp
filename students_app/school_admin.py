from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import *
from .admin import *  # Import all the admin classes

# Create a separate admin site for school admins
school_admin_site = AdminSite(name='school_admin')
school_admin_site.site_header = "School Management System"
school_admin_site.site_title = "School Admin Portal"
school_admin_site.index_title = "Manage Your School"

# Register all school-related models with school admin site
school_admin_site.register(Student, StudentAdmin)
school_admin_site.register(Class, ClassAdmin)
school_admin_site.register(Section, SectionAdmin)
school_admin_site.register(Subject, SubjectAdmin)
school_admin_site.register(Teacher, TeacherAdmin)
school_admin_site.register(ClassTeacher, ClassTeacherAdmin)
school_admin_site.register(Attendance, AttendanceAdmin)
school_admin_site.register(FeeStructure, FeeStructureAdmin)
school_admin_site.register(FeePayment, FeePaymentAdmin)
school_admin_site.register(AcademicYear, AcademicYearAdmin)
school_admin_site.register(IDCardTemplate, IDCardTemplateAdmin)
school_admin_site.register(StudentIDCard, StudentIDCardAdmin)
school_admin_site.register(TimeSlot, TimeSlotAdmin)
school_admin_site.register(Timetable, TimetableAdmin)
school_admin_site.register(Exam, ExamAdmin)
school_admin_site.register(ExamSchedule, ExamScheduleAdmin)
school_admin_site.register(Marks, MarksAdmin)
school_admin_site.register(ClassTest, ClassTestAdmin)
school_admin_site.register(ClassTestScore, ClassTestScoreAdmin)
school_admin_site.register(BookCategory, BookCategoryAdmin)
school_admin_site.register(Book, BookAdmin)
school_admin_site.register(BookIssue, BookIssueAdmin)
school_admin_site.register(Parent, ParentAdmin)
school_admin_site.register(Notice, NoticeAdmin)
school_admin_site.register(Announcement, AnnouncementAdmin)
school_admin_site.register(Event, EventAdmin)

# Register new models for school admin
from .models import (
    Homework, HomeworkSubmission, InventoryCategory, InventoryItem, InventoryTransaction,
    LeaveType, LeaveApplication, StaffCategory, Staff, SalaryComponent, Salary,
    CertificateTemplate, Certificate, HealthCheckup, MedicalRecord,
    Hostel, HostelRoom, HostelAllocation, CanteenItem, CanteenOrder, OrderItem,
    Alumni, OnlineExam, OnlineExamQuestion, OnlineExamAttempt, OnlineExamAnswer
)

# Register new models with school admin site
school_admin_site.register(Homework)
school_admin_site.register(HomeworkSubmission)
school_admin_site.register(InventoryCategory)
school_admin_site.register(InventoryItem)
school_admin_site.register(InventoryTransaction)
school_admin_site.register(LeaveType)
school_admin_site.register(LeaveApplication)
school_admin_site.register(StaffCategory)
school_admin_site.register(Staff)
school_admin_site.register(SalaryComponent)
school_admin_site.register(Salary)
school_admin_site.register(CertificateTemplate)
school_admin_site.register(Certificate)
school_admin_site.register(HealthCheckup)
school_admin_site.register(MedicalRecord)
school_admin_site.register(Hostel)
school_admin_site.register(HostelRoom)
school_admin_site.register(HostelAllocation)
school_admin_site.register(CanteenItem)
school_admin_site.register(CanteenOrder)
school_admin_site.register(OrderItem)
school_admin_site.register(Alumni)
school_admin_site.register(OnlineExam)
school_admin_site.register(OnlineExamQuestion)
school_admin_site.register(OnlineExamAttempt)
school_admin_site.register(OnlineExamAnswer)
school_admin_site.register(TransportRoute, TransportRouteAdmin)
school_admin_site.register(Bus, BusAdmin)
school_admin_site.register(StudentTransport, StudentTransportAdmin)
school_admin_site.register(QuestionPaper, QuestionPaperAdmin)
school_admin_site.register(SchoolSettings, SchoolSettingsAdmin)

# Register User Roles and School Users for school management
school_admin_site.register(UserRole, UserRoleAdmin)
school_admin_site.register(SchoolUser, SchoolUserAdmin)

# Register User with school admin site
school_admin_site.register(User, CustomUserAdmin)
