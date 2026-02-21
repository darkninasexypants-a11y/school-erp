"""
Advanced ID Card Generation System
Features:
- Pillow-based image processing
- Batch automation from CSV/Excel
- QR code integration with security
- OCR capabilities (EasyOCR)
- AI facial verification
- Modern template system
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import qrcode
from qrcode.constants import ERROR_CORRECT_H
import io
import zipfile
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import re
from django.core.files.base import ContentFile
from django.conf import settings

# Optional imports for advanced features
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False


class AdvancedIDCardSystem:
    """Professional-grade ID card generation system"""
    
    def __init__(self, template=None):
        self.template = template
        self.reader = None
        
        # Initialize OCR if available
        if EASYOCR_AVAILABLE:
            try:
                self.reader = easyocr.Reader(['en'], gpu=False)
            except:
                self.reader = None
    
    def generate_secure_qr_code(self, data, size=200, error_correction=ERROR_CORRECT_H):
        """
        Generate secure QR code with high error correction
        Can embed URLs, encrypted data, or verification codes
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=error_correction,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)
        
        return qr_img
    
    def process_photo(self, photo_path, target_size=(200, 250), enhance=True):
        """
        Process and enhance photo for ID card
        - Resize with aspect ratio
        - Enhance quality
        - Apply filters if needed
        """
        try:
            img = Image.open(photo_path).convert('RGB')
            
            # Calculate aspect ratio
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Create new image with exact size and paste centered
            new_img = Image.new('RGB', target_size, (255, 255, 255))
            x_offset = (target_size[0] - img.width) // 2
            y_offset = (target_size[1] - img.height) // 2
            new_img.paste(img, (x_offset, y_offset))
            
            if enhance:
                # Enhance contrast and sharpness
                enhancer = ImageEnhance.Contrast(new_img)
                new_img = enhancer.enhance(1.1)
                enhancer = ImageEnhance.Sharpness(new_img)
                new_img = enhancer.enhance(1.2)
            
            return new_img
        except Exception as e:
            print(f"Error processing photo: {e}")
            # Return placeholder
            placeholder = Image.new('RGB', target_size, (200, 200, 200))
            draw = ImageDraw.Draw(placeholder)
            draw.text((10, 10), "No Photo", fill=(100, 100, 100))
            return placeholder
    
    def extract_text_from_id(self, image_path, template=None):
        """
        Extract text from existing ID card using OCR
        Returns dictionary with extracted text fields (only what's in the image)
        No predefined field assumptions - extracts only what's actually present
        
        Args:
            image_path: Path to the ID card image
            template: Optional IDCardTemplate object for storing detected fields for learning
        """
        if not EASYOCR_AVAILABLE or not self.reader:
            return None
        
        try:
            result = self.reader.readtext(image_path)
            extracted_data = {}
            detected_fields_list = []
            
            # Extract all text with their positions and confidence
            # No predefined patterns - just extract what's in the image
            for idx, detection in enumerate(result):
                # detection format: (bbox, text, confidence)
                bbox = detection[0]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                text = detection[1].strip()
                confidence = detection[2]
                
                # Only include high confidence text
                if confidence > 0.5 and text:
                    # Calculate center position and dimensions
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    x_center = sum(x_coords) / len(x_coords)
                    y_center = sum(y_coords) / len(y_coords)
                    width = max(x_coords) - min(x_coords)
                    height = max(y_coords) - min(y_coords)
                    
                    # Use sequential field names based on position (top to bottom, left to right)
                    # This allows learning which fields are in the template
                    field_key = f"field_{idx + 1}"
                    
                    # Store extracted text with metadata
                    extracted_data[field_key] = text
                    
                    # Store field info for learning (can be saved to template)
                    detected_fields_list.append({
                        'field_key': field_key,
                        'text': text,
                        'confidence': float(confidence),
                        'position': {
                            'x': float(x_center),
                            'y': float(y_center),
                            'width': float(width),
                            'height': float(height),
                            'bbox': [[float(p[0]), float(p[1])] for p in bbox]
                        }
                    })
            
            # Store detected fields in template for learning purposes (if template provided)
            if template and hasattr(template, 'layout_json') and detected_fields_list:
                if template.layout_json is None:
                    template.layout_json = {}
                
                # Store detected fields in layout_json for learning
                if 'detected_fields' not in template.layout_json:
                    template.layout_json['detected_fields'] = []
                
                # Merge with existing detected fields (avoid duplicates)
                existing_fields = template.layout_json['detected_fields']
                for new_field in detected_fields_list:
                    # Check if similar field already exists (same position)
                    is_duplicate = False
                    for existing_field in existing_fields:
                        pos1 = existing_field.get('position', {})
                        pos2 = new_field.get('position', {})
                        if (abs(pos1.get('x', 0) - pos2.get('x', 0)) < 10 and 
                            abs(pos1.get('y', 0) - pos2.get('y', 0)) < 10):
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        existing_fields.append(new_field)
                
                template.layout_json['detected_fields'] = existing_fields
                template.save()
            
            # Also add raw text for reference
            if extracted_data:
                all_text_values = [v for v in extracted_data.values() if v]
                extracted_data['_raw_text_all'] = ' | '.join(all_text_values)
                extracted_data['_total_fields'] = len(extracted_data) - 2  # Excluding _raw_text_all and _total_fields
            
            return extracted_data if extracted_data else None
        except Exception as e:
            print(f"OCR Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def verify_face(self, photo1_path, photo2_path, fast_mode=True):
        """
        Verify if two photos are of the same person
        Returns True if match, False otherwise
        
        Args:
            photo1_path: Path to first photo (reference/staff photo)
            photo2_path: Path to second photo (captured photo)
            fast_mode: If True, uses faster model (Facenet) instead of VGG-Face
        """
        if not DEEPFACE_AVAILABLE:
            return None
        
        try:
            # Optimize images before processing (resize to max 640px for faster processing)
            from PIL import Image as PILImage
            import tempfile
            
            # Process and optimize images
            def optimize_image(img_path, max_size=640):
                img = PILImage.open(img_path)
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), PILImage.Resampling.LANCZOS)
                    temp_path = tempfile.mktemp(suffix='.jpg')
                    img.save(temp_path, 'JPEG', quality=85, optimize=True)
                    return temp_path
                return img_path
            
            opt_photo1 = optimize_image(photo1_path)
            opt_photo2 = optimize_image(photo2_path)
            
            # Use faster model for speed (Facenet is ~3x faster than VGG-Face)
            model_name = 'Facenet' if fast_mode else 'VGG-Face'
            
            result = DeepFace.verify(
                img1_path=opt_photo1,
                img2_path=opt_photo2,
                model_name=model_name,
                enforce_detection=False,
                distance_metric='cosine'  # Faster than euclidean
            )
            
            # Clean up temp files if created
            if opt_photo1 != photo1_path and os.path.exists(opt_photo1):
                try:
                    os.unlink(opt_photo1)
                except:
                    pass
            if opt_photo2 != photo2_path and os.path.exists(opt_photo2):
                try:
                    os.unlink(opt_photo2)
                except:
                    pass
            
            return result['verified']
        except Exception as e:
            print(f"Face verification error: {e}")
            return None
    
    def generate_card_advanced(self, data_dict, template_path=None):
        """
        Generate ID card with advanced features
        data_dict should contain:
        - name, photo, id_number, class, section, etc.
        - qr_data (optional)
        - custom_fields (optional dict)
        """
        # Load template or create default
        if template_path and os.path.exists(template_path):
            card = Image.open(template_path).convert('RGB')
        else:
            # Create default template
            card = Image.new('RGB', (850, 550), (255, 255, 255))
            draw = ImageDraw.Draw(card)
            # Add border
            draw.rectangle([0, 0, 849, 549], outline=(0, 0, 0), width=5)
        
        draw = ImageDraw.Draw(card)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 32)
            name_font = ImageFont.truetype("arial.ttf", 28)
            text_font = ImageFont.truetype("arial.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 14)
        except:
            title_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Add photo
        if 'photo' in data_dict and data_dict['photo']:
            photo = self.process_photo(data_dict['photo'], (200, 250))
            card.paste(photo, (50, 100))
        
        # Add name
        name = data_dict.get('name', 'N/A').upper()
        draw.text((280, 120), name, fill=(0, 0, 0), font=name_font)
        
        # Add ID number
        id_num = data_dict.get('id_number', data_dict.get('admission_number', 'N/A'))
        draw.text((280, 180), f"ID: {id_num}", fill=(50, 50, 50), font=text_font)
        
        # Add class/section
        if 'class' in data_dict or 'section' in data_dict:
            class_info = f"{data_dict.get('class', '')} - {data_dict.get('section', '')}"
            draw.text((280, 220), class_info, fill=(50, 50, 50), font=text_font)
        
        # Add QR code
        qr_data = data_dict.get('qr_data', f"ID:{id_num}|Name:{name}")
        qr_img = self.generate_secure_qr_code(qr_data, size=150)
        card.paste(qr_img, (650, 350))
        
        # Add custom fields
        y_pos = 280
        for key, value in data_dict.get('custom_fields', {}).items():
            draw.text((280, y_pos), f"{key}: {value}", fill=(80, 80, 80), font=small_font)
            y_pos += 25
        
        # Add validity date
        valid_until = datetime.now() + timedelta(days=365)
        draw.text((50, 500), f"Valid until: {valid_until.strftime('%d/%m/%Y')}", 
                 fill=(100, 100, 100), font=small_font)
        
        return card
    
    def batch_generate_from_excel(self, excel_path, template_path=None, 
                                  photo_folder=None, output_format='zip', template=None):
        """
        Generate ID cards in batch from Excel file
        Supports CSV and Excel formats
        """
        # Read Excel/CSV
        try:
            if excel_path.endswith('.csv'):
                df = pd.read_csv(excel_path)
            else:
                df = pd.read_excel(excel_path)
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")
        
        generated_cards = []
        errors = []
        
        # Create output buffer
        if output_format == 'zip':
            zip_buffer = io.BytesIO()
            zip_file = zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED)
        
        # Get field mappings from template if available
        field_mappings = {}
        if template and hasattr(template, 'layout_json') and template.layout_json:
            field_mappings = template.layout_json.get('field_mappings', {})
        elif self.template and hasattr(self.template, 'layout_json') and self.template.layout_json:
            field_mappings = self.template.layout_json.get('field_mappings', {})
        
        # Helper function to get value from Excel row using mappings
        def get_excel_value(field_type, default_columns):
            # Check if there's a mapping for this field
            mapped_column = field_mappings.get(field_type)
            if mapped_column:
                # Try the mapped column first
                value = row.get(mapped_column, '')
                if value:
                    return str(value).strip()
            
            # Try default columns
            for col in default_columns:
                value = row.get(col, '')
                if value:
                    return str(value).strip()
            return ''
        
        for idx, row in df.iterrows():
            try:
                # Prepare data dictionary using mappings
                data_dict = {
                    'name': get_excel_value('name', ['Name', 'name', 'Student Name', 'F. Name', 'full_name', 'first_name']),
                    'id_number': get_excel_value('admission', ['ID', 'id', 'Admission Number', 'Admission No', 'Student ID']),
                    'class': get_excel_value('class', ['Class', 'class', 'Class Name', 'Grade']),
                    'section': str(row.get('Section', row.get('section', ''))),
                    'dob': get_excel_value('dob', ['DOB', 'dob', 'Date of Birth', 'Birth Date', 'date_of_birth']),
                    'contact': get_excel_value('contact', ['Mobile', 'mobile', 'Phone', 'phone', 'Contact']),
                    'address': get_excel_value('address', ['Address', 'address', 'Home Address']),
                    'photo': None,
                }
                
                # Fallback if name is empty
                if not data_dict['name']:
                    data_dict['name'] = f'Person_{idx}'
                
                # Find photo using photo number
                if photo_folder:
                    photo_number = str(row.get('Photo', row.get('photo', row.get('Photo No', row.get('photo_no', row.get('Photo Number', row.get('photo_number', '')))))))
                    if photo_number:
                        # Try to find photo by number with common extensions
                        photo_number = photo_number.strip()
                        photo_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
                        photo_found = False
                        
                        for ext in photo_extensions:
                            photo_filename = f"{photo_number}{ext}"
                            photo_path = os.path.join(photo_folder, photo_filename)
                            if os.path.exists(photo_path):
                                data_dict['photo'] = photo_path
                                photo_found = True
                                break
                        
                        # If not found with extension, try direct match (in case user provided full filename)
                        if not photo_found:
                            photo_path = os.path.join(photo_folder, photo_number)
                            if os.path.exists(photo_path):
                                data_dict['photo'] = photo_path
                
                # Generate QR data
                qr_data = f"ID:{data_dict['id_number']}|Name:{data_dict['name']}|Class:{data_dict['class']}"
                data_dict['qr_data'] = qr_data
                
                # Generate card
                card = self.generate_card_advanced(data_dict, template_path)
                
                # Save card
                if output_format == 'zip':
                    img_buffer = io.BytesIO()
                    card.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    filename = f"{data_dict['name'].replace(' ', '_')}_{data_dict['id_number']}.png"
                    zip_file.writestr(filename, img_buffer.read())
                else:
                    generated_cards.append(card)
                
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                continue
        
        if output_format == 'zip':
            zip_file.close()
            zip_buffer.seek(0)
            return zip_buffer, errors
        
        return generated_cards, errors
    
    def generate_pdf_batch(self, cards, output_path=None):
        """
        Generate PDF with multiple ID cards (for printing)
        """
        try:
            from reportlab.lib.pagesizes import A4, letter
            from reportlab.lib.units import mm
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            
            if output_path:
                c = canvas.Canvas(output_path, pagesize=A4)
            else:
                pdf_buffer = io.BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=A4)
            
            cards_per_page = 2
            page_width, page_height = A4
            
            for idx, card in enumerate(cards):
                if idx > 0 and idx % cards_per_page == 0:
                    c.showPage()
                
                # Convert PIL image to format ReportLab can use
                img_buffer = io.BytesIO()
                card.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Calculate position
                x = 50
                y = page_height - (idx % cards_per_page) * 300 - 200
                
                c.drawImage(ImageReader(img_buffer), x, y, width=200, height=250)
            
            c.save()
            
            if output_path:
                return output_path
            else:
                pdf_buffer.seek(0)
                return pdf_buffer
                
        except ImportError:
            raise ImportError("ReportLab required for PDF generation. Install: pip install reportlab")
    
    def create_printable_sheet(self, card_image_path, paper_size="A4", dpi=300, gap_mm=2, output_path=None):
        """
        Tiles an ID card image onto a specific paper size for printing.
        
        :param card_image_path: Path to the single ID card image (front or back).
        :param paper_size: "A4" or "12x18".
        :param dpi: Print resolution (default 300).
        :param gap_mm: Gap between cards for cutting (in millimeters).
        :param output_path: Optional output path. If None, returns BytesIO buffer.
        :return: Path to saved file or BytesIO buffer
        """
        
        # 1. Define conversions
        mm_to_px = lambda mm: int(mm * dpi / 25.4)
        inch_to_px = lambda inch: int(inch * dpi)
        
        # 2. Define Paper Dimensions (in pixels)
        if paper_size == "A4":
            # A4 is 210mm x 297mm
            sheet_w = mm_to_px(210)
            sheet_h = mm_to_px(297)
        elif paper_size == "12x18":
            # 12x18 is 12 inches x 18 inches
            sheet_w = inch_to_px(12)
            sheet_h = inch_to_px(18)
        else:
            raise ValueError("Unsupported paper size. Use 'A4' or '12x18'.")

        # 3. Load the ID Card
        try:
            if isinstance(card_image_path, str):
                card = Image.open(card_image_path)
            elif hasattr(card_image_path, 'read'):  # File-like object
                card = Image.open(card_image_path)
            else:  # PIL Image object
                card = card_image_path.copy()
        except Exception as e:
            raise ValueError(f"Error loading card image: {str(e)}")

        # Standard ID Card (CR80) is usually roughly 1013x638 px at 300 DPI
        # We use the actual size of the image provided
        card_w, card_h = card.size
        
        # Gap in pixels
        gap = mm_to_px(gap_mm)

        # 4. Calculate Grid
        # Available space accounting for a small margin (e.g., 10mm)
        margin = mm_to_px(10)
        
        usable_w = sheet_w - (2 * margin)
        usable_h = sheet_h - (2 * margin)
        
        # How many columns and rows fit?
        cols = max(1, usable_w // (card_w + gap))
        rows = max(1, usable_h // (card_h + gap))
        
        print(f"Generating {paper_size} sheet...")
        print(f"Layout: {cols} columns x {rows} rows (Total: {cols*rows} cards)")

        # 5. Create the Sheet
        # 'RGB' for color, white background
        sheet = Image.new('RGB', (sheet_w, sheet_h), 'white')
        
        # 6. Paste Cards
        current_y = margin
        for row in range(rows):
            current_x = margin
            for col in range(cols):
                sheet.paste(card, (current_x, current_y))
                current_x += card_w + gap
            current_y += card_h + gap

        # 7. Save or return
        if output_path:
            sheet.save(output_path, quality=95, dpi=(dpi, dpi))
            print(f"Saved: {output_path}")
            return output_path
        else:
            # Return as BytesIO buffer
            buffer = io.BytesIO()
            sheet.save(buffer, format='JPEG', quality=95, dpi=(dpi, dpi))
            buffer.seek(0)
            return buffer
    
    def create_printable_sheets_batch(self, card_images, paper_size="A4", dpi=300, gap_mm=2, output_format='zip'):
        """
        Create printable sheets for multiple ID cards.
        
        :param card_images: List of card image paths or PIL Image objects
        :param paper_size: "A4" or "12x18"
        :param dpi: Print resolution
        :param gap_mm: Gap between cards
        :param output_format: 'zip' or 'list' (returns list of file paths)
        :return: ZIP file buffer or list of file paths
        """
        sheets = []
        
        for idx, card_image in enumerate(card_images):
            sheet_buffer = self.create_printable_sheet(
                card_image, 
                paper_size=paper_size, 
                dpi=dpi, 
                gap_mm=gap_mm
            )
            
            if output_format == 'zip':
                sheets.append((f"sheet_{idx+1}.jpg", sheet_buffer))
            else:
                # Save to temporary file
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                if isinstance(sheet_buffer, io.BytesIO):
                    temp_file.write(sheet_buffer.getvalue())
                else:
                    with open(sheet_buffer, 'rb') as f:
                        temp_file.write(f.read())
                temp_file.close()
                sheets.append(temp_file.name)
        
        if output_format == 'zip':
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, buffer in sheets:
                    if isinstance(buffer, io.BytesIO):
                        zip_file.writestr(filename, buffer.getvalue())
                    else:
                        zip_file.write(buffer, filename)
            zip_buffer.seek(0)
            return zip_buffer
        else:
            return sheets

    def validate_id_card(self, image_path):
        """
        Validate ID card using OCR and image analysis
        Returns validation results
        """
        validation_results = {
            'valid': False,
            'extracted_data': {},
            'issues': []
        }
        
        try:
            # Extract text using OCR
            if EASYOCR_AVAILABLE and self.reader:
                extracted = self.extract_text_from_id(image_path)
                if extracted:
                    validation_results['extracted_data'] = extracted
                    validation_results['valid'] = True
                else:
                    validation_results['issues'].append("Could not extract text from ID")
            else:
                validation_results['issues'].append("OCR not available")
            
            # Check image quality
            img = Image.open(image_path)
            width, height = img.size
            
            if width < 400 or height < 300:
                validation_results['issues'].append("Image resolution too low")
            
            if img.mode != 'RGB':
                validation_results['issues'].append("Image format should be RGB")
            
        except Exception as e:
            validation_results['issues'].append(f"Validation error: {str(e)}")
        
        return validation_results


# Convenience functions for Django integration
def generate_id_card_for_student(student, template=None):
    """Generate ID card for a student"""
    system = AdvancedIDCardSystem(template)
    
    data_dict = {
        'name': student.get_full_name(),
        'id_number': student.admission_number,
        'class': student.current_class.name if student.current_class else '',
        'section': student.section.name if student.section else '',
        'photo': student.photo.path if student.photo else None,
        'qr_data': f"StudentID:{student.admission_number}|Name:{student.get_full_name()}",
    }
    
    return system.generate_card_advanced(data_dict)


def batch_generate_from_students(students, template=None, output_format='zip'):
    """Generate ID cards for multiple students"""
    system = AdvancedIDCardSystem(template)
    
    cards = []
    for student in students:
        try:
            card = generate_id_card_for_student(student, template)
            cards.append(card)
        except Exception as e:
            print(f"Error generating card for {student.admission_number}: {e}")
    
    if output_format == 'zip':
        zip_buffer = io.BytesIO()
        zip_file = zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED)
        
        for student, card in zip(students, cards):
            img_buffer = io.BytesIO()
            card.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            filename = f"id_card_{student.admission_number}.png"
            zip_file.writestr(filename, img_buffer.read())
        
        zip_file.close()
        zip_buffer.seek(0)
        return zip_buffer
    
    return cards

