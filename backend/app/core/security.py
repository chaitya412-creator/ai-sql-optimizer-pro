"""
Security and Encryption Utilities
"""
from cryptography.fernet import Fernet
import base64
import hashlib
from app.config import settings


class SecurityManager:
    """Manages encryption and decryption of sensitive data"""
    
    def __init__(self):
        # Generate a key from the encryption key in settings
        key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(key))
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string"""
        if not plaintext:
            return ""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext string"""
        if not ciphertext:
            return ""
        return self.cipher.decrypt(ciphertext.encode()).decode()


# Global security manager instance
security_manager = SecurityManager()
