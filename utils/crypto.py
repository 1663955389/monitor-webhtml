"""
Cryptography utilities for secure storage of credentials
"""

import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Union


class CryptoManager:
    """Manager for encryption and decryption of sensitive data"""
    
    def __init__(self, password: str = "default_password"):
        self.password = password.encode()
        self._key = self._derive_key()
        self._fernet = Fernet(self._key)
    
    def _derive_key(self) -> bytes:
        """Derive encryption key from password"""
        salt = b'salt_'  # In production, use a random salt and store it
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        return key
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data and return base64 encoded string"""
        try:
            if isinstance(data, str):
                data = data.encode()
            encrypted = self._fernet.encrypt(data)
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logging.error(f"Encryption error: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded encrypted data"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logging.error(f"Decryption error: {e}")
            raise
    
    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt all string values in a dictionary"""
        encrypted_dict = {}
        for key, value in data.items():
            if isinstance(value, str) and value:
                encrypted_dict[key] = self.encrypt(value)
            else:
                encrypted_dict[key] = value
        return encrypted_dict
    
    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """Decrypt all encrypted string values in a dictionary"""
        decrypted_dict = {}
        for key, value in encrypted_data.items():
            if isinstance(value, str) and value:
                try:
                    decrypted_dict[key] = self.decrypt(value)
                except:
                    # If decryption fails, assume it's not encrypted
                    decrypted_dict[key] = value
            else:
                decrypted_dict[key] = value
        return decrypted_dict