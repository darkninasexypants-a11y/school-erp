"""
Advanced ID Card Generator
Integrated from external ID card system with JSON layout support
"""
import io
import zipfile
import base64
import os
import time
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from datetime import datetime, date, timedelta
import qrcode


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    elif len(hex_color) == 8:
        # RGBA
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4, 6))
    return (0, 0, 0)


def wrap_text(text, max_width, font, draw):
    """Wrap text to fit within max_width"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines if lines else [text]


class AdvancedIDCardGenerator:
    """Advanced ID card generator with JSON layout support"""
    
    def __init__(self, student, template):
        self.student = student
        self.template = template
        self.layout = template.get_layout()
    
    def generate_card(self):
        """Generate ID card using JSON layout or legacy fields"""
        # Check if using JSON layout
        if self.layout and self.layout.get('elements'):
            return self._generate_with_json_layout()
        else:
            return self._generate_with_legacy_fields()
    
    def _generate_with_json_layout(self):
        """Generate card using JSON layout system"""
        layout = self.layout
        elements = layout.get('elements', [])
        background_image = layout.get('backgroundImage')
        
        # Create base image
        if background_image:
            if background_image.startswith('data:image'):
                # Base64 image
                header, encoded = background_image.split(',', 1)
                image_data = base64.b64decode(encoded)
                base_img = Image.open(io.BytesIO(image_data)).convert('RGBA')
            elif self.template.template_image:
                # Use template image
                base_img = Image.open(self.template.template_image.path).convert('RGBA')
            else:
                # Create blank image
                base_img = Image.new('RGBA', (self.template.width, self.template.height), (255, 255, 255, 255))
        elif self.template.template_image:
            base_img = Image.open(self.template.template_image.path).convert('RGBA')
        else:
            base_img = Image.new('RGBA', (self.template.width, self.template.height), (255, 255, 255, 255))
        
        # Resize if needed
        if base_img.size != (self.template.width, self.template.height):
            base_img = base_img.resize((self.template.width, self.template.height), Image.Resampling.LANCZOS)
        
        draw = ImageDraw.Draw(base_img)
        
        # Process each element
        for element in elements:
            element_type = element.get('type', 'text')
            x = int(element.get('x', 0))
            y = int(element.get('y', 0))
            width = int(element.get('width', 100))
            height = int(element.get('height', 100))

            if element_type == 'logo':
                # Place school logo (single source of truth)
                school = getattr(self.template, 'school', None) or getattr(self.student, 'school', None)
                logo_field = getattr(school, 'logo', None) if school else None
                if logo_field and getattr(logo_field, 'path', None):
                    try:
                        logo_img = Image.open(logo_field.path).convert('RGBA')
                        logo_img.thumbnail((width, height), Image.Resampling.LANCZOS)
                        logo_x = x + (width - logo_img.width) // 2
                        logo_y = y + (height - logo_img.height) // 2
                        base_img.paste(logo_img, (logo_x, logo_y), logo_img)
                    except Exception as e:
                        print(f"Error placing logo: {e}")
                continue

            field = element.get('field')
            if not field:
                continue
            
            if element_type == 'text':
                # Get value based on field name
                value = self._get_field_value(field)
                if not value:
                    continue
                
                font_size = element.get('fontSize', 16)
                color = element.get('color', '#000000')
                font_family = element.get('fontFamily', 'Arial')
                label = element.get('label', '')  # Support for label
                show_label = element.get('showLabel', False)  # Only show label if explicitly enabled
                # Auto-generate label only if showLabel is True
                if show_label and not label:
                    label = self._get_default_label(field)
                label_width = element.get('labelWidth', 0)  # Fixed width for label alignment
                text_align = element.get('textAlign', 'left')  # left, center, right
                line_height = element.get('lineHeight', font_size + 2)  # Spacing between lines
                
                try:
                    font = ImageFont.truetype(font_family, font_size)
                except:
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                
                color_rgb = hex_to_rgb(color)
                
                # Handle label-value pairs with proper alignment
                if label:
                    # Calculate label width if not provided
                    if label_width == 0:
                        label_bbox = draw.textbbox((0, 0), label, font=font)
                        label_width = label_bbox[2] - label_bbox[0] + 5  # Add 5px spacing
                    
                    # Draw label
                    draw.text((x, y), label, fill=color_rgb, font=font)
                    
                    # Draw value aligned after label
                    value_x = x + label_width
                    value_text = str(value)
                    text_lines = wrap_text(value_text, width - label_width, font, draw)
                    current_y = y
                    for line in text_lines:
                        # Handle text alignment
                        if text_align == 'center':
                            line_bbox = draw.textbbox((0, 0), line, font=font)
                            line_width = line_bbox[2] - line_bbox[0]
                            line_x = value_x + (width - label_width - line_width) // 2
                        elif text_align == 'right':
                            line_bbox = draw.textbbox((0, 0), line, font=font)
                            line_width = line_bbox[2] - line_bbox[0]
                            line_x = value_x + (width - label_width - line_width)
                        else:  # left (default)
                            line_x = value_x
                        
                        draw.text((line_x, current_y), line, fill=color_rgb, font=font)
                        current_y += line_height
                else:
                    # No label, just render value
                    value_text = str(value)
                    text_lines = wrap_text(value_text, width, font, draw)
                    current_y = y
                    for line in text_lines:
                        # Handle text alignment
                        if text_align == 'center':
                            line_bbox = draw.textbbox((0, 0), line, font=font)
                            line_width = line_bbox[2] - line_bbox[0]
                            line_x = x + (width - line_width) // 2
                        elif text_align == 'right':
                            line_bbox = draw.textbbox((0, 0), line, font=font)
                            line_width = line_bbox[2] - line_bbox[0]
                            line_x = x + (width - line_width)
                        else:  # left (default)
                            line_x = x
                        
                        draw.text((line_x, current_y), line, fill=color_rgb, font=font)
                        current_y += line_height
            
            elif element_type == 'photo':
                # Place student photo
                if self.student.photo:
                    try:
                        photo_img = Image.open(self.student.photo.path).convert('RGBA')
                        photo_img.thumbnail((width, height), Image.Resampling.LANCZOS)
                        
                        photo_x = x + (width - photo_img.width) // 2
                        photo_y = y + (height - photo_img.height) // 2
                        
                        base_img.paste(photo_img, (photo_x, photo_y), photo_img)
                    except Exception as e:
                        print(f"Error placing photo: {e}")
                        draw.rectangle([x, y, x + width, y + height], outline=(0, 0, 0, 255), width=2)
                        draw.text((x + 10, y + 10), "No Photo", fill=(128, 128, 128, 255))
                else:
                    draw.rectangle([x, y, x + width, y + height], outline=(0, 0, 0, 255), width=2)
                    draw.text((x + 10, y + 10), "No Photo", fill=(128, 128, 128, 255))
            
            elif element_type == 'qr_code':
                # Generate QR code
                qr_data = self._generate_qr_data()
                qr_img = self._create_qr_code(qr_data, width)
                base_img.paste(qr_img, (x, y), qr_img)
        
        # Generate QR data for saving
        qr_data = self._generate_qr_data() if self.template.show_qr_code else ""
        
        return base_img, qr_data
    
    def _generate_with_legacy_fields(self):
        """Generate card using legacy position fields (backward compatibility)"""
        if not self.template.template_image:
            raise ValueError("Template image not found")
        
        card = Image.open(self.template.template_image.path).convert('RGB')
        card = card.resize((self.template.width, self.template.height))
        draw = ImageDraw.Draw(card)
        
        # Try to load fonts
        try:
            name_font = ImageFont.truetype("arial.ttf", self.template.name_font_size)
            text_font = ImageFont.truetype("arial.ttf", 16)
            small_font = ImageFont.truetype("arial.ttf", 12)
        except:
            name_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Add student photo
        if self.student.photo:
            try:
                photo = Image.open(self.student.photo.path).convert('RGB')
                photo = photo.resize((self.template.photo_width, self.template.photo_height))
                card.paste(photo, (self.template.photo_x, self.template.photo_y))
            except Exception as e:
                print(f"Error adding photo: {e}")
        
        # Add student name
        name = self.student.get_full_name().upper()
        draw.text(
            (self.template.name_x, self.template.name_y),
            name,
            fill='black',
            font=name_font
        )
        
        # Add admission number
        draw.text(
            (self.template.admission_no_x, self.template.admission_no_y),
            f"ID: {self.student.admission_number}",
            fill='black',
            font=text_font
        )
        
        # Add class and section
        class_section = self.student.get_class_section()
        draw.text(
            (self.template.class_x, self.template.class_y),
            f"Class: {class_section}",
            fill='black',
            font=text_font
        )
        
        # Add contact
        draw.text(
            (self.template.contact_x, self.template.contact_y),
            f"Contact: {self.student.father_phone}",
            fill='black',
            font=small_font
        )
        
        # Add blood group if enabled
        if self.template.show_blood_group and self.student.blood_group:
            y_offset = self.template.contact_y + 25
            draw.text(
                (self.template.contact_x, y_offset),
                f"Blood Group: {self.student.blood_group}",
                fill='red',
                font=small_font
            )
        
        # Add DOB if enabled
        if self.template.show_dob:
            y_offset = self.template.contact_y + 50
            draw.text(
                (self.template.contact_x, y_offset),
                f"DOB: {self.student.date_of_birth.strftime('%d-%m-%Y')}",
                fill='black',
                font=small_font
            )
        
        # Add QR code if enabled
        qr_data = ""
        if self.template.show_qr_code:
            qr_img, qr_data = self._generate_qr_code()
            qr_img = qr_img.resize((self.template.qr_code_size, self.template.qr_code_size))
            card.paste(qr_img, (self.template.qr_code_x, self.template.qr_code_y))
        
        return card, qr_data
    
    def _get_default_label(self, field_name):
        """Get default label for a field name"""
        label_mapping = {
            'name': 'Name:',
            'full_name': 'Name:',
            'first_name': 'First Name:',
            'last_name': 'Last Name:',
            'admission_number': 'ID:',
            'admission_no': 'ID:',
            'id': 'ID:',
            'roll_number': 'Roll No:',
            'class': 'Class:',
            'class_section': 'Class:',
            'father_name': 'F. Name:',
            'f_name': 'F. Name:',
            'mother_name': 'M. Name:',
            'father_phone': 'Contact:',
            'phone': 'Mobile:',
            'contact': 'Contact:',
            'mobile': 'Mobile:',
            'address': 'Address:',
            'dob': 'DOB:',
            'date_of_birth': 'DOB:',
            'blood_group': 'Blood Group:',
            'gender': 'Gender:',
        }
        return label_mapping.get(field_name.lower(), '')
    
    def _get_field_value(self, field_name):
        """Get field value from student based on field name, using template mappings if available"""
        # Check if template has field mappings configured
        template_mappings = {}
        if self.template.layout_json and self.template.layout_json.get('field_mappings'):
            template_mappings = self.template.layout_json.get('field_mappings', {})
        
        # Map template field names to student data fields
        # First check if there's a direct mapping for this field
        mapped_field = None
        if field_name.lower() in ['name', 'full_name', 'f. name']:
            mapped_field = template_mappings.get('name')
        elif field_name.lower() in ['dob', 'date_of_birth', 'date of birth']:
            mapped_field = template_mappings.get('dob')
        elif field_name.lower() in ['class', 'class name', 'grade']:
            mapped_field = template_mappings.get('class')
        elif field_name.lower() in ['admission_number', 'admission_no', 'id', 'student id']:
            mapped_field = template_mappings.get('admission')
        elif field_name.lower() in ['contact', 'mobile', 'phone']:
            mapped_field = template_mappings.get('contact')
        elif field_name.lower() in ['address', 'home address']:
            mapped_field = template_mappings.get('address')
        
        # Default field mapping
        field_mapping = {
            'name': self.student.get_full_name().upper(),
            'full_name': self.student.get_full_name().upper(),
            'first_name': self.student.first_name,
            'last_name': self.student.last_name,
            'f. name': self.student.father_name or '',
            'admission_number': self.student.admission_number,
            'admission_no': self.student.admission_number,
            'id': self.student.admission_number,
            'student id': self.student.admission_number,
            'roll_number': self.student.roll_number or '',
            'class': self.student.get_class_section() if self.student.current_class and self.student.section else (self.student.current_class.name if self.student.current_class else ''),
            'class name': self.student.current_class.name if self.student.current_class else '',
            'grade': self.student.current_class.name if self.student.current_class else '',
            'class_section': self.student.get_class_section() if self.student.current_class and self.student.section else '',
            'father_name': self.student.father_name or '',
            'mother_name': self.student.mother_name or '',
            'father_phone': self.student.father_phone or '',
            'phone': self.student.father_phone or '',
            'contact': self.student.father_phone or '',
            'mobile': self.student.father_phone or '',
            'address': self.student.address or '',
            'home address': self.student.address or '',
            'dob': self.student.date_of_birth.strftime('%d-%m-%Y') if self.student.date_of_birth else '',
            'date_of_birth': self.student.date_of_birth.strftime('%d-%m-%Y') if self.student.date_of_birth else '',
            'date of birth': self.student.date_of_birth.strftime('%d-%m-%Y') if self.student.date_of_birth else '',
            'blood_group': self.student.blood_group or '',
            'gender': self.student.get_gender_display() if hasattr(self.student, 'get_gender_display') else '',
        }
        
        # If there's a mapped field, use it
        if mapped_field:
            return field_mapping.get(mapped_field.lower(), '')
        
        # Otherwise use default mapping
        return field_mapping.get(field_name.lower(), '')
    
    def _generate_qr_data(self):
        """Generate QR code data"""
        qr_data = f"Student ID: {self.student.admission_number}\n"
        qr_data += f"Name: {self.student.get_full_name()}\n"
        qr_data += f"Class: {self.student.get_class_section()}\n"
        qr_data += f"Contact: {self.student.father_phone}"
        return qr_data
    
    def _generate_qr_code(self):
        """Generate QR code image"""
        qr_data = self._generate_qr_data()
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        return qr_img, qr_data
    
    def _create_qr_code(self, data, size):
        """Create QR code with specified size"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((size, size))
        return qr_img
    
    def save_card(self, replace_existing='replace', delete_old=False):
        """
        Generate and save the ID card
        
        Args:
            replace_existing: 'replace' (update existing), 'delete_old' (delete all old and create new), 
                            'keep_both' (create new even if exists), 'skip' (skip if exists)
            delete_old: If True, delete all old cards for this student before creating new one
        """
        from .models import StudentIDCard
        
        card_image, qr_data = self.generate_card()
        
        # Save image to BytesIO
        buffer = io.BytesIO()
        card_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Generate card number
        card_number = f"CARD-{self.student.admission_number}-{date.today().year}"
        
        # Calculate valid until date (1 year from now)
        valid_until = date.today() + timedelta(days=365)
        
        # Check for existing cards
        existing_cards = StudentIDCard.objects.filter(student=self.student)
        
        # Handle existing cards based on replace_existing parameter
        if existing_cards.exists():
            if replace_existing == 'delete_old' or delete_old:
                # Delete all old cards
                for old_card in existing_cards:
                    if old_card.generated_image:
                        old_card.generated_image.delete(save=False)
                    old_card.delete()
                # Create new card
                id_card = StudentIDCard.objects.create(
                    student=self.student,
                    card_number=card_number,
                    template=self.template,
                    valid_until=valid_until,
                    qr_code_data=qr_data,
                    status='active'
                )
            elif replace_existing == 'keep_both':
                # Create new card with unique card number
                import time
                card_number = f"CARD-{self.student.admission_number}-{date.today().year}-{int(time.time())}"
                id_card = StudentIDCard.objects.create(
                    student=self.student,
                    card_number=card_number,
                    template=self.template,
                    valid_until=valid_until,
                    qr_code_data=qr_data,
                    status='active'
                )
            elif replace_existing == 'skip':
                # Skip if exists
                existing = existing_cards.filter(card_number=card_number).first()
                if existing:
                    return existing
                # Create if card_number doesn't match
                id_card = StudentIDCard.objects.create(
                    student=self.student,
                    card_number=card_number,
                    template=self.template,
                    valid_until=valid_until,
                    qr_code_data=qr_data,
                    status='active'
                )
            else:  # 'replace' - default behavior
                # Update existing card with same card_number or first active card
                id_card, created = StudentIDCard.objects.get_or_create(
                    student=self.student,
                    card_number=card_number,
                    defaults={
                        'template': self.template,
                        'valid_until': valid_until,
                        'qr_code_data': qr_data,
                        'status': 'active'
                    }
                )
                
                if not created:
                    # Update existing card
                    old_image = id_card.generated_image
                    id_card.template = self.template
                    id_card.valid_until = valid_until
                    id_card.qr_code_data = qr_data
                    id_card.status = 'active'
                    # Delete old image if exists
                    if old_image:
                        old_image.delete(save=False)
        else:
            # No existing cards, create new
            id_card = StudentIDCard.objects.create(
                student=self.student,
                card_number=card_number,
                template=self.template,
                valid_until=valid_until,
                qr_code_data=qr_data,
                status='active'
            )
        
        # Save the generated image
        filename = f"id_card_{self.student.admission_number}_{int(time.time()) if replace_existing == 'keep_both' else ''}.png"
        id_card.generated_image.save(filename, ContentFile(buffer.getvalue()), save=True)
        
        return id_card


