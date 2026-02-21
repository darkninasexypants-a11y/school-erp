from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import SchoolUser, UserRole, School, Student, Teacher, Parent, Class, Section
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .auth_forms import ParentLoginForm, TeacherLoginForm, SchoolUserCreationForm, SchoolCreationForm, SchoolUserEditForm, SchoolLogoUpdateForm
from .authentication import create_default_roles
from .messaging_utils import send_sms_via_twilio
import json
import random


@login_required
def update_school_logo(request):
    try:
        school_user = request.user.school_profile
    except (SchoolUser.DoesNotExist, AttributeError):
        messages.error(request, 'User profile not found. Please contact administrator.')
        return redirect('students_app:home')

    if not school_user.school:
        messages.error(request, 'No school assigned to your account.')
        return redirect('students_app:admin_dashboard')

    school = school_user.school

    if request.method == 'POST':
        form = SchoolLogoUpdateForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, 'School logo updated successfully.')
            return redirect('students_app:admin_dashboard')
    else:
        form = SchoolLogoUpdateForm(instance=school)

    return render(request, 'auth/update_school_logo.html', {'form': form, 'school': school})


def multi_login(request):
    """Multi-user login page with different login options"""
    if request.user.is_authenticated:
        return redirect('students_app:dashboard')
    
    if request.method == 'POST':
        login_type = request.POST.get('login_type')
        
        if login_type == 'admin':
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_superuser:
                    return redirect('students_app:admin_dashboard')
                else:
                    return redirect('students_app:dashboard')
            else:
                messages.error(request, 'Invalid admin credentials.')
        
        elif login_type == 'parent':
            admission_id = request.POST.get('admission_id')
            password = request.POST.get('child_dob')  # Can be DOB, special chars, or any format
            
            try:
                # First, get student by admission_id
                student = Student.objects.get(admission_number=admission_id)
                
                # If password is provided, validate it
                if password:
                    # Try multiple validation methods
                    password_valid = False
                    
                    # Method 1: Check if password matches DOB (date format)
                    try:
                        from datetime import datetime
                        dob_str = student.date_of_birth.strftime('%Y-%m-%d')
                        if password == dob_str:
                            password_valid = True
                    except:
                        pass
                    
                    # Method 2: Check if password matches DOB in other formats
                    if not password_valid:
                        try:
                            dob_formats = [
                                student.date_of_birth.strftime('%d-%m-%Y'),
                                student.date_of_birth.strftime('%d/%m/%Y'),
                                student.date_of_birth.strftime('%Y/%m/%d'),
                                student.date_of_birth.strftime('%d%m%Y'),
                            ]
                            if password in dob_formats:
                                password_valid = True
                        except:
                            pass
                    
                    # Method 3: Check if password matches phone numbers (father/mother)
                    if not password_valid:
                        if password == student.father_phone or password == student.mother_phone:
                            password_valid = True
                    
                    # Method 4: Check if password matches admission_number (as backup)
                    if not password_valid:
                        if password == admission_id:
                            password_valid = True
                    
                    # If password provided but doesn't match any method, show error
                    if not password_valid:
                        messages.error(request, 'Invalid admission ID or password.')
                        return render(request, 'auth/multi_login.html')
                
                # If we reach here, login is valid
                # Create a session for parent
                request.session['parent_student_id'] = student.id
                request.session['parent_logged_in'] = True
                messages.success(request, f'Welcome! You are viewing {student.get_full_name()}\'s progress.')
                return redirect('students_app:parent_dashboard')
                
            except Student.DoesNotExist:
                if password:
                    messages.error(request, 'Invalid admission ID or password.')
                else:
                    messages.error(request, 'Invalid admission ID.')
        
        elif login_type == 'teacher':
            mobile = request.POST.get('mobile')
            teacher_name = request.POST.get('teacher_name')
            
            try:
                teacher = Teacher.objects.get(phone=mobile)
                if teacher.user.get_full_name().lower() == teacher_name.lower():
                    # Create a session for teacher
                    request.session['teacher_id'] = teacher.id
                    request.session['teacher_logged_in'] = True
                    messages.success(request, f'Welcome, {teacher.user.get_full_name()}!')
                    return redirect('students_app:teacher_dashboard')
                else:
                    messages.error(request, 'Name does not match our records.')
            except Teacher.DoesNotExist:
                messages.error(request, 'Mobile number not found in our records.')
        
        elif login_type == 'student':
            admission_id = request.POST.get('admission_id')
            student_dob = request.POST.get('student_dob')
            
            try:
                student = Student.objects.get(admission_number=admission_id, date_of_birth=student_dob)
                # Create a session for student
                request.session['student_id'] = student.id
                request.session['student_logged_in'] = True
                messages.success(request, f'Welcome back, {student.get_full_name()}!')
                return redirect('students_app:student_dashboard')
            except Student.DoesNotExist:
                messages.error(request, 'Invalid admission ID or date of birth.')
        
        elif login_type == 'librarian':
            employee_id = request.POST.get('employee_id')
            password = request.POST.get('password')
            
            try:
                librarian = Staff.objects.get(employee_id=employee_id, is_librarian=True)
                if librarian.user.check_password(password):
                    # Create a session for librarian
                    request.session['librarian_id'] = librarian.id
                    request.session['librarian_logged_in'] = True
                    messages.success(request, f'Welcome, {librarian.user.get_full_name()}!')
                    return redirect('students_app:librarian_dashboard')
                else:
                    messages.error(request, 'Invalid password.')
            except Staff.DoesNotExist:
                messages.error(request, 'Invalid employee ID or not a librarian.')
    
    context = {}
    return render(request, 'auth/multi_login.html', context)


