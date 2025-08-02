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
        self.setWindowTitle("网站配置")
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
        self.name_edit.setPlaceholderText("此网站的唯一名称")
        layout.addRow("名称:", self.name_edit)
        
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com")
        layout.addRow("网址:", self.url_edit)
        
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.setChecked(True)
        layout.addRow("启用:", self.enabled_checkbox)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 86400)  # 10 seconds to 1 day
        self.interval_spin.setValue(300)  # 5 minutes default
        self.interval_spin.setSuffix(" 秒")
        layout.addRow("检查间隔:", self.interval_spin)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)  # 5 seconds to 5 minutes
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" 秒")
        layout.addRow("超时时间:", self.timeout_spin)
        
        # Expected status codes
        self.status_codes_edit = QLineEdit()
        self.status_codes_edit.setText("200")
        self.status_codes_edit.setPlaceholderText("200,301,302")
        layout.addRow("预期状态码:", self.status_codes_edit)
        
        # Content checks
        self.content_checks_edit = QTextEdit()
        self.content_checks_edit.setMaximumHeight(100)
        self.content_checks_edit.setPlaceholderText("输入页面上应该存在的文本（每行一个）")
        layout.addRow("内容检查:", self.content_checks_edit)
        
        self.tab_widget.addTab(basic_widget, "基本")
    
    def create_auth_tab(self):
        """Create authentication configuration tab"""
        auth_widget = QWidget()
        layout = QVBoxLayout(auth_widget)
        
        # Authentication type
        auth_type_layout = QFormLayout()
        self.auth_type_combo = QComboBox()
        self.auth_type_combo.addItems(["无", "HTTP 基本认证", "Bearer 令牌", "表单登录"])
        self.auth_type_combo.currentTextChanged.connect(self.on_auth_type_changed)
        auth_type_layout.addRow("身份验证类型:", self.auth_type_combo)
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
        
        self.tab_widget.addTab(auth_widget, "身份验证")
    
    def create_checks_tab(self):
        """Create custom checks configuration tab"""
        checks_widget = QWidget()
        layout = QVBoxLayout(checks_widget)
        
        layout.addWidget(QLabel("自定义检查（高级）:"))
        
        # Custom checks text area (placeholder for advanced functionality)
        self.custom_checks_edit = QTextEdit()
        self.custom_checks_edit.setPlaceholderText(
            "高级自定义检查配置将在此处实现。\n"
            "这将允许 XPath、CSS 选择器和自定义验证规则。"
        )
        layout.addWidget(self.custom_checks_edit)
        
        self.tab_widget.addTab(checks_widget, "自定义检查")
    
    def create_features_tab(self):
        """Create features configuration tab"""
        features_widget = QWidget()
        layout = QVBoxLayout(features_widget)
        
        # Screenshots
        screenshot_group = QGroupBox("截图")
        screenshot_layout = QVBoxLayout(screenshot_group)
        
        self.screenshot_checkbox = QCheckBox("检查时截取屏幕快照")
        self.screenshot_checkbox.setChecked(True)
        screenshot_layout.addWidget(self.screenshot_checkbox)
        
        layout.addWidget(screenshot_group)
        
        # File downloads
        download_group = QGroupBox("文件下载")
        download_layout = QVBoxLayout(download_group)
        
        download_layout.addWidget(QLabel("要下载的网址（每行一个）:"))
        self.download_urls_edit = QTextEdit()
        self.download_urls_edit.setMaximumHeight(100)
        download_layout.addWidget(self.download_urls_edit)
        
        layout.addWidget(download_group)
        
        # Custom headers
        headers_group = QGroupBox("自定义请求头")
        headers_layout = QVBoxLayout(headers_group)
        
        headers_layout.addWidget(QLabel("自定义 HTTP 请求头（键:值，每行一个）:"))
        self.headers_edit = QTextEdit()
        self.headers_edit.setMaximumHeight(100)
        self.headers_edit.setPlaceholderText("User-Agent: Custom Bot 1.0\nX-Custom-Header: value")
        headers_layout.addWidget(self.headers_edit)
        
        layout.addWidget(headers_group)
        
        self.tab_widget.addTab(features_widget, "功能")
    
    def on_auth_type_changed(self, auth_type):
        """Handle authentication type change"""
        # Clear previous fields
        for i in reversed(range(self.auth_details_layout.count())):
            self.auth_details_layout.itemAt(i).widget().hide()
        
        if auth_type == "无":
            self.auth_details_widget.hide()
        else:
            self.auth_details_widget.show()
            
            if auth_type == "HTTP 基本认证":
                self.auth_details_layout.addRow("用户名:", self.username_edit)
                self.auth_details_layout.addRow("密码:", self.password_edit)
                self.username_edit.show()
                self.password_edit.show()
                
            elif auth_type == "Bearer 令牌":
                self.auth_details_layout.addRow("令牌:", self.token_edit)
                self.token_edit.show()
                
            elif auth_type == "表单登录":
                self.auth_details_layout.addRow("登录网址:", self.login_url_edit)
                self.auth_details_layout.addRow("用户名:", self.username_edit)
                self.auth_details_layout.addRow("密码:", self.password_edit)
                self.auth_details_layout.addRow("用户名字段名:", self.username_field_edit)
                self.auth_details_layout.addRow("密码字段名:", self.password_field_edit)
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
                'basic': 'HTTP 基本认证',
                'bearer': 'Bearer 令牌',
                'form': '表单登录'
            }
            auth_type = auth_type_map.get(config.auth_type, '无')
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
            raise ValueError("网站名称是必需的")
        
        if not self.url_edit.text().strip():
            raise ValueError("网址是必需的")
        
        if not is_url_valid(self.url_edit.text().strip()):
            raise ValueError("无效的网址格式")
        
        # Parse status codes
        try:
            status_codes = [int(code.strip()) for code in self.status_codes_edit.text().split(',') if code.strip()]
            if not status_codes:
                status_codes = [200]
        except ValueError:
            raise ValueError("状态码格式无效")
        
        # Parse content checks
        content_checks = [line.strip() for line in self.content_checks_edit.toPlainText().split('\n') if line.strip()]
        
        # Parse authentication
        auth_type = None
        auth_config = None
        
        auth_type_text = self.auth_type_combo.currentText()
        if auth_type_text != "无":
            auth_type_map = {
                'HTTP 基本认证': 'basic',
                'Bearer 令牌': 'bearer',
                '表单登录': 'form'
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
            QMessageBox.warning(self, "验证错误", str(e))