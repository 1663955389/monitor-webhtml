"""
Dialog for configuring notification settings
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QCheckBox, QComboBox, QTextEdit,
    QPushButton, QDialogButtonBox, QTabWidget, QWidget,
    QLabel, QMessageBox
)
from PyQt5.QtCore import Qt

from config.settings import config_manager


class NotificationConfigDialog(QDialog):
    """Dialog for configuring notification settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_current_config()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Notification Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_email_tab()
        self.create_webhook_tab()
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        buttons.accepted.connect(self.save_config)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def create_email_tab(self):
        """Create email notification configuration tab"""
        email_widget = QWidget()
        layout = QVBoxLayout(email_widget)
        
        # Email enabled
        self.email_enabled_checkbox = QCheckBox("Enable email notifications")
        layout.addWidget(self.email_enabled_checkbox)
        
        # Email settings group
        email_group = QGroupBox("SMTP Settings")
        email_layout = QFormLayout(email_group)
        
        self.smtp_server_edit = QLineEdit()
        self.smtp_server_edit.setPlaceholderText("smtp.gmail.com")
        email_layout.addRow("SMTP Server:", self.smtp_server_edit)
        
        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.smtp_port_spin.setValue(587)
        email_layout.addRow("SMTP Port:", self.smtp_port_spin)
        
        self.use_tls_checkbox = QCheckBox("Use TLS")
        self.use_tls_checkbox.setChecked(True)
        email_layout.addRow("Security:", self.use_tls_checkbox)
        
        self.sender_email_edit = QLineEdit()
        self.sender_email_edit.setPlaceholderText("your-email@gmail.com")
        email_layout.addRow("Sender Email:", self.sender_email_edit)
        
        self.sender_password_edit = QLineEdit()
        self.sender_password_edit.setEchoMode(QLineEdit.Password)
        self.sender_password_edit.setPlaceholderText("App password or email password")
        email_layout.addRow("Password:", self.sender_password_edit)
        
        layout.addWidget(email_group)
        
        # Recipients group
        recipients_group = QGroupBox("Recipients")
        recipients_layout = QVBoxLayout(recipients_group)
        
        recipients_layout.addWidget(QLabel("Email addresses (one per line):"))
        self.recipients_edit = QTextEdit()
        self.recipients_edit.setMaximumHeight(100)
        self.recipients_edit.setPlaceholderText("admin@example.com\nteam@example.com")
        recipients_layout.addWidget(self.recipients_edit)
        
        layout.addWidget(recipients_group)
        
        # Test button
        test_email_btn = QPushButton("Test Email Configuration")
        test_email_btn.clicked.connect(self.test_email)
        layout.addWidget(test_email_btn)
        
        self.tab_widget.addTab(email_widget, "Email")
    
    def create_webhook_tab(self):
        """Create webhook notification configuration tab"""
        webhook_widget = QWidget()
        layout = QVBoxLayout(webhook_widget)
        
        # Webhook enabled
        self.webhook_enabled_checkbox = QCheckBox("Enable webhook notifications")
        layout.addWidget(self.webhook_enabled_checkbox)
        
        # Webhook settings group
        webhook_group = QGroupBox("Webhook Settings")
        webhook_layout = QFormLayout(webhook_group)
        
        self.webhook_url_edit = QLineEdit()
        self.webhook_url_edit.setPlaceholderText("https://your-webhook-endpoint.com/notifications")
        webhook_layout.addRow("Webhook URL:", self.webhook_url_edit)
        
        self.webhook_timeout_spin = QSpinBox()
        self.webhook_timeout_spin.setRange(1, 300)
        self.webhook_timeout_spin.setValue(10)
        self.webhook_timeout_spin.setSuffix(" seconds")
        webhook_layout.addRow("Timeout:", self.webhook_timeout_spin)
        
        layout.addWidget(webhook_group)
        
        # Custom headers group
        headers_group = QGroupBox("Custom Headers")
        headers_layout = QVBoxLayout(headers_group)
        
        headers_layout.addWidget(QLabel("Custom headers (key:value, one per line):"))
        self.webhook_headers_edit = QTextEdit()
        self.webhook_headers_edit.setMaximumHeight(100)
        self.webhook_headers_edit.setPlaceholderText("Authorization: Bearer your-token\nContent-Type: application/json")
        headers_layout.addWidget(self.webhook_headers_edit)
        
        layout.addWidget(headers_group)
        
        # Notification conditions group
        conditions_group = QGroupBox("Notification Conditions")
        conditions_layout = QVBoxLayout(conditions_group)
        
        self.notify_on_failure_checkbox = QCheckBox("Notify on monitoring failures")
        self.notify_on_failure_checkbox.setChecked(True)
        conditions_layout.addWidget(self.notify_on_failure_checkbox)
        
        self.notify_on_success_checkbox = QCheckBox("Notify on monitoring success")
        conditions_layout.addWidget(self.notify_on_success_checkbox)
        
        self.notify_on_recovery_checkbox = QCheckBox("Notify on service recovery")
        self.notify_on_recovery_checkbox.setChecked(True)
        conditions_layout.addWidget(self.notify_on_recovery_checkbox)
        
        layout.addWidget(conditions_group)
        
        # Test button
        test_webhook_btn = QPushButton("Test Webhook Configuration")
        test_webhook_btn.clicked.connect(self.test_webhook)
        layout.addWidget(test_webhook_btn)
        
        self.tab_widget.addTab(webhook_widget, "Webhook")
    
    def load_current_config(self):
        """Load current configuration into the dialog"""
        notifications_config = config_manager.get_notifications_config()
        
        # Email configuration
        email_config = notifications_config.email
        self.email_enabled_checkbox.setChecked(email_config.enabled)
        self.smtp_server_edit.setText(email_config.smtp_server)
        self.smtp_port_spin.setValue(email_config.smtp_port)
        self.use_tls_checkbox.setChecked(email_config.use_tls)
        self.sender_email_edit.setText(email_config.sender_email)
        self.sender_password_edit.setText(email_config.sender_password)
        
        # Webhook configuration
        webhook_config = notifications_config.webhook
        self.webhook_enabled_checkbox.setChecked(webhook_config.enabled)
        self.webhook_url_edit.setText(webhook_config.url)
        self.webhook_timeout_spin.setValue(webhook_config.timeout)
    
    def save_config(self):
        """Save the configuration"""
        try:
            # Prepare email configuration
            email_config = {
                'enabled': self.email_enabled_checkbox.isChecked(),
                'smtp_server': self.smtp_server_edit.text(),
                'smtp_port': self.smtp_port_spin.value(),
                'use_tls': self.use_tls_checkbox.isChecked(),
                'sender_email': self.sender_email_edit.text(),
                'sender_password': self.sender_password_edit.text()
            }
            
            # Prepare webhook configuration
            webhook_config = {
                'enabled': self.webhook_enabled_checkbox.isChecked(),
                'url': self.webhook_url_edit.text(),
                'timeout': self.webhook_timeout_spin.value()
            }
            
            # Update configuration
            notifications_config = {
                'email': email_config,
                'webhook': webhook_config
            }
            
            config_manager.update_config('notifications', notifications_config)
            
            QMessageBox.information(self, "Success", "Notification settings saved successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
    
    def test_email(self):
        """Test email configuration"""
        # Placeholder for email testing
        QMessageBox.information(
            self,
            "Test Email",
            "Email test functionality will be implemented here.\n"
            "This will send a test email using the configured settings."
        )
    
    def test_webhook(self):
        """Test webhook configuration"""
        # Placeholder for webhook testing
        QMessageBox.information(
            self,
            "Test Webhook",
            "Webhook test functionality will be implemented here.\n"
            "This will send a test notification to the configured webhook URL."
        )