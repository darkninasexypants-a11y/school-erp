"""
System Configuration Model - Feature Flags
Stored separately to avoid model file conflicts
"""
from __future__ import annotations

from typing import Optional

from django.db import models

from .feature_registry import FEATURE_MAP, FeatureDefinition, iter_all_features


class SystemConfiguration(models.Model):
    """System-wide configuration and feature flags."""

    # Legacy Feature Flags (kept for backwards compatibility)
    crm_enabled = models.BooleanField(default=True, help_text="Enable CRM Module")
    erp_enabled = models.BooleanField(default=True, help_text="Enable ERP Module")
    id_card_generator = models.BooleanField(default=True, help_text="Enable ID Card Generator")
    fee_payment_online = models.BooleanField(default=True, help_text="Enable Online Fee Payment")
    attendance_tracking = models.BooleanField(default=True, help_text="Enable Attendance Tracking")
    marks_entry = models.BooleanField(default=True, help_text="Enable Marks Entry")
    library_management = models.BooleanField(default=True, help_text="Enable Library Management")
    transport_management = models.BooleanField(default=False, help_text="Enable Transport Management")
    hostel_management = models.BooleanField(default=False, help_text="Enable Hostel Management")
    canteen_management = models.BooleanField(default=False, help_text="Enable Canteen Management")

    # Flexible storage for additional feature flags
    feature_settings = models.JSONField(default=dict, blank=True)
    
    # Additional settings
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configuration"
        db_table = 'students_app_systemconfiguration'
    
    def __str__(self) -> str:
        return "System Configuration"
    
    # ------------------------------------------------------------------ #
    # Persistence helpers
    # ------------------------------------------------------------------ #
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SystemConfiguration.objects.exists():
            existing = SystemConfiguration.objects.first()
            for field in self._meta.fields:
                if field.name not in ['id', 'created_at', 'updated_at']:
                    setattr(existing, field.name, getattr(self, field.name))
            existing._ensure_feature_defaults()
            existing.save()
            return

        # Normalise JSON store
        if self.feature_settings is None:
            self.feature_settings = {}
        self._ensure_feature_defaults()

        super().save(*args, **kwargs)
    
    def _ensure_feature_defaults(self):
        """
        Populate missing keys in feature_settings with registry defaults so that
        configuration pages always display deterministic initial values.
        """
        feature_settings = self.feature_settings or {}
        updated = False
        for definition in iter_all_features():
            # Legacy fields persist on model fields and do not need JSON copy
            if definition.legacy_field:
                continue
            if definition.key not in feature_settings:
                feature_settings[definition.key] = definition.default
                updated = True
        if updated:
            self.feature_settings = feature_settings

    # ------------------------------------------------------------------ #
    # Feature state helpers
    # ------------------------------------------------------------------ #
    def set_feature_state(self, key: str, value: bool, definition: Optional[FeatureDefinition] = None):
        """
        Update feature state for a given key. Legacy fields are kept in sync when
        their definition declares a matching legacy_field.
        """
        definition = definition or FEATURE_MAP.get(key)
        if definition and definition.legacy_field:
            setattr(self, definition.legacy_field, bool(value))
        else:
            feature_settings = self.feature_settings or {}
            feature_settings[key] = bool(value)
            self.feature_settings = feature_settings

    def get_feature_state(self, key: str, definition: Optional[FeatureDefinition] = None) -> bool:
        """
        Resolve the effective feature state for the configuration instance.
        Order of precedence:
            1. Legacy model field (for backwards compatibility)
            2. JSON feature_settings store
            3. Registry default
            4. Fallback to model attribute with same name
        """
        definition = definition or FEATURE_MAP.get(key)

        if definition and definition.legacy_field and hasattr(self, definition.legacy_field):
            legacy_value = getattr(self, definition.legacy_field)
            if legacy_value is not None:
                return bool(legacy_value)

        settings = self.feature_settings or {}
        if key in settings:
            return bool(settings[key])

        if definition:
            return bool(definition.default)

        # Fallback: attempt to read attribute directly if it exists
        if hasattr(self, key):
            return bool(getattr(self, key))

        return True

    # ------------------------------------------------------------------ #
    # Class helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def get_config(cls) -> "SystemConfiguration":
        """Get system configuration, creating default if not present."""
        config, _created = cls.objects.get_or_create(pk=1)
        config._ensure_feature_defaults()
        return config
    
    @classmethod
    def is_feature_enabled(cls, feature_name: str, school=None) -> bool:
        """Check if a feature is enabled (globally or for a specific school)."""
        definition = FEATURE_MAP.get(feature_name)

        try:
            if school:
                try:
                    school_config = SchoolFeatureConfiguration.objects.get(school=school)
                    override = school_config.get_feature_state(feature_name, definition)
                    if override is not None:
                        return override
                except SchoolFeatureConfiguration.DoesNotExist:
                    pass
            
            config = cls.get_config()
            return config.get_feature_state(feature_name, definition)
        except Exception as exc:  # pragma: no cover - fallback guard
            print(f"Error checking feature {feature_name}: {exc}")
            return True  # Default to enabled if error

