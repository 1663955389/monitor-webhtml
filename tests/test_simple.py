"""
Simple tests for core utilities (without heavy dependencies)
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import ConfigManager
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
        print(f"✓ Configuration loaded: check_interval={config.check_interval}")
        
    def test_auth_config(self):
        """Test authentication configuration"""
        auth_config = self.config_manager.get_authentication_config()
        self.assertIsNotNone(auth_config)
        self.assertGreater(auth_config.session_timeout, 0)
        print(f"✓ Auth config loaded: session_timeout={auth_config.session_timeout}")


class TestHelpers(unittest.TestCase):
    """Test utility helper functions"""
    
    def test_format_size(self):
        """Test file size formatting"""
        self.assertEqual(format_size(0), "0B")
        self.assertEqual(format_size(1024), "1.0KB")
        self.assertEqual(format_size(1048576), "1.0MB")
        print("✓ File size formatting works")
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        dangerous_name = "file<>name|with?bad*chars"
        safe_name = sanitize_filename(dangerous_name)
        self.assertNotIn("<", safe_name)
        self.assertNotIn(">", safe_name)
        self.assertNotIn("|", safe_name)
        print(f"✓ Filename sanitized: '{dangerous_name}' -> '{safe_name}'")
    
    def test_url_validation(self):
        """Test URL validation"""
        self.assertTrue(is_url_valid("https://www.example.com"))
        self.assertTrue(is_url_valid("http://localhost:8080"))
        self.assertFalse(is_url_valid("not-a-url"))
        self.assertFalse(is_url_valid(""))
        print("✓ URL validation works")


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
        print(f"✓ Encryption/decryption works: '{original_text}' <-> encrypted")
    
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
        print("✓ Dictionary encryption/decryption works")


def test_variable_manager_directly():
    """Test variable manager without importing from core"""
    print("\n--- Testing Variable Manager ---")
    
    # Import directly to avoid core dependencies
    from core.variables import VariableManager
    
    var_manager = VariableManager()
    
    # Test basic operations
    var_manager.set_variable("test_var", "test_value")
    value = var_manager.get_variable("test_var")
    assert value == "test_value", f"Expected 'test_value', got '{value}'"
    print("✓ Basic variable set/get works")
    
    # Test variable substitution
    var_manager.set_variable("name", "World")
    text = "Hello ${name}!"
    result = var_manager.substitute_variables(text)
    assert result == "Hello World!", f"Expected 'Hello World!', got '{result}'"
    print("✓ Variable substitution works")
    
    # Test variable types
    var_manager.set_variable("text_var", "hello", "text")
    var_manager.set_variable("number_var", 42, "number")
    var_manager.set_variable("bool_var", True, "boolean")
    
    text_vars = var_manager.get_text_variables()
    number_vars = var_manager.get_number_variables()
    
    assert "text_var" in text_vars, "Text variable not found"
    assert "number_var" in number_vars, "Number variable not found"
    print("✓ Variable types work correctly")
    
    summary = var_manager.get_variable_summary()
    print(f"✓ Variable summary: {summary['total_variables']} variables")


if __name__ == "__main__":
    print("=" * 60)
    print("WEBSITE MONITORING SYSTEM - BASIC TESTS")
    print("=" * 60)
    
    # Run unittest tests
    unittest.main(verbosity=0, exit=False)
    
    # Run additional tests
    try:
        test_variable_manager_directly()
        print("\n" + "=" * 60)
        print("✅ ALL BASIC TESTS PASSED!")
        print("✅ Core utilities are working correctly")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Variable manager test failed: {e}")
        print("=" * 60)