def generate_bulk_id_cards_advanced(students, template, replace_existing='replace', delete_old=False):
    """
    Generate ID cards for multiple students using advanced generator
    
    Args:
        students: QuerySet of Student objects
        template: IDCardTemplate object
        replace_existing: 'replace' (update existing), 'delete_old' (delete all old and create new), 
                         'keep_both' (create new even if exists), 'skip' (skip if exists)
        delete_old: If True, delete all old cards before creating new ones
    """
    generated_cards = []
    errors = []
    
    for student in students:
        try:
            generator = AdvancedIDCardGenerator(student, template)
            card = generator.save_card(replace_existing=replace_existing, delete_old=delete_old)
            generated_cards.append(card)
        except Exception as e:
            errors.append(f"{student.get_full_name()}: {str(e)}")
    
    return generated_cards, errors


def generate_id_cards_batch_from_excel(template, excel_data, mapping, photos_dict=None):
    """
    Generate ID cards in batch from Excel data (integrated from external system)
    
    Args:
        template: IDCardTemplate model object
        excel_data: List of dictionaries from Excel
        mapping: Dictionary mapping template fields to Excel columns
        photos_dict: Dictionary of photo data keyed by filename (without extension)
    
    Returns:
        BytesIO buffer containing ZIP file
    """
    photos_dict = photos_dict or {}
    layout = template.get_layout()
    elements = layout.get('elements', []) if layout else []
    background_image = layout.get('backgroundImage') if layout else None
    
    # Create ZIP buffer
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for idx, row in enumerate(excel_data):
            try:
                # Create base image
                if background_image:
                    if background_image.startswith('data:image'):
                        header, encoded = background_image.split(',', 1)
                        image_data = base64.b64decode(encoded)
                        base_img = Image.open(io.BytesIO(image_data)).convert('RGBA')
                    elif template.template_image:
                        base_img = Image.open(template.template_image.path).convert('RGBA')
                    else:
                        base_img = Image.new('RGBA', (template.width, template.height), (255, 255, 255, 255))
                elif template.template_image:
                    base_img = Image.open(template.template_image.path).convert('RGBA')
                else:
                    base_img = Image.new('RGBA', (template.width, template.height), (255, 255, 255, 255))
                
                # Resize if needed
                if base_img.size != (template.width, template.height):
                    base_img = base_img.resize((template.width, template.height), Image.Resampling.LANCZOS)
                
                draw = ImageDraw.Draw(base_img)
                
                # Process each element
                for element in elements:
                    field = element.get('field')
                    if not field:
                        continue
                    
                    # Get mapped Excel column
                    excel_column = mapping.get(field)
                    if not excel_column:
                        continue
                    
                    # Get value from Excel row
                    value = str(row.get(excel_column, '')).strip()
                    if not value:
                        continue
                    
                    element_type = element.get('type', 'text')
                    x = int(element.get('x', 0))
                    y = int(element.get('y', 0))
                    width = int(element.get('width', 100))
                    height = int(element.get('height', 100))

                    if element_type == 'logo':
                        school = getattr(template, 'school', None)
                        logo_field = getattr(school, 'logo', None) if school else None
                        if logo_field and getattr(logo_field, 'path', None):
                            try:
                                logo_img = Image.open(logo_field.path).convert('RGBA')
                                logo_img.thumbnail((width, height), Image.Resampling.LANCZOS)
                                logo_x = x + (width - logo_img.width) // 2
                                logo_y = y + (height - logo_img.height) // 2
                                base_img.paste(logo_img, (logo_x, logo_y), logo_img)
                            except Exception as e:
                                print(f"Error placing logo: {e}")
                        continue
                    
                    if element_type == 'text':
                        font_size = element.get('fontSize', 16)
                        color = element.get('color', '#000000')
                        font_family = element.get('fontFamily', 'Arial')
                        
                        try:
                            font = ImageFont.truetype(font_family, font_size)
                        except:
                            try:
                                font = ImageFont.truetype("arial.ttf", font_size)
                            except:
                                font = ImageFont.load_default()
                        
                        color_rgb = hex_to_rgb(color)
                        text_lines = wrap_text(value, width, font, draw)
                        current_y = y
                        for line in text_lines:
                            draw.text((x, current_y), line, fill=color_rgb, font=font)
                            current_y += font_size + 2
                    
                    elif element_type == 'photo':
                        photo_key = value.lower().replace(' ', '_').replace('.', '').replace('-', '_')
                        photo_data = photos_dict.get(photo_key)
                        
                        if photo_data:
                            try:
                                photo_img = Image.open(io.BytesIO(photo_data)).convert('RGBA')
                                photo_img.thumbnail((width, height), Image.Resampling.LANCZOS)
                                
                                photo_x = x + (width - photo_img.width) // 2
                                photo_y = y + (height - photo_img.height) // 2
                                
                                base_img.paste(photo_img, (photo_x, photo_y), photo_img)
                            except Exception as e:
                                print(f"Error placing photo {value}: {e}")
                                draw.rectangle([x, y, x + width, y + height], outline=(0, 0, 0, 255), width=2)
                                draw.text((x + 10, y + 10), "No Photo", fill=(128, 128, 128, 255))
                        else:
                            draw.rectangle([x, y, x + width, y + height], outline=(0, 0, 0, 255), width=2)
                            draw.text((x + 10, y + 10), "No Photo", fill=(128, 128, 128, 255))
                
                # Save image to ZIP
                img_buffer = io.BytesIO()
                base_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Generate filename
                name = row.get(mapping.get('Name') or mapping.get('name') or 'Name', f'id_{idx}')
                filename = f"{name.replace(' ', '_')}.png"
                zipf.writestr(filename, img_buffer.read())
                
            except Exception as e:
                print(f"Error generating ID card for row {idx}: {e}")
                continue
    
    zip_buffer.seek(0)
    return zip_buffer