def parent_login(request):
    """Parent login using admission ID and child name"""
    if request.user.is_authenticated:
        return redirect('students_app:parent_dashboard')
    
    if request.method == 'POST':
        form = ParentLoginForm(request.POST)
        if form.is_valid():
            admission_id = form.cleaned_data['admission_id']
            child_name = form.cleaned_data['child_name']
            
            # Authenticate using custom backend
            user = authenticate(
                request,
                username=admission_id,
                password=child_name,
                user_type='parent'
            )
            
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('students_app:parent_dashboard')
            else:
                messages.error(request, 'Invalid admission ID or child name.')
    else:
        form = ParentLoginForm()
    
    context = {'form': form}
    return render(request, 'auth/parent_login.html', context)


def teacher_login(request):
    """Teacher login using mobile number and name - Also allows Staff login"""
    if request.user.is_authenticated:
        return redirect('students_app:teacher_dashboard')
    
    if request.method == 'POST':
        form = TeacherLoginForm(request.POST)
        if form.is_valid():
            mobile = form.cleaned_data['mobile']
            name = form.cleaned_data['name']
            
            # Try to authenticate teacher first
            user = authenticate(
                request,
                username=mobile,
                password=name,
                user_type='teacher'
            )
            
            # If teacher not found, try staff
            if not user:
                try:
                    from .models import Staff
                    staff = Staff.objects.get(phone=mobile)
                    if staff.user and staff.user.get_full_name().lower() == name.lower():
                        user = staff.user
                        if staff.is_librarian:
                            login(request, user)
                            request.session['librarian_logged_in'] = True
                            request.session['librarian_id'] = staff.id
                            messages.success(request, f'Welcome, Librarian {staff.get_full_name()}!')
                            return redirect('students_app:librarian_dashboard')
                        else:
                            login(request, user)
                            request.session['teacher_logged_in'] = True
                            request.session['staff_id'] = staff.id
                            messages.success(request, f'Welcome, {staff.get_full_name()}!')
                            return redirect('students_app:teacher_dashboard')
                except Staff.DoesNotExist:
                    pass
            
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('students_app:teacher_dashboard')
            else:
                messages.error(request, 'Invalid mobile number or name.')
    else:
        form = TeacherLoginForm()
    
    context = {'form': form}
    return render(request, 'auth/teacher_login.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard for user management"""
    # Check if user is superuser (Django superuser)
    if request.user.is_superuser:
        is_super_admin = True
        school_user = None
    else:
        # Check if user has admin permissions
        try:
            school_user = request.user.school_profile
            if school_user.role.name not in ['super_admin', 'school_admin']:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('students_app:home')
            is_super_admin = school_user.role.name == 'super_admin'
        except SchoolUser.DoesNotExist:
            messages.error(request, 'User profile not found.')
            return redirect('students_app:home')
    
    if is_super_admin:
        # Super admin gets system-wide data
        total_schools = School.objects.count()
        active_schools = School.objects.filter(subscription_active=True).count()
        total_users = SchoolUser.objects.count()
        total_revenue = 0  # You can implement revenue tracking
        
        # Get all schools
        schools = School.objects.all().order_by('-created_at')[:10]
        
        # Get recent users across all schools
        recent_users = SchoolUser.objects.select_related('user', 'role', 'school').order_by('-created_at')[:10]
        
        # ========== ADD CRM METRICS ==========
        try:
            from .enrollment_crm_models import Lead, Campaign, Application
            total_leads = Lead.objects.filter(is_active=True).count()
            new_leads = Lead.objects.filter(status='new', is_active=True).count()
            enrolled_leads = Lead.objects.filter(status='enrolled', is_active=True).count()
            active_campaigns_count = Campaign.objects.filter(status='running').count()
            recent_leads = Lead.objects.filter(is_active=True).order_by('-enquiry_date')[:5]
        except:
            total_leads = 0
            new_leads = 0
            enrolled_leads = 0
            active_campaigns_count = 0
            recent_leads = []
        
        # ========== ADD ERP METRICS ==========
        total_students = Student.objects.filter(status='active').count()
        total_teachers = Teacher.objects.filter(is_active=True).count()
        total_classes = Class.objects.count()
        total_sections = Section.objects.count()
        
        # ========== ANALYTICS & PERFORMANCE METRICS ==========
        from django.db.models import Count, Avg, Q
        from django.utils import timezone
        from datetime import timedelta
        
        # School Performance Analytics
        # Get schools with basic info
        schools_list = School.objects.all().order_by('-created_at')[:5]
        
        # Calculate user counts for each school manually
        school_performance = []
        for school in schools_list:
            user_count = SchoolUser.objects.filter(school=school).count()
            school.user_count = user_count
            school.total_students = 0  # Placeholder - can be calculated if Student has school relationship
            school.total_teachers = 0  # Placeholder - can be calculated if Teacher has school relationship
            school_performance.append(school)
        
        # User Role Distribution
        role_distribution = SchoolUser.objects.values('role__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent Activity (Last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_schools = School.objects.filter(created_at__gte=seven_days_ago).count()
        recent_users_created = SchoolUser.objects.filter(created_at__gte=seven_days_ago).count()
        
        # Error Monitoring (System Health)
        # You can add error logging model later
        system_health = {
            'status': 'healthy',
            'active_schools_percentage': (active_schools / total_schools * 100) if total_schools > 0 else 0,
            'avg_users_per_school': (total_users / total_schools) if total_schools > 0 else 0,
        }
        
        # Access Level Summary
        access_levels = {
            'super_admin': SchoolUser.objects.filter(role__name='super_admin').count(),
            'school_admin': SchoolUser.objects.filter(role__name='school_admin').count(),
            'teacher': SchoolUser.objects.filter(role__name='teacher').count(),
            'student': SchoolUser.objects.filter(role__name='student').count(),
            'parent': SchoolUser.objects.filter(role__name='parent').count(),
        }
        
        context = {
            'is_super_admin': True,
            'total_schools': total_schools,
            'active_schools': active_schools,
            'total_users': total_users,
            'total_revenue': total_revenue,
            'schools': schools,
            'recent_users': recent_users,
            # CRM Data
            'total_leads': total_leads,
            'new_leads': new_leads,
            'enrolled_leads': enrolled_leads,
            'active_campaigns_count': active_campaigns_count,
            'recent_leads': recent_leads,
            # ERP Data
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_classes': total_classes,
            'total_sections': total_sections,
            # Analytics Data
            'school_performance': school_performance,
            'role_distribution': role_distribution,
            'recent_schools': recent_schools,
            'recent_users_created': recent_users_created,
            'system_health': system_health,
            'access_levels': access_levels,
        }
        return render(request, 'auth/super_admin_dashboard.html', context)
    else:
        # School admin gets school-specific data
        school = school_user.school
        total_users = SchoolUser.objects.filter(school=school).count()
        total_students = Student.objects.count()  # You can filter by school if needed
        total_teachers = Teacher.objects.count()
        total_parents = Parent.objects.count()
        
        # Get recent users for this school
        recent_users = SchoolUser.objects.filter(school=school).select_related('user', 'role').order_by('-created_at')[:10]
        
        # ========== ADD CRM METRICS ==========
        try:
            from .enrollment_crm_models import Lead, Campaign, Application
            total_leads = Lead.objects.filter(is_active=True).count()
            new_leads = Lead.objects.filter(status='new', is_active=True).count()
            enrolled_leads = Lead.objects.filter(status='enrolled', is_active=True).count()
            active_campaigns_count = Campaign.objects.filter(status='running').count()
            recent_leads = Lead.objects.filter(is_active=True).order_by('-enquiry_date')[:5]
        except:
            total_leads = 0
            new_leads = 0
            enrolled_leads = 0
            active_campaigns_count = 0
            recent_leads = []
        
        # ========== ADD ERP METRICS ==========
        # Count only classes that have active students
        total_classes = Class.objects.filter(students__status='active').distinct().count()
        total_sections = Section.objects.filter(students__status='active').distinct().count()
        
        # Today's attendance
        from django.utils import timezone
        from .models import Attendance
        today = timezone.localdate()
        today_attendance = Attendance.objects.filter(date=today).count()
        present_today = Attendance.objects.filter(date=today, status='P').count()
        
        # Today's fee collection
        from django.db.models import Sum
        from .models import FeePayment, FeeStructure, AcademicYear
        today_fees = FeePayment.objects.filter(
            payment_date=today,
            payment_status='completed'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Fee Structure Statistics
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_year:
            current_year = AcademicYear.objects.order_by('-start_date').first()
        
        total_fee_structures = 0
        total_fee_collected = 0
        pending_fees = 0
        classes_without_fee_structure = []
        
        if current_year:
            total_fee_structures = FeeStructure.objects.filter(academic_year=current_year).count()
            # Calculate total fee collected
            total_fee_collected = FeePayment.objects.filter(
                academic_year=current_year,
                payment_status='completed'
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            # Calculate pending fees (simplified - total due - total paid)
            total_due = 0
            for fee_structure in FeeStructure.objects.filter(academic_year=current_year):
                # Use 'students' as related_name (not 'student_set')
                student_count = fee_structure.class_assigned.students.filter(status='active').count() if fee_structure.class_assigned else 0
                total_due += float(fee_structure.get_total_fee()) * student_count
            pending_fees = max(0, total_due - float(total_fee_collected))
            
            # Find classes with students but no fee structure
            classes_with_students = Class.objects.filter(students__status='active').distinct()
            for cls in classes_with_students:
                if not FeeStructure.objects.filter(class_assigned=cls, academic_year=current_year).exists():
                    classes_without_fee_structure.append(cls)
        
        context = {
            'is_super_admin': False,
            'school': school,
            'total_users': total_users,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_parents': total_parents,
            'recent_users': recent_users,
            # CRM Data
            'total_leads': total_leads,
            'new_leads': new_leads,
            'enrolled_leads': enrolled_leads,
            'active_campaigns_count': active_campaigns_count,
            'recent_leads': recent_leads,
            # ERP Data
            'total_classes': total_classes,
            'total_sections': total_sections,
            'today_attendance': today_attendance,
            'present_today': present_today,
            'today_fees': today_fees,
            # Fee Structure Data
            'total_fee_structures': total_fee_structures,
            'total_fee_collected': total_fee_collected,
            'pending_fees': pending_fees,
            'current_academic_year': current_year,
            'classes_without_fee_structure': classes_without_fee_structure,
        }
        return render(request, 'auth/admin_dashboard.html', context)


@login_required
def create_user(request):
    """Create new school user"""
    # Check admin permissions
    try:
        school_user = request.user.school_profile
        if school_user.role.name not in ['super_admin', 'school_admin']:
            messages.error(request, 'You do not have permission to create users.')
            return redirect('students_app:home')
    except SchoolUser.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('students_app:home')
    
    if request.method == 'POST':
        form = SchoolUserCreationForm(request.POST, user=request.user)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, 'User created successfully!')
            return redirect('students_app:admin_dashboard')
    else:
        # Prefill role from query param if provided (e.g., ?role=assistant_viewer)
        role_code = request.GET.get('role')
        initial = {}
        if role_code:
            try:
                role = UserRole.objects.get(name=role_code)
                initial['role'] = role.id
            except UserRole.DoesNotExist:
                pass
        form = SchoolUserCreationForm(initial=initial, user=request.user)
    
    context = {'form': form}
    return render(request, 'auth/create_user.html', context)


@login_required
def send_school_otp(request):
    """Send OTP to phone number during school creation"""
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        
        # Clean phone number (remove non-digits)
        phone = ''.join(filter(str.isdigit, phone))
        
        # Validate phone number
        if not phone or len(phone) != 10:
            return JsonResponse({'success': False, 'error': 'Please enter a valid 10-digit phone number.'})
        
        if phone[0] == '0':
            return JsonResponse({'success': False, 'error': 'Phone number cannot start with 0.'})
        
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        
        # Store OTP in session
        request.session['school_creation_otp'] = otp
        request.session['school_creation_phone'] = phone
        request.session['school_creation_otp_time'] = timezone.now().isoformat()
        
        # Send OTP via SMS
        message = f"Your OTP for school creation is {otp}. Valid for 10 minutes."
        result = send_sms_via_twilio(phone, message)
        
        # Always include OTP in response for development/testing (remove in production)
        response_data = {
            'success': True,
            'otp': otp  # Include OTP for testing purposes
        }
        
        if result.get('success'):
            response_data['message'] = 'OTP sent successfully to your phone number.'
        else:
            # Even if SMS fails, store OTP in session for testing
            response_data['message'] = f'OTP generated: {otp} (SMS sending failed: {result.get("error", "Unknown error")})'
        
        return JsonResponse(response_data)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def verify_school_otp(request):
    """Verify OTP during school creation"""
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        
        # Get stored OTP from session
        stored_otp = request.session.get('school_creation_otp')
        stored_phone = request.session.get('school_creation_phone', '')
        otp_time_str = request.session.get('school_creation_otp_time')
        
        if not stored_otp:
            return JsonResponse({'success': False, 'error': 'OTP not found. Please request a new OTP.'})
        
        if otp_time_str:
            # Check if OTP is expired (10 minutes)
            otp_time = timezone.datetime.fromisoformat(otp_time_str)
            if timezone.now() - otp_time > timedelta(minutes=10):
                return JsonResponse({'success': False, 'error': 'OTP has expired. Please request a new OTP.'})
        
        if entered_otp != stored_otp:
            return JsonResponse({'success': False, 'error': 'Invalid OTP. Please check and try again.'})
        
        # OTP is valid, mark as verified in session
        request.session['school_creation_otp_verified'] = True
        return JsonResponse({'success': True, 'message': 'OTP verified successfully!'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def send_login_otp(request):
    """Send OTP to phone number or email for login"""
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                identifier = data.get('mobile') or data.get('identifier', '').strip()
                login_type = data.get('login_type', 'phone')
                device_id = data.get('device_id', '').strip()  # For mobile app
                is_mobile_app = data.get('is_mobile_app', False)  # Flag to identify mobile app
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON data.'})
        else:
            identifier = request.POST.get('mobile') or request.POST.get('identifier', '').strip()
            login_type = request.POST.get('login_type', 'phone')
            device_id = request.POST.get('device_id', '').strip()
            is_mobile_app = request.POST.get('is_mobile_app', 'false').lower() == 'true'
        
        # For mobile app: Check if device is already verified
        if is_mobile_app and device_id:
            from .models import VerifiedDevice
            # Clean identifier for phone lookup
            if login_type == 'phone':
                phone = ''.join(filter(str.isdigit, identifier))
                try:
                    # Find user by phone
                    school_user = SchoolUser.objects.get(phone=phone)
                    user = school_user.user
                    
                    # Check if device is already verified for this user
                    verified_device = VerifiedDevice.objects.filter(
                        device_id=device_id,
                        user=user,
                        is_active=True
                    ).first()
                    
                    if verified_device:
                        # Device already verified, no need for OTP
                        return JsonResponse({
                            'success': True,
                            'device_verified': True,
                            'message': 'Device already verified. You can login directly.',
                            'skip_otp': True
                        })
                except SchoolUser.DoesNotExist:
                    pass  # Continue to send OTP
        
        # Clean phone number if it's a phone login
        if login_type == 'phone':
            phone = ''.join(filter(str.isdigit, identifier))
            
            # Validate phone number
            if not phone or len(phone) != 10:
                return JsonResponse({'success': False, 'error': 'Please enter a valid 10-digit phone number.'})
            
            if phone[0] == '0':
                return JsonResponse({'success': False, 'error': 'Phone number cannot start with 0.'})
            
            # For mobile app: Check if device is already verified
            if is_mobile_app and device_id:
                from .models import VerifiedDevice
                try:
                    # Find user by phone
                    school_user = SchoolUser.objects.get(phone=phone)
                    user = school_user.user
                    
                    # Check if device is already verified for this user
                    verified_device = VerifiedDevice.objects.filter(
                        device_id=device_id,
                        user=user,
                        is_active=True
                    ).first()
                    
                    if verified_device:
                        # Device already verified, no need for OTP
                        verified_device.update_last_used()
                        return JsonResponse({
                            'success': True,
                            'device_verified': True,
                            'message': 'Device already verified. You can login directly.',
                            'skip_otp': True
                        })
                except SchoolUser.DoesNotExist:
                    pass  # Continue to send OTP
            
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Store OTP in session (also store device_id for mobile app)
            request.session['login_otp'] = otp
            request.session['login_identifier'] = phone
            request.session['login_type'] = 'phone'
            request.session['login_otp_time'] = timezone.now().isoformat()
            if device_id:
                request.session['login_device_id'] = device_id
            if is_mobile_app:
                request.session['is_mobile_app'] = True
            
            # Send OTP via SMS
            message = f"Your login OTP is {otp}. Valid for 10 minutes."
            result = send_sms_via_twilio(phone, message)
            
            if result.get('success'):
                response_data = {
                    'success': True,
                    'message': 'OTP sent successfully to your phone number.'
                }
                # For development: include OTP in response (remove in production)
                import os
                if os.environ.get('DEBUG', 'False') == 'True' or True:  # Always show for now
                    response_data['otp'] = otp
                return JsonResponse(response_data)
            else:
                # Even if SMS fails, store OTP in session for testing
                response_data = {
                    'success': True,
                    'message': f'OTP generated: {otp} (SMS sending failed: {result.get("error", "Unknown error")})'
                }
                # For development: include OTP in response
                response_data['otp'] = otp
                return JsonResponse(response_data)
        
        elif login_type == 'email':
            email = identifier.strip().lower()
            
            # Validate email format
            if '@' not in email or '.' not in email:
                return JsonResponse({'success': False, 'error': 'Please enter a valid email address.'})
            
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Store OTP in session
            request.session['login_otp'] = otp
            request.session['login_identifier'] = email
            request.session['login_type'] = 'email'
            request.session['login_otp_time'] = timezone.now().isoformat()
            
            # TODO: Send OTP via email (implement email sending functionality)
            # For now, return OTP in response for testing
            return JsonResponse({
                'success': True,
                'message': f'OTP generated: {otp} (Email sending not implemented yet)'
            })
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid login type.'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def verify_login_otp(request):
    """Verify OTP and login user"""
    if request.method == 'POST':
        # Handle both JSON and form data
        request_data = {}
        if request.content_type == 'application/json':
            try:
                request_data = json.loads(request.body)
                entered_otp = request_data.get('otp', '').strip()
                identifier = request_data.get('mobile') or request_data.get('identifier', '').strip()
                login_type = request_data.get('login_type', 'phone')
                device_id = request_data.get('device_id', '').strip()
                is_mobile_app = request_data.get('is_mobile_app', False)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON data.'})
        else:
            entered_otp = request.POST.get('otp', '').strip()
            identifier = request.POST.get('mobile') or request.POST.get('identifier', '').strip()
            login_type = request.POST.get('login_type', 'phone')
            device_id = request.POST.get('device_id', '').strip()
            is_mobile_app = request.POST.get('is_mobile_app', 'false').lower() == 'true'
        
        # Get stored OTP from session
        stored_otp = request.session.get('login_otp')
        stored_identifier = request.session.get('login_identifier', '')
        stored_login_type = request.session.get('login_type', 'phone')
        otp_time_str = request.session.get('login_otp_time')
        
        if not stored_otp:
            return JsonResponse({'success': False, 'error': 'OTP not found. Please request a new OTP.'})
        
        # Verify login type matches
        if stored_login_type != login_type:
            return JsonResponse({'success': False, 'error': 'Login type mismatch. Please request a new OTP.'})
        
        # Clean identifier for comparison
        if login_type == 'phone':
            identifier = ''.join(filter(str.isdigit, identifier))
            stored_identifier = ''.join(filter(str.isdigit, stored_identifier))
        else:
            identifier = identifier.strip().lower()
            stored_identifier = stored_identifier.strip().lower()
        
        if stored_identifier != identifier:
            return JsonResponse({'success': False, 'error': 'Identifier does not match. Please request a new OTP.'})
        
        if otp_time_str:
            # Check if OTP is expired (10 minutes)
            otp_time = timezone.datetime.fromisoformat(otp_time_str)
            if timezone.now() - otp_time > timedelta(minutes=10):
                return JsonResponse({'success': False, 'error': 'OTP has expired. Please request a new OTP.'})
        
        if entered_otp != stored_otp:
            return JsonResponse({'success': False, 'error': 'Invalid OTP. Please check and try again.'})
        
        # OTP is valid, now find and login the user
        user = None
        if login_type == 'phone':
            # Find user by phone number in SchoolUser
            try:
                school_user = SchoolUser.objects.get(phone=identifier)
                user = school_user.user
            except SchoolUser.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'No account found with this phone number.'})
        elif login_type == 'email':
            # Find user by email
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'No account found with this email address.'})
        
        if user and user.is_active:
            # Login the user
            login(request, user)
            
            # For mobile app: Register/verify device after successful OTP verification
            device_id = request.session.get('login_device_id') or device_id
            is_mobile_app = request.session.get('is_mobile_app', False) or is_mobile_app
            
            if is_mobile_app and device_id:
                from .models import VerifiedDevice
                # Register device as verified
                verified_device, created = VerifiedDevice.objects.get_or_create(
                    device_id=device_id,
                    user=user,
                    defaults={
                        'phone': identifier if login_type == 'phone' else '',
                        'device_name': request.POST.get('device_name', '') or (request.content_type == 'application/json' and json.loads(request.body).get('device_name', '')) or '',
                        'device_type': request.POST.get('device_type', 'android') or (request.content_type == 'application/json' and json.loads(request.body).get('device_type', 'android')) or 'android',
                    }
                )
                if not created:
                    # Update existing verified device
                    verified_device.update_last_used()
                    verified_device.phone = identifier if login_type == 'phone' else verified_device.phone
                    verified_device.save()
            
            # Set session expiry to end of day (23:59:59) for OTP login
            # This makes the login valid for the whole day
            now = timezone.now()
            # Calculate end of day (23:59:59)
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            # Calculate seconds until end of day
            seconds_until_midnight = (end_of_day - now).total_seconds()
            # Set session expiry to end of day (minimum 1 second)
            request.session.set_expiry(max(int(seconds_until_midnight), 1))
            
            # Also store a flag to indicate this is an OTP login (for tracking)
            request.session['otp_login'] = True
            request.session['otp_login_date'] = now.date().isoformat()
            
            # Clear OTP from session
            request.session.pop('login_otp', None)
            request.session.pop('login_identifier', None)
            request.session.pop('login_type', None)
            request.session.pop('login_otp_time', None)
            request.session.pop('login_device_id', None)
            request.session.pop('is_mobile_app', None)
            
            return JsonResponse({
                'success': True,
                'message': 'OTP verified successfully! Logging you in...',
                'redirect_url': '/dashboard/',  # You can customize this
                'device_verified': is_mobile_app and device_id  # Indicate if device was verified
            })
        else:
            return JsonResponse({'success': False, 'error': 'User account is inactive.'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def mobile_direct_login(request):
    """Direct login for mobile app when device is already verified (skip OTP)"""
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                identifier = data.get('mobile') or data.get('identifier', '').strip()
                login_type = data.get('login_type', 'phone')
                device_id = data.get('device_id', '').strip()
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Invalid JSON data.'})
        else:
            identifier = request.POST.get('mobile') or request.POST.get('identifier', '').strip()
            login_type = request.POST.get('login_type', 'phone')
            device_id = request.POST.get('device_id', '').strip()
        
        if not device_id:
            return JsonResponse({'success': False, 'error': 'Device ID is required for mobile app login.'})
        
        # Find user
        user = None
        if login_type == 'phone':
            phone = ''.join(filter(str.isdigit, identifier))
            try:
                school_user = SchoolUser.objects.get(phone=phone)
                user = school_user.user
            except SchoolUser.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'No account found with this phone number.'})
        elif login_type == 'email':
            email = identifier.strip().lower()
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'No account found with this email address.'})
        
        if not user or not user.is_active:
            return JsonResponse({'success': False, 'error': 'User account not found or inactive.'})
        
        # Check if device is verified
        from .models import VerifiedDevice
        verified_device = VerifiedDevice.objects.filter(
            device_id=device_id,
            user=user,
            is_active=True
        ).first()
        
        if not verified_device:
            return JsonResponse({
                'success': False,
                'error': 'Device not verified. Please login with OTP first.',
                'requires_otp': True
            })
        
        # Device is verified, login directly
        login(request, user)
        
        # Update last used
        verified_device.update_last_used()
        
        # Set session expiry to end of day
        now = timezone.now()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        seconds_until_midnight = (end_of_day - now).total_seconds()
        request.session.set_expiry(max(int(seconds_until_midnight), 1))
        
        request.session['otp_login'] = True
        request.session['otp_login_date'] = now.date().isoformat()
        request.session['mobile_app_login'] = True
        
        return JsonResponse({
            'success': True,
            'message': 'Login successful!',
            'redirect_url': '/dashboard/',
            'device_verified': True
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def create_school(request):
    """Create new school with admin user"""
    # Check super admin permissions
    try:
        school_user = request.user.school_profile
        if school_user.role.name not in ['super_admin', 'assistant_creator']:
            messages.error(request, 'You do not have permission to create schools.')
            return redirect('students_app:home')
    except (SchoolUser.DoesNotExist, AttributeError):
        # Handle case where user doesn't have school_profile
        messages.error(request, 'User profile not found. Please contact administrator.')
        return redirect('students_app:home')
    
    if request.method == 'POST':
        # Check if OTP is verified
        phone = request.POST.get('phone', '').strip()
        phone_cleaned = ''.join(filter(str.isdigit, phone))
        
        if phone_cleaned:
            otp_verified = request.session.get('school_creation_otp_verified', False)
            stored_phone = request.session.get('school_creation_phone', '')
            
            # Check if phone matches and OTP is verified
            if phone_cleaned != stored_phone or not otp_verified:
                messages.error(request, 'Please verify your mobile number with OTP before creating the school.')
                form = SchoolCreationForm(request.POST, request.FILES)
                context = {'form': form}
                return render(request, 'auth/create_school.html', context)
        
        form = SchoolCreationForm(request.POST, request.FILES)
        
        if form.is_valid():
            school = form.save()
            
            # Get custom username, email, and password from form
            admin_username = form.cleaned_data.get('admin_username')
            admin_email = form.cleaned_data.get('admin_email') or school.email
            admin_password = form.cleaned_data.get('admin_password')
            
            # Create school admin user
            admin_user = User.objects.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                first_name=school.principal_name or 'School',
                last_name='Admin',
                is_staff=True,
                is_active=True
            )
            
            # Create school admin role
            school_admin_role = UserRole.objects.get(name='school_admin')
            SchoolUser.objects.create(
                user=admin_user,
                role=school_admin_role,
                school=school,
                login_id=admin_username,
                custom_password=admin_password,
                phone=school.phone
            )
            
            # Create school-specific feature configuration
            try:
                from .system_config import SchoolFeatureConfiguration
                school_config = SchoolFeatureConfiguration.get_or_create_for_school(school)
                
                # Set features based on form data
                feature_fields = [
                    'crm_enabled', 'erp_enabled', 'id_card_generator', 'fee_payment_online',
                    'attendance_tracking', 'marks_entry', 'library_management',
                    'transport_management', 'hostel_management', 'canteen_management'
                ]
                
                for field in feature_fields:
                    if hasattr(school_config, field):
                        # If checkbox is checked, set to True, otherwise None (use global)
                        if field in request.POST and request.POST[field] == 'on':
                            setattr(school_config, field, True)
                        else:
                            setattr(school_config, field, None)  # Use global setting
                
                school_config.save()
            except Exception as e:
                # If feature config fails, continue anyway
                print(f"Error creating school feature config: {e}")
            
            # Clear OTP session data after successful school creation
            request.session.pop('school_creation_otp', None)
            request.session.pop('school_creation_phone', None)
            request.session.pop('school_creation_otp_time', None)
            request.session.pop('school_creation_otp_verified', None)
            
            messages.success(request, f'School "{school.name}" and admin user created successfully!')
            messages.info(request, f'Admin login credentials - Username: {admin_username}')
            return redirect('students_app:admin_dashboard')
    else:
        form = SchoolCreationForm()
    
    context = {'form': form}
    return render(request, 'auth/create_school.html', context)


@login_required
def user_list(request):
    """List all users with filtering"""
    # Check admin permissions
    is_superuser = False
    user_school = None
    
    if request.user.is_superuser:
        is_superuser = True
    else:
        try:
            school_user = request.user.school_profile
            user_school = school_user.school
            if school_user.role.name not in ['super_admin', 'school_admin', 'assistant_viewer', 'assistant_creator']:
                messages.error(request, 'You do not have permission to view users.')
                return redirect('students_app:home')
            
            # Check if role is super_admin (can see all)
            if school_user.role.name == 'super_admin':
                is_superuser = True
                
        except SchoolUser.DoesNotExist:
            messages.error(request, 'User profile not found.')
            return redirect('students_app:home')
    
    # Get users with filters
    users = SchoolUser.objects.select_related('user', 'role', 'school').all()
    
    # If not superuser, restrict to own school
    if not is_superuser and user_school:
        users = users.filter(school=user_school)
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role__name=role_filter)
    
    # Filter by school (only for superusers)
    school_filter = request.GET.get('school', '')
    if is_superuser and school_filter:
        users = users.filter(school_id=school_filter)
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Search
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(user__first_name__icontains=search) | 
            Q(user__last_name__icontains=search) | 
            Q(user__email__icontains=search) |
            Q(login_id__icontains=search)
        )
    
    # Get filter options
    roles = UserRole.objects.filter(is_active=True)
    
    # Schools filter only for superusers
    schools = School.objects.all() if is_superuser else None
    
    context = {
        'users': users,
        'roles': roles,
        'schools': schools,
        'is_superuser': is_superuser,
        'current_school': school_filter,
        'current_role': role_filter,
        'current_status': status_filter,
        'current_search': search,
    }
    return render(request, 'auth/user_list.html', context)


