"""
Patrol task configuration dialog (巡检任务配置对话框)
"""

import logging
import re
from datetime import datetime, time
from typing import Dict, List, Optional, Any

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QTabWidget, QWidget, QLabel, QLineEdit, QTextEdit, QComboBox,
    QSpinBox, QTimeEdit, QCheckBox, QListWidget, QListWidgetItem,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QDialogButtonBox, QMessageBox, QFrame, QScrollArea,
    QSizePolicy, QFileDialog
)
from PyQt5.QtCore import Qt, QTime, pyqtSignal
from PyQt5.QtGui import QFont, QPalette

from core.patrol import PatrolTask, PatrolCheck, PatrolFrequency, PatrolType


class PatrolCheckWidget(QWidget):
    """Widget for configuring individual patrol checks"""
    
    check_changed = pyqtSignal()
    
    def __init__(self, check: Optional[PatrolCheck] = None, parent=None):
        super().__init__(parent)
        self.check = check or PatrolCheck(name="", type=PatrolType.CONTENT_CHECK, target="")
        self.setup_ui()
        self.load_check_data()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        
        # Check basic info
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("检查项名称")
        self.name_edit.textChanged.connect(self.check_changed.emit)
        basic_layout.addRow("名称*:", self.name_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "内容检查", "视觉检查", "下载检查", "表单检查", "API检查"
        ])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        basic_layout.addRow("检查类型:", self.type_combo)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("检查项描述（可选）")
        self.description_edit.textChanged.connect(self.check_changed.emit)
        basic_layout.addRow("描述:", self.description_edit)
        
        self.enabled_check = QCheckBox("启用此检查项")
        self.enabled_check.setChecked(True)
        self.enabled_check.toggled.connect(self.check_changed.emit)
        basic_layout.addRow("", self.enabled_check)
        
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("留空则对所有网站执行，否则仅对指定URL执行")
        self.url_edit.textChanged.connect(self.check_changed.emit)
        basic_layout.addRow("关联URL:", self.url_edit)
        
        layout.addWidget(basic_group)
        
        # Check configuration
        config_group = QGroupBox("检查配置")
        config_layout = QFormLayout(config_group)
        
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("CSS选择器、XPath、URL或文本内容")
        self.target_edit.textChanged.connect(self.check_changed.emit)
        self.target_label = QLabel("目标*:")
        config_layout.addRow(self.target_label, self.target_edit)
        
        self.expected_edit = QLineEdit()
        self.expected_edit.setPlaceholderText("期望值（可选）")
        self.expected_edit.textChanged.connect(self.check_changed.emit)
        self.expected_label = QLabel("期望值:")
        config_layout.addRow(self.expected_label, self.expected_edit)
        
        self.tolerance_edit = QLineEdit()
        self.tolerance_edit.setPlaceholderText("容错范围（可选）")
        self.tolerance_edit.textChanged.connect(self.check_changed.emit)
        self.tolerance_label = QLabel("容错范围:")
        config_layout.addRow(self.tolerance_label, self.tolerance_edit)
        
        layout.addWidget(config_group)
        
        # Variables info group
        variables_group = QGroupBox("生成的变量")
        variables_layout = QVBoxLayout(variables_group)
        
        self.variables_info_label = QLabel()
        self.variables_info_label.setWordWrap(True)
        self.variables_info_label.setStyleSheet("background-color: #f0f0f0; padding: 8px; border: 1px solid #ccc;")
        self.variables_info_label.setFont(QFont("Consolas", 9))
        variables_layout.addWidget(self.variables_info_label)
        
        layout.addWidget(variables_group)
        
        # Update variables info when check changes
        self.check_changed.connect(self.update_variables_info)
        
        # Update UI based on type
        self.on_type_changed()
    
    def on_type_changed(self):
        """Update UI based on selected check type"""
        check_type = self.type_combo.currentText()
        
        if check_type == "内容检查":
            self.target_label.setText("CSS选择器/XPath*:")
            self.target_edit.setPlaceholderText("CSS选择器或XPath路径")
            self.expected_label.setText("期望值:")
            self.expected_edit.setPlaceholderText("可选：期望的文本内容，用于验证提取的值")
            self.tolerance_label.setText("匹配模式:")
            self.tolerance_edit.setPlaceholderText("exact|contains|regex （默认：contains）")
            
        elif check_type == "API检查":
            self.target_label.setText("API端点*:")
            self.target_edit.setPlaceholderText("API URL或JSON字段路径")
            self.expected_label.setText("期望状态码:")
            self.expected_edit.setPlaceholderText("200")
            self.tolerance_label.setText("超时时间:")
            self.tolerance_edit.setPlaceholderText("30")
            
        elif check_type == "下载检查":
            self.target_label.setText("下载URL*:")
            self.target_edit.setPlaceholderText("要下载的文件URL")
            self.expected_label.setText("文件大小范围:")
            self.expected_edit.setPlaceholderText("最小-最大 字节数（可选）")
            self.tolerance_label.setText("文件类型:")
            self.tolerance_edit.setPlaceholderText("pdf|doc|xlsx|zip（可选）")
            
        elif check_type == "视觉检查":
            self.target_label.setText("截图类型*:")
            self.target_edit.setPlaceholderText("full（全页）|viewport（视口）|CSS选择器（特定元素）")
            self.expected_label.setText("相似度阈值:")
            self.expected_edit.setPlaceholderText("0.95（未来功能）")
            self.tolerance_label.setText("对比区域:")
            self.tolerance_edit.setPlaceholderText("对比功能待实现")
            
        elif check_type == "表单检查":
            self.target_label.setText("表单选择器*:")
            self.target_edit.setPlaceholderText("表单的CSS选择器")
            self.expected_label.setText("测试数据:")
            self.expected_edit.setPlaceholderText("JSON格式的表单数据")
            self.tolerance_label.setText("成功条件:")
            self.tolerance_edit.setPlaceholderText("成功提交的判断条件")
        
        self.check_changed.emit()
    
    def update_variables_info(self):
        """Update the variables information display"""
        check_name = self.name_edit.text().strip()
        check_type = self.type_combo.currentText()
        url = self.url_edit.text().strip()
        
        if not check_name:
            self.variables_info_label.setText("请先输入检查项名称以查看将生成的变量")
            return
        
        # Generate variable names based on check configuration
        variables = []
        safe_check_name = check_name.replace(' ', '_').replace('-', '_')
        
        if check_type == "内容检查":
            variables.append(f"${{extracted_{safe_check_name}_任务名}} - 提取的文本内容")
            variables.append(f"${{status_{safe_check_name}_任务名}} - 检查状态 (成功/失败)")
            if self.expected_edit.text().strip():
                variables.append(f"${{validation_{safe_check_name}_任务名}} - 验证结果 (通过/失败)")
        elif check_type == "API检查":
            variables.append(f"${{api_status_{safe_check_name}_任务名}} - API状态码")
            variables.append(f"${{api_response_{safe_check_name}_任务名}} - API响应内容")
        elif check_type == "下载检查":
            variables.append(f"${{download_path_{safe_check_name}_任务名}} - 下载文件路径")
            variables.append(f"${{download_size_{safe_check_name}_任务名}} - 文件大小")
            variables.append(f"${{download_name_{safe_check_name}_任务名}} - 文件名")
        elif check_type == "视觉检查":
            variables.append(f"${{visual_{safe_check_name}_任务名}} - 截图路径")
            variables.append(f"${{status_{safe_check_name}_任务名}} - 截图状态 (成功/失败)")
        elif check_type == "表单检查":
            variables.append(f"${{form_result_{safe_check_name}_任务名}} - 表单提交结果")
            variables.append(f"${{status_{safe_check_name}_任务名}} - 检查状态 (成功/失败)")
        
        # Add common variables for all checks
        variables.append(f"${{timestamp_{safe_check_name}_任务名}} - 检查执行时间")
        
        # Add URL-specific variables if URL is specified
        if url:
            safe_url = url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_').replace('.', '_')
            variables.append(f"${{screenshot_{safe_url}_任务名}} - 页面截图路径")
            variables.append(f"${{response_time_{safe_url}_任务名}} - 页面响应时间")
        
        variables_text = "\n".join(variables)
        if url:
            variables_text = f"此检查项将为URL '{url}' 生成以下变量:\n\n{variables_text}"
        else:
            variables_text = f"此检查项将为所有任务URL生成以下变量:\n\n{variables_text}"
        
        self.variables_info_label.setText(variables_text)
    
    def load_check_data(self):
        """Load check data into UI"""
        if not self.check:
            return
        
        self.name_edit.setText(self.check.name)
        self.description_edit.setText(self.check.description)
        self.target_edit.setText(self.check.target)
        self.expected_edit.setText(self.check.expected_value or "")
        self.tolerance_edit.setText(self.check.tolerance or "")
        self.enabled_check.setChecked(self.check.enabled)
        self.url_edit.setText(self.check.associated_url or "")
        
        # Set type combo
        type_map = {
            PatrolType.CONTENT_CHECK: "内容检查",
            PatrolType.API_CHECK: "API检查",
            PatrolType.DOWNLOAD_CHECK: "下载检查",
            PatrolType.VISUAL_CHECK: "视觉检查",
            PatrolType.FORM_CHECK: "表单检查"
        }
        type_text = type_map.get(self.check.type, "内容检查")
        index = self.type_combo.findText(type_text)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        
        # Update variables info after loading data
        self.update_variables_info()
    
    def get_check(self) -> PatrolCheck:
        """Get patrol check from UI"""
        type_map = {
            "内容检查": PatrolType.CONTENT_CHECK,
            "API检查": PatrolType.API_CHECK,
            "下载检查": PatrolType.DOWNLOAD_CHECK,
            "视觉检查": PatrolType.VISUAL_CHECK,
            "表单检查": PatrolType.FORM_CHECK
        }
        
        return PatrolCheck(
            name=self.name_edit.text().strip(),
            type=type_map[self.type_combo.currentText()],
            target=self.target_edit.text().strip(),
            expected_value=self.expected_edit.text().strip() or None,
            tolerance=self.tolerance_edit.text().strip() or None,
            description=self.description_edit.text().strip(),
            enabled=self.enabled_check.isChecked(),
            associated_url=self.url_edit.text().strip() or None
        )
    
    def is_valid(self) -> bool:
        """Check if the configuration is valid"""
        return bool(self.name_edit.text().strip() and self.target_edit.text().strip())


