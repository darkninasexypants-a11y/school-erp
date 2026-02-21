"""
School Billing Management Views
For Super Admin to send bills to schools and track payments
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import models
from django.template.loader import render_to_string
from datetime import timedelta
from decimal import Decimal
import io

from .models import School, SchoolBilling, SchoolUser, Student

# PDF libraries will be imported lazily when needed
WEASYPRINT_AVAILABLE = False
XHTML2PDF_AVAILABLE = False


@login_required
def school_billing_dashboard(request):
    """
    School Billing Dashboard - Super Admin Only
    View all school bills, payment status, and send new bills
    """
    # Check if user is superuser
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name != 'super_admin':
                messages.error(request, 'Access denied. Super admin only.')
                return redirect('students_app:admin_dashboard')
        except:
            messages.error(request, 'Access denied.')
            return redirect('students_app:admin_dashboard')
    
    # Get all schools with billing info and student counts
    schools = School.objects.all().order_by('name')
    
    # Add student count for each school
    for school in schools:
        school.active_students_count = Student.objects.filter(school=school, status='active').count()
    
    # Get billing statistics
    total_schools = schools.count()
    
    # Billing records
    all_billings = SchoolBilling.objects.select_related('school').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        all_billings = all_billings.filter(payment_status=status_filter)
    
    # Filter by school
    school_filter = request.GET.get('school', '')
    if school_filter:
        all_billings = all_billings.filter(school_id=school_filter)
    
    # Statistics
    pending_bills = SchoolBilling.objects.filter(payment_status='pending').count()
    overdue_bills = SchoolBilling.objects.filter(payment_status='overdue').count()
    paid_bills = SchoolBilling.objects.filter(payment_status='paid').count()
    
    # Revenue calculations
    total_revenue = SchoolBilling.objects.filter(payment_status='paid').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    pending_revenue = SchoolBilling.objects.filter(payment_status='pending').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    # Overdue bills (due date passed and still pending)
    today = timezone.now().date()
    overdue_billings = SchoolBilling.objects.filter(
        payment_status='pending',
        due_date__lt=today
    )
    
    # Update overdue status
    overdue_billings.update(payment_status='overdue')
    
    context = {
        'schools': schools,
        'billings': all_billings[:50],  # Limit for performance
        'total_schools': total_schools,
        'pending_bills': pending_bills,
        'overdue_bills': overdue_bills,
        'paid_bills': paid_bills,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'current_status': status_filter,
        'current_school': school_filter,
    }
    
    return render(request, 'billing/school_billing_dashboard.html', context)


@login_required
def send_school_bill(request):
    """
    Send/Create a new bill for a school
    """
    # Check if user is superuser
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name != 'super_admin':
                return JsonResponse({'error': 'Access denied'}, status=403)
        except:
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        try:
            school_id = request.POST.get('school_id')
            billing_type = request.POST.get('billing_type', 'per_student')
            amount = request.POST.get('amount')
            rate_per_student = request.POST.get('rate_per_student')
            billing_period = request.POST.get('billing_period')
            due_date = request.POST.get('due_date')
            notes = request.POST.get('notes', '')
            
            # Validation
            if not all([school_id, billing_period]):
                return JsonResponse({
                    'success': False,
                    'error': 'School and billing period are required'
                }, status=400)
            
            school = get_object_or_404(School, id=school_id)
            
            # Get active student count for this school
            student_count = Student.objects.filter(school=school, status='active').count()
            
            # Calculate amount based on billing type
            if billing_type == 'per_student':
                if not rate_per_student:
                    return JsonResponse({
                        'success': False,
                        'error': 'Rate per student is required for per-student billing'
                    }, status=400)
                
                rate = Decimal(rate_per_student)
                calculated_amount = rate * student_count
                amount = calculated_amount
            else:
                # Fixed amount billing
                if not amount:
                    return JsonResponse({
                        'success': False,
                        'error': 'Amount is required for fixed billing'
                    }, status=400)
                amount = Decimal(amount)
                rate_per_student = None
                student_count = None
            
            # If due_date not provided, set to 30 days from now
            if not due_date:
                due_date = (timezone.now() + timedelta(days=30)).date()
            
            # Create billing record
            billing = SchoolBilling.objects.create(
                school=school,
                billing_period=billing_period,
                billing_type=billing_type,
                amount=amount,
                rate_per_student=Decimal(rate_per_student) if rate_per_student else None,
                student_count=student_count if billing_type == 'per_student' else None,
                due_date=due_date,
                payment_status='pending',
                notes=notes
            )
            
            # TODO: Send email/SMS notification to school
            
            return JsonResponse({
                'success': True,
                'message': f'Bill sent to {school.name}',
                'billing_id': billing.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # GET request - show form
    schools = School.objects.all().order_by('name')
    
    # Add student count for each school
    for school in schools:
        school.active_students_count = Student.objects.filter(school=school, status='active').count()
    
    return render(request, 'billing/send_bill.html', {'schools': schools})


@login_required
def update_bill_status(request, billing_id):
    """
    Update billing payment status
    """
    # Check if user is superuser
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name != 'super_admin':
                return JsonResponse({'error': 'Access denied'}, status=403)
        except:
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        try:
            billing = get_object_or_404(SchoolBilling, id=billing_id)
            
            status = request.POST.get('status')
            payment_date = request.POST.get('payment_date')
            payment_method = request.POST.get('payment_method', '')
            transaction_id = request.POST.get('transaction_id', '')
            
            if status:
                billing.payment_status = status
            if payment_date:
                billing.payment_date = payment_date
            if payment_method:
                billing.payment_method = payment_method
            if transaction_id:
                billing.transaction_id = transaction_id
            
            billing.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Billing status updated'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def school_billing_history(request, school_id):
    """
    View billing history for a specific school
    """
    # Check if user is superuser or school admin
    school = get_object_or_404(School, id=school_id)
    
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            # Allow school admin to view their own school's billing
            if school_user.role.name not in ['super_admin', 'school_admin'] or school_user.school != school:
                messages.error(request, 'Access denied.')
                return redirect('students_app:admin_dashboard')
        except:
            messages.error(request, 'Access denied.')
            return redirect('students_app:admin_dashboard')
    
    # Get all bills for this school
    billings = SchoolBilling.objects.filter(school=school).order_by('-created_at')
    
    # Statistics for this school
    total_billed = billings.aggregate(total=models.Sum('amount'))['total'] or 0
    total_paid = billings.filter(payment_status='paid').aggregate(total=models.Sum('amount'))['total'] or 0
    pending_amount = billings.filter(payment_status__in=['pending', 'overdue']).aggregate(total=models.Sum('amount'))['total'] or 0
    
    context = {
        'school': school,
        'billings': billings,
        'total_billed': total_billed,
        'total_paid': total_paid,
        'pending_amount': pending_amount,
    }
    
    return render(request, 'billing/school_billing_history.html', context)


@login_required
def view_invoice(request, billing_id):
    """
    View invoice in browser (HTML)
    """
    billing = get_object_or_404(SchoolBilling, id=billing_id)
    
    # Check permissions
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name not in ['super_admin', 'school_admin'] or school_user.school != billing.school:
                messages.error(request, 'Access denied.')
                return redirect('students_app:admin_dashboard')
        except:
            messages.error(request, 'Access denied.')
            return redirect('students_app:admin_dashboard')
    
    return render(request, 'billing/invoice_template.html', {'billing': billing})


@login_required
def download_invoice_pdf(request, billing_id):
    """
    Download invoice as PDF
    """
    billing = get_object_or_404(SchoolBilling, id=billing_id)
    
    # Check permissions
    if not request.user.is_superuser:
        try:
            school_user = request.user.school_profile
            if school_user.role.name not in ['super_admin', 'school_admin'] or school_user.school != billing.school:
                return JsonResponse({'error': 'Access denied'}, status=403)
        except:
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Render HTML template
    html_string = render_to_string('billing/invoice_template.html', {'billing': billing})
    
    # Try WeasyPrint first (lazy import)
    try:
        from weasyprint import HTML
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()
        
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{billing.id}.pdf"'
        return response
    except ImportError:
        pass
    except Exception as e:
        print(f"WeasyPrint error: {e}")
    
    # Try xhtml2pdf as fallback (lazy import)
    try:
        from xhtml2pdf import pisa
        result = io.BytesIO()
        pdf = pisa.pisaDocument(io.BytesIO(html_string.encode("UTF-8")), result)
        
        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{billing.id}.pdf"'
            return response
    except ImportError:
        pass
    except Exception as e:
        print(f"xhtml2pdf error: {e}")
    
    # No PDF library available - show HTML invoice instead
    messages.warning(request, 'PDF generation not available. Showing HTML invoice. To enable PDF: pip install xhtml2pdf')
    return view_invoice(request, billing_id)