@login_required
def toggle_user_status(request, user_id):
    """Toggle user active/inactive status"""
    # Check admin permissions
    is_superuser = False
    user_school = None
    
    if request.user.is_superuser:
        is_superuser = True
    else:
        try:
            school_user = request.user.school_profile
            user_school = school_user.school
            if school_user.role.name not in ['super_admin', 'school_admin']:
                messages.error(request, 'You do not have permission to modify users.')
                return redirect('students_app:user_list')
            
            if school_user.role.name == 'super_admin':
                is_superuser = True
        except SchoolUser.DoesNotExist:
            messages.error(request, 'User profile not found.')
            return redirect('students_app:user_list')
    
    # Get the user to toggle
    school_user = get_object_or_404(SchoolUser, id=user_id)
    
    # Prevent toggling yourself
    if school_user.user.id == request.user.id:
        messages.error(request, 'You cannot deactivate your own account!')
        return redirect('students_app:user_list')
    
    # If not superuser, restrict to own school
    if not is_superuser and user_school:
        if school_user.school != user_school:
            messages.error(request, 'You can only modify users from your own school.')
            return redirect('students_app:user_list')
    
    # Toggle status
    school_user.is_active = not school_user.is_active
    school_user.user.is_active = school_user.is_active
    school_user.save()
    school_user.user.save()
    
    status_text = "activated" if school_user.is_active else "deactivated"
    messages.success(request, f'User "{school_user.user.get_full_name()}" has been {status_text} successfully!')
    
    return redirect('students_app:user_list')


