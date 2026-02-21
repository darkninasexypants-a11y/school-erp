from django import template
from students_app.system_config import SystemConfiguration

register = template.Library()


@register.filter
def feature_enabled(value, school=None):
    """
    Checks if a given feature is enabled in SystemConfiguration.
    Usage: {% if 'crm_enabled'|feature_enabled %}
    Or with school context: {% if 'library_management'|feature_enabled:request.user.school_profile.school %}
    """
    school_obj = None
    if school:
        # Allow passing SchoolFeatureConfiguration or SchoolUser instances
        school_obj = getattr(school, 'school', school)
        school_obj = getattr(school_obj, 'school', school_obj)  # Support nested school_profile
    return SystemConfiguration.is_feature_enabled(value, school=school_obj)

