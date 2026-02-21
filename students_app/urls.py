
from django.urls import path
from django.shortcuts import redirect
from . import views, auth_views, simple_views, id_card_generator_views, language_views, logout_views
from . import enrollment_crm_views, unified_dashboard_views, super_admin_views, fee_management_views
from . import communication_views, billing_views, mobile_api, work_tracking_views
from .views_school_setup import school_setup_wizard, check_school_setup_status, get_school_designations
from .views_class_selector import class_selector_view, ajax_get_sections, ajax_get_classes_by_school
from .views_attendance import attendance_dashboard, take_attendance, ajax_get_students_for_attendance, attendance_report
from .views_id_card_progress import generate_id_cards_with_progress, start_bulk_id_card_generation, get_generation_progress, id_card_generation_status, list_generated_id_cards_with_status
from .views_credentials_display import display_credentials, export_credentials, reset_passwords
from .views_class_list_management import (
    class_list_management, add_class, add_section, edit_class, edit_section, 
    delete_class, delete_section, get_class_sections, export_class_data
)
from .views_timetable_management import timetable_management, upload_timetable, download_sample_timetable, add_timetable_entry, delete_timetable_entry
from .views_teacher_access import teacher_dashboard_restricted, teacher_student_list, teacher_timetable, check_import_permission, teacher_class_sections
from .views import ( 
  StudentListView, StudentDetailView,
  IDCardTemplateListView,
)

app_name = 'students_app'