@login_required
def edit_user(request, user_id):
    """Edit user details and change password"""
    # Check admin permissions
    is_superuser = False
    user_school = None
    
    if request.user.is_superuser:
        is_superuser = True
    else:
        try:
            school_user = request.user.school_profile
            user_school = school_user.school
            if school_user.role.name not in ['super_admin', 'school_admin']:
                messages.error(request, 'You do not have permission to edit users.')
                return redirect('students_app:user_list')
            
            if school_user.role.name == 'super_admin':
                is_superuser = True
        except SchoolUser.DoesNotExist:
            messages.error(request, 'User profile not found.')
            return redirect('students_app:user_list')
    
    # Get the user to edit
    school_user = get_object_or_404(SchoolUser, id=user_id)
    user = school_user.user
    
    # If not superuser, restrict to own school
    if not is_superuser and user_school:
        if school_user.school != user_school:
            messages.error(request, 'You can only edit users from your own school.')
            return redirect('students_app:user_list')
    
    if request.method == 'POST':
        form = SchoolUserEditForm(request.POST, instance=user, school_user=school_user, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user.get_full_name()}" has been updated successfully!')
            return redirect('students_app:user_list')
    else:
        form = SchoolUserEditForm(instance=user, school_user=school_user, user=request.user)
    
    context = {
        'form': form,
        'school_user': school_user,
        'user': user,
    }
    return render(request, 'auth/edit_user.html', context)


