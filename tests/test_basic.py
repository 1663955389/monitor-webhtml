"""
Basic tests for the monitoring system
"""

import unittest
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import ConfigManager
from core.variables import VariableManager
from utils.helpers import format_size, sanitize_filename, is_url_valid
from utils.crypto import CryptoManager


class TestConfiguration(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        self.config_manager = ConfigManager()
    
    def test_config_loading(self):
        """Test basic configuration loading"""
        config = self.config_manager.get_monitoring_config()
        self.assertIsNotNone(config)
        self.assertGreater(config.check_interval, 0)
        
    def test_auth_config(self):
        """Test authentication configuration"""
        auth_config = self.config_manager.get_authentication_config()
        self.assertIsNotNone(auth_config)
        self.assertGreater(auth_config.session_timeout, 0)


class TestVariableManager(unittest.TestCase):
    """Test variable management system"""
    
    def setUp(self):
        self.var_manager = VariableManager()
    
    def test_set_get_variable(self):
        """Test setting and getting variables"""
        self.var_manager.set_variable("test_var", "test_value")
        value = self.var_manager.get_variable("test_var")
        self.assertEqual(value, "test_value")
    
    def test_variable_types(self):
        """Test different variable types"""
        self.var_manager.set_variable("text_var", "hello", "text")
        self.var_manager.set_variable("number_var", 42, "number")
        self.var_manager.set_variable("bool_var", True, "boolean")
        
        text_vars = self.var_manager.get_text_variables()
        number_vars = self.var_manager.get_number_variables()
        
        self.assertIn("text_var", text_vars)
        self.assertIn("number_var", number_vars)
    
    def test_variable_substitution(self):
        """Test variable substitution in text"""
        self.var_manager.set_variable("name", "World")
        text = "Hello ${name}!"
        result = self.var_manager.substitute_variables(text)
        self.assertEqual(result, "Hello World!")


class TestHelpers(unittest.TestCase):
    """Test utility helper functions"""
    
    def test_format_size(self):
        """Test file size formatting"""
        self.assertEqual(format_size(0), "0B")
        self.assertEqual(format_size(1024), "1.0KB")
        self.assertEqual(format_size(1048576), "1.0MB")
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        dangerous_name = "file<>name|with?bad*chars"
        safe_name = sanitize_filename(dangerous_name)
        self.assertNotIn("<", safe_name)
        self.assertNotIn(">", safe_name)
        self.assertNotIn("|", safe_name)
    
    def test_url_validation(self):
        """Test URL validation"""
        self.assertTrue(is_url_valid("https://www.example.com"))
        self.assertTrue(is_url_valid("http://localhost:8080"))
        self.assertFalse(is_url_valid("not-a-url"))
        self.assertFalse(is_url_valid(""))


class TestCrypto(unittest.TestCase):
    """Test cryptography utilities"""
    
    def setUp(self):
        self.crypto = CryptoManager("test_password")
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption"""
        original_text = "sensitive_data"
        encrypted = self.crypto.encrypt(original_text)
        decrypted = self.crypto.decrypt(encrypted)
        
        self.assertNotEqual(encrypted, original_text)
        self.assertEqual(decrypted, original_text)
    
    def test_encrypt_dict(self):
        """Test dictionary encryption"""
        original_dict = {
            "username": "user123",
            "password": "secret123",
            "enabled": True
        }
        
        encrypted_dict = self.crypto.encrypt_dict(original_dict)
        decrypted_dict = self.crypto.decrypt_dict(encrypted_dict)
        
        self.assertEqual(decrypted_dict["username"], "user123")
        self.assertEqual(decrypted_dict["password"], "secret123")
        self.assertEqual(decrypted_dict["enabled"], True)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)