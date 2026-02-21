"""
Enhanced Fee Management Views
- Fee Analytics Dashboard
- Fee Notifications
- Fee Reconciliation
- E-Receipt Generation
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import FeePayment, FeeStructure, Student, AcademicYear, Class, Section

# Import enhanced models from models.py (moved from fee_enhancements.py)
try:
    from .models import FeeNotification, FeeReconciliation, FeeConcession, StudentFeeConcession
except ImportError:
    FeeNotification = None
    FeeReconciliation = None
    FeeConcession = None
    StudentFeeConcession = None


@login_required
def fee_analytics(request):
    """Fee Analytics Dashboard with charts and insights"""
    # Date range filter
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get payments in date range
    payments = FeePayment.objects.filter(
        payment_date__gte=start_date,
        payment_status='completed'
    )
    
    # Overall Statistics
    total_collected = payments.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_discounts = payments.aggregate(total=Sum('discount'))['total'] or 0
    total_late_fees = payments.aggregate(total=Sum('late_fee'))['total'] or 0
    payment_count = payments.count()
    avg_payment = total_collected / payment_count if payment_count > 0 else 0
    
    # Payment Method Distribution
    payment_methods = payments.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('amount_paid')
    ).order_by('-total')
    
    # Daily Collection Trends
    daily_trends = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        # Fix for Django 5: Use range filter instead of payment_date__date lookup
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        day_payments = payments.filter(payment_date__range=[date_start, date_end])
        day_total = day_payments.aggregate(total=Sum('amount_paid'))['total'] or 0
        day_count = day_payments.count()
        daily_trends.append({
            'date': date.date(),
            'amount': float(day_total),
            'count': day_count,
        })
    
    # Class-wise Collection
    class_collection = payments.values(
        'student__current_class__name'
    ).annotate(
        total=Sum('amount_paid'),
        count=Count('id')
    ).order_by('-total')
    
    # Pending Fees (students with no payment in date range)
    current_year = AcademicYear.objects.filter(is_current=True).first()
    if current_year:
        fee_structures = FeeStructure.objects.filter(academic_year=current_year)
        total_students = Student.objects.filter(status='active').count()
        paid_students = payments.values('student').distinct().count()
        pending_students = total_students - paid_students
    else:
        pending_students = 0
    
    # Monthly Comparison (if days >= 30)
    monthly_data = []
    if days >= 30:
        for i in range(3):  # Last 3 months
            month_start = (timezone.now() - timedelta(days=30*(i+1))).replace(day=1)
            month_end = (timezone.now() - timedelta(days=30*i)).replace(day=1) - timedelta(days=1)
            month_payments = FeePayment.objects.filter(
                payment_date__gte=month_start,
                payment_date__lte=month_end,
                payment_status='completed'
            )
            month_total = month_payments.aggregate(total=Sum('amount_paid'))['total'] or 0
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'total': float(month_total),
            })
        monthly_data.reverse()
    
    context = {
        'days': days,
        'total_collected': total_collected,
        'total_discounts': total_discounts,
        'total_late_fees': total_late_fees,
        'payment_count': payment_count,
        'avg_payment': round(avg_payment, 2),
        'payment_methods': payment_methods,
        'daily_trends': daily_trends,
        'class_collection': class_collection,
        'pending_students': pending_students,
        'monthly_data': monthly_data,
    }
    
    return render(request, 'students/fee_analytics.html', context)


@login_required
def fee_notifications(request):
    """Manage fee notifications and send reminders via Email, SMS, and WhatsApp"""
    from .messaging_utils import send_fee_notification
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send_reminder':
            student_ids = request.POST.getlist('students')
            notification_type = request.POST.get('notification_type', 'pending')
            send_via = request.POST.get('send_via', 'email')  # email, sms, whatsapp, both, all
            custom_message = request.POST.get('custom_message', '')
            
            students = Student.objects.filter(id__in=student_ids, status='active')
            sent_count = 0
            email_sent = 0
            sms_sent = 0
            whatsapp_sent = 0
            errors = []
            
            for student in students:
                try:
                    # Send notification via selected method
                    results = send_fee_notification(
                        student=student,
                        notification_type=notification_type,
                        send_via=send_via,
                        custom_message=custom_message if custom_message else None
                    )
                    
                    # Determine sent_via string for database
                    sent_via_list = []
                    if results.get('email', {}).get('success'):
                        sent_via_list.append('email')
                        email_sent += 1
                    if results.get('sms', {}).get('success'):
                        sent_via_list.append('sms')
                        sms_sent += 1
                    if results.get('whatsapp', {}).get('success'):
                        sent_via_list.append('whatsapp')
                        whatsapp_sent += 1
                    
                    sent_via_str = ', '.join(sent_via_list) if sent_via_list else 'none'
                    
                    # Get contact info - check multiple possible field names
                    parent_phone = (
                        getattr(student, 'parent_phone', None) or 
                        getattr(student, 'father_phone', None) or 
                        getattr(student, 'phone', None) or 
                        ''
                    )
                    parent_email = (
                        getattr(student, 'parent_email', None) or 
                        getattr(student, 'email', None) or 
                        ''
                    )
                    
                    # Create notification record
                    if FeeNotification:
                        try:
                            notification = FeeNotification.objects.create(
                                student=student,
                                notification_type=notification_type,
                                subject=f"Fee Payment Reminder - {student.get_full_name()}",
                                message=custom_message or f"Fee payment reminder for {student.get_full_name()}",
                                sent_via=sent_via_str if sent_via_str else 'email',
                                sent_to_email=parent_email,
                                sent_to_phone=parent_phone,
                                is_sent=len(sent_via_list) > 0,
                            )
                        except Exception as e:
                            # Table doesn't exist - skip notification record creation
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Could not create FeeNotification record: {str(e)}")
                    
                    if len(sent_via_list) > 0:
                        sent_count += 1
                    else:
                        errors.append(f"{student.get_full_name()}: No contact method available")
                        
                except Exception as e:
                    errors.append(f"{student.get_full_name()}: {str(e)}")
            
            # Prepare success message
            msg_parts = [f'Notifications sent to {sent_count} students']
            if email_sent > 0:
                msg_parts.append(f'{email_sent} emails')
            if sms_sent > 0:
                msg_parts.append(f'{sms_sent} SMS')
            if whatsapp_sent > 0:
                msg_parts.append(f'{whatsapp_sent} WhatsApp')
            
            if errors:
                messages.warning(request, f"{', '.join(msg_parts)}. Some errors: {len(errors)} failed")
            else:
                messages.success(request, ', '.join(msg_parts) + '.')
            
            return redirect('students_app:fee_notifications')
    
    # Get students with pending fees with search and filter
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    # Search and filter parameters
    search_query = request.GET.get('search', '').strip()
    class_filter = request.GET.get('class', '')
    section_filter = request.GET.get('section', '')
    
    if current_year:
        # Students who haven't paid in current year
        paid_students = FeePayment.objects.filter(
            academic_year=current_year,
            payment_status='completed'
        ).values_list('student_id', flat=True).distinct()
        
        pending_students = Student.objects.filter(
            status='active'
        ).exclude(id__in=paid_students)
    else:
        pending_students = Student.objects.filter(status='active')
    
    # Apply search filter
    if search_query:
        pending_students = pending_students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(admission_number__icontains=search_query) |
            Q(roll_number__icontains=search_query) |
            Q(father_name__icontains=search_query) |
            Q(father_phone__icontains=search_query)
        )
    
    # Apply class filter
    if class_filter:
        pending_students = pending_students.filter(current_class_id=class_filter)
    
    # Apply section filter
    if section_filter:
        pending_students = pending_students.filter(section_id=section_filter)
    
    # Get all classes and sections for filter dropdowns
    all_classes = Class.objects.all().order_by('numeric_value', 'name')
    all_sections = []
    if class_filter:
        all_sections = Section.objects.filter(class_name_id=class_filter).order_by('name')
    
    # Recent notifications - handle case where table doesn't exist
    recent_notifications = []
    if FeeNotification:
        try:
            recent_notifications = FeeNotification.objects.all().order_by('-sent_at')[:50]
        except Exception as e:
            # Table doesn't exist or other database error
            recent_notifications = []
            # Log error but don't break the page
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"FeeNotification table not available: {str(e)}")
    
    context = {
        'pending_students': pending_students,
        'recent_notifications': recent_notifications,
        'all_classes': all_classes,
        'all_sections': all_sections,
        'search_query': search_query,
        'class_filter': class_filter,
        'section_filter': section_filter,
        'total_pending': pending_students.count(),
    }
    
    return render(request, 'students/fee_notifications.html', context)


@login_required
def get_sections_by_class(request, class_id):
    """AJAX endpoint to get sections for a class"""
    try:
        sections = Section.objects.filter(class_name_id=class_id).order_by('name')
        sections_data = [{'id': sec.id, 'name': sec.name} for sec in sections]
        return JsonResponse({'sections': sections_data})
    except Exception as e:
        return JsonResponse({'error': str(e), 'sections': []}, status=400)


@login_required
def fee_reconciliation(request):
    """Fee payment reconciliation with bank statements"""
    if request.method == 'POST':
        reconciliation_date = request.POST.get('reconciliation_date')
        bank_name = request.POST.get('bank_name')
        bank_statement_amount = Decimal(request.POST.get('bank_statement_amount', 0))
        
        # Calculate system recorded amount for the date
        date_obj = datetime.strptime(reconciliation_date, '%Y-%m-%d').date()
        system_amount = FeePayment.objects.filter(
            payment_date=date_obj,
            payment_status='completed',
            payment_method__in=['netbanking', 'card', 'upi']
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        
        difference = bank_statement_amount - system_amount
        
        # Create reconciliation if model exists
        if FeeReconciliation:
            reconciliation = FeeReconciliation.objects.create(
                reconciliation_date=date_obj,
                bank_name=bank_name,
                bank_statement_amount=bank_statement_amount,
                system_recorded_amount=system_amount,
                difference=difference,
                status='matched' if difference == 0 else 'mismatch',
                reconciled_by=request.user,
                notes=request.POST.get('notes', ''),
            )
        else:
            # Store in session or log if model doesn't exist
            messages.info(request, f'Reconciliation calculated. Difference: ₹{difference} (Model not available)')
        
        messages.success(request, f'Reconciliation created. Difference: ₹{difference}')
        return redirect('students_app:fee_reconciliation')
    
    # List all reconciliations
    reconciliations = []
    if FeeReconciliation:
        reconciliations = FeeReconciliation.objects.all().order_by('-reconciliation_date')[:50]
    
    # Summary statistics
    total_reconciliations = len(reconciliations)
    matched_count = len([r for r in reconciliations if r.status == 'matched'])
    mismatch_count = len([r for r in reconciliations if r.status == 'mismatch'])
    
    context = {
        'reconciliations': reconciliations,
        'total_reconciliations': total_reconciliations,
        'matched_count': matched_count,
        'mismatch_count': mismatch_count,
    }
    
    return render(request, 'students/fee_reconciliation.html', context)


@login_required
def generate_e_receipt(request, receipt_id):
    """Generate and email e-receipt for fee payment"""
    payment = get_object_or_404(FeePayment, id=receipt_id)
    
    if request.method == 'POST' and 'send_email' in request.POST:
        # Send email with receipt
        student = payment.student
        parent_email = getattr(student, 'parent_email', None) or request.POST.get('email')
        
        if parent_email:
            # Generate receipt HTML
            receipt_html = render_to_string('students/e_receipt_template.html', {
                'payment': payment,
                'student': student,
            })
            
            # Send email
            try:
                send_mail(
                    subject=f'Fee Payment Receipt - {payment.receipt_number}',
                    message=f'Fee payment receipt for {student.get_full_name()}',
                    from_email='noreply@schoolerp.com',  # Configure in settings
                    recipient_list=[parent_email],
                    html_message=receipt_html,
                    fail_silently=False,
                )
                
                # Create notification record
                if FeeNotification:
                    try:
                        FeeNotification.objects.create(
                            student=student,
                            notification_type='receipt',
                            subject=f'Fee Payment Receipt - {payment.receipt_number}',
                            message=f'Receipt sent via email to {parent_email}',
                            sent_via='email',
                            sent_to_email=parent_email,
                            is_sent=True,
                        )
                    except Exception as e:
                        # Table doesn't exist - skip notification record creation
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Could not create FeeNotification record: {str(e)}")
                
                messages.success(request, f'Receipt sent to {parent_email}')
            except Exception as e:
                messages.error(request, f'Error sending email: {str(e)}')
        else:
            messages.error(request, 'No email address found for student.')
        
        return redirect('students_app:fee_receipt', receipt_id=receipt_id)
    
    # Display receipt
    context = {
        'payment': payment,
        'student': payment.student,
    }
    
    return render(request, 'students/e_receipt.html', context)

