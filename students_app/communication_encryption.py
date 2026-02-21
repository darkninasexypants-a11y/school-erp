"""
Encryption utilities for communication system
Uses Fernet symmetric encryption for secure message storage
"""
from django.conf import settings
import base64
import os

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None


def get_encryption_key():
    """
    Get or generate encryption key from settings
    Store in settings.COMMUNICATION_ENCRYPTION_KEY
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise ImportError("cryptography library is not installed. Install with: pip install cryptography")
    
    key = getattr(settings, 'COMMUNICATION_ENCRYPTION_KEY', None)
    
    if not key:
        # Generate a new key if not set
        key = Fernet.generate_key().decode()
        # In production, set this in settings.py
        # COMMUNICATION_ENCRYPTION_KEY = 'your-generated-key-here'
    
    # If key is a string, encode it
    if isinstance(key, str):
        key = key.encode()
    
    return key


def get_cipher():
    """Get Fernet cipher instance"""
    if not CRYPTOGRAPHY_AVAILABLE:
        raise ImportError("cryptography library is not installed. Install with: pip install cryptography")
    key = get_encryption_key()
    return Fernet(key)


def encrypt_text(text):
    """
    Encrypt text data
    Returns encrypted bytes as base64 string
    """
    if not text:
        return text
    
    if not CRYPTOGRAPHY_AVAILABLE:
        # If cryptography is not available, return text as-is (no encryption)
        # This allows the app to run but without encryption
        print("WARNING: cryptography not installed. Data will not be encrypted!")
        return text
    
    try:
        cipher = get_cipher()
        encrypted = cipher.encrypt(text.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        # Log error but don't fail silently
        print(f"Encryption error: {str(e)}")
        raise


def decrypt_text(encrypted_text):
    """
    Decrypt text data
    Accepts base64 encoded encrypted string
    Returns decrypted plain text
    """
    if not encrypted_text:
        return encrypted_text
    
    if not CRYPTOGRAPHY_AVAILABLE:
        # If cryptography is not available, return text as-is
        return encrypted_text
    
    try:
        cipher = get_cipher()
        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_text.encode('utf-8'))
        decrypted = cipher.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')
    except Exception as e:
        # Log error but don't fail silently
        print(f"Decryption error: {str(e)}")
        raise


def encrypt_file(file_path):
    """
    Encrypt file content
    Returns encrypted bytes
    """
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        cipher = get_cipher()
        encrypted = cipher.encrypt(file_data)
        return encrypted
    except Exception as e:
        print(f"File encryption error: {str(e)}")
        raise


def decrypt_file(encrypted_data, output_path):
    """
    Decrypt file content and save to output path
    """
    try:
        cipher = get_cipher()
        decrypted = cipher.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted)
        
        return output_path
    except Exception as e:
        print(f"File decryption error: {str(e)}")
        raise


def is_encrypted(text):
    """
    Check if text appears to be encrypted (base64 format)
    """
    if not text:
        return False
    
    try:
        # Try to decode as base64
        base64.b64decode(text.encode('utf-8'))
        # If successful, likely encrypted
        return len(text) > 50  # Encrypted text is usually longer
    except:
        return False

