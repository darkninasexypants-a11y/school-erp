"""
Enhanced ID Card Models inspired by AlphaCard ID Software
Features:
- Multiple layouts per template
- Conditional layers
- Encoding support (barcodes, magnetic stripe, smart cards)
- Security features (password protection, user permissions)
- Rich text editing with database field integration
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


class EnhancedIDCardTemplate(models.Model):
    """
    Enhanced ID Card Template with AlphaCard-inspired features
    Supports multiple layouts, conditional layers, and advanced encoding
    """
    ENCODING_TYPE_CHOICES = [
        ('none', 'No Encoding'),
        ('barcode_1d', '1D Barcode (Code128, Code39, EAN)'),
        ('barcode_2d', '2D Barcode (QR Code, Data Matrix)'),
        ('magnetic_stripe', 'Magnetic Stripe (LoCo/HiCo)'),
        ('smart_card', 'Smart Card (MIFARE, HID Proximity)'),
        ('rfid', 'RFID'),
    ]
    
    SECURITY_LEVEL_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('high', 'High Security'),
        ('enterprise', 'Enterprise'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, help_text="Template name")
    description = models.TextField(blank=True, help_text="Template description")
    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True, blank=True, related_name='enhanced_id_templates')
    
    # Card Dimensions
    card_width = models.IntegerField(default=338, help_text="Width in pixels (standard: 338px = 85.6mm)")
    card_height = models.IntegerField(default=528, help_text="Height in pixels (standard: 528px = 133.4mm)")
    orientation = models.CharField(max_length=10, choices=[
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
    ], default='portrait')
    
    # Background
    background_image = models.ImageField(upload_to='id_card_templates/', blank=True, null=True, 
                                        help_text="Background image for the card")
    background_color = models.CharField(max_length=7, default='#FFFFFF', help_text="Hex color code")
    
    # Multiple Layouts Support (AlphaCard feature)
    layouts = models.JSONField(default=list, help_text="Multiple layout configurations")
    default_layout = models.CharField(max_length=50, default='default', 
                                     help_text="Default layout name")
    
    # Conditional Layers (AlphaCard feature)
    conditional_layers = models.JSONField(default=list, 
                                         help_text="Layers that show/hide based on database conditions")
    
    # Encoding Settings (AlphaCard feature)
    encoding_type = models.CharField(max_length=20, choices=ENCODING_TYPE_CHOICES, default='barcode_2d')
    barcode_type = models.CharField(max_length=50, default='QRCode', 
                                    help_text="Barcode type: QRCode, Code128, Code39, EAN13, etc.")
    magnetic_stripe_type = models.CharField(max_length=10, blank=True, 
                                           choices=[('loco', 'LoCo'), ('hico', 'HiCo')],
                                           help_text="Magnetic stripe encoding type")
    encoding_data_field = models.CharField(max_length=100, default='admission_number',
                                         help_text="Database field to use for encoding")
    
    # Security Features (AlphaCard feature)
    security_level = models.CharField(max_length=20, choices=SECURITY_LEVEL_CHOICES, default='standard')
    password_protected = models.BooleanField(default=False, help_text="Require password to edit template")
    template_password = models.CharField(max_length=255, blank=True, help_text="Template password (hashed)")
    digital_key = models.CharField(max_length=255, blank=True, 
                                  help_text="Digital key for template authentication")
    watermark_enabled = models.BooleanField(default=False, help_text="Add watermark to cards")
    watermark_text = models.CharField(max_length=100, blank=True, help_text="Watermark text")
    
    # User Permissions (AlphaCard feature)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_id_templates')
    allowed_users = models.ManyToManyField(User, blank=True, related_name='allowed_id_templates',
                                          help_text="Users who can use this template")
    allowed_groups = models.JSONField(default=list, help_text="User groups that can use this template")
    
    # Rich Text Editing Support (AlphaCard feature)
    supports_rich_text = models.BooleanField(default=True, 
                                            help_text="Enable rich text editing with database fields")
    database_fields = models.JSONField(default=list, 
                                      help_text="Available database fields for rich text editing")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default template for school")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1, help_text="Template version number")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Enhanced ID Card Template"
        verbose_name_plural = "Enhanced ID Card Templates"
    
    def __str__(self):
        return f"{self.name} ({self.get_encoding_type_display()})"
    
    def get_layout(self, layout_name=None):
        """Get layout configuration by name"""
        if not layout_name:
            layout_name = self.default_layout
        
        for layout in self.layouts:
            if layout.get('name') == layout_name:
                return layout
        return self.layouts[0] if self.layouts else None
    
    def add_layout(self, layout_name, layout_config):
        """Add a new layout to the template"""
        layouts = self.layouts or []
        layouts.append({
            'name': layout_name,
            'config': layout_config,
            'created_at': timezone.now().isoformat()
        })
        self.layouts = layouts
        self.save()
    
    def get_conditional_elements(self, cardholder_data):
        """Get elements to show based on conditional layers and cardholder data"""
        visible_elements = []
        for layer in self.conditional_layers:
            condition = layer.get('condition', {})
            field = condition.get('field')
            operator = condition.get('operator', 'equals')
            value = condition.get('value')
            
            # Evaluate condition
            cardholder_value = cardholder_data.get(field)
            show = False
            
            if operator == 'equals':
                show = str(cardholder_value) == str(value)
            elif operator == 'not_equals':
                show = str(cardholder_value) != str(value)
            elif operator == 'contains':
                show = str(value) in str(cardholder_value)
            elif operator == 'greater_than':
                show = float(cardholder_value) > float(value)
            elif operator == 'less_than':
                show = float(cardholder_value) < float(value)
            
            if show:
                visible_elements.extend(layer.get('elements', []))
        
        return visible_elements


class IDCardElement(models.Model):
    """
    Individual elements that can be placed on ID cards
    Supports text, images, barcodes, signatures, fingerprints
    """
    ELEMENT_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('photo', 'Photo'),
        ('barcode', 'Barcode'),
        ('qr_code', 'QR Code'),
        ('signature', 'Signature'),
        ('fingerprint', 'Fingerprint'),
        ('shape', 'Shape (Rectangle, Circle)'),
        ('logo', 'Logo'),
    ]
    
    template = models.ForeignKey(EnhancedIDCardTemplate, on_delete=models.CASCADE, related_name='elements')
    element_type = models.CharField(max_length=20, choices=ELEMENT_TYPE_CHOICES)
    name = models.CharField(max_length=100, help_text="Element name for reference")
    
    # Position and Size
    x = models.IntegerField(default=0, help_text="X position in pixels")
    y = models.IntegerField(default=0, help_text="Y position in pixels")
    width = models.IntegerField(default=100, help_text="Width in pixels")
    height = models.IntegerField(default=50, help_text="Height in pixels")
    
    # Text Properties (for text elements)
    text_content = models.TextField(blank=True, help_text="Text content or database field reference")
    font_family = models.CharField(max_length=50, default='Arial')
    font_size = models.IntegerField(default=12)
    font_weight = models.CharField(max_length=20, default='normal', choices=[
        ('normal', 'Normal'),
        ('bold', 'Bold'),
        ('italic', 'Italic'),
    ])
    text_color = models.CharField(max_length=7, default='#000000')
    text_align = models.CharField(max_length=10, default='left', choices=[
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
    ])
    
    # Rich Text with Database Fields (AlphaCard feature)
    uses_database_field = models.BooleanField(default=False, 
                                             help_text="Use database field for content")
    database_field = models.CharField(max_length=100, blank=True, 
                                     help_text="Database field name (e.g., student.name, student.admission_number)")
    format_string = models.CharField(max_length=200, blank=True, 
                                   help_text="Format string with {field} placeholders")
    
    # Image Properties
    image_source = models.CharField(max_length=20, default='upload', choices=[
        ('upload', 'Uploaded Image'),
        ('database', 'From Database'),
        ('logo', 'School Logo'),
    ])
    image_file = models.ImageField(upload_to='id_card_elements/', blank=True, null=True)
    
    # Barcode/QR Code Properties
    barcode_data_field = models.CharField(max_length=100, default='admission_number',
                                         help_text="Field to encode in barcode")
    barcode_format = models.CharField(max_length=50, default='QRCode',
                                    help_text="Barcode format: QRCode, Code128, Code39, etc.")
    
    # Encoding Properties (for magnetic stripe, smart cards)
    encoding_data = models.TextField(blank=True, help_text="Data to encode")
    encoding_format = models.CharField(max_length=50, blank=True, 
                                      help_text="Encoding format specification")
    
    # Conditional Display (AlphaCard feature)
    is_conditional = models.BooleanField(default=False, help_text="Show/hide based on condition")
    condition_field = models.CharField(max_length=100, blank=True, help_text="Field to check")
    condition_operator = models.CharField(max_length=20, default='equals', choices=[
        ('equals', 'Equals'),
        ('not_equals', 'Not Equals'),
        ('contains', 'Contains'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
    ])
    condition_value = models.CharField(max_length=200, blank=True, help_text="Value to compare")
    
    # Layer Properties
    layer_order = models.IntegerField(default=0, help_text="Z-order for layering")
    opacity = models.DecimalField(max_digits=3, decimal_places=2, default=1.0,
                                 validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['layer_order', 'id']
        verbose_name = "ID Card Element"
        verbose_name_plural = "ID Card Elements"
    
    def __str__(self):
        return f"{self.template.name} - {self.name} ({self.get_element_type_display()})"
    
    def should_display(self, cardholder_data):
        """Check if element should be displayed based on conditions"""
        if not self.is_conditional:
            return True
        
        field_value = cardholder_data.get(self.condition_field, '')
        condition_value = self.condition_value
        
        if self.condition_operator == 'equals':
            return str(field_value) == str(condition_value)
        elif self.condition_operator == 'not_equals':
            return str(field_value) != str(condition_value)
        elif self.condition_operator == 'contains':
            return str(condition_value) in str(field_value)
        elif self.condition_operator == 'greater_than':
            try:
                return float(field_value) > float(condition_value)
            except:
                return False
        elif self.condition_operator == 'less_than':
            try:
                return float(field_value) < float(condition_value)
            except:
                return False
        
        return True


class IDCardEncoding(models.Model):
    """
    Track encoding data for ID cards (barcodes, magnetic stripes, smart cards)
    """
    ENCODING_TYPE_CHOICES = [
        ('barcode_1d', '1D Barcode'),
        ('barcode_2d', '2D Barcode (QR Code)'),
        ('magnetic_stripe', 'Magnetic Stripe'),
        ('smart_card', 'Smart Card'),
        ('rfid', 'RFID'),
    ]
    
    card = models.ForeignKey('StudentIDCard', on_delete=models.CASCADE, related_name='encodings')
    encoding_type = models.CharField(max_length=20, choices=ENCODING_TYPE_CHOICES)
    encoded_data = models.TextField(help_text="Encoded data")
    format_type = models.CharField(max_length=50, help_text="Format: QRCode, Code128, LoCo, HiCo, etc.")
    
    # Track encoding status
    is_encoded = models.BooleanField(default=False)
    encoded_at = models.DateTimeField(null=True, blank=True)
    encoded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, help_text="Additional encoding metadata")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "ID Card Encoding"
        verbose_name_plural = "ID Card Encodings"
    
    def __str__(self):
        return f"{self.card.student.get_full_name()} - {self.get_encoding_type_display()}"


class IDCardTemplateVersion(models.Model):
    """
    Version control for ID card templates (AlphaCard feature)
    """
    template = models.ForeignKey(EnhancedIDCardTemplate, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    layout_data = models.JSONField(help_text="Snapshot of layout at this version")
    changes_description = models.TextField(blank=True, help_text="What changed in this version")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ['template', 'version_number']
    
    def __str__(self):
        return f"{self.template.name} v{self.version_number}"












