from django.utils.translation import gettext as _
from django.conf import settings

def get_sidebar_text(language='en'):
    """Get sidebar text based on language preference"""
    
    if language == 'hi':
        return {
            # Common
            'dashboard': 'डैशबोर्ड',
            'logout': 'लॉगआउट',
            'admin_panel': 'एडमिन पैनल',
            'communication': 'कम्युनिकेशन',
            'notices': 'नोटिस',
            'events': 'इवेंट्स',
            'system': 'सिस्टम',
            
            # Company Admin
            'company_admin_panel': 'Company Admin Panel',
            'school_management': 'स्कूल प्रबंधन',
            'new_school': 'नया स्कूल',
            'all_schools': 'सभी स्कूल',
            'new_user': 'नया यूजर',
            'all_users': 'सभी यूजर',
            'super_admin_tools': 'सुपर एडमिन टूल्स',
            'id_card_generator': 'ID कार्ड जनरेटर',
            'calculator': 'कैलकुलेटर',
            
            # School Admin
            'school_admin_panel': 'School Admin Panel',
            'students_teachers': 'छात्र और शिक्षक',
            'all_students': 'सभी छात्र',
            'student_import': 'छात्र इम्पोर्ट (Excel)',
            'all_teachers': 'सभी शिक्षक',
            'academics': 'शैक्षणिक (ACADEMICS)',
            'timetable': 'टाइमटेबल',
            'attendance': 'अटेंडेंस (Attendance)',
            'marks_entry': 'मार्क्स एंट्री',
            'fees_finance': 'फीस और वित्त (FINANCE)',
            'fee_history': 'फीस इतिहास',
            'pay_fees': 'फीस भुगतान',
            'all_receipts': 'सभी रसीदें',
            'id_certificates': 'ID और सर्टिफिकेट',
            'id_cards': 'ID कार्ड्स',
            'bulk_id_generation': 'बल्क ID जनरेशन',
            'certificates': 'सर्टिफिकेट्स',
            
            # Teacher
            'teacher_panel': 'Teacher Panel',
            'my_classes': 'मेरी कक्षाएं',
            'my_dashboard': 'मेरा डैशबोर्ड',
            'my_timetable': 'मेरा टाइमटेबल',
            'student_management': 'छात्र प्रबंधन',
            'my_students': 'मेरे छात्र',
            
            # Student
            'student_panel': 'Student Panel',
            'my_info': 'मेरी जानकारी',
            'my_profile': 'मेरा प्रोफाइल',
            'my_attendance': 'मेरी अटेंडेंस',
            'my_marks': 'मेरे मार्क्स',
            'exams': 'परीक्षाएं',
            
            # Parent
            'parent_panel': 'Parent Panel',
            'my_children': 'मेरे बच्चे',
            'academic_info': 'शैक्षणिक जानकारी',
            'marks': 'मार्क्स',
            
            # Librarian
            'library_panel': 'Library Panel',
            'library_management': 'लाइब्रेरी प्रबंधन',
            'library_dashboard': 'लाइब्रेरी डैशबोर्ड',
            'all_books': 'सभी किताबें',
            'issue_book': 'किताब जारी करें',
            'return_book': 'किताब वापसी',
        }
    else:  # English
        return {
            # Common
            'dashboard': 'Dashboard',
            'logout': 'Logout',
            'admin_panel': 'Admin Panel',
            'communication': 'Communication',
            'notices': 'Notices',
            'events': 'Events',
            'system': 'System',
            
            # Company Admin
            'company_admin_panel': 'Company Admin Panel',
            'school_management': 'School Management',
            'new_school': 'New School',
            'all_schools': 'All Schools',
            'new_user': 'New User',
            'all_users': 'All Users',
            'super_admin_tools': 'Super Admin Tools',
            'id_card_generator': 'ID Card Generator',
            'calculator': 'Calculator',
            
            # School Admin
            'school_admin_panel': 'School Admin Panel',
            'students_teachers': 'Students & Teachers',
            'all_students': 'All Students',
            'student_import': 'Student Import (Excel)',
            'all_teachers': 'All Teachers',
            'academics': 'Academics',
            'timetable': 'Timetable',
            'attendance': 'Attendance',
            'marks_entry': 'Marks Entry',
            'fees_finance': 'Fees & Finance',
            'fee_history': 'Fee History',
            'pay_fees': 'Pay Fees',
            'all_receipts': 'All Receipts',
            'id_certificates': 'ID & Certificates',
            'id_cards': 'ID Cards',
            'bulk_id_generation': 'Bulk ID Generation',
            'certificates': 'Certificates',
            
            # Teacher
            'teacher_panel': 'Teacher Panel',
            'my_classes': 'My Classes',
            'my_dashboard': 'My Dashboard',
            'my_timetable': 'My Timetable',
            'student_management': 'Student Management',
            'my_students': 'My Students',
            
            # Student
            'student_panel': 'Student Panel',
            'my_info': 'My Information',
            'my_profile': 'My Profile',
            'my_attendance': 'My Attendance',
            'my_marks': 'My Marks',
            'exams': 'Exams',
            
            # Parent
            'parent_panel': 'Parent Panel',
            'my_children': 'My Children',
            'academic_info': 'Academic Information',
            'marks': 'Marks',
            
            # Librarian
            'library_panel': 'Library Panel',
            'library_management': 'Library Management',
            'library_dashboard': 'Library Dashboard',
            'all_books': 'All Books',
            'issue_book': 'Issue Book',
            'return_book': 'Return Book',
        }

def get_user_language(request):
    """Get user's preferred language from session or default to English"""
    return request.session.get('language', 'en')

def set_user_language(request, language):
    """Set user's preferred language in session"""
    if language in ['en', 'hi']:
        request.session['language'] = language
        return True
    return False

