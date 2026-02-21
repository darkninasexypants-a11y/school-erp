"""
API URL Configuration for Mobile App
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import api_views

router = DefaultRouter()
router.register(r'students', api_views.StudentViewSet, basename='student')
router.register(r'attendance', api_views.AttendanceViewSet, basename='attendance')
router.register(r'fees', api_views.FeeViewSet, basename='fee')
router.register(r'id-cards', api_views.IDCardViewSet, basename='idcard')
router.register(r'id-cards/templates', api_views.IDCardTemplateViewSet, basename='idcardtemplate')
router.register(r'notices', api_views.NoticeViewSet, basename='notice')
router.register(r'events', api_views.EventViewSet, basename='event')
router.register(r'books', api_views.BookViewSet, basename='book')
router.register(r'book-issues', api_views.BookIssueViewSet, basename='bookissue')
router.register(r'exams', api_views.ExamViewSet, basename='exam')

urlpatterns = [
    # Authentication
    path('auth/login/', api_views.api_login, name='api_login'),
    path('auth/logout/', api_views.api_logout, name='api_logout'),
    path('auth/profile/', api_views.api_profile, name='api_profile'),
    
    # Dashboard
    path('dashboard/', api_views.api_dashboard, name='api_dashboard'),
    
    # Reference data
    path('classes/', api_views.api_classes, name='api_classes'),
    path('sections/', api_views.api_sections, name='api_sections'),
    path('academic-years/', api_views.api_academic_years, name='api_academic_years'),
    
    # Bulk upload
    path('bulk-upload/excel/', api_views.bulk_upload_excel, name='api_bulk_upload_excel'),
    path('bulk-upload/photos/', api_views.bulk_upload_photos, name='api_bulk_upload_photos'),
    
    # ID Card generation
    path('id-cards/generate/', api_views.generate_id_cards, name='api_generate_id_cards'),
    
    # Library
    path('book-categories/', api_views.api_book_categories, name='api_book_categories'),
    
    # Timetable
    path('timetable/', api_views.api_timetable, name='api_timetable'),
    
    # Exams & Marks
    path('students/<int:student_id>/marks/', api_views.api_student_marks, name='api_student_marks'),
    path('students/<int:student_id>/report-card/<int:exam_id>/', api_views.api_student_report_card, name='api_student_report_card'),
    
    # Error Logging
    path('errors/log/', api_views.api_log_error, name='api_log_error'),
    path('errors/batch/', api_views.api_log_errors_batch, name='api_log_errors_batch'),
    path('errors/logs/', api_views.api_get_error_logs, name='api_get_error_logs'),
    
    # Backend Health & Diagnostics
    path('health/', api_views.api_health_check, name='api_health_check'),
    path('diagnostics/', api_views.api_backend_diagnostics, name='api_backend_diagnostics'),
    path('check-endpoints/', api_views.api_check_endpoints, name='api_check_endpoints'),
    
    # Device Tracking
    path('devices/register/', api_views.api_register_device, name='api_register_device'),
    path('devices/list/', api_views.api_list_devices, name='api_list_devices'),
    
    # School Billing (Super Admin Only)
    path('billing/schools/', api_views.api_get_schools_for_billing, name='api_get_schools_for_billing'),
    path('billing/send/', api_views.api_send_school_bill, name='api_send_school_bill'),
    path('billing/list/', api_views.api_get_school_billings, name='api_get_school_billings'),
    path('billing/view/<int:billing_id>/', api_views.api_view_bill_template, name='api_view_bill_template'),
    path('billing/pdf/<int:billing_id>/', api_views.api_download_bill_pdf, name='api_download_bill_pdf'),
    
    # Router URLs
    path('', include(router.urls)),
]

