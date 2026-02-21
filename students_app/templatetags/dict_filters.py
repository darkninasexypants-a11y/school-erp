from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def get_dict_value(dictionary, key):
    """Get nested dictionary value by key (for accessing dict['key'])"""
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

