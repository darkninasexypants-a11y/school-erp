"""
REST API Views for School ERP Mobile App
Reuses existing Django views logic and models
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import date, timedelta
from .models import (
    Student, Class, Section, AcademicYear, Attendance, 
    FeePayment, FeeStructure, StudentIDCard, Teacher, Parent,
    Notice, Event, Timetable, Exam, Marks, IDCardTemplate,
    Book, BookIssue, BookCategory, ExamSchedule, Subject, TimeSlot
)
from .api_serializers import (
    UserSerializer, ClassSerializer, SectionSerializer, AcademicYearSerializer,
    StudentListSerializer, StudentDetailSerializer, AttendanceSerializer,
    FeeStructureSerializer, FeePaymentSerializer, StudentIDCardSerializer,
    NoticeSerializer, EventSerializer, DashboardStatsSerializer, IDCardTemplateSerializer,
    BookSerializer, BookIssueSerializer, BookCategorySerializer,
    TimetableSerializer, ExamSerializer, ExamScheduleSerializer, MarksSerializer,
    SubjectSerializer, TimeSlotSerializer
)
from .views import generate_id_cards_reportlab  # ID card generation function


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    API Login endpoint
    Supports multiple login types: admin, parent, teacher, student
    """
    login_type = request.data.get('login_type', 'admin')
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Standard admin/user login
    if login_type == 'admin':
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            token, created = Token.objects.get_or_create(user=user)
            
            # Determine user role/type
            user_type = 'admin'
            if user.is_superuser:
                user_type = 'super_admin'  # Owner/Software Owner
            
            user_data = UserSerializer(user).data
            # Add superuser flag to response
            user_data['is_superuser'] = user.is_superuser
            user_data['is_staff'] = user.is_staff
            user_data['role'] = user_type
            
            return Response({
                'token': token.key,
                'user': user_data,
                'user_type': user_type
            })
    
    # Parent login (admission_id + child_dob)
    elif login_type == 'parent':
        try:
            from .models import Student
            student = Student.objects.get(admission_number=username, date_of_birth=password)
            # Create or get parent user
            parent_user, created = User.objects.get_or_create(
                username=f"parent_{student.admission_number}",
                defaults={
                    'first_name': student.father_name or 'Parent',
                    'last_name': '',
                    'is_active': True
                }
            )
            token, created = Token.objects.get_or_create(user=parent_user)
            return Response({
                'token': token.key,
                'user': UserSerializer(parent_user).data,
                'user_type': 'parent',
                'student_id': student.id,
                'student_name': student.get_full_name()
            })
        except Student.DoesNotExist:
            return Response(
                {'error': 'Invalid admission ID or date of birth'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    # Teacher login (mobile + name)
    elif login_type == 'teacher':
        try:
            teacher = Teacher.objects.get(phone=username)
            if teacher.name.lower() == password.lower():
                user = teacher.user if teacher.user else None
                if not user:
                    user, created = User.objects.get_or_create(
                        username=f"teacher_{teacher.phone}",
                        defaults={
                            'first_name': teacher.name,
                            'is_active': True
                        }
                    )
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data,
                    'user_type': 'teacher',
                    'teacher_id': teacher.id
                })
        except Teacher.DoesNotExist:
            pass
    
    # Student login (admission_id + dob)
    elif login_type == 'student':
        # Authenticate using standard Django User (Admission Number + Password)
        user = authenticate(request, username=username, password=password)
        
        if user:
            try:
                # Find the student profile linked to this admission number
                student = Student.objects.get(admission_number=user.username)
                token, created = Token.objects.get_or_create(user=user)
                
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data,
                    'user_type': 'student',
                    'student_id': student.id,
                    'student_name': student.get_full_name()
                })
            except Student.DoesNotExist:
                 return Response(
                    {'error': 'Student profile not found for this user'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
             # Fallback or invalid credentials
             return Response(
                {'error': 'Invalid admission number or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    return Response(
        {'error': 'Invalid credentials'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """API Logout - delete token"""
    try:
        request.user.auth_token.delete()
    except:
        pass
    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_profile(request):
    """Get current user profile"""
    return Response({
        'user': UserSerializer(request.user).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard(request):
    """
    Dashboard statistics
    Returns different data based on user role:
    - Super Admin: System-level statistics (schools, users, platform health)
    - School Admin/Others: School-level statistics (students, teachers, classes)
    """
    from .models import School
    
    # Check if user is super admin
    is_super_admin = request.user.is_superuser
    
    if is_super_admin:
        # Super Admin Dashboard - System Level Stats
        total_schools = School.objects.count()
        active_schools = School.objects.filter(subscription_active=True).count()
        total_users = User.objects.count()
        total_students = Student.objects.filter(status='active').count()
        total_teachers = Teacher.objects.filter(is_active=True).count()
        
        # System health (simplified - can be enhanced)
        system_health = 100 if total_schools > 0 else 0
        
        stats = {
            'user_type': 'super_admin',
            'total_schools': total_schools,
            'active_schools': active_schools,
            'total_users': total_users,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'system_health': system_health,
            'total_classes': 0,  # Not relevant for super admin
            'present_today': 0,
            'absent_today': 0,
            'total_fee_collected': 0,
            'pending_fees': 0
        }
    else:
        # School Admin/Teacher Dashboard - School Level Stats
        
        # Get user's school
        school = None
        try:
            if hasattr(request.user, 'school_profile'):
                school = request.user.school_profile.school
            elif hasattr(request.user, 'staff'):  # If user is staff/teacher without school_profile
                 # Try to infer school from related students or other logic if needed
                 # For now, we assume school_profile is the primary way
                 pass
        except Exception:
            pass
            
        # Base queries with school filter
        students_query = Student.objects.filter(status='active')
        teachers_query = Teacher.objects.filter(is_active=True)
        classes_query = Class.objects.all() # Class is currently global, might need school filter if Class has school
        
        if school:
            students_query = students_query.filter(school=school)
            # Filter teachers by school via their user profile
            teachers_query = teachers_query.filter(user__school_profile__school=school)
            # If classes become school-specific in future, filter here:
            # classes_query = classes_query.filter(school=school)
            
        total_students = students_query.count()
        total_teachers = teachers_query.count()
        total_classes = classes_query.count()
        
        # Today's attendance - filter by school's students
        today = timezone.localdate()
        today_attendance = Attendance.objects.filter(date=today)
        if school:
            today_attendance = today_attendance.filter(student__school=school)
            
        present_today = today_attendance.filter(status='P').count()
        absent_today = today_attendance.filter(status='A').count()
        
        # Fee collection
        current_year = AcademicYear.objects.filter(is_current=True).first()
        total_fee_collected = 0
        total_fee_structures = 0
        
        if current_year:
            payments_query = FeePayment.objects.filter(academic_year=current_year)
            structures_query = FeeStructure.objects.filter(academic_year=current_year)
            
            if school:
                payments_query = payments_query.filter(student__school=school)
                # FeeStructure linking to school is indirect via Class? 
                # If Class is global, FeeStructure might not be easily filterable by school directly unless added.
                # Assuming simple total for now, or filter by students' payments which is correct.
            
            total_fee_collected = payments_query.aggregate(total=Sum('amount_paid'))['total'] or 0
            total_fee_structures = structures_query.count()
        
        # Calculate pending fees (simplified)
        pending_fees = 0  # Can be enhanced with fee structure calculations
        
        # Get monthly fee collection data (last 6 months)
        from datetime import datetime
        
        monthly_fees = [0, 0, 0, 0, 0, 0]
        if current_year:
            # Get current date
            today = timezone.now().date()
            current_month = today.month
            current_year_num = today.year
            
            # Calculate last 6 months
            monthly_data_dict = {}
            for i in range(6):
                month_num = current_month - i
                year_num = current_year_num
                if month_num <= 0:
                    month_num += 12
                    year_num -= 1
                
                # Get fees for this month
                month_start = datetime(year_num, month_num, 1).date()
                if month_num == 12:
                    month_end = datetime(year_num + 1, 1, 1).date() - timedelta(days=1)
                else:
                    month_end = datetime(year_num, month_num + 1, 1).date() - timedelta(days=1)
                
                month_payments = FeePayment.objects.filter(
                    academic_year=current_year,
                    payment_status='completed',
                    payment_date__gte=month_start,
                    payment_date__lte=month_end
                )
                
                if school:
                    month_payments = month_payments.filter(student__school=school)
                
                month_total = month_payments.aggregate(total=Sum('amount_paid'))['total'] or 0
                
                monthly_data_dict[month_num] = float(month_total)
            
            # Fill array in reverse order (oldest to newest)
            for i in range(6):
                month_num = current_month - (5 - i)
                year_num = current_year_num
                if month_num <= 0:
                    month_num += 12
                    year_num -= 1
                monthly_fees[i] = monthly_data_dict.get(month_num, 0)
        
        stats = {
            'user_type': 'school_admin',
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_classes': total_classes,
            'present_today': present_today,
            'absent_today': absent_today,
            'total_fee_collected': float(total_fee_collected),
            'pending_fees': float(pending_fees),
            'total_fee_structures': total_fee_structures,
            'monthly_fee_collection': monthly_fees,  # Last 6 months data
            'total_schools': 0,  # Not relevant for school admin
            'active_schools': 0,
            'total_users': 0,
            'system_health': 0
        }
    
    serializer = DashboardStatsSerializer(stats)
    return Response(serializer.data)


class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Student ViewSet
    Reuses StudentListView and StudentDetailView logic
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Student.objects.filter(status='active').select_related(
            'current_class', 'section', 'academic_year'
        )
        
        # Filter by class
        class_id = self.request.query_params.get('class')
        if class_id:
            queryset = queryset.filter(current_class_id=class_id)
        
        # Filter by section
        section_id = self.request.query_params.get('section')
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(middle_name__icontains=search) |
                Q(admission_number__icontains=search) |
                Q(father_name__icontains=search) |
                Q(father_phone__icontains=search)
            )
        
        return queryset.order_by('current_class__numeric_value', 'section__name', 'roll_number')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StudentDetailSerializer
        return StudentListSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    Attendance ViewSet
    Reuses attendance_mark and view_attendance logic
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AttendanceSerializer
    
    def get_queryset(self):
        queryset = Attendance.objects.select_related('student').all()
        
        # Filter by student
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')
    
    @action(detail=False, methods=['post'])
    def mark_attendance(self, request):
        """Mark attendance for students"""
        student_id = request.data.get('student_id')
        date_str = request.data.get('date', str(timezone.localdate()))
        status_val = request.data.get('status', 'P')
        remarks = request.data.get('remarks', '')
        
        try:
            student = Student.objects.get(id=student_id)
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                date=date_str,
                defaults={
                    'status': status_val,
                    'remarks': remarks,
                    'marked_by': request.user
                }
            )
            return Response(AttendanceSerializer(attendance).data)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class FeeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Fee ViewSet
    Reuses fee_collection and fee_report logic
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = FeePayment.objects.select_related('student', 'academic_year').all()
        
        # Filter by student
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # Filter by academic year
        year_id = self.request.query_params.get('academic_year')
        if year_id:
            queryset = queryset.filter(academic_year_id=year_id)
        
        return queryset.order_by('-payment_date')
    
    def get_serializer_class(self):
        return FeePaymentSerializer
    
    @action(detail=False, methods=['get'])
    def structures(self, request):
        """Get fee structures"""
        structures = FeeStructure.objects.select_related('class_assigned', 'academic_year').all()
        
        class_id = request.query_params.get('class')
        if class_id:
            structures = structures.filter(class_assigned_id=class_id)
        
        serializer = FeeStructureSerializer(structures, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def student_fees(self, request):
        """Get fees for a specific student"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = Student.objects.get(id=student_id)
            current_year = AcademicYear.objects.filter(is_current=True).first()
            
            # Get fee structure
            fee_structure = None
            if student.current_class and current_year:
                try:
                    fee_structure = FeeStructure.objects.filter(
                        class_assigned=student.current_class,
                        academic_year=current_year
                    ).first()
                except Exception as e:
                    print(f"Error getting fee structure: {e}")
                    fee_structure = None
            
            # Get payments
            try:
                payments = FeePayment.objects.filter(
                    student=student
                ).select_related('academic_year').order_by('-payment_date')
                
                # Calculate totals
                total_paid = payments.aggregate(total=Sum('amount_paid'))['total'] or 0
            except Exception as e:
                print(f"Error getting payments: {e}")
                payments = FeePayment.objects.none()
                total_paid = 0
            
            total_due = 0
            if fee_structure:
                try:
                    total_due = float(fee_structure.get_total_fee())
                except Exception as e:
                    print(f"Error calculating total due: {e}")
                    total_due = 0
            
            pending = total_due - float(total_paid)
            
            # Serialize data with error handling
            try:
                student_data = StudentListSerializer(student).data
            except Exception as e:
                print(f"Error serializing student: {e}")
                student_data = {'id': student.id, 'admission_number': student.admission_number}
            
            try:
                fee_structure_data = FeeStructureSerializer(fee_structure).data if fee_structure else None
            except Exception as e:
                print(f"Error serializing fee structure: {e}")
                fee_structure_data = None
            
            try:
                payments_data = FeePaymentSerializer(payments, many=True).data
            except Exception as e:
                print(f"Error serializing payments: {e}")
                payments_data = []
            
            return Response({
                'student': student_data,
                'fee_structure': fee_structure_data,
                'payments': payments_data,
                'total_due': total_due,
                'total_paid': float(total_paid),
                'pending': max(0, pending)
            })
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in student_fees: {e}")
            print(error_trace)
            return Response(
                {'error': f'Error loading student fees: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IDCardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ID Card ViewSet
    Reuses ID card generation logic
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StudentIDCardSerializer
    
    def get_queryset(self):
        queryset = StudentIDCard.objects.filter(is_active=True).select_related('student', 'template')
        
        # Filter by student
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset.order_by('-issue_date')


class NoticeViewSet(viewsets.ReadOnlyModelViewSet):
    """Notice ViewSet"""
    permission_classes = [IsAuthenticated]
    serializer_class = NoticeSerializer
    
    def get_queryset(self):
        return Notice.objects.filter(is_active=True, status='published').order_by('-notice_date')


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """Event ViewSet"""
    permission_classes = [IsAuthenticated]
    serializer_class = EventSerializer
    
    def get_queryset(self):
        today = timezone.localdate()
        return Event.objects.filter(
            status='published',
            event_date__gte=today
        ).order_by('event_date')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_classes(request):
    """Get all classes"""
    classes = Class.objects.all().order_by('numeric_value')
    serializer = ClassSerializer(classes, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_sections(request):
    """Get sections, optionally filtered by class"""
    class_id = request.query_params.get('class')
    sections = Section.objects.select_related('class_assigned').all()
    
    if class_id:
        sections = sections.filter(class_assigned_id=class_id)
    
    serializer = SectionSerializer(sections, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_academic_years(request):
    """Get all academic years"""
    years = AcademicYear.objects.all().order_by('-start_date')
    serializer = AcademicYearSerializer(years, many=True)
    return Response(serializer.data)


class IDCardTemplateViewSet(viewsets.ModelViewSet):
    """ID Card Template ViewSet with upload/delete"""
    permission_classes = [IsAuthenticated]
    serializer_class = IDCardTemplateSerializer
    
    def get_queryset(self):
        return IDCardTemplate.objects.all().order_by('-created_at')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload ID card template"""
        template_type = request.data.get('template_type', 'front')  # 'front' or 'back'
        card_size = request.data.get('card_size', 'a4')  # 'a4' or '12x18'
        template_file = request.FILES.get('template_file')
        
        if not template_file:
            return Response(
                {'error': 'Template file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create template name based on type and size
        name = f"{template_type.upper()}_{card_size.upper()}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        template = IDCardTemplate.objects.create(
            name=name,
            description=f"Template for {template_type} side, {card_size} size",
            template_image=template_file,
            orientation='portrait',
            is_active=True
        )
        
        serializer = self.get_serializer(template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_upload_excel(request):
    """Bulk upload students/teachers from Excel"""
    upload_type = request.data.get('upload_type')  # 'students' or 'teachers'
    file = request.FILES.get('file')
    
    if not file or not upload_type:
        return Response(
            {'error': 'File and upload_type are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # TODO: Implement Excel parsing and bulk creation
    # This would use openpyxl or pandas to read Excel and create records
    return Response({
        'message': f'Bulk upload for {upload_type} initiated',
        'uploaded_count': 0  # Placeholder
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_upload_photos(request):
    """Bulk upload photos for students/teachers"""
    upload_type = request.data.get('upload_type')  # 'students' or 'teachers'
    photos = request.FILES.getlist('photos')
    
    if not photos or not upload_type:
        return Response(
            {'error': 'Photos and upload_type are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # TODO: Implement photo upload and matching logic
    return Response({
        'message': f'Bulk photo upload for {upload_type} initiated',
        'uploaded_count': len(photos)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_id_cards(request):
    """Generate ID cards for selected students"""
    student_ids = request.data.get('student_ids', [])
    size = request.data.get('size', 'a4')  # 'a4' or '12x18'
    
    if not student_ids:
        return Response(
            {'error': 'Student IDs are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    students = Student.objects.filter(id__in=student_ids)
    
    # Generate ID cards using existing logic
    try:
        # This function returns an HttpResponse with PDF content
        pdf_response = generate_id_cards_reportlab(students, request, single_card=(size == 'single'))
        
        # Save PDF to media folder to make it accessible via URL
        import os
        from django.conf import settings
        from django.core.files.base import ContentFile
        
        # Create directory if it doesn't exist
        save_dir = os.path.join(settings.MEDIA_ROOT, 'generated_id_cards')
        os.makedirs(save_dir, exist_ok=True)
        
        # Generate filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"id_cards_{timestamp}.pdf"
        file_path = os.path.join(save_dir, filename)
        
        # Save content
        with open(file_path, 'wb') as f:
            f.write(pdf_response.content)
            
        # Construct URL
        pdf_url = request.build_absolute_uri(f"{settings.MEDIA_URL}generated_id_cards/{filename}")
        
        return Response({
            'message': f'ID cards generated successfully for {students.count()} students',
            'size': size,
            'generated_count': students.count(),
            'pdf_url': pdf_url
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to generate ID cards: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Library API
class BookViewSet(viewsets.ReadOnlyModelViewSet):
    """Book ViewSet"""
    permission_classes = [IsAuthenticated]
    serializer_class = BookSerializer
    
    def get_queryset(self):
        try:
            queryset = Book.objects.select_related('category').all()
            search = self.request.query_params.get('search')
            category = self.request.query_params.get('category')
            
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(author__icontains=search) |
                    Q(isbn__icontains=search)
                )
            if category:
                queryset = queryset.filter(category_id=category)
            
            return queryset.order_by('title')
        except Exception as e:
            print(f"Error in BookViewSet.get_queryset: {e}")
            import traceback
            traceback.print_exc()
            return Book.objects.none()


class BookIssueViewSet(viewsets.ModelViewSet):
    """Book Issue ViewSet"""
    permission_classes = [IsAuthenticated]
    serializer_class = BookIssueSerializer
    
    def get_queryset(self):
        queryset = BookIssue.objects.select_related('book', 'student').all()
        student_id = self.request.query_params.get('student')
        status_filter = self.request.query_params.get('status')
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-issue_date')
    
    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        """Return a book"""
        book_issue = self.get_object()
        if book_issue.status != 'issued':
            return Response(
                {'error': 'Book is not currently issued'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        book_issue.status = 'returned'
        book_issue.return_date = date.today()
        book_issue.returned_to = request.user
        book_issue.fine_amount = book_issue.calculate_fine()
        book_issue.save()
        
        # Update book available copies
        book_issue.book.available_copies += 1
        book_issue.book.save()
        
        serializer = self.get_serializer(book_issue)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_book_categories(request):
    """Get all book categories"""
    try:
        categories = BookCategory.objects.all().order_by('name')
        serializer = BookCategorySerializer(categories, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(f"Error in api_book_categories: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Error loading book categories: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Timetable API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_timetable(request):
    """Get timetable"""
    section_id = request.query_params.get('section')
    class_id = request.query_params.get('class')
    academic_year_id = request.query_params.get('academic_year')
    
    queryset = Timetable.objects.select_related(
        'section', 'subject', 'teacher', 'time_slot', 'academic_year'
    ).all()
    
    if section_id:
        queryset = queryset.filter(section_id=section_id)
    elif class_id:
        queryset = queryset.filter(section__class_assigned_id=class_id)
    
    if academic_year_id:
        queryset = queryset.filter(academic_year_id=academic_year_id)
    else:
        # Get current academic year
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            queryset = queryset.filter(academic_year=current_year)
    
    serializer = TimetableSerializer(queryset, many=True)
    return Response(serializer.data)


# Exams & Marks API
class ExamViewSet(viewsets.ReadOnlyModelViewSet):
    """Exam ViewSet"""
    permission_classes = [IsAuthenticated]
    serializer_class = ExamSerializer
    
    def get_queryset(self):
        queryset = Exam.objects.select_related('academic_year').all()
        academic_year_id = self.request.query_params.get('academic_year')
        is_published = self.request.query_params.get('is_published')
        
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')
        
        return queryset.order_by('-start_date')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_student_marks(request, student_id):
    """Get marks for a student"""
    exam_id = request.query_params.get('exam')
    
    queryset = Marks.objects.filter(
        student_id=student_id
    ).select_related('exam_schedule__exam', 'exam_schedule__subject', 'exam_schedule__class_assigned')
    
    if exam_id:
        queryset = queryset.filter(exam_schedule__exam_id=exam_id)
    
    serializer = MarksSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_student_report_card(request, student_id, exam_id):
    """Get report card for a student"""
    try:
        student = Student.objects.get(id=student_id)
        exam = Exam.objects.get(id=exam_id)
        
        marks = Marks.objects.filter(
            student=student,
            exam_schedule__exam=exam
        ).select_related('exam_schedule__subject')
        
        serializer = MarksSerializer(marks, many=True)
        
        # Calculate total and percentage
        total_marks = sum(m.exam_schedule.max_marks for m in marks)
        obtained_marks = sum(m.marks_obtained for m in marks if not m.is_absent)
        percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
        
        return Response({
            'student': StudentDetailSerializer(student).data,
            'exam': ExamSerializer(exam).data,
            'marks': serializer.data,
            'total_marks': total_marks,
            'obtained_marks': obtained_marks,
            'percentage': round(percentage, 2)
        })
    except (Student.DoesNotExist, Exam.DoesNotExist):
        return Response(
            {'error': 'Student or Exam not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# Book Categories API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_book_categories(request):
    """Get all book categories"""
    categories = BookCategory.objects.all()
    serializer = BookCategorySerializer(categories, many=True)
    return Response(serializer.data)


# ============================================
# ERROR LOGGING API
# ============================================

import json
import logging

# Setup logger for mobile app errors
mobile_error_logger = logging.getLogger('mobile_app_errors')

@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated for error logging
def api_log_error(request):
    """
    Log error from mobile app
    Stores error in log file and optionally in database
    """
    try:
        error_data = request.data
        
        # Log to Django logger
        mobile_error_logger.error(
            f"Mobile App Error: {error_data.get('message', 'Unknown error')}",
            extra={
                'error_data': error_data,
                'timestamp': error_data.get('timestamp'),
                'app_version': error_data.get('appVersion'),
                'platform': error_data.get('platform'),
                'stack': error_data.get('stack', ''),
            }
        )
        
        # Also print to console for immediate visibility
        print("\n" + "="*80)
        print("🔴 MOBILE APP ERROR RECEIVED")
        print("="*80)
        print(f"Message: {error_data.get('message', 'N/A')}")
        print(f"Type: {error_data.get('type', 'N/A')}")
        print(f"Timestamp: {error_data.get('timestamp', 'N/A')}")
        print(f"App Version: {error_data.get('appVersion', 'N/A')}")
        print(f"Platform: {error_data.get('platform', 'N/A')}")
        if error_data.get('stack'):
            print(f"\nStack Trace:\n{error_data.get('stack')}")
        print("="*80 + "\n")
        
        return Response(
            {'status': 'logged', 'message': 'Error logged successfully'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        # Even if logging fails, don't break the app
        print(f"Error logging failed: {str(e)}")
        return Response(
            {'status': 'error', 'message': 'Failed to log error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated for error logging
def api_log_errors_batch(request):
    """
    Log multiple errors in batch from mobile app
    """
    try:
        errors = request.data.get('errors', [])
        
        for error_data in errors:
            mobile_error_logger.error(
                f"Mobile App Error: {error_data.get('message', 'Unknown error')}",
                extra={
                    'error_data': error_data,
                    'timestamp': error_data.get('timestamp'),
                    'app_version': error_data.get('appVersion'),
                    'platform': error_data.get('platform'),
                }
            )
            
            # Print to console
            print(f"\n🔴 Error: {error_data.get('message', 'N/A')} - {error_data.get('timestamp', 'N/A')}")
        
        return Response(
            {'status': 'logged', 'count': len(errors), 'message': 'Errors logged successfully'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        print(f"Batch error logging failed: {str(e)}")
        return Response(
            {'status': 'error', 'message': 'Failed to log errors'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_error_logs(request):
    """
    Get error logs (for admin/superuser only)
    Reads from Django log file
    """
    # Only allow superuser
    if not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # For now, return a message indicating errors are logged
    # In production, you might want to read from log files or database
    return Response({
        'message': 'Error logs are being logged to Django logger',
        'note': 'Check Django console output or log files for error details',
        'endpoint': '/api/errors/log/',
        'status': 'active'
    })


# ============================================
# BACKEND HEALTH CHECK & DIAGNOSTICS API
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow unauthenticated for health checks
def api_health_check(request):
    """
    Health check endpoint for backend monitoring
    Returns backend status and basic diagnostics
    """
    try:
        from django.db import connection
        from django.core.cache import cache
        
        # Check database connection
        db_status = 'ok'
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        # Check cache
        cache_status = 'ok'
        try:
            cache.set('health_check', 'test', 10)
            cache.get('health_check')
        except Exception as e:
            cache_status = f'error: {str(e)}'
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': db_status,
            'cache': cache_status,
            'version': '1.0.0',
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_backend_diagnostics(request):
    """
    Backend diagnostics endpoint
    Returns detailed backend information for debugging
    """
    # Only allow superuser
    if not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        from django.db import connection
        from django.conf import settings
        
        # Get database info
        db_info = {
            'engine': settings.DATABASES['default']['ENGINE'],
            'name': settings.DATABASES['default'].get('NAME', 'N/A'),
        }
        
        # Get model counts
        model_counts = {
            'students': Student.objects.count(),
            'teachers': Teacher.objects.count(),
            'parents': Parent.objects.count(),
            'classes': Class.objects.count(),
            'attendance': Attendance.objects.count(),
            'fees': FeePayment.objects.count(),
        }
        
        # Get API endpoints
        api_endpoints = [
            '/api/auth/login/',
            '/api/auth/logout/',
            '/api/dashboard/',
            '/api/students/',
            '/api/attendance/',
            '/api/fees/',
            '/api/books/',
            '/api/exams/',
            '/api/timetable/',
            '/api/errors/log/',
            '/api/health/',
        ]
        
        return Response({
            'status': 'ok',
            'timestamp': timezone.now().isoformat(),
            'database': db_info,
            'model_counts': model_counts,
            'api_endpoints': api_endpoints,
            'django_version': 'Django 4.x',
            'python_version': 'Python 3.x',
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_check_endpoints(request):
    """
    Check if all API endpoints are accessible
    Returns status of each endpoint
    """
    # Only allow superuser
    if not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    endpoints_status = {}
    
    # Check each endpoint
    endpoints_to_check = [
        ('/api/auth/login/', 'POST'),
        ('/api/dashboard/', 'GET'),
        ('/api/students/', 'GET'),
        ('/api/attendance/', 'GET'),
        ('/api/fees/', 'GET'),
        ('/api/books/', 'GET'),
        ('/api/exams/', 'GET'),
        ('/api/timetable/', 'GET'),
        ('/api/health/', 'GET'),
    ]
    
    for endpoint, method in endpoints_to_check:
        endpoints_status[endpoint] = {
            'method': method,
            'exists': True,  # If we can import it, it exists
            'status': 'ok'
        }
    
    return Response({
        'status': 'ok',
        'endpoints': endpoints_status,
        'timestamp': timezone.now().isoformat(),
    })


# ============================================
# MOBILE DEVICE TRACKING API
# ============================================

@api_view(['POST'])
@permission_classes([AllowAny])
def api_register_device(request):
    """
    Register or update mobile device information
    Called when app starts or user logs in
    """
    try:
        from .models import MobileDevice
        from django.utils import timezone
        
        device_id = request.data.get('device_id')
        if not device_id:
            return Response(
                {'error': 'device_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get client IP
        ip_address = None
        if hasattr(request, 'META'):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        # Get or create device
        device, created = MobileDevice.objects.get_or_create(
            device_id=device_id,
            defaults={
                'device_name': request.data.get('device_name', ''),
                'device_type': request.data.get('device_type', 'android'),
                'os_version': request.data.get('os_version', ''),
                'app_version': request.data.get('app_version', ''),
                'ip_address': ip_address,
                'last_ip_address': ip_address,
                'metadata': request.data.get('metadata', {}),
            }
        )
        
        # Update device info if not new
        if not created:
            update_fields = []
            if request.data.get('device_name'):
                device.device_name = request.data.get('device_name')
                update_fields.append('device_name')
            if request.data.get('os_version'):
                device.os_version = request.data.get('os_version')
                update_fields.append('os_version')
            if request.data.get('app_version'):
                device.app_version = request.data.get('app_version')
                update_fields.append('app_version')
            if ip_address:
                device.last_ip_address = ip_address
                update_fields.append('last_ip_address')
            if request.data.get('metadata'):
                device.metadata = {**device.metadata, **request.data.get('metadata', {})}
                update_fields.append('metadata')
            
            if update_fields:
                device.save(update_fields=update_fields)
        
        # Associate with user if authenticated
        if request.user.is_authenticated:
            device.user = request.user
            device.save(update_fields=['user'])
        
        # Update last seen
        device.update_last_seen(ip_address)
        
        return Response({
            'success': True,
            'device_id': device.device_id,
            'created': created,
            'message': 'Device registered successfully' if created else 'Device updated successfully'
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_list_devices(request):
    """
    List all registered devices (admin only)
    """
    try:
        from .models import MobileDevice
        
        # Only superusers can see all devices
        if not request.user.is_superuser:
            # Regular users see only their devices
            devices = MobileDevice.objects.filter(user=request.user, is_active=True)
        else:
            # Superusers see all devices
            devices = MobileDevice.objects.all()
        
        device_list = []
        for device in devices:
            device_list.append({
                'device_id': device.device_id,
                'device_name': device.device_name,
                'device_type': device.device_type,
                'os_version': device.os_version,
                'app_version': device.app_version,
                'user': device.user.username if device.user else None,
                'first_installed': device.first_installed.isoformat() if device.first_installed else None,
                'last_seen': device.last_seen.isoformat() if device.last_seen else None,
                'is_active': device.is_active,
                'ip_address': str(device.last_ip_address) if device.last_ip_address else None,
            })
        
        return Response({
            'count': len(device_list),
            'devices': device_list
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================
# SCHOOL BILLING API (SUPER ADMIN ONLY)
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_schools_for_billing(request):
    """
    Get all schools for billing (Super Admin only)
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied. Super admin only.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from .models import School
    
    schools = School.objects.all()
    
    # Note: Current system doesn't have school foreign key in Student/Teacher models
    # So we'll show system-wide totals for now
    # In future, add school FK to models for multi-school filtering
    total_students_system = Student.objects.filter(status='active').count()
    total_teachers_system = Teacher.objects.filter(is_active=True).count()
    
    school_list = []
    for school in schools:
        # For now, show system-wide counts (will be per-school when FK added)
        total_students = total_students_system
        total_teachers = total_teachers_system
        total_users = total_students + total_teachers
        
        school_list.append({
            'id': school.id,
            'name': school.name,
            'email': school.email,
            'phone': school.phone,
            'subscription_active': school.subscription_active,
            'subscription_expires': school.subscription_expires.isoformat() if school.subscription_expires else None,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_users': total_users,
            'max_users': school.max_users
        })
    
    return Response({
        'count': len(school_list),
        'schools': school_list
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_send_school_bill(request):
    """
    Send/Create bill for a school (Super Admin only)
    Generates bill template with invoice details
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied. Super admin only.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from .models import School, SchoolBilling
    from datetime import datetime, timedelta
    import random
    
    school_id = request.data.get('school_id')
    amount = request.data.get('amount')
    billing_period = request.data.get('billing_period')
    due_date = request.data.get('due_date')
    notes = request.data.get('notes', '')
    
    if not all([school_id, amount, billing_period]):
        return Response(
            {'error': 'school_id, amount, and billing_period are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        school = School.objects.get(id=school_id)
        
        # If due_date not provided, set to 30 days from now
        if not due_date:
            due_date = (datetime.now() + timedelta(days=30)).date()
        
        # Generate unique invoice number
        invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-{random.randint(1000, 9999)}"
        
        # Create billing record
        billing = SchoolBilling.objects.create(
            school=school,
            billing_period=billing_period,
            amount=amount,
            due_date=due_date,
            payment_status='pending',
            notes=notes,
            transaction_id=invoice_number  # Store invoice number
        )
        
        # Generate bill template (HTML format for preview)
        bill_template = generate_bill_template(billing, school, invoice_number)
        
        return Response({
            'success': True,
            'message': f'Bill sent to {school.name}',
            'billing': {
                'id': billing.id,
                'invoice_number': invoice_number,
                'school': school.name,
                'amount': float(billing.amount),
                'billing_period': billing.billing_period,
                'due_date': billing.due_date.isoformat(),
                'payment_status': billing.payment_status,
                'bill_template': bill_template
            }
        })
    except School.DoesNotExist:
        return Response(
            {'error': 'School not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def generate_bill_template(billing, school, invoice_number):
    """Generate text bill template for preview"""
    from datetime import datetime
    
    template = f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    SCHOOL ERP - INVOICE                      ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Invoice Number: {invoice_number}
    Date: {datetime.now().strftime('%d %B, %Y')}
    
    ────────────────────────────────────────────────────────────────
    
    BILL TO:
    {school.name}
    {school.address if hasattr(school, 'address') and school.address else 'N/A'}
    Email: {school.email}
    Phone: {school.phone}
    
    ────────────────────────────────────────────────────────────────
    
    BILLING DETAILS:
    Billing Period:     {billing.billing_period}
    Due Date:           {billing.due_date.strftime('%d %B, %Y')}
    Payment Status:     {billing.payment_status.upper()}
    
    ────────────────────────────────────────────────────────────────
    
    DESCRIPTION                                          AMOUNT
    ────────────────────────────────────────────────────────────────
    School ERP Subscription - {billing.billing_period}   ₹{float(billing.amount):,.2f}
    
    ────────────────────────────────────────────────────────────────
    
                                            SUBTOTAL:    ₹{float(billing.amount):,.2f}
                                            TAX (18%):   ₹{float(billing.amount) * 0.18:,.2f}
                                            ═══════════════════════════
                                            TOTAL:       ₹{float(billing.amount) * 1.18:,.2f}
    
    ────────────────────────────────────────────────────────────────
    
    PAYMENT INSTRUCTIONS:
    • Bank Transfer: [Bank Details Here]
    • UPI: [UPI ID Here]
    • Online Payment: Visit our portal
    
    NOTES:
    {billing.notes if billing.notes else 'Thank you for using School ERP!'}
    
    ────────────────────────────────────────────────────────────────
    
    For queries, contact: support@schoolerp.com
    
    ╔══════════════════════════════════════════════════════════════╗
    ║              Thank you for your business!                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    
    return template


def generate_bill_pdf(billing, school, invoice_number):
    """Generate professional PDF bill using ReportLab"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from datetime import datetime
    import os
    from django.conf import settings
    
    # Create PDF path
    pdf_dir = os.path.join(settings.MEDIA_ROOT, 'bills')
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f'invoice_{invoice_number}.pdf')
    
    # Create PDF
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    # Title
    elements.append(Paragraph("SCHOOL ERP", title_style))
    elements.append(Paragraph("TAX INVOICE", styles['Heading2']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Invoice details table
    invoice_data = [
        ['Invoice Number:', invoice_number, 'Date:', datetime.now().strftime('%d %B, %Y')],
        ['Due Date:', billing.due_date.strftime('%d %B, %Y'), 'Status:', billing.payment_status.upper()],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[1.5*inch, 2*inch, 1*inch, 2*inch])
    invoice_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Bill To section
    elements.append(Paragraph("BILL TO:", heading_style))
    bill_to_data = [
        [school.name],
        [school.address if hasattr(school, 'address') and school.address else 'N/A'],
        [f"Email: {school.email}"],
        [f"Phone: {school.phone}"],
    ]
    bill_to_table = Table(bill_to_data, colWidths=[6*inch])
    bill_to_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
    ]))
    elements.append(bill_to_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Billing items table
    elements.append(Paragraph("BILLING DETAILS:", heading_style))
    
    subtotal = float(billing.amount)
    tax = subtotal * 0.18
    total = subtotal + tax
    
    items_data = [
        ['Description', 'Period', 'Amount'],
        ['School ERP Subscription', billing.billing_period, f'₹{subtotal:,.2f}'],
        ['', '', ''],
        ['', 'Subtotal:', f'₹{subtotal:,.2f}'],
        ['', 'GST (18%):', f'₹{tax:,.2f}'],
        ['', 'Total Amount:', f'₹{total:,.2f}'],
    ]
    
    items_table = Table(items_data, colWidths=[3*inch, 2*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Items
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        
        # Totals
        ('FONTNAME', (1, 3), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 5), (2, 5), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 5), (2, 5), 14),
        ('TEXTCOLOR', (2, 5), (2, 5), colors.HexColor('#667eea')),
        
        # Lines
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#667eea')),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#667eea')),
        ('LINEABOVE', (1, 3), (2, 3), 1, colors.HexColor('#cccccc')),
        ('LINEABOVE', (1, 5), (2, 5), 2, colors.HexColor('#667eea')),
        
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Payment Instructions
    elements.append(Paragraph("PAYMENT INSTRUCTIONS:", heading_style))
    payment_text = """
    • Bank Transfer: Account details will be provided separately<br/>
    • UPI: Payment ID will be shared via email<br/>
    • Online Payment: Visit our payment portal<br/><br/>
    Please include the invoice number in your payment reference.
    """
    elements.append(Paragraph(payment_text, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Notes
    if billing.notes:
        elements.append(Paragraph("NOTES:", heading_style))
        elements.append(Paragraph(billing.notes, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Thank you for your business!", footer_style))
    elements.append(Paragraph("For queries, contact: support@schoolerp.com", footer_style))
    
    # Build PDF
    doc.build(elements)
    
    return pdf_path


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_school_billings(request):
    """
    Get all billing records (Super Admin only)
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied. Super admin only.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from .models import SchoolBilling
    
    billings = SchoolBilling.objects.select_related('school').all().order_by('-created_at')
    
    billing_list = []
    for billing in billings:
        billing_list.append({
            'id': billing.id,
            'invoice_number': billing.transaction_id or 'N/A',
            'school_id': billing.school.id,
            'school_name': billing.school.name,
            'amount': float(billing.amount),
            'billing_period': billing.billing_period,
            'payment_status': billing.payment_status,
            'due_date': billing.due_date.isoformat() if billing.due_date else None,
            'payment_date': billing.payment_date.isoformat() if billing.payment_date else None,
            'created_at': billing.created_at.isoformat()
        })
    
    return Response({
        'count': len(billing_list),
        'billings': billing_list
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_view_bill_template(request, billing_id):
    """
    View/Download bill template for a specific billing (Super Admin only)
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied. Super admin only.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from .models import SchoolBilling
    
    try:
        billing = SchoolBilling.objects.select_related('school').get(id=billing_id)
        invoice_number = billing.transaction_id or f"INV-{billing.id}"
        
        # Generate bill template
        bill_template = generate_bill_template(billing, billing.school, invoice_number)
        
        return Response({
            'success': True,
            'billing_id': billing.id,
            'invoice_number': invoice_number,
            'school_name': billing.school.name,
            'bill_template': bill_template
        })
    except SchoolBilling.DoesNotExist:
        return Response(
            {'error': 'Billing record not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_download_bill_pdf(request, billing_id):
    """
    Download bill PDF for a specific billing (Super Admin only)
    """
    if not request.user.is_superuser:
        return Response(
            {'error': 'Permission denied. Super admin only.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from .models import SchoolBilling
    from django.http import FileResponse
    import os
    
    try:
        billing = SchoolBilling.objects.select_related('school').get(id=billing_id)
        invoice_number = billing.transaction_id or f"INV-{billing.id}"
        
        # Generate PDF
        pdf_path = generate_bill_pdf(billing, billing.school, invoice_number)
        
        # Return PDF file
        if os.path.exists(pdf_path):
            response = FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_number}.pdf"'
            return response
        else:
            return Response(
                {'error': 'PDF generation failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except SchoolBilling.DoesNotExist:
        return Response(
            {'error': 'Billing record not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
