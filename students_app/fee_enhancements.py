"""
Enhanced Fee Management System
Based on ideas from MasterSoft Fees Management System

⚠️ NOTE: Models have been moved to models.py for Django auto-detection.
This file is kept for reference only.

To use these models, import from models.py:
    from students_app.models import FeeNotification, FeeReconciliation, FeeConcession, StudentFeeConcession
"""

# Models moved to models.py - DO NOT USE THESE
# Import from models.py instead:
# from students_app.models import FeeNotification, FeeReconciliation, FeeConcession, StudentFeeConcession

"""
# ============================================
# MODELS MOVED TO models.py
# ============================================

class FeeConcession(models.Model):
    """Fee concessions based on category, merit, scholarship, etc."""
    CONCESSION_TYPE_CHOICES = [
        ('merit', 'Merit-based'),
        ('scholarship', 'Scholarship'),
        ('category', 'Category-based (SC/ST/OBC)'),
        ('religion', 'Religion-based'),
        ('sibling', 'Sibling Discount'),
        ('staff_child', 'Staff Child'),
        ('sports', 'Sports Achievement'),
        ('academic', 'Academic Excellence'),
        ('financial', 'Financial Aid'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    concession_type = models.CharField(max_length=20, choices=CONCESSION_TYPE_CHOICES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                    validators=[MinValueValidator(0), MaxValueValidator(100)],
                                    help_text="Percentage discount (0-100)")
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                      help_text="Fixed amount discount (if not percentage)")
    is_percentage = models.BooleanField(default=True, help_text="True for percentage, False for fixed amount")
    applicable_to = models.CharField(max_length=50, blank=True, 
                                    help_text="Category/Class/Other criteria")
    min_marks_required = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                            help_text="Minimum marks required for merit-based")
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Fee Concession"
        verbose_name_plural = "Fee Concessions"
    
    def __str__(self):
        return f"{self.name} - {self.get_concession_type_display()}"


class StudentFeeConcession(models.Model):
    """Link students to fee concessions"""
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='fee_concessions')
    concession = models.ForeignKey(FeeConcession, on_delete=models.CASCADE)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    approved_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'concession', 'academic_year']
        ordering = ['-approved_date']
    
    def __str__(self):
        return f"{self.student} - {self.concession}"


class FeeNotification(models.Model):
    """Fee payment notifications and reminders"""
    NOTIFICATION_TYPE_CHOICES = [
        ('pending', 'Pending Fee Reminder'),
        ('overdue', 'Overdue Fee Alert'),
        ('receipt', 'Payment Receipt'),
        ('reminder', 'General Reminder'),
    ]
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='fee_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sent_via = models.CharField(max_length=20, choices=[('email', 'Email'), ('sms', 'SMS'), ('both', 'Both')])
    sent_at = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)
    sent_to_email = models.EmailField(blank=True)
    sent_to_phone = models.CharField(max_length=15, blank=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.student} - {self.get_notification_type_display()}"


class FeeReconciliation(models.Model):
    """Payment reconciliation - cross-check bank statements with payments"""
    reconciliation_date = models.DateField()
    bank_name = models.CharField(max_length=100)
    bank_statement_amount = models.DecimalField(max_digits=12, decimal_places=2)
    system_recorded_amount = models.DecimalField(max_digits=12, decimal_places=2)
    difference = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('matched', 'Matched'),
        ('mismatch', 'Mismatch'),
        ('resolved', 'Resolved'),
    ], default='pending')
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reconciliation_date']
        verbose_name = "Fee Reconciliation"
        verbose_name_plural = "Fee Reconciliations"
    
    def __str__(self):
        return f"Reconciliation - {self.reconciliation_date} - {self.bank_name}"
    
    def calculate_difference(self):
        """Calculate difference between bank and system amounts"""
        self.difference = self.bank_statement_amount - self.system_recorded_amount
        return self.difference

# ============================================
# END OF MOVED MODELS
# ============================================
"""

# Enhanced FeeStructure with category-based calculations
def enhance_fee_structure():
    """
    Add methods to FeeStructure model for:
    - Category-based fee calculation
    - Merit-based discounts
    - Auto-calculation considering all factors
    """
    pass