urlpatterns = [
    # Add Academic Year from modal
    path('add-academic-year/', views.add_academic_year, name='add_academic_year'),

    # 0. (Authentication)
    path('login/', auth_views.multi_login, name='multi_login'),
    path('simple-login/', simple_views.simple_login, name='simple_login'),
    path('setup-page/', lambda request: redirect('students_app:simple_login'), name='setup_page'),  # Redirected to login
    path('parent/login/', auth_views.parent_login, name='parent_login'),
    path('teacher/login/', auth_views.teacher_login, name='teacher_login'),
    path('logout/', auth_views.user_logout, name='user_logout'),
    path('parent/logout/', simple_views.parent_logout, name='parent_logout'),
    path('student/logout/', simple_views.student_logout, name='student_logout'),
    path('teacher/logout/', simple_views.teacher_logout, name='teacher_logout'),
    path('librarian/logout/', simple_views.librarian_logout, name='librarian_logout'),
    path('setup/', auth_views.setup_initial_data, name='setup_initial_data'),
    path('admin-dashboard/', auth_views.admin_dashboard, name='admin_dashboard'),
    path('create-user/', auth_views.create_user, name='create_user'),
    path('create-school/', auth_views.create_school, name='create_school'),
    path('create-school/send-otp/', auth_views.send_school_otp, name='send_school_otp'),
    path('create-school/verify-otp/', auth_views.verify_school_otp, name='verify_school_otp'),
    path('school/logo/', auth_views.update_school_logo, name='update_school_logo'),
    path('send-login-otp/', auth_views.send_login_otp, name='send_login_otp'),
    path('verify-login-otp/', auth_views.verify_login_otp, name='verify_login_otp'),
    path('mobile-direct-login/', auth_views.mobile_direct_login, name='mobile_direct_login'),
    path('user-list/', auth_views.user_list, name='user_list'),
    path('user-list/edit/<int:user_id>/', auth_views.edit_user, name='edit_user'),
    path('user-list/toggle-status/<int:user_id>/', auth_views.toggle_user_status, name='toggle_user_status'),
    path('django-admin/', auth_views.django_admin_redirect, name='django-admin'),
    
    # Super Admin Advanced Features
    path('super-admin/user-management/', super_admin_views.super_admin_user_management, name='super_admin_user_management'),
    path('super-admin/analytics/', super_admin_views.super_admin_analytics, name='super_admin_analytics'),
    path('super-admin/analytics/export/', super_admin_views.super_admin_analytics_export, name='super_admin_analytics_export'),
    path('super-admin/schools/<int:school_id>/features/', super_admin_views.edit_school_features, name='edit_school_features'),
    path('super-admin/notifications/', super_admin_views.notifications_feed, name='notifications_feed'),
    path('super-admin/notifications/json/', super_admin_views.notifications_json, name='notifications_json'),
    path('super-admin/configuration/', super_admin_views.super_admin_configuration, name='super_admin_configuration'),
    path('super-admin/security/', super_admin_views.super_admin_security, name='super_admin_security'),
    path('super-admin/update-user-access/<int:user_id>/', super_admin_views.update_user_access_level, name='update_user_access_level'),
    path('super-admin/delete-user/<int:user_id>/', super_admin_views.delete_user, name='delete_user'),
    
    # School Billing (Super Admin)
    path('billing/dashboard/', billing_views.school_billing_dashboard, name='school_billing_dashboard'),
    path('billing/send/', billing_views.send_school_bill, name='send_school_bill'),
    path('billing/<int:billing_id>/update-status/', billing_views.update_bill_status, name='update_bill_status'),
    path('billing/school/<int:school_id>/history/', billing_views.school_billing_history, name='school_billing_history'),
    path('billing/invoice/<int:billing_id>/', billing_views.view_invoice, name='view_invoice'),
    path('billing/invoice/<int:billing_id>/download/', billing_views.download_invoice_pdf, name='download_invoice_pdf'),
    
    # Work & Expense Tracking (Super Admin)
    path('work-tracking/', work_tracking_views.work_entry_list, name='work_list'),
    path('work-tracking/create/', work_tracking_views.work_entry_create, name='work_create'),
    path('work-tracking/<int:work_id>/', work_tracking_views.work_entry_detail, name='work_detail'),
    path('work-tracking/<int:work_id>/edit/', work_tracking_views.work_entry_edit, name='work_edit'),
    path('work-tracking/<int:work_id>/delete/', work_tracking_views.work_delete, name='work_delete'),
    path('work-tracking/<int:work_id>/expense/add/', work_tracking_views.expense_create, name='expense_create'),
    path('work-tracking/expense/<int:expense_id>/edit/', work_tracking_views.expense_edit, name='expense_edit'),
    path('work-tracking/expense/<int:expense_id>/delete/', work_tracking_views.expense_delete, name='expense_delete'),
    path('work-tracking/team-members/', work_tracking_views.team_member_list, name='team_member_list'),
    path('work-tracking/team-members/create/', work_tracking_views.team_member_create, name='team_member_create'),
    path('work-tracking/reports/', work_tracking_views.reports_work_summary, name='reports_work_summary'),
    path('work-tracking/dashboard/', work_tracking_views.work_tracking_dashboard, name='work_tracking_dashboard'),

    # 1. (Home/Dashboard)
    path('', views.login_redirect, name='home'),
    path('dashboard/', views.home, name='dashboard'),
    path('unified-dashboard/', unified_dashboard_views.unified_dashboard, name='unified_dashboard'),

    # 2.  (Student Management)
    path('students/demo/', lambda request: redirect('students_app:student_dashboard'), name='student_demo'),  # Redirect to actual student portal
    path('students/', StudentListView.as_view(), name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/import/', views.student_bulk_import, name='student_import'),
    path('students/bulk-delete/', views.bulk_delete_students, name='bulk_delete_students'),
    path('students/download-template/', views.download_sample_template, name='download_sample_template'),
    path('students/export/', views.export_student_data, name='export_student_data'),
    path('students/download-photos/', views.bulk_download_photos, name='bulk_download_photos'),
    path('students/<str:admission_number>/', StudentDetailView.as_view(), name='student_detail'),
    path('students/<str:admission_number>/change-photo/', views.student_change_photo, name='student_change_photo'),
    path('students/<str:admission_number>/update/', views.StudentUpdateView.as_view(), name='student_update'),
    path('students/<str:admission_number>/delete/', views.delete_student, name='delete_student'),

    # 3.  (ID Cards)
    path('id-cards/', views.list_generated_id_cards, name='id_card_list'),
    path('id-cards/<int:card_id>/detail/', views.id_card_detail_view, name='id_card_detail'), 
    path('id-cards/<int:card_id>/download/', views.download_id_card, name='download_id_card'),
    path('id-cards/<int:card_id>/delete/', views.delete_id_card, name='delete_id_card'),
    path('id-cards/bulk-delete/', views.bulk_delete_id_cards, name='bulk_delete_id_cards'),
    path('id-cards/templates/', views.IDCardTemplateListView.as_view(), name='idcard_template_list'),
    path('id-cards/generate-bulk-selection/', views.generate_bulk_id_cards, name='generate_bulk_id_cards'), 
    path('id-cards/process-bulk-generation/', views.process_bulk_id_card_generation, name='process_bulk_id_card_generation'),
    path('id-cards/generate-for-class/', views.generate_id_cards_for_class, name='generate_id_cards_for_class'),
    path('id-cards/<int:student_id>/generate-single/', views.generate_single_id_card, name='generate_id_card'), 
    path('id-cards/generate-pdf/', views.generate_pdf_id_cards, name='generate_pdf_id_cards'),
    path('id-cards/bulk-download/', views.bulk_download_id_cards, name='bulk_download_id_cards'),
    path('id-cards/advanced-batch-excel/', views.advanced_id_card_batch_excel, name='advanced_id_card_batch'),
    path('id-cards/verify-ocr/', views.verify_id_card_ocr, name='verify_id_card_ocr'),
    path('id-cards/verify-face/', views.verify_face_match, name='verify_face_match'),
    path('id-cards/generate-printable-sheets/', views.generate_printable_sheets, name='generate_printable_sheets'), 

    # 4.  (Exams & Marks)
    path('exams/marks-entry/', views.marks_entry, name='marks_entry'),
    path('exams/teacher-entry/', views.marks_entry, name='teacher_exam_entry'),  # Alias for sidebar
    path('exams/report-card/<str:admission_number>/<int:exam_id>/', views.student_report_card, name='student_report_card'),

    # 5.  (Attendance)
    path('attendance/mark/', views.attendance_mark, name='attendance_mark'),
    path('attendance/teachers/mark/', views.teacher_attendance_mark, name='teacher_attendance_mark'),
    path('attendance/teachers/ocr-verify/', views.teacher_attendance_ocr_verify, name='teacher_attendance_ocr_verify'),
    path('attendance/teachers/face-verify/', views.teacher_attendance_face_verify, name='teacher_attendance_face_verify'),
    path('teachers/attendance/students/', views.teacher_student_attendance, name='teacher_student_attendance'),
    path('teachers/attendance/students-by-section/<int:section_id>/', views.teacher_get_section_students, name='teacher_get_section_students'),
    path('attendance/staff/mark/', views.staff_attendance_mark, name='staff_attendance_mark'),
    path('attendance/staff/ocr-verify/', views.staff_attendance_ocr_verify, name='staff_attendance_ocr_verify'),
    path('attendance/staff/face-verify/', views.staff_attendance_face_verify, name='staff_attendance_face_verify'),
    path('attendance/view/', views.view_attendance, name='view_attendance'),
    path('attendance/students-by-section/<int:section_id>/', views.get_section_students, name='get_section_students'),
    path('attendance/students-by-class/<int:class_id>/', views.get_class_students, name='get_class_students'),
    path('attendance/sections-by-class/<int:class_id>/', views.get_sections_for_class, name='attendance_sections_by_class'),
    path('attendance/report/', views.attendance_report, name='attendance_report'),
    
    # QR Code Attendance Punching
    path('attendance/qr-scan/', views.qr_attendance_scan, name='qr_attendance_scan'),
    path('attendance/qr-process/', views.qr_attendance_process, name='qr_attendance_process'),
    path('attendance/qr-records/', views.qr_attendance_records, name='qr_attendance_records'),
    
    # Staff ID Card Generation
    path('id-cards/staff/generate/', views.generate_staff_id_cards, name='generate_staff_id_cards'), 

    # 6.  (Fees)
    path('fees/collect/', views.fee_collection, name='fee_collection'),
    path('fees/structures/', views.fee_structure_management, name='fee_structure_management'),
    path('fees/search-students/', views.search_students_autocomplete, name='search_students_autocomplete'),
    path('fees/get-student-fee-structure/', views.get_student_fee_structure, name='get_student_fee_structure'),
    path('fees/receipts/', views.receipts_list, name='receipts_list'),
    path('fees/receipt/<int:receipt_id>/', views.fee_receipt, name='fee_receipt'), 
    path('fees/report/', views.fee_report, name='fee_report'), 
    path('fees/history/', views.fee_report, name='fee_history'),  # Alias for sidebar 
    path('fees/online/order/', views.create_fee_order, name='create_fee_order'),
    path('fees/online/verify/', views.verify_fee_payment, name='verify_fee_payment'),
    # Enhanced Fee Management
    path('fees/analytics/', fee_management_views.fee_analytics, name='fee_analytics'),
    path('fees/notifications/', fee_management_views.fee_notifications, name='fee_notifications'),
    path('fees/reconciliation/', fee_management_views.fee_reconciliation, name='fee_reconciliation'),
    path('fees/e-receipt/<int:receipt_id>/', fee_management_views.generate_e_receipt, name='generate_e_receipt'),
    path('fees/sections-by-class/<int:class_id>/', fee_management_views.get_sections_by_class, name='get_sections_by_class'),



    # 7. (Library)
    path('library/dashboard/', views.library_dashboard, name='library_dashboard'),
    path('library/issue-book/', views.issue_book, name='issue_book'),
    # Teacher book request
    path('teachers/book-request/', views.teacher_book_request, name='teacher_book_request'),
    path('library/return-book/<int:issue_id>/', views.return_book, name='return_book'),
    path('library/books/', views.book_list, name='book_list'),
    path('library/books/add/', views.add_book, name='add_book'),
    path('library/books/<int:book_id>/edit/', views.edit_book, name='edit_book'),
    path('library/books/<int:book_id>/qr-code/', views.book_qr_code_view, name='book_qr_code_view'),
    path('library/books/<int:book_id>/qr-code/download/', views.book_qr_code, name='book_qr_code'),
    path('library/books/bulk-qr-codes/', views.bulk_qr_codes, name='bulk_qr_codes'),

    # 8.  (Academics & Communication)
    path('academics/timetable/', views.view_timetable, name='view_timetable'),
    path('academics/timetable/request-change/', views.request_timetable_change, name='request_timetable_change'),
    path('academics/timetable/requests/', views.manage_timetable_requests, name='manage_timetable_requests'),
    path('academics/timetable/requests/<int:request_id>/review/', views.review_timetable_request, name='review_timetable_request'),
    path('academics/timetable/edit/', views.edit_timetable_redirect, name='edit_timetable_root'),
    path('academics/timetable/edit/<int:section_id>/', views.edit_timetable, name='edit_timetable'),
    path('academics/timetable/manage/', views.manage_timetables, name='manage_timetables'),
    path('academics/timetable/conflicts/', views.timetable_conflicts, name='timetable_conflicts'),
    path('academics/timetable/bulk/', views.bulk_timetable_operations, name='bulk_timetable_operations'),
    path('academics/timetable/export/<int:section_id>/', views.export_timetable, name='export_timetable'),
    path('academics/timetable/import/', views.import_timetable, name='import_timetable'),
    # Notice Management
    path('communication/notices/', views.notice_list, name='notice_list'),
    path('communication/notices/create/', views.notice_create, name='notice_create'),
    path('communication/notices/<int:notice_id>/', views.notice_detail, name='notice_detail'),
    path('communication/notices/<int:notice_id>/edit/', views.notice_edit, name='notice_edit'),
    path('communication/notices/<int:notice_id>/delete/', views.notice_delete, name='notice_delete'),
    path('communication/notices/<int:notice_id>/toggle-active/', views.notice_toggle_active, name='notice_toggle_active'),
    path('communication/notices/<int:notice_id>/toggle-publish/', views.notice_toggle_publish, name='notice_toggle_publish'),
    # Events Management (visible to all: students, parents, teachers)
    path('communication/events/', views.event_calendar, name='event_calendar'),
    path('communication/events/create/', views.event_create, name='event_create'),
    path('communication/events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('communication/events/<int:event_id>/toggle-publish/', views.event_toggle_publish, name='event_toggle_publish'),

    # 9. (Reports & Analytics)
    path('reports/', views.reports_dashboard, name='reports_dashboard'),

    # 10. (Parent Portal)
    path('parents/login/', views.parent_login, name='parent_login'),
    path('parents/', views.parent_dashboard, name='parent_dashboard'),
    path('parents/student/<int:student_id>/progress/', views.parent_student_progress, name='parent_student_progress'),
    path('parents/demo/', lambda request: redirect('students_app:parent_dashboard'), name='parent_demo'),  # Redirect to actual parent dashboard

    # 11. (Teacher Portal)
    path('teachers/demo/', lambda request: redirect('students_app:teacher_dashboard_restricted'), name='teacher_demo'),  # Redirect to actual teacher dashboard
    path('teachers/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teachers/bulk-upload/', views.teacher_bulk_upload, name='teacher_bulk_upload'),
    path('smart-bulk-upload/', views.smart_bulk_upload, name='smart_bulk_upload'),
    path('school-setup/', school_setup_wizard, name='school_setup_wizard'),
    path('api/check-school-setup/', check_school_setup_status, name='check_school_setup_status'),
    path('api/get-designations/', get_school_designations, name='get_school_designations'),
    
    # Simple Class Selector
    path('select-class/', class_selector_view, name='class_selector'),
    path('api/classes/<int:class_id>/sections-simple/', ajax_get_sections, name='ajax_get_sections'),
    path('api/school/<int:school_id>/classes/', ajax_get_classes_by_school, name='ajax_get_classes_by_school'),
    
    # Attendance System
    path('attendance/', attendance_dashboard, name='attendance_dashboard'),
    path('attendance/take/', take_attendance, name='take_attendance'),
    path('attendance/report/', attendance_report, name='attendance_report'),
    path('api/attendance/students/<int:class_id>/<int:section_id>/', ajax_get_students_for_attendance, name='ajax_get_students_for_attendance'),
    
    # ID Card Generation with Progress
    path('id-cards/generate-with-progress/', generate_id_cards_with_progress, name='generate_id_cards_with_progress'),
    path('id-cards/start-generation/', start_bulk_id_card_generation, name='start_bulk_id_card_generation'),
    path('id-cards/progress/<str:job_id>/', get_generation_progress, name='get_generation_progress'),
    path('id-cards/generation-status/', id_card_generation_status, name='id_card_generation_status'),
    path('id-cards/list-with-status/', list_generated_id_cards_with_status, name='list_generated_id_cards_with_status'),
    
    # Credentials Management
    path('credentials/', display_credentials, name='display_credentials'),
    path('credentials/export/', export_credentials, name='export_credentials'),
    path('credentials/reset-passwords/', reset_passwords, name='reset_passwords'),
    
    # Class List Management
    path('class-management/', class_list_management, name='class_list_management'),
    path('class-management/add/', add_class, name='add_class'),
    path('class-management/add-section/', add_section, name='add_section'),
    path('class-management/edit/<int:class_id>/', edit_class, name='edit_class'),
    path('class-management/edit-section/<int:section_id>/', edit_section, name='edit_section'),
    path('class-management/delete/<int:class_id>/', delete_class, name='delete_class'),
    path('class-management/delete-section/<int:section_id>/', delete_section, name='delete_section'),
    path('class-management/get-sections/<int:class_id>/', get_class_sections, name='get_class_sections'),
    path('class-management/export/', export_class_data, name='export_class_data'),
    path('class-management/bulk-create-sections/', lambda request: JsonResponse({'success': True, 'message': 'Default sections created for all classes'}), name='bulk_create_sections'),
    
    # Timetable Management
    path('timetable/', timetable_management, name='timetable_management'),
    path('timetable/upload/', upload_timetable, name='upload_timetable'),
    path('timetable/download-sample/', download_sample_timetable, name='download_sample_timetable'),
    path('timetable/add-entry/', add_timetable_entry, name='add_timetable_entry'),
    path('timetable/delete/<int:timetable_id>/', delete_timetable_entry, name='delete_timetable_entry'),
    
    # Teacher Access Control
    path('teacher/dashboard-restricted/', teacher_dashboard_restricted, name='teacher_dashboard_restricted'),
    path('teacher/students/', teacher_student_list, name='teacher_student_list'),
    path('teacher/timetable/', teacher_timetable, name='teacher_timetable'),
    path('api/teacher/check-import-permission/', check_import_permission, name='check_import_permission'),
    path('api/teacher/class-sections/', teacher_class_sections, name='teacher_class_sections'),
    
    path('teachers/list/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/edit/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('teachers/delete/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),
    path('teachers/bulk-delete/', views.bulk_delete_teachers, name='bulk_delete_teachers'),
    path('teachers/question-paper/', views.teacher_question_paper, name='teacher_question_paper'),
    path('teachers/whatsapp/', views.teacher_whatsapp, name='teacher_whatsapp'),
    path('teachers/my-attendance/', views.teacher_my_attendance, name='teacher_my_attendance'),
    path('teachers/change-photo/', views.teacher_change_photo, name='teacher_change_photo'),
    path('assign-class-teacher/', views.assign_class_teacher, name='assign_class_teacher'),
    path('assign-class-teacher/<int:teacher_id>/', views.assign_class_teacher, name='assign_class_teacher'),
    
    # Staff Management (Non-Teaching Staff)
    path('staff/list/', views.staff_list, name='staff_list'),
    path('staff/add/', views.add_staff, name='add_staff'),
    path('staff/bulk-upload/', views.staff_bulk_upload, name='staff_bulk_upload'),
    path('staff/delete/<int:staff_id>/', views.delete_staff, name='delete_staff'),
    path('staff/bulk-delete/', views.bulk_delete_staff, name='bulk_delete_staff'),
    
    # 12. (Student Portal)
    path('student-portal/', views.student_dashboard, name='student_dashboard'),
    
    # 13. (Librarian Portal)
    path('librarian/demo/', lambda request: redirect('students_app:librarian_dashboard'), name='librarian_demo'),  # Redirect to actual librarian dashboard
    # Librarian dashboard - uses modern library dashboard template
    path('librarian/', views.librarian_dashboard, name='librarian_dashboard'),
    
        # 14. (Educational Games)
        path('games/', views.games_home, name='games_home'),
        path('games/class/<int:class_id>/', views.games_by_class, name='games_by_class'),
        path('games/play/<int:game_id>/', views.play_game, name='play_game'),
        path('games/submit/<int:game_id>/', views.submit_game, name='submit_game'),
        path('games/leaderboard/<int:game_id>/', views.game_leaderboard, name='game_leaderboard'),
        path('games/stats/', views.student_game_stats, name='student_game_stats'),
        
        # 15. (Mock Tests for 9th-12th Class)
        path('mock-tests/', views.mock_tests_home, name='mock_tests_home'),
        path('mock-tests/class/<int:class_id>/', views.mock_tests_by_class, name='mock_tests_by_class'),
        path('mock-tests/start/<int:test_id>/', views.start_mock_test, name='start_mock_test'),
        path('mock-tests/submit/<int:session_id>/', views.submit_mock_test, name='submit_mock_test'),
        path('mock-tests/results/<int:session_id>/', views.mock_test_results, name='mock_test_results'),
        path('mock-tests/leaderboard/<int:test_id>/', views.mock_test_leaderboard, name='mock_test_leaderboard'),
        
    # 16. (ID Card Template Management)
    path('id-card-templates/upload/', views.upload_id_card_template, name='upload_id_card_template'),
    path('id-card-templates/', views.id_card_template_list, name='id_card_template_list'),
    path('id-card-templates/edit/<int:template_id>/', views.edit_id_card_template, name='edit_id_card_template'),
    path('id-card-templates/delete/<int:template_id>/', views.delete_id_card_template, name='delete_id_card_template'),
    
    # 17. (ID Card Generator for Super User)
    path('id-card-generator/', id_card_generator_views.id_card_generator_dashboard, name='id_card_generator_dashboard'),
    path('id-card-generator/create/', id_card_generator_views.create_id_card_generator, name='create_id_card_generator'),
    path('id-card-generator/edit/<int:generator_id>/', id_card_generator_views.edit_id_card_generator, name='edit_id_card_generator'),
    path('id-card-generator/data-entry/<int:generator_id>/', id_card_generator_views.id_card_data_entry, name='id_card_data_entry'),
    path('id-card-generator/edit-data/<int:card_id>/', id_card_generator_views.edit_id_card_data, name='edit_id_card_data'),
    path('id-card-generator/generate-pdf/<int:generator_id>/', id_card_generator_views.generate_id_cards_pdf, name='generate_id_cards_pdf'),
    path('calculator/', id_card_generator_views.calculator, name='calculator'),
    path('calculator/calculate/', id_card_generator_views.calculator_calculate, name='calculator_calculate'),
    
    # 18. (Language Switching)
    path('switch-language/', language_views.switch_language, name='switch_language'),
    path('get-language-text/', language_views.get_language_text, name='get_language_text'),
    
    # 19. (Logout)
    # path('logout/', logout_views.custom_logout, name='custom_logout'),  # Removed due to conflict

    path('ajax-logout/', logout_views.ajax_logout, name='ajax_logout'),
    
    # 20. (CRM - Enrollment Management - Similar to Meritto/Zoho)
    # path('crm/', enrollment_crm_views.crm_dashboard, name='crm_dashboard'),  # Removed - use unified_dashboard instead
    path('crm/leads/', enrollment_crm_views.lead_list, name='lead_list'),
    path('crm/leads/create/', enrollment_crm_views.lead_create, name='lead_create'),
    path('crm/leads/<int:lead_id>/', enrollment_crm_views.lead_detail, name='lead_detail'),
    path('crm/campaigns/', enrollment_crm_views.campaign_list, name='campaign_list'),
    path('crm/analytics/', enrollment_crm_views.enrollment_analytics, name='enrollment_analytics'),
    
    # 21. (Communication System - Teacher-Parent-Student)
    path('communication/', communication_views.communication_dashboard, name='communication_dashboard'),
    
    # 22. (Mobile API Endpoints - Simple JSON APIs for Mobile App)
    path('api/mobile/attendance/mark/', mobile_api.mobile_mark_attendance, name='mobile_mark_attendance'),
    path('api/mobile/students/', mobile_api.mobile_get_students, name='mobile_get_students'),
    path('api/mobile/classes/', mobile_api.mobile_get_classes, name='mobile_get_classes'),
    path('api/mobile/attendance/summary/', mobile_api.mobile_attendance_summary, name='mobile_attendance_summary'),
    path('api/mobile/timetable/', mobile_api.mobile_get_timetable, name='mobile_get_timetable'),
    path('api/mobile/timetable/edit/', mobile_api.mobile_edit_timetable, name='mobile_edit_timetable'),
    # Marks Management
    path('api/mobile/exams/', mobile_api.mobile_get_exams, name='mobile_get_exams'),
    path('api/mobile/marks/', mobile_api.mobile_get_marks, name='mobile_get_marks'),
    path('api/mobile/marks/enter/', mobile_api.mobile_enter_marks, name='mobile_enter_marks'),
    # Events
    path('api/mobile/events/', mobile_api.mobile_get_events, name='mobile_get_events'),
    # Messaging
    path('communication/messages/', communication_views.message_list, name='message_list'),
    path('communication/messages/<int:message_id>/', communication_views.message_detail, name='message_detail'),
    path('communication/messages/compose/', communication_views.message_compose, name='message_compose'),
    # Assignments
    path('communication/assignments/', communication_views.assignment_list, name='assignment_list'),
    path('communication/assignments/<int:assignment_id>/', communication_views.assignment_detail, name='assignment_detail'),
    path('communication/assignments/create/', communication_views.assignment_create, name='assignment_create'),
    path('communication/assignments/<int:assignment_id>/submit/', communication_views.assignment_submit, name='assignment_submit'),
    # Homework
    path('communication/homework/', communication_views.homework_list, name='homework_list'),
    path('communication/homework/create/', communication_views.homework_create, name='homework_create'),
    path('communication/homework/<int:homework_id>/submit/', communication_views.homework_submit, name='homework_submit'),
    # Timetable
    path('communication/timetable/', communication_views.timetable_view, name='timetable_view'),
    path('communication/timetable/upload/', communication_views.timetable_upload, name='timetable_upload'),
    # Events - duplicate URLs removed (event_calendar and event_create already defined above)
    
    # Exam Management
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/create/', views.exam_create, name='exam_create'),
    path('exams/<int:exam_id>/schedule/add/', views.exam_schedule_create, name='exam_schedule_create'),
    
    # Exam Schedule Management
    path('exams/schedules/', views.exam_schedule_list, name='exam_schedule_list'),
    path('exams/schedules/create/', views.exam_schedule_create_standalone, name='exam_schedule_create_standalone'),
    path('exams/schedules/<int:schedule_id>/edit/', views.exam_schedule_edit, name='exam_schedule_edit'),
    path('exams/schedules/<int:schedule_id>/delete/', views.exam_schedule_delete, name='exam_schedule_delete'),
    
    # Academic & Timetable Management
    path('academics/years/', views.academic_year_list, name='academic_year_list'),
    path('academics/years/create/', views.academic_year_create, name='academic_year_create'),
    path('academics/timeslots/', views.time_slot_list, name='time_slot_list'),
    path('academics/timeslots/create/', views.time_slot_create, name='time_slot_create'),
]