"""
Messaging Utilities for WhatsApp and SMS
Supports Twilio API for SMS and WhatsApp
"""
from django.conf import settings
from django.core.mail import send_mail
import requests
import json


def send_sms_via_twilio(phone_number, message):
    """
    Send SMS using Twilio API
    Requires: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER in settings
    """
    try:
        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
        
        if not all([account_sid, auth_token, from_number]):
            return {'success': False, 'error': 'Twilio credentials not configured'}
        
        # Clean phone number (remove + if present, add country code if needed)
        phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone  # Add India country code
        
        url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
        data = {
            'From': from_number,
            'To': f'+{phone}',
            'Body': message
        }
        
        response = requests.post(url, data=data, auth=(account_sid, auth_token))
        
        if response.status_code == 201:
            return {'success': True, 'message_id': response.json().get('sid')}
        else:
            return {'success': False, 'error': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_whatsapp_via_twilio(phone_number, message):
    """
    Send WhatsApp message using Twilio API
    Requires: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER in settings
    """
    try:
        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        from_whatsapp = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')  # Twilio sandbox
        
        if not all([account_sid, auth_token]):
            return {'success': False, 'error': 'Twilio credentials not configured'}
        
        # Clean phone number
        phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        
        url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
        data = {
            'From': from_whatsapp,
            'To': f'whatsapp:+{phone}',
            'Body': message
        }
        
        response = requests.post(url, data=data, auth=(account_sid, auth_token))
        
        if response.status_code == 201:
            return {'success': True, 'message_id': response.json().get('sid')}
        else:
            return {'success': False, 'error': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_sms_via_api(phone_number, message, api_url=None, api_key=None):
    """
    Generic SMS API sender (for other providers like MSG91, TextLocal, etc.)
    """
    try:
        # Example for MSG91 API
        if api_url and api_key:
            data = {
                'sender': 'SCHOOL',
                'route': '4',
                'country': '91',
                'sms': [{
                    'message': message,
                    'to': [phone_number]
                }]
            }
            headers = {
                'authkey': api_key,
                'Content-Type': 'application/json'
            }
            response = requests.post(api_url, json=data, headers=headers)
            if response.status_code == 200:
                return {'success': True, 'response': response.json()}
            return {'success': False, 'error': response.text}
        return {'success': False, 'error': 'API credentials not provided'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_email_notification(email, subject, message, html_message=None):
    """
    Send email notification
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@schoolerp.com'),
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_fee_notification(student, notification_type='pending', send_via='email', custom_message=None):
    """
    Send fee notification via selected method (email/SMS/WhatsApp)
    send_via can be: 'email', 'sms', 'whatsapp', 'both' (sms+whatsapp), 'all' (email+sms+whatsapp)
    """
    # Get parent contact info - check multiple possible field names
    parent_phone = (
        getattr(student, 'parent_phone', None) or 
        getattr(student, 'father_phone', None) or 
        getattr(student, 'phone', None)
    )
    parent_email = (
        getattr(student, 'parent_email', None) or 
        getattr(student, 'email', None)
    )
    
    # Prepare message based on notification type
    class_name = student.get_class_section() if hasattr(student, 'get_class_section') else (student.current_class.name if student.current_class else 'N/A')
    roll_no = getattr(student, 'roll_number', '') or ''
    
    if notification_type == 'pending':
        subject = f"Fee Payment Reminder - {student.get_full_name()}"
        message = f"Dear Parent,\n\nThis is a reminder for pending fee payment for {student.get_full_name()}"
        if roll_no:
            message += f" (Roll No: {roll_no})"
        if class_name and class_name != 'N/A':
            message += f" (Class: {class_name})"
        message += ".\n\nPlease pay the fee at your earliest convenience.\n\nThank you,\nSchool Administration"
    elif notification_type == 'overdue':
        subject = f"Overdue Fee Alert - {student.get_full_name()}"
        message = f"Dear Parent,\n\nThis is an urgent reminder that the fee payment for {student.get_full_name()} is overdue. Please clear the dues immediately."
        if roll_no:
            message += f"\nRoll No: {roll_no}"
        if class_name and class_name != 'N/A':
            message += f"\nClass: {class_name}"
        message += "\n\nThank you,\nSchool Administration"
    elif notification_type == 'receipt':
        subject = f"Fee Payment Receipt - {student.get_full_name()}"
        message = f"Dear Parent,\n\nFee payment received for {student.get_full_name()}.\n\nThank you for your payment.\n\nSchool Administration"
    else:
        subject = f"Fee Reminder - {student.get_full_name()}"
        message = custom_message or f"Dear Parent,\n\nThis is a reminder regarding fee payment for {student.get_full_name()}.\n\nThank you,\nSchool Administration"
    
    results = {'email': None, 'sms': None, 'whatsapp': None}
    
    # Send via selected method
    if send_via in ['email', 'all']:
        if parent_email:
            results['email'] = send_email_notification(parent_email, subject, message)
        else:
            results['email'] = {'success': False, 'error': 'No email address found'}
    
    if send_via in ['sms', 'both', 'all']:
        if parent_phone:
            results['sms'] = send_sms_via_twilio(parent_phone, message)
        else:
            results['sms'] = {'success': False, 'error': 'No phone number found'}
    
    if send_via in ['whatsapp', 'both', 'all']:
        if parent_phone:
            results['whatsapp'] = send_whatsapp_via_twilio(parent_phone, message)
        else:
            results['whatsapp'] = {'success': False, 'error': 'No phone number found'}
    
    return results