@login_required
def user_logout(request):
    """Logout user and clear all sessions"""
    # Clear parent session
    if 'parent_logged_in' in request.session:
        del request.session['parent_logged_in']
    if 'parent_student_id' in request.session:
        del request.session['parent_student_id']
    
    # Clear teacher session
    if 'teacher_logged_in' in request.session:
        del request.session['teacher_logged_in']
    if 'teacher_id' in request.session:
        del request.session['teacher_id']
    
    # Clear student session
    if 'student_logged_in' in request.session:
        del request.session['student_logged_in']
    if 'student_id' in request.session:
        del request.session['student_id']
    
    # Clear librarian session
    if 'librarian_logged_in' in request.session:
        del request.session['librarian_logged_in']
    if 'librarian_id' in request.session:
        del request.session['librarian_id']
    
    # Logout Django user
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('students_app:multi_login')


def setup_initial_data(request):
    """Setup initial roles and super admin"""
    # Create default roles
    create_default_roles()
    
    # Create super admin if doesn't exist
    if not User.objects.filter(username='superadmin').exists():
        user = User.objects.create_user(
            username='superadmin',
            email='admin@schoolerp.com',
            password='admin123',
            first_name='Super',
            last_name='Admin',
            is_staff=True,
            is_superuser=True
        )
        
        # Create super admin role
        super_admin_role = UserRole.objects.get(name='super_admin')
        SchoolUser.objects.create(
            user=user,
            role=super_admin_role,
            login_id='superadmin',
            custom_password='admin123'
        )
        
        messages.success(request, 'Initial setup completed! Super admin created.')
    else:
        messages.info(request, 'Initial setup already completed.')
    
    return redirect('students_app:multi_login')


def django_admin_redirect(request):
    """Redirect to Django admin"""
    return redirect('/django-admin/')
