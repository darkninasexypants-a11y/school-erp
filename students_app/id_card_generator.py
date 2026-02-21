from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from datetime import date, timedelta
import os


# Standard ID card size (CR80 standard at 150 DPI)
CARD_WIDTH  = 638   # px  ≈ 85.6 mm × 150 DPI
CARD_HEIGHT = 1009  # px  ≈ 54 mm × 150 DPI  (portrait)


def _load_font(size):
    """Load a font, falling back gracefully."""
    font_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/verdana.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_text_centered(draw, text, y, card_w, font, fill='black'):
    """Draw text horizontally centered."""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
    except AttributeError:
        text_w, _ = draw.textsize(text, font=font)
    x = (card_w - text_w) // 2
    draw.text((x, y), text, fill=fill, font=font)


class IDCardGenerator:
    """Generate properly-sized ID cards for students."""

    def __init__(self, student, template):
        self.student  = student
        self.template = template

    # ------------------------------------------------------------------
    def generate_card(self):
        """Return (PIL.Image, qr_data_str)."""

        # ── 1. Load / create background ──────────────────────────────
        if self.template.template_image:
            try:
                bg = Image.open(self.template.template_image.path).convert('RGBA')
                # Always resize to our standard size
                bg = bg.resize((CARD_WIDTH, CARD_HEIGHT), Image.LANCZOS)
            except Exception as e:
                print(f"Warning: could not open template image ({e}), using solid background")
                bg = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), (0, 100, 0, 255))
        else:
            bg = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), (0, 100, 0, 255))

        card = bg.convert('RGB')
        draw = ImageDraw.Draw(card)

        # ── 2. Fonts ─────────────────────────────────────────────────
        font_name   = _load_font(28)
        font_bold   = _load_font(22)
        font_normal = _load_font(18)
        font_small  = _load_font(15)

        # ── 3. Student photo ─────────────────────────────────────────
        photo_w, photo_h = 160, 190
        photo_x = (CARD_WIDTH - photo_w) // 2
        photo_y = 120

        if self.student.photo:
            try:
                photo = Image.open(self.student.photo.path).convert('RGB')
                photo = photo.resize((photo_w, photo_h), Image.LANCZOS)
                # White border
                border = Image.new('RGB', (photo_w + 6, photo_h + 6), 'white')
                border.paste(photo, (3, 3))
                card.paste(border, (photo_x - 3, photo_y - 3))
            except Exception as e:
                print(f"Warning: could not paste photo ({e})")
                draw.rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h],
                                outline='white', width=2)
                _draw_text_centered(draw, "No Photo", photo_y + photo_h // 2, CARD_WIDTH, font_small, 'white')
        else:
            draw.rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h],
                            outline='white', width=2)
            _draw_text_centered(draw, "No Photo", photo_y + photo_h // 2, CARD_WIDTH, font_small, 'white')

        # ── 4. Student details ────────────────────────────────────────
        text_start_y = photo_y + photo_h + 25
        line_gap     = 34

        # Name
        name = self.student.get_full_name().upper()
        _draw_text_centered(draw, name, text_start_y, CARD_WIDTH, font_name, 'white')

        # Divider line
        y_line = text_start_y + 38
        draw.line([(40, y_line), (CARD_WIDTH - 40, y_line)], fill='white', width=1)

        y = y_line + 15

        def row(label, value, y_pos):
            draw.text((50, y_pos), f"{label}:", fill='#ccffcc', font=font_bold)
            draw.text((220, y_pos), str(value), fill='white', font=font_normal)

        # Admission No
        row("Adm. No", self.student.admission_number, y)
        y += line_gap

        # Class & Section
        class_name = self.student.current_class.name if self.student.current_class else "N/A"
        section    = self.student.section.name if self.student.section else ""
        row("Class", f"{class_name} {section}".strip(), y)
        y += line_gap

        # Father name
        if self.student.father_name:
            row("Father", self.student.father_name, y)
            y += line_gap

        # Contact
        phone = self.student.father_phone or getattr(self.student, 'phone', '') or ''
        if phone:
            row("Contact", phone, y)
            y += line_gap

        # DOB
        if self.student.date_of_birth:
            row("DOB", self.student.date_of_birth.strftime('%d-%m-%Y'), y)
            y += line_gap

        # Blood Group
        if self.student.blood_group:
            row("Blood Grp", self.student.blood_group, y)
            y += line_gap

        # ── 5. QR Code ───────────────────────────────────────────────
        qr_data = (
            f"Name:{self.student.get_full_name()}|"
            f"Adm:{self.student.admission_number}|"
            f"Class:{class_name} {section}|"
            f"Contact:{phone}"
        )
        try:
            qr = qrcode.QRCode(version=2, box_size=4, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color='black', back_color='white').convert('RGB')
            qr_size = 120
            qr_img  = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
            qr_x    = CARD_WIDTH - qr_size - 30
            qr_y    = CARD_HEIGHT - qr_size - 30
            # White bg for QR
            qr_bg = Image.new('RGB', (qr_size + 8, qr_size + 8), 'white')
            qr_bg.paste(qr_img, (4, 4))
            card.paste(qr_bg, (qr_x - 4, qr_y - 4))
        except Exception as e:
            print(f"Warning: QR generation failed ({e})")
            qr_data = ""

        # ── 6. Bottom bar ─────────────────────────────────────────────
        bar_h = 40
        bar_y = CARD_HEIGHT - bar_h
        draw.rectangle([(0, bar_y), (CARD_WIDTH, CARD_HEIGHT)], fill=(0, 80, 0))
        school_name = ""
        try:
            if self.student.school:
                school_name = self.student.school.name
        except Exception:
            pass
        if school_name:
            _draw_text_centered(draw, school_name.upper(), bar_y + 10, CARD_WIDTH, font_small, 'white')

        return card, qr_data

    # ------------------------------------------------------------------
    def save_card(self):
        """Generate, save to DB and return StudentIDCard instance."""
        from .models import StudentIDCard

        card_image, qr_data = self.generate_card()

        buffer = BytesIO()
        card_image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        card_number = f"CARD-{self.student.admission_number}-{date.today().year}"
        valid_until = date.today() + timedelta(days=365)

        # Update existing card OR create new one
        try:
            id_card = StudentIDCard.objects.get(card_number=card_number)
            id_card.template    = self.template
            id_card.valid_until = valid_until
            id_card.qr_code_data = qr_data
            id_card.status      = 'active'
            id_card.save()
        except StudentIDCard.DoesNotExist:
            id_card = StudentIDCard.objects.create(
                student      = self.student,
                card_number  = card_number,
                template     = self.template,
                valid_until  = valid_until,
                qr_code_data = qr_data,
                status       = 'active',
            )

        filename = f"id_card_{self.student.admission_number}.png"
        id_card.generated_image.save(filename, ContentFile(buffer.getvalue()), save=True)
        return id_card


# ── Bulk helper ──────────────────────────────────────────────────────────
def generate_bulk_id_cards(students, template):
    generated_cards = []
    errors = []
    for student in students:
        try:
            card = IDCardGenerator(student, template).save_card()
            generated_cards.append(card)
        except Exception as e:
            errors.append(f"{student.get_full_name()}: {str(e)}")
    return generated_cards, errors
