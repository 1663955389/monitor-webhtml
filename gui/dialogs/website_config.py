"""
Dialog for configuring website monitoring settings
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QCheckBox, QComboBox, QTextEdit,
    QPushButton, QDialogButtonBox, QTabWidget, QWidget,
    QLabel, QMessageBox
)
from PyQt5.QtCore import Qt

from core.monitor import WebsiteConfig, CustomCheck
from utils.helpers import is_url_valid


class WebsiteConfigDialog(QDialog):
    """Dialog for configuring website monitoring"""
    
    def __init__(self, parent=None, website_config=None):
        super().__init__(parent)
        self.website_config = website_config
        self.init_ui()
        
        if website_config:
            self.load_config(website_config)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Website Configuration")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_basic_tab()
        self.create_auth_tab()
        self.create_checks_tab()
        self.create_features_tab()
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def create_basic_tab(self):
        """Create basic configuration tab"""
        basic_widget = QWidget()
        layout = QFormLayout(basic_widget)
        
        # Basic settings
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Unique name for this website")
        layout.addRow("Name:", self.name_edit)
        
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com")
        layout.addRow("URL:", self.url_edit)
        
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.setChecked(True)
        layout.addRow("Enabled:", self.enabled_checkbox)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 86400)  # 10 seconds to 1 day
        self.interval_spin.setValue(300)  # 5 minutes default
        self.interval_spin.setSuffix(" seconds")
        layout.addRow("Check Interval:", self.interval_spin)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)  # 5 seconds to 5 minutes
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        layout.addRow("Timeout:", self.timeout_spin)
        
        # Expected status codes
        self.status_codes_edit = QLineEdit()
        self.status_codes_edit.setText("200")
        self.status_codes_edit.setPlaceholderText("200,301,302")
        layout.addRow("Expected Status Codes:", self.status_codes_edit)
        
        # Content checks
        self.content_checks_edit = QTextEdit()
        self.content_checks_edit.setMaximumHeight(100)
        self.content_checks_edit.setPlaceholderText("Enter text that should be present on the page (one per line)")
        layout.addRow("Content Checks:", self.content_checks_edit)
        
        self.tab_widget.addTab(basic_widget, "Basic")
    
    def create_auth_tab(self):
        """Create authentication configuration tab"""
        auth_widget = QWidget()
        layout = QVBoxLayout(auth_widget)
        
        # Authentication type
        auth_type_layout = QFormLayout()
        self.auth_type_combo = QComboBox()
        self.auth_type_combo.addItems(["None", "HTTP Basic", "Bearer Token", "Form Login"])
        self.auth_type_combo.currentTextChanged.connect(self.on_auth_type_changed)
        auth_type_layout.addRow("Authentication Type:", self.auth_type_combo)
        layout.addLayout(auth_type_layout)
        
        # Authentication details (will be shown/hidden based on type)
        self.auth_details_widget = QWidget()
        self.auth_details_layout = QFormLayout(self.auth_details_widget)
        
        # HTTP Basic / Form fields
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        
        # Bearer token field
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.Password)
        
        # Form login specific fields
        self.login_url_edit = QLineEdit()
        self.username_field_edit = QLineEdit()
        self.username_field_edit.setText("username")
        self.password_field_edit = QLineEdit()
        self.password_field_edit.setText("password")
        
        layout.addWidget(self.auth_details_widget)
        
        # Initially hide auth details
        self.auth_details_widget.hide()
        
        self.tab_widget.addTab(auth_widget, "Authentication")
    
    def create_checks_tab(self):
        """Create custom checks configuration tab"""
        checks_widget = QWidget()
        layout = QVBoxLayout(checks_widget)
        
        layout.addWidget(QLabel("Custom Checks (Advanced):"))
        
        # Custom checks text area (placeholder for advanced functionality)
        self.custom_checks_edit = QTextEdit()
        self.custom_checks_edit.setPlaceholderText(
            "Advanced custom checks configuration will be implemented here.\n"
            "This will allow XPath, CSS selectors, and custom validation rules."
        )
        layout.addWidget(self.custom_checks_edit)
        
        self.tab_widget.addTab(checks_widget, "Custom Checks")
    
    def create_features_tab(self):
        """Create features configuration tab"""
        features_widget = QWidget()
        layout = QVBoxLayout(features_widget)
        
        # Screenshots
        screenshot_group = QGroupBox("Screenshots")
        screenshot_layout = QVBoxLayout(screenshot_group)
        
        self.screenshot_checkbox = QCheckBox("Take screenshots during checks")
        self.screenshot_checkbox.setChecked(True)
        screenshot_layout.addWidget(self.screenshot_checkbox)
        
        layout.addWidget(screenshot_group)
        
        # File downloads
        download_group = QGroupBox("File Downloads")
        download_layout = QVBoxLayout(download_group)
        
        download_layout.addWidget(QLabel("URLs to download (one per line):"))
        self.download_urls_edit = QTextEdit()
        self.download_urls_edit.setMaximumHeight(100)
        download_layout.addWidget(self.download_urls_edit)
        
        layout.addWidget(download_group)
        
        # Custom headers
        headers_group = QGroupBox("Custom Headers")
        headers_layout = QVBoxLayout(headers_group)
        
        headers_layout.addWidget(QLabel("Custom HTTP headers (key:value, one per line):"))
        self.headers_edit = QTextEdit()
        self.headers_edit.setMaximumHeight(100)
        self.headers_edit.setPlaceholderText("User-Agent: Custom Bot 1.0\nX-Custom-Header: value")
        headers_layout.addWidget(self.headers_edit)
        
        layout.addWidget(headers_group)
        
        self.tab_widget.addTab(features_widget, "Features")
    
    def on_auth_type_changed(self, auth_type):
        """Handle authentication type change"""
        # Clear previous fields
        for i in reversed(range(self.auth_details_layout.count())):
            self.auth_details_layout.itemAt(i).widget().hide()
        
        if auth_type == "None":
            self.auth_details_widget.hide()
        else:
            self.auth_details_widget.show()
            
            if auth_type == "HTTP Basic":
                self.auth_details_layout.addRow("Username:", self.username_edit)
                self.auth_details_layout.addRow("Password:", self.password_edit)
                self.username_edit.show()
                self.password_edit.show()
                
            elif auth_type == "Bearer Token":
                self.auth_details_layout.addRow("Token:", self.token_edit)
                self.token_edit.show()
                
            elif auth_type == "Form Login":
                self.auth_details_layout.addRow("Login URL:", self.login_url_edit)
                self.auth_details_layout.addRow("Username:", self.username_edit)
                self.auth_details_layout.addRow("Password:", self.password_edit)
                self.auth_details_layout.addRow("Username Field Name:", self.username_field_edit)
                self.auth_details_layout.addRow("Password Field Name:", self.password_field_edit)
                self.login_url_edit.show()
                self.username_edit.show()
                self.password_edit.show()
                self.username_field_edit.show()
                self.password_field_edit.show()
    
    def load_config(self, config: WebsiteConfig):
        """Load configuration into the dialog"""
        self.name_edit.setText(config.name)
        self.url_edit.setText(config.url)
        self.enabled_checkbox.setChecked(config.enabled)
        self.interval_spin.setValue(config.check_interval)
        self.timeout_spin.setValue(config.timeout)
        
        # Status codes
        status_codes = ",".join(map(str, config.expected_status_codes))
        self.status_codes_edit.setText(status_codes)
        
        # Content checks
        content_checks = "\n".join(config.content_checks)
        self.content_checks_edit.setPlainText(content_checks)
        
        # Authentication
        if config.auth_type:
            auth_type_map = {
                'basic': 'HTTP Basic',
                'bearer': 'Bearer Token',
                'form': 'Form Login'
            }
            auth_type = auth_type_map.get(config.auth_type, 'None')
            self.auth_type_combo.setCurrentText(auth_type)
            
            if config.auth_config:
                self.username_edit.setText(config.auth_config.get('username', ''))
                self.password_edit.setText(config.auth_config.get('password', ''))
                self.token_edit.setText(config.auth_config.get('token', ''))
                self.login_url_edit.setText(config.auth_config.get('login_url', ''))
        
        # Features
        self.screenshot_checkbox.setChecked(config.take_screenshot)
        
        download_urls = "\n".join(config.download_files)
        self.download_urls_edit.setPlainText(download_urls)
        
        # Headers
        headers_text = "\n".join([f"{k}:{v}" for k, v in config.headers.items()])
        self.headers_edit.setPlainText(headers_text)
    
    def get_config(self) -> WebsiteConfig:
        """Get configuration from the dialog"""
        # Validate inputs
        if not self.name_edit.text().strip():
            raise ValueError("Website name is required")
        
        if not self.url_edit.text().strip():
            raise ValueError("URL is required")
        
        if not is_url_valid(self.url_edit.text().strip()):
            raise ValueError("Invalid URL format")
        
        # Parse status codes
        try:
            status_codes = [int(code.strip()) for code in self.status_codes_edit.text().split(',') if code.strip()]
            if not status_codes:
                status_codes = [200]
        except ValueError:
            raise ValueError("Invalid status codes format")
        
        # Parse content checks
        content_checks = [line.strip() for line in self.content_checks_edit.toPlainText().split('\n') if line.strip()]
        
        # Parse authentication
        auth_type = None
        auth_config = None
        
        auth_type_text = self.auth_type_combo.currentText()
        if auth_type_text != "None":
            auth_type_map = {
                'HTTP Basic': 'basic',
                'Bearer Token': 'bearer',
                'Form Login': 'form'
            }
            auth_type = auth_type_map[auth_type_text]
            
            auth_config = {}
            if auth_type == 'basic':
                auth_config = {
                    'username': self.username_edit.text(),
                    'password': self.password_edit.text()
                }
            elif auth_type == 'bearer':
                auth_config = {
                    'token': self.token_edit.text()
                }
            elif auth_type == 'form':
                auth_config = {
                    'login_url': self.login_url_edit.text(),
                    'username': self.username_edit.text(),
                    'password': self.password_edit.text(),
                    'username_field': self.username_field_edit.text(),
                    'password_field': self.password_field_edit.text()
                }
        
        # Parse download URLs
        download_files = [line.strip() for line in self.download_urls_edit.toPlainText().split('\n') if line.strip()]
        
        # Parse headers
        headers = {}
        for line in self.headers_edit.toPlainText().split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
        
        return WebsiteConfig(
            name=self.name_edit.text().strip(),
            url=self.url_edit.text().strip(),
            enabled=self.enabled_checkbox.isChecked(),
            check_interval=self.interval_spin.value(),
            timeout=self.timeout_spin.value(),
            auth_type=auth_type,
            auth_config=auth_config,
            expected_status_codes=status_codes,
            content_checks=content_checks,
            take_screenshot=self.screenshot_checkbox.isChecked(),
            download_files=download_files,
            headers=headers
        )
    
    def accept(self):
        """Handle dialog acceptance with validation"""
        try:
            self.get_config()  # Validate configuration
            super().accept()
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))