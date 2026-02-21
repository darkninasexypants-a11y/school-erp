"""
Staff ID Card Generator with QR Code for Attendance Punching
"""
from PIL import Image, ImageDraw, ImageFont
import qrcode
import json
import hashlib
from io import BytesIO
from django.core.files.base import ContentFile
from datetime import date, timedelta
from django.conf import settings


class StaffIDCardGenerator:
    """Generate ID cards for staff/teachers with attendance QR codes"""
    
    def __init__(self, staff_member, template):
        """
        Initialize with staff member (Staff or Teacher) and template
        """
        self.staff_member = staff_member
        self.template = template
        self.is_teacher = hasattr(staff_member, 'user') and hasattr(staff_member, 'subjects')
        
    def generate_attendance_qr_data(self):
        """
        Generate QR code data for attendance punching
        Format: JSON with staff details and attendance endpoint
        """
        if self.is_teacher:
            # Teacher
            employee_id = getattr(self.staff_member, 'employee_id', None)
            if not employee_id:
                employee_id = f"T{self.staff_member.id}"
            
            staff_data = {
                'type': 'teacher',
                'id': self.staff_member.id,
                'employee_id': employee_id,
                'name': self.staff_member.user.get_full_name(),
                'email': self.staff_member.user.email,
                'designation': 'Teacher',
                'school_id': self.staff_member.school.id if self.staff_member.school else None,
            }
        else:
            # Staff
            staff_data = {
                'type': 'staff',
                'id': self.staff_member.id,
                'employee_id': self.staff_member.employee_id,
                'name': self.staff_member.get_full_name(),
                'email': self.staff_member.user.email,
                'designation': self.staff_member.designation,
                'department': self.staff_member.department,
                'school_id': self.staff_member.school.id if self.staff_member.school else None,
            }
        
        # Create attendance URL
        base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        attendance_url = f"{base_url}/attendance/qr-scan/"
        
        qr_data = {
            'attendance_url': attendance_url,
            'staff': staff_data,
            'card_issue_date': str(date.today()),
        }
        
        # Convert to JSON string
        qr_json = json.dumps(qr_data)
        
        # Generate hash for verification
        qr_hash = hashlib.sha256(qr_json.encode()).hexdigest()
        
        # Add hash to QR data
        qr_data['hash'] = qr_hash
        qr_json = json.dumps(qr_data)
        
        return qr_json, qr_hash
    
    def generate_qr_code(self):
        """Generate QR code image for attendance"""
        qr_data, qr_hash = self.generate_attendance_qr_data()
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        return qr_img, qr_data, qr_hash
    
    def generate_card(self):
        """Generate the ID card image"""
        if not self.template.template_image:
            raise ValueError("Template image is required")
        
        # Load template image
        template_img = Image.open(self.template.template_image.path)
        card = template_img.copy()
        draw = ImageDraw.Draw(card)
        
        # Get staff photo
        if self.is_teacher:
            photo = self.staff_member.photo if hasattr(self.staff_member, 'photo') and self.staff_member.photo else None
            name = self.staff_member.user.get_full_name()
            employee_id = self.staff_member.employee_id
            designation = 'Teacher'  # Teachers don't have designation field
            phone = self.staff_member.phone
        else:
            photo = self.staff_member.photo if self.staff_member.photo else None
            name = self.staff_member.get_full_name()
            employee_id = self.staff_member.employee_id
            designation = self.staff_member.designation
            phone = self.staff_member.phone
        
        # Add photo if enabled and available
        if self.template.show_photo and photo:
            try:
                staff_photo = Image.open(photo.path)
                staff_photo = staff_photo.resize((self.template.photo_width, self.template.photo_height))
                card.paste(staff_photo, (self.template.photo_x, self.template.photo_y))
            except:
                pass
        
        # Load fonts
        try:
            name_font = ImageFont.truetype("arial.ttf", self.template.name_font_size)
            text_font = ImageFont.truetype("arial.ttf", 14)
            small_font = ImageFont.truetype("arial.ttf", 12)
        except:
            name_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Add name if enabled
        if self.template.show_name:
            draw.text(
                (self.template.name_x, self.template.name_y),
                name,
                fill='black',
                font=name_font
            )
        
        # Add employee ID if enabled
        if self.template.show_admission_no:
            draw.text(
                (self.template.admission_no_x, self.template.admission_no_y),
                f"ID: {employee_id}",
                fill='black',
                font=text_font
            )
        
        # Add designation if enabled
        if self.template.show_class:
            draw.text(
                (self.template.class_x, self.template.class_y),
                f"Designation: {designation}",
                fill='black',
                font=text_font
            )
        
        # Add phone if enabled
        if self.template.show_mobile and phone:
            draw.text(
                (self.template.contact_x, self.template.contact_y),
                f"Phone: {phone}",
                fill='black',
                font=small_font
            )
        
        # Add QR code if enabled
        if self.template.show_qr_code:
            qr_img, qr_data, qr_hash = self.generate_qr_code()
            qr_img = qr_img.resize((self.template.qr_code_size, self.template.qr_code_size))
            card.paste(qr_img, (self.template.qr_code_x, self.template.qr_code_y))
        else:
            qr_data = ""
            qr_hash = ""
        
        return card, qr_data, qr_hash
    
    def save_card(self):
        """Generate and save the ID card"""
        from .models import StaffIDCard
        
        card_image, qr_data, qr_hash = self.generate_card()
        
        # Save image to BytesIO
        buffer = BytesIO()
        card_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Generate card number
        employee_id = self.staff_member.employee_id
        card_number = f"STAFF-{employee_id}-{date.today().year}"
        
        # Calculate valid until date (1 year from now)
        valid_until = date.today() + timedelta(days=365)
        
        # Determine if staff or teacher
        staff_obj = None
        teacher_obj = None
        if self.is_teacher:
            teacher_obj = self.staff_member
        else:
            staff_obj = self.staff_member
        
        # Create or update StaffIDCard
        id_card, created = StaffIDCard.objects.get_or_create(
            staff=staff_obj,
            teacher=teacher_obj,
            card_number=card_number,
            defaults={
                'template': self.template,
                'valid_until': valid_until,
                'qr_code_data': qr_data,
                'qr_code_hash': qr_hash,
                'status': 'active'
            }
        )
        
        if not created:
            id_card.template = self.template
            id_card.valid_until = valid_until
            id_card.qr_code_data = qr_data
            id_card.qr_code_hash = qr_hash
            id_card.status = 'active'
        
        # Save the generated image
        filename = f"staff_id_card_{employee_id}.png"
        id_card.generated_image.save(filename, ContentFile(buffer.getvalue()), save=True)
        
        return id_card