class PatrolTaskConfigDialog(QDialog):
    """Dialog for configuring patrol tasks"""
    
    def __init__(self, task: Optional[PatrolTask] = None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.task = task
        self.check_widgets: List[PatrolCheckWidget] = []
        
        self.setWindowTitle("巡检任务配置" if not task else f"编辑巡检任务: {task.name}")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        
        if task:
            self.load_task_data()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Basic configuration tab
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "基本设置")
        
        # Websites tab
        websites_tab = self.create_websites_tab()
        tab_widget.addTab(websites_tab, "巡检网站")
        
        # Checks tab
        checks_tab = self.create_checks_tab()
        tab_widget.addTab(checks_tab, "检查项目")
        
        # Authentication tab
        auth_tab = self.create_auth_tab()
        tab_widget.addTab(auth_tab, "认证设置")
        
        # Schedule tab
        schedule_tab = self.create_schedule_tab()
        tab_widget.addTab(schedule_tab, "调度设置")
        
        # Reports tab
        reports_tab = self.create_reports_tab()
        tab_widget.addTab(reports_tab, "报告设置")
        
        # Notifications tab
        notifications_tab = self.create_notifications_tab()
        tab_widget.addTab(notifications_tab, "通知设置")
        
        layout.addWidget(tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_basic_tab(self) -> QWidget:
        """Create basic configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Task info group
        info_group = QGroupBox("任务信息")
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("巡检任务名称")
        info_layout.addRow("任务名称*:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("任务描述和目的")
        self.description_edit.setMaximumHeight(100)
        info_layout.addRow("任务描述:", self.description_edit)
        
        self.enabled_check = QCheckBox("启用此巡检任务")
        self.enabled_check.setChecked(True)
        info_layout.addRow("", self.enabled_check)
        
        layout.addWidget(info_group)
        
        # Execution settings group
        exec_group = QGroupBox("执行设置")
        exec_layout = QFormLayout(exec_group)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" 秒")
        exec_layout.addRow("超时时间:", self.timeout_spin)
        
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setValue(2)
        exec_layout.addRow("重试次数:", self.retry_spin)
        
        layout.addWidget(exec_group)
        
        layout.addStretch()
        return tab
    
    def create_websites_tab(self) -> QWidget:
        """Create websites configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        info_label = QLabel("配置需要巡检的网站列表。每行一个URL。")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Websites list
        self.websites_text = QTextEdit()
        self.websites_text.setPlaceholderText(
            "请输入要巡检的网站URL，每行一个：\n"
            "https://example.com\n"
            "https://api.example.com/status\n"
            "https://admin.example.com/dashboard"
        )
        layout.addWidget(self.websites_text)
        
        # Quick add section
        quick_group = QGroupBox("快速添加")
        quick_layout = QHBoxLayout(quick_group)
        
        self.quick_url_edit = QLineEdit()
        self.quick_url_edit.setPlaceholderText("输入URL")
        quick_layout.addWidget(self.quick_url_edit)
        
        add_button = QPushButton("添加")
        add_button.clicked.connect(self.add_quick_url)
        quick_layout.addWidget(add_button)
        
        layout.addWidget(quick_group)
        
        return tab
    
    def create_checks_tab(self) -> QWidget:
        """Create checks configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        info_label = QLabel("配置巡检时要执行的具体检查项目。")
        layout.addWidget(info_label)
        
        # Checks list controls
        controls_layout = QHBoxLayout()
        
        add_check_button = QPushButton("添加检查项")
        add_check_button.clicked.connect(self.add_check_widget)
        controls_layout.addWidget(add_check_button)
        
        controls_layout.addStretch()
        
        clear_checks_button = QPushButton("清空所有")
        clear_checks_button.clicked.connect(self.clear_checks)
        controls_layout.addWidget(clear_checks_button)
        
        layout.addLayout(controls_layout)
        
        # Checks scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.checks_widget = QWidget()
        self.checks_layout = QVBoxLayout(self.checks_widget)
        scroll_area.setWidget(self.checks_widget)
        
        layout.addWidget(scroll_area)
        
        # Don't add a default check - let users add their own
        
        return tab
    
    def create_auth_tab(self) -> QWidget:
        """Create authentication configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Authentication group
        auth_group = QGroupBox("登录认证设置")
        auth_layout = QFormLayout(auth_group)
        
        # Auth type
        self.auth_type_combo = QComboBox()
        self.auth_type_combo.addItems(["无需认证", "表单登录", "HTTP基础认证", "Bearer令牌"])
        self.auth_type_combo.currentTextChanged.connect(self.on_auth_type_changed)
        auth_layout.addRow("认证类型:", self.auth_type_combo)
        
        # Login URL for form auth
        self.login_url_edit = QLineEdit()
        self.login_url_edit.setPlaceholderText("登录页面URL")
        self.login_url_edit.setEnabled(False)
        auth_layout.addRow("登录URL:", self.login_url_edit)
        
        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("用户名")
        self.username_edit.setEnabled(False)
        auth_layout.addRow("用户名:", self.username_edit)
        
        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("密码")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setEnabled(False)
        auth_layout.addRow("密码:", self.password_edit)
        
        # Token for bearer auth
        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText("访问令牌")
        self.token_edit.setEnabled(False)
        auth_layout.addRow("令牌:", self.token_edit)
        
        # Form field names for form auth
        form_fields_group = QGroupBox("表单字段设置")
        form_fields_layout = QFormLayout(form_fields_group)
        
        self.username_field_edit = QLineEdit()
        self.username_field_edit.setPlaceholderText("用户名字段名 (默认: username)")
        self.username_field_edit.setEnabled(False)
        form_fields_layout.addRow("用户名字段:", self.username_field_edit)
        
        self.password_field_edit = QLineEdit()
        self.password_field_edit.setPlaceholderText("密码字段名 (默认: password)")
        self.password_field_edit.setEnabled(False)
        form_fields_layout.addRow("密码字段:", self.password_field_edit)
        
        self.additional_fields_edit = QTextEdit()
        self.additional_fields_edit.setPlaceholderText("附加字段 (JSON格式)\n例如: {\"csrf_token\": \"value\"}")
        self.additional_fields_edit.setMaximumHeight(80)
        self.additional_fields_edit.setEnabled(False)
        form_fields_layout.addRow("附加字段:", self.additional_fields_edit)
        
        layout.addWidget(auth_group)
        layout.addWidget(form_fields_group)
        layout.addStretch()
        
        return tab
    
    def on_auth_type_changed(self):
        """Handle authentication type change"""
        auth_type = self.auth_type_combo.currentText()
        
        # Enable/disable fields based on auth type
        is_none = auth_type == "无需认证"
        is_form = auth_type == "表单登录"
        is_basic = auth_type == "HTTP基础认证"
        is_bearer = auth_type == "Bearer令牌"
        
        # Basic fields
        self.username_edit.setEnabled(is_form or is_basic)
        self.password_edit.setEnabled(is_form or is_basic)
        self.token_edit.setEnabled(is_bearer)
        
        # Form-specific fields
        self.login_url_edit.setEnabled(is_form)
        self.username_field_edit.setEnabled(is_form)
        self.password_field_edit.setEnabled(is_form)
        self.additional_fields_edit.setEnabled(is_form)
    
    def create_schedule_tab(self) -> QWidget:
        """Create schedule configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Frequency group
        freq_group = QGroupBox("巡检频率")
        freq_layout = QFormLayout(freq_group)
        
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["每日", "每日多次", "每周", "每月", "自定义"])
        self.frequency_combo.currentTextChanged.connect(self.on_frequency_changed)
        freq_layout.addRow("频率:", self.frequency_combo)
        
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setTime(QTime(9, 0))
        self.start_time_edit.setDisplayFormat("HH:mm")
        freq_layout.addRow("开始时间:", self.start_time_edit)
        
        # Multiple daily times
        self.multiple_times_edit = QLineEdit()
        self.multiple_times_edit.setPlaceholderText("多个时间用逗号分隔，如: 09:00,14:00,18:00")
        self.multiple_times_edit.setEnabled(False)
        freq_layout.addRow("每日多次时间:", self.multiple_times_edit)
        
        self.custom_schedule_edit = QLineEdit()
        self.custom_schedule_edit.setPlaceholderText("Cron表达式，如: 0 9 * * 1 (每周一9点)")
        self.custom_schedule_edit.setEnabled(False)
        freq_layout.addRow("自定义调度:", self.custom_schedule_edit)
        
        layout.addWidget(freq_group)
        
        # Schedule info
        info_group = QGroupBox("调度说明")
        info_layout = QVBoxLayout(info_group)
        
        self.schedule_info_label = QLabel()
        self.schedule_info_label.setWordWrap(True)
        self.update_schedule_info()
        info_layout.addWidget(self.schedule_info_label)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        return tab
    
    def create_reports_tab(self) -> QWidget:
        """Create reports configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Report settings group
        report_group = QGroupBox("报告设置")
        report_layout = QFormLayout(report_group)
        
        self.generate_report_check = QCheckBox("巡检完成后自动生成报告")
        self.generate_report_check.setChecked(True)
        self.generate_report_check.toggled.connect(self.on_report_settings_changed)
        self.generate_report_check.setToolTip("勾选后，每次巡检任务执行完成时会自动生成Word格式的巡检报告")
        report_layout.addRow("", self.generate_report_check)
        
        self.report_format_combo = QComboBox()
        self.report_format_combo.addItems(["Word文档", "HTML网页", "JSON数据"])
        report_layout.addRow("报告格式:", self.report_format_combo)
        
        self.custom_template_edit = QLineEdit()
        self.custom_template_edit.setPlaceholderText("留空使用默认模板")
        report_layout.addRow("自定义模板:", self.custom_template_edit)
        
        browse_template_button = QPushButton("浏览...")
        browse_template_button.clicked.connect(self.browse_template)
        template_layout = QHBoxLayout()
        template_layout.addWidget(self.custom_template_edit)
        template_layout.addWidget(browse_template_button)
        report_layout.addRow("模板文件:", template_layout)
        
        layout.addWidget(report_group)
        
        layout.addStretch()
        return tab
    
    def create_notifications_tab(self) -> QWidget:
        """Create notifications configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Notification settings group
        notif_group = QGroupBox("通知设置")
        notif_layout = QFormLayout(notif_group)
        
        self.notify_failure_check = QCheckBox("巡检失败时通知")
        self.notify_failure_check.setChecked(True)
        notif_layout.addRow("", self.notify_failure_check)
        
        self.notify_success_check = QCheckBox("巡检成功时通知")
        self.notify_success_check.setChecked(False)
        notif_layout.addRow("", self.notify_success_check)
        
        self.recipients_text = QTextEdit()
        self.recipients_text.setPlaceholderText(
            "通知接收者邮箱地址，每行一个：\nadmin@example.com\nmonitor@example.com"
        )
        self.recipients_text.setMaximumHeight(100)
        notif_layout.addRow("通知接收者:", self.recipients_text)
        
        layout.addWidget(notif_group)
        
        layout.addStretch()
        return tab
    
    def add_quick_url(self):
        """Add URL from quick add field"""
        url = self.quick_url_edit.text().strip()
        if url:
            current_text = self.websites_text.toPlainText()
            if current_text:
                self.websites_text.setPlainText(current_text + "\n" + url)
            else:
                self.websites_text.setPlainText(url)
            self.quick_url_edit.clear()
    
    def add_check_widget(self):
        """Add a new check configuration widget"""
        self.load_single_check_widget()
    
    def load_single_check_widget(self, check: Optional[PatrolCheck] = None):
        """Load a single check widget - used for both adding new and loading existing checks"""
        check_widget = PatrolCheckWidget(check)
        check_widget.check_changed.connect(self.on_check_changed)
        
        # Create container for the check widget
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # Header with remove button
        header_layout = QHBoxLayout()
        header_label = QLabel(f"检查项 {len(self.check_widgets) + 1}")
        header_label.setFont(QFont("", weight=QFont.Bold))
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        remove_button = QPushButton("删除")
        # Store the container reference directly on the button to avoid closure issues
        remove_button.container_ref = container
        remove_button.clicked.connect(lambda: self.remove_check_widget(remove_button.container_ref))
        header_layout.addWidget(remove_button)
        
        container_layout.addLayout(header_layout)
        container_layout.addWidget(check_widget)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        container_layout.addWidget(separator)
        
        self.checks_layout.addWidget(container)
        self.check_widgets.append(check_widget)
    
    def remove_check_widget(self, container):
        """Remove a check widget with improved safety"""
        try:
            # Find the widget to remove by directly checking the container's children
            widget_to_remove = None
            index_to_remove = -1
            
            # Look through all check widgets to find the one in this container
            for i, check_widget in enumerate(self.check_widgets):
                # Check if this widget is directly contained in the provided container
                current_parent = check_widget.parent()
                if current_parent and current_parent == container:
                    widget_to_remove = check_widget
                    index_to_remove = i
                    break
            
            if widget_to_remove is not None and index_to_remove >= 0:
                # Remove from our list first to maintain consistency
                del self.check_widgets[index_to_remove]
                
                # Remove from layout and delete the container
                self.checks_layout.removeWidget(container)
                container.setParent(None)
                container.deleteLater()
                
                # Update labels after removal
                self.update_check_labels()
                
                self.logger.info(f"Successfully removed check widget at index {index_to_remove}")
            else:
                self.logger.warning("Could not find the check widget to remove")
                
        except Exception as e:
            self.logger.error(f"Error removing check widget: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't let the error crash the application
    
    def clear_checks(self):
        """Clear all check widgets"""
        try:
            for widget in self.check_widgets:
                container = widget.parent().parent()
                if container:
                    self.checks_layout.removeWidget(container)
                    container.setParent(None)
                    container.deleteLater()
            self.check_widgets.clear()
            
            # Don't automatically add a default check after clearing
            self.logger.debug("Cleared all check widgets")
        except Exception as e:
            self.logger.error(f"Error clearing check widgets: {e}")
            # Clear the list anyway to avoid inconsistent state
            self.check_widgets.clear()
    
    def update_check_labels(self):
        """Update check widget labels"""
        try:
            for i, widget in enumerate(self.check_widgets):
                container = widget.parent().parent()
                if container and container.layout():
                    header_layout_item = container.layout().itemAt(0)
                    if header_layout_item and header_layout_item.layout():
                        header_layout = header_layout_item.layout()
                        label_item = header_layout.itemAt(0)
                        if label_item and label_item.widget():
                            label = label_item.widget()
                            label.setText(f"检查项 {i + 1}")
        except Exception as e:
            self.logger.error(f"Error updating check labels: {e}")
    
    def update_delete_buttons(self):
        """Update delete button states - all check items can be deleted"""
        # Allow deletion of all check items, even if it results in zero checks
        # The validation will handle the requirement for at least one valid check during save
        pass
    
    def on_check_changed(self):
        """Handle check configuration changes"""
        pass  # Could add validation here
    
    def on_frequency_changed(self):
        """Handle frequency selection change"""
        frequency = self.frequency_combo.currentText()
        self.custom_schedule_edit.setEnabled(frequency == "自定义")
        self.multiple_times_edit.setEnabled(frequency == "每日多次")
        self.update_schedule_info()
    
    def update_schedule_info(self):
        """Update schedule information display"""
        frequency = self.frequency_combo.currentText()
        start_time = self.start_time_edit.time().toString("HH:mm")
        
        if frequency == "每日":
            info = f"每天 {start_time} 执行巡检"
        elif frequency == "每周":
            info = f"每周一 {start_time} 执行巡检"
        elif frequency == "每月":
            info = f"每月1号 {start_time} 执行巡检"
        elif frequency == "自定义":
            cron = self.custom_schedule_edit.text()
            if cron:
                info = f"按照Cron表达式执行: {cron}"
            else:
                info = "请输入有效的Cron表达式"
        else:
            info = ""
        
        self.schedule_info_label.setText(info)
    
    def on_report_settings_changed(self):
        """Handle report settings changes"""
        enabled = self.generate_report_check.isChecked()
        self.report_format_combo.setEnabled(enabled)
        self.custom_template_edit.setEnabled(enabled)
    
    def browse_template(self):
        """Browse for template file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模板文件", "", 
            "Word模板 (*.docx);;HTML模板 (*.html);;所有文件 (*)"
        )
        if file_path:
            self.custom_template_edit.setText(file_path)
    
    def load_task_data(self):
        """Load existing task data into UI"""
        if not self.task:
            return
        
        # Basic tab
        self.name_edit.setText(self.task.name)
        self.description_edit.setPlainText(self.task.description)
        self.enabled_check.setChecked(self.task.enabled)
        self.timeout_spin.setValue(self.task.timeout)
        self.retry_spin.setValue(self.task.retry_count)
        
        # Websites tab
        self.websites_text.setPlainText('\n'.join(self.task.websites))
        
        # Checks tab
        self.clear_checks()
        for check in self.task.checks:
            self.load_single_check_widget(check)
        
        # Schedule tab
        freq_map = {
            PatrolFrequency.DAILY: "每日",
            PatrolFrequency.MULTIPLE_DAILY: "每日多次",
            PatrolFrequency.WEEKLY: "每周",
            PatrolFrequency.MONTHLY: "每月",
            PatrolFrequency.CUSTOM: "自定义"
        }
        freq_text = freq_map.get(self.task.frequency, "每日")
        index = self.frequency_combo.findText(freq_text)
        if index >= 0:
            self.frequency_combo.setCurrentIndex(index)
        
        # Parse start time
        try:
            hour, minute = map(int, self.task.start_time.split(':'))
            self.start_time_edit.setTime(QTime(hour, minute))
        except:
            pass
        
        if self.task.custom_schedule:
            self.custom_schedule_edit.setText(self.task.custom_schedule)
        
        # Load multiple daily times
        if hasattr(self.task, 'multiple_times') and self.task.multiple_times:
            self.multiple_times_edit.setText(','.join(self.task.multiple_times))
        
        # Authentication tab
        if hasattr(self.task, 'auth_config') and self.task.auth_config:
            auth_config = self.task.auth_config
            auth_type = auth_config.get('type', 'none')
            
            if auth_type == 'form':
                self.auth_type_combo.setCurrentText("表单登录")
                self.login_url_edit.setText(auth_config.get('login_url', ''))
                self.username_edit.setText(auth_config.get('username', ''))
                self.password_edit.setText(auth_config.get('password', ''))
                self.username_field_edit.setText(auth_config.get('username_field', ''))
                self.password_field_edit.setText(auth_config.get('password_field', ''))
                
                additional_fields = auth_config.get('additional_fields', {})
                if additional_fields:
                    import json
                    self.additional_fields_edit.setPlainText(json.dumps(additional_fields, indent=2))
                    
            elif auth_type == 'basic':
                self.auth_type_combo.setCurrentText("HTTP基础认证")
                self.username_edit.setText(auth_config.get('username', ''))
                self.password_edit.setText(auth_config.get('password', ''))
                
            elif auth_type == 'bearer':
                self.auth_type_combo.setCurrentText("Bearer令牌")
                self.token_edit.setText(auth_config.get('token', ''))
        
        # Trigger auth type change to enable/disable fields
        self.on_auth_type_changed()
        
        # Reports tab
        self.generate_report_check.setChecked(self.task.generate_report)
        
        format_map = {
            "word": "Word文档",
            "html": "HTML网页",
            "json": "JSON数据"
        }
        format_text = format_map.get(self.task.report_format, "Word文档")
        index = self.report_format_combo.findText(format_text)
        if index >= 0:
            self.report_format_combo.setCurrentIndex(index)
        
        if self.task.custom_template:
            self.custom_template_edit.setText(self.task.custom_template)
        
        # Notifications tab
        self.notify_failure_check.setChecked(self.task.notify_on_failure)
        self.notify_success_check.setChecked(self.task.notify_on_success)
        self.recipients_text.setPlainText('\n'.join(self.task.notification_recipients))
    
    def get_task(self) -> PatrolTask:
        """Get patrol task from UI"""
        # Get websites list
        websites_text = self.websites_text.toPlainText().strip()
        websites = [url.strip() for url in websites_text.split('\n') if url.strip()]
        
        # Get checks list
        checks = []
        for widget in self.check_widgets:
            if widget.is_valid():
                checks.append(widget.get_check())
        
        # Map frequency
        freq_map = {
            "每日": PatrolFrequency.DAILY,
            "每日多次": PatrolFrequency.MULTIPLE_DAILY,
            "每周": PatrolFrequency.WEEKLY,
            "每月": PatrolFrequency.MONTHLY,
            "自定义": PatrolFrequency.CUSTOM
        }
        frequency = freq_map[self.frequency_combo.currentText()]
        
        # Map report format
        format_map = {
            "Word文档": "word",
            "HTML网页": "html",
            "JSON数据": "json"
        }
        report_format = format_map[self.report_format_combo.currentText()]
        
        # Get notification recipients
        recipients_text = self.recipients_text.toPlainText().strip()
        recipients = [email.strip() for email in recipients_text.split('\n') if email.strip()]
        
        # Get authentication configuration
        auth_config = None
        auth_type = self.auth_type_combo.currentText()
        if auth_type != "无需认证":
            auth_config = {"type": "none"}  # Default
            
            if auth_type == "表单登录":
                auth_config = {
                    "type": "form",
                    "login_url": self.login_url_edit.text().strip(),
                    "username": self.username_edit.text().strip(),
                    "password": self.password_edit.text().strip(),
                    "username_field": self.username_field_edit.text().strip() or "username",
                    "password_field": self.password_field_edit.text().strip() or "password"
                }
                
                # Add additional fields if specified
                additional_text = self.additional_fields_edit.toPlainText().strip()
                if additional_text:
                    try:
                        import json
                        additional_fields = json.loads(additional_text)
                        auth_config["additional_fields"] = additional_fields
                    except:
                        pass  # Ignore invalid JSON
                        
            elif auth_type == "HTTP基础认证":
                auth_config = {
                    "type": "basic",
                    "username": self.username_edit.text().strip(),
                    "password": self.password_edit.text().strip()
                }
                
            elif auth_type == "Bearer令牌":
                auth_config = {
                    "type": "bearer",
                    "token": self.token_edit.text().strip()
                }
        
        # Get multiple daily times
        multiple_times = []
        if frequency == PatrolFrequency.MULTIPLE_DAILY:
            times_text = self.multiple_times_edit.text().strip()
            if times_text:
                multiple_times = [t.strip() for t in times_text.split(',') if t.strip()]
        
        return PatrolTask(
            name=self.name_edit.text().strip(),
            description=self.description_edit.toPlainText().strip(),
            websites=websites,
            checks=checks,
            frequency=frequency,
            custom_schedule=self.custom_schedule_edit.text().strip() or None,
            start_time=self.start_time_edit.time().toString("HH:mm"),
            multiple_times=multiple_times,
            auth_config=auth_config,
            generate_report=self.generate_report_check.isChecked(),
            report_format=report_format,
            custom_template=self.custom_template_edit.text().strip() or None,
            notify_on_failure=self.notify_failure_check.isChecked(),
            notify_on_success=self.notify_success_check.isChecked(),
            notification_recipients=recipients,
            timeout=self.timeout_spin.value(),
            retry_count=self.retry_spin.value(),
            enabled=self.enabled_check.isChecked()
        )
    
    def accept(self):
        """Validate and accept dialog"""
        # Force focus away from all input fields to commit any pending changes
        self.setFocus()
        
        # Process any pending events to ensure all widgets are updated
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Validate required fields
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "验证错误", "请输入任务名称")
            self.name_edit.setFocus()
            return
        
        websites_text = self.websites_text.toPlainText().strip()
        if not websites_text:
            QMessageBox.warning(self, "验证错误", "请至少添加一个巡检网站")
            self.websites_text.setFocus()
            return
        
        # Check if any checks are valid
        if not self.check_widgets:
            QMessageBox.warning(self, "验证错误", "请至少添加一个检查项")
            return
            
        valid_checks = [w for w in self.check_widgets if w.is_valid()]
        if not valid_checks:
            QMessageBox.warning(self, "验证错误", "请至少配置一个有效的检查项（名称和目标不能为空）")
            return
        
        # Validate custom schedule if selected
        if self.frequency_combo.currentText() == "自定义":
            if not self.custom_schedule_edit.text().strip():
                QMessageBox.warning(self, "验证错误", "请输入自定义调度的Cron表达式")
                self.custom_schedule_edit.setFocus()
                return
        
        # Validate multiple daily times if selected
        if self.frequency_combo.currentText() == "每日多次":
            times_text = self.multiple_times_edit.text().strip()
            if not times_text:
                QMessageBox.warning(self, "验证错误", "请输入多次执行的时间（格式: 09:00,14:00,18:00）")
                self.multiple_times_edit.setFocus()
                return
            # Validate time format
            try:
                times = [t.strip() for t in times_text.split(',') if t.strip()]
                for time_str in times:
                    if not re.match(r'^\d{1,2}:\d{2}$', time_str):
                        raise ValueError(f"时间格式错误: {time_str}")
                    # Validate hour and minute ranges
                    hour, minute = map(int, time_str.split(':'))
                    if hour < 0 or hour > 23:
                        raise ValueError(f"小时必须在0-23之间: {time_str}")
                    if minute < 0 or minute > 59:
                        raise ValueError(f"分钟必须在0-59之间: {time_str}")
                if not times:
                    raise ValueError("请至少输入一个有效时间")
            except ValueError as e:
                QMessageBox.warning(self, "验证错误", f"时间格式错误: {str(e)}\n请使用格式: 09:00,14:00,18:00")
                self.multiple_times_edit.setFocus()
                return
        
        super().accept()