from cryptography.fernet import Fernet
from django.conf import settings
import base64
import os

# Ensure we have a key for encryption.
# In a real app, this should be in environment variables.
ENCRYPTION_KEY = os.getenv('TELEGRAM_TOKEN_ENCRYPTION_KEY')

def get_cipher():
    if not ENCRYPTION_KEY:
        # Fallback to a key derived from SECRET_KEY if not provided
        # This is better than nothing but ideally use a separate key.
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b'0'))
        return Fernet(key)
    return Fernet(ENCRYPTION_KEY.encode())

def encrypt_token(token: str) -> str:
    if not token:
        return ""
    cipher = get_cipher()
    return cipher.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        return ""
    cipher = get_cipher()
    try:
        return cipher.decrypt(encrypted_token.encode()).decode()
    except Exception:
        # If decryption fails (e.g. key changed), return empty or log error
        return ""
