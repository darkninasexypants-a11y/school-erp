"""
Communication System Models
Handles messaging, assignments, homework, notices, timetables, and events
All sensitive data is encrypted at rest
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Student, Teacher, Parent, Class, Section, Subject
from .communication_encryption import encrypt_text, decrypt_text, is_encrypted


class Message(models.Model):
    """Direct messaging between teachers, parents, and students"""
    MESSAGE_TYPE_CHOICES = [
        ('teacher_parent', 'Teacher to Parent'),
        ('parent_teacher', 'Parent to Teacher'),
        ('teacher_student', 'Teacher to Student'),
        ('student_teacher', 'Student to Teacher'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES)
    subject = models.CharField(max_length=200)
    message = models.TextField()  # Encrypted in save()
    message_encrypted = models.BooleanField(default=False)  # Flag to track encryption
    attachment = models.FileField(upload_to='messages/attachments/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Related entities
    related_student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, 
                                      help_text="Student this message is about")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'recipient']),
            models.Index(fields=['is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.subject}"
    
    def save(self, *args, **kwargs):
        # Encrypt message content before saving
        if self.message and not is_encrypted(self.message):
            self.message = encrypt_text(self.message)
            self.message_encrypted = True
        super().save(*args, **kwargs)
    
    def get_decrypted_message(self):
        """Get decrypted message content"""
        if self.message_encrypted and is_encrypted(self.message):
            try:
                return decrypt_text(self.message)
            except:
                return self.message  # Return as-is if decryption fails
        return self.message
    
    @property
    def decrypted_message(self):
        """Property to access decrypted message"""
        return self.get_decrypted_message()
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class Assignment(models.Model):
    """Assignments created by teachers for students"""
    SUBMISSION_TYPE_CHOICES = [
        ('digital', 'Digital Only'),
        ('physical', 'Physical Only'),
        ('both', 'Both Digital and Physical'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()  # Encrypted in save()
    description_encrypted = models.BooleanField(default=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    target_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    target_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
    
    submission_type = models.CharField(max_length=20, choices=SUBMISSION_TYPE_CHOICES, default='digital')
    due_date = models.DateTimeField()
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True)
    instructions = models.TextField(blank=True)  # Encrypted in save()
    instructions_encrypted = models.BooleanField(default=False)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', 'target_class']),
            models.Index(fields=['due_date', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        # Encrypt description and instructions before saving
        if self.description and not is_encrypted(self.description):
            self.description = encrypt_text(self.description)
            self.description_encrypted = True
        if self.instructions and not is_encrypted(self.instructions):
            self.instructions = encrypt_text(self.instructions)
            self.instructions_encrypted = True
        super().save(*args, **kwargs)
    
    def get_decrypted_description(self):
        """Get decrypted description"""
        if self.description_encrypted and is_encrypted(self.description):
            try:
                return decrypt_text(self.description)
            except:
                return self.description
        return self.description
    
    def get_decrypted_instructions(self):
        """Get decrypted instructions"""
        if self.instructions_encrypted and is_encrypted(self.instructions):
            try:
                return decrypt_text(self.instructions)
            except:
                return self.instructions
        return self.instructions
    
    @property
    def decrypted_description(self):
        return self.get_decrypted_description()
    
    @property
    def decrypted_instructions(self):
        return self.get_decrypted_instructions()
    
    def __str__(self):
        return f"{self.title} - {self.target_class.name}"


class AssignmentSubmission(models.Model):
    """Student submissions for assignments"""
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('late', 'Late Submission'),
        ('missing', 'Missing'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    
    # Digital submission
    digital_file = models.FileField(upload_to='assignments/submissions/digital/', blank=True, null=True)
    digital_text = models.TextField(blank=True)  # Encrypted in save()
    digital_text_encrypted = models.BooleanField(default=False)
    digital_submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Physical submission
    physical_submitted = models.BooleanField(default=False)
    physical_submitted_at = models.DateTimeField(null=True, blank=True)
    physical_remarks = models.CharField(max_length=500, blank=True)  # Encrypted in save()
    physical_remarks_encrypted = models.BooleanField(default=False)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)  # Encrypted in save()
    feedback_encrypted = models.BooleanField(default=False)
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['assignment', 'student']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assignment.title}"
    
    def save(self, *args, **kwargs):
        # Encrypt sensitive fields before saving
        if self.digital_text and not is_encrypted(self.digital_text):
            self.digital_text = encrypt_text(self.digital_text)
            self.digital_text_encrypted = True
        if self.physical_remarks and not is_encrypted(self.physical_remarks):
            self.physical_remarks = encrypt_text(self.physical_remarks)
            self.physical_remarks_encrypted = True
        if self.feedback and not is_encrypted(self.feedback):
            self.feedback = encrypt_text(self.feedback)
            self.feedback_encrypted = True
        super().save(*args, **kwargs)
    
    def get_decrypted_digital_text(self):
        """Get decrypted digital text"""
        if self.digital_text_encrypted and is_encrypted(self.digital_text):
            try:
                return decrypt_text(self.digital_text)
            except:
                return self.digital_text
        return self.digital_text
    
    def get_decrypted_physical_remarks(self):
        """Get decrypted physical remarks"""
        if self.physical_remarks_encrypted and is_encrypted(self.physical_remarks):
            try:
                return decrypt_text(self.physical_remarks)
            except:
                return self.physical_remarks
        return self.physical_remarks
    
    def get_decrypted_feedback(self):
        """Get decrypted feedback"""
        if self.feedback_encrypted and is_encrypted(self.feedback):
            try:
                return decrypt_text(self.feedback)
            except:
                return self.feedback
        return self.feedback
    
    @property
    def decrypted_digital_text(self):
        return self.get_decrypted_digital_text()
    
    @property
    def decrypted_physical_remarks(self):
        return self.get_decrypted_physical_remarks()
    
    @property
    def decrypted_feedback(self):
        return self.get_decrypted_feedback()
    
    def is_late(self):
        if self.assignment.due_date and self.digital_submitted_at:
            return self.digital_submitted_at > self.assignment.due_date
        return False


class CommunicationHomework(models.Model):
    """Homework assignments and management"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()  # Encrypted in save()
    description_encrypted = models.BooleanField(default=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    target_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    target_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
    
    due_date = models.DateField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    attachment = models.FileField(upload_to='homework/', blank=True, null=True)
    instructions = models.TextField(blank=True)  # Encrypted in save()
    instructions_encrypted = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-due_date', '-created_at']
    
    def save(self, *args, **kwargs):
        # Encrypt description and instructions before saving
        if self.description and not is_encrypted(self.description):
            self.description = encrypt_text(self.description)
            self.description_encrypted = True
        if self.instructions and not is_encrypted(self.instructions):
            self.instructions = encrypt_text(self.instructions)
            self.instructions_encrypted = True
        super().save(*args, **kwargs)
    
    def get_decrypted_description(self):
        """Get decrypted description"""
        if self.description_encrypted and is_encrypted(self.description):
            try:
                return decrypt_text(self.description)
            except:
                return self.description
        return self.description
    
    def get_decrypted_instructions(self):
        """Get decrypted instructions"""
        if self.instructions_encrypted and is_encrypted(self.instructions):
            try:
                return decrypt_text(self.instructions)
            except:
                return self.instructions
        return self.instructions
    
    @property
    def decrypted_description(self):
        return self.get_decrypted_description()
    
    @property
    def decrypted_instructions(self):
        return self.get_decrypted_instructions()
    
    def __str__(self):
        return f"{self.title} - {self.target_class.name}"


class CommunicationHomeworkSubmission(models.Model):
    """Student homework submissions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('late', 'Late'),
        ('not_submitted', 'Not Submitted'),
    ]
    
    homework = models.ForeignKey(CommunicationHomework, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    
    submission_file = models.FileField(upload_to='homework/submissions/', blank=True, null=True)
    submission_text = models.TextField(blank=True)  # Encrypted in save()
    submission_text_encrypted = models.BooleanField(default=False)
    submission_date = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(blank=True)  # Encrypted in save()
    remarks_encrypted = models.BooleanField(default=False)
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['homework', 'student']
        ordering = ['-submission_date']
    
    def save(self, *args, **kwargs):
        # Encrypt sensitive fields before saving
        if self.submission_text and not is_encrypted(self.submission_text):
            self.submission_text = encrypt_text(self.submission_text)
            self.submission_text_encrypted = True
        if self.remarks and not is_encrypted(self.remarks):
            self.remarks = encrypt_text(self.remarks)
            self.remarks_encrypted = True
        super().save(*args, **kwargs)
    
    def get_decrypted_submission_text(self):
        """Get decrypted submission text"""
        if self.submission_text_encrypted and is_encrypted(self.submission_text):
            try:
                return decrypt_text(self.submission_text)
            except:
                return self.submission_text
        return self.submission_text
    
    def get_decrypted_remarks(self):
        """Get decrypted remarks"""
        if self.remarks_encrypted and is_encrypted(self.remarks):
            try:
                return decrypt_text(self.remarks)
            except:
                return self.remarks
        return self.remarks
    
    @property
    def decrypted_submission_text(self):
        return self.get_decrypted_submission_text()
    
    @property
    def decrypted_remarks(self):
        return self.get_decrypted_remarks()
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.homework.title}"


class CommunicationTimetable(models.Model):
    """Class timetables"""
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    period_number = models.IntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    room_number = models.CharField(max_length=50, blank=True)
    
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['class_assigned', 'section', 'day', 'period_number']
        unique_together = ['class_assigned', 'section', 'day', 'period_number']
    
    def __str__(self):
        section_str = f" - {self.section.name}" if self.section else ""
        return f"{self.class_assigned.name}{section_str} - {self.day} - Period {self.period_number}"


class CommunicationEventSchedule(models.Model):
    """Event scheduling system"""
    EVENT_TYPE_CHOICES = [
        ('academic', 'Academic'),
        ('sports', 'Sports'),
        ('cultural', 'Cultural'),
        ('parent_meeting', 'Parent Meeting'),
        ('exam', 'Exam'),
        ('holiday', 'Holiday'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='other')
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    venue = models.CharField(max_length=200, blank=True)
    target_audience = models.CharField(max_length=50, default='all', 
                                       help_text="all, class, section, or specific")
    target_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True)
    target_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
    
    attachment = models.FileField(upload_to='events/', blank=True, null=True)
    is_all_day = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_date', 'start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_date}"