class SchoolFeatureConfiguration(models.Model):
    """Per-school feature configuration - overrides global settings."""

    school = models.OneToOneField('School', on_delete=models.CASCADE, related_name='feature_config')
    
    # Legacy Feature Flags (None = use global, True/False = override)
    crm_enabled = models.BooleanField(null=True, blank=True, help_text="None = use global, True/False = override")
    erp_enabled = models.BooleanField(null=True, blank=True)
    id_card_generator = models.BooleanField(null=True, blank=True)
    fee_payment_online = models.BooleanField(null=True, blank=True)
    attendance_tracking = models.BooleanField(null=True, blank=True)
    marks_entry = models.BooleanField(null=True, blank=True)
    library_management = models.BooleanField(null=True, blank=True)
    transport_management = models.BooleanField(null=True, blank=True)
    hostel_management = models.BooleanField(null=True, blank=True)
    canteen_management = models.BooleanField(null=True, blank=True)

    # Flexible overrides for extended feature set
    feature_overrides = models.JSONField(default=dict, blank=True, help_text="Override flags for extended feature set")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "School Feature Configuration"
        verbose_name_plural = "School Feature Configurations"
        db_table = 'students_app_schoolfeatureconfiguration'
    
    def __str__(self):
        return f"Features for {self.school.name}"
    
    def get_feature_state(self, key: str, definition: Optional[FeatureDefinition] = None) -> Optional[bool]:
        """
        Return the school-specific override for a feature.
        Returns:
            True / False -> explicit override
            None         -> inherit system default
        """
        definition = definition or FEATURE_MAP.get(key)

        if definition and definition.legacy_field and hasattr(self, definition.legacy_field):
            legacy_value = getattr(self, definition.legacy_field)
            if legacy_value is not None:
                return bool(legacy_value)

        overrides = self.feature_overrides or {}
        if key in overrides:
            return bool(overrides[key])

        return None

    def set_feature_state(self, key: str, value: Optional[bool], definition: Optional[FeatureDefinition] = None):
        """Persist tri-state override (None=inherit, True/False=explicit override)."""
        definition = definition or FEATURE_MAP.get(key)

        if definition and definition.legacy_field and hasattr(self, definition.legacy_field):
            setattr(self, definition.legacy_field, value)
        else:
            overrides = self.feature_overrides or {}
            if value is None:
                overrides.pop(key, None)
            else:
                overrides[key] = bool(value)
            self.feature_overrides = overrides

    @classmethod
    def get_or_create_for_school(cls, school):
        """Get or create configuration for a school."""
        config, _created = cls.objects.get_or_create(school=school)
        if config.feature_overrides is None:
            config.feature_overrides = {}
        return config


class SecuritySettings(models.Model):
    """System-wide security settings"""
    # Two-Factor Authentication
    require_2fa = models.BooleanField(default=False, help_text="Require 2FA for all admin users")
    
    # Password Settings
    password_min_length = models.IntegerField(default=8, help_text="Minimum password length")
    password_complexity = models.BooleanField(default=True, help_text="Require uppercase, lowercase, numbers, and symbols")
    
    # Session Settings
    session_timeout = models.IntegerField(default=30, help_text="Session timeout in minutes")
    
    # IP Whitelist
    ip_whitelist_enabled = models.BooleanField(default=False, help_text="Restrict access to specific IP addresses")
    
    # Audit Logging
    audit_logging = models.BooleanField(default=True, help_text="Log all user actions and system changes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Security Settings"
        verbose_name_plural = "Security Settings"
        db_table = 'students_app_securitysettings'
    
    def __str__(self):
        return "Security Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SecuritySettings.objects.exists():
            # Update existing instance instead of creating new one
            existing = SecuritySettings.objects.first()
            for field in self._meta.fields:
                if field.name not in ['id', 'created_at', 'updated_at']:
                    setattr(existing, field.name, getattr(self, field.name))
            existing.save()
            return
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get security settings, create default if doesn't exist"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

