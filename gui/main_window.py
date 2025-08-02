"""
Main window for the Website Monitoring and Reporting System
"""

import logging
import asyncio
from typing import Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTextEdit, QStatusBar, QMenuBar, QAction,
    QSplitter, QLabel, QPushButton, QMessageBox, QApplication
)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

from core.auth import AuthenticationManager
from core.variables import VariableManager
from core.patrol import PatrolEngine
from gui.widgets.patrol_widget import PatrolTaskWidget
from gui.dialogs.notification_config import NotificationConfigDialog
from config.settings import config_manager


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.patrol_engine = PatrolEngine()
        self.auth_manager = AuthenticationManager()
        self.variable_manager = VariableManager()
        
        self.init_ui()
        self.setup_connections()
        self.setup_timer()
        
        self.logger.info("Main window initialized")
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("网站巡检和报告系统")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set application icon (if available)
        # self.setWindowIcon(QIcon('icon.png'))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_patrol_tab()
        self.create_results_tab()
        self.create_variables_tab()
        self.create_reports_tab()
        self.create_settings_tab()
        
        # Create status bar
        self.create_status_bar()
        
        # Apply styling
        self.apply_styling()
    
    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('文件')
        
        new_patrol_action = QAction('添加巡检任务', self)
        new_patrol_action.setShortcut('Ctrl+P')
        new_patrol_action.triggered.connect(self.add_patrol_task)
        file_menu.addAction(new_patrol_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Patrol menu (changed from Monitoring)
        patrol_menu = menubar.addMenu('巡检')
        
        execute_patrol_action = QAction('执行巡检', self)
        execute_patrol_action.setShortcut('F5')
        execute_patrol_action.triggered.connect(self.execute_selected_patrol)
        patrol_menu.addAction(execute_patrol_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('工具')
        
        notifications_action = QAction('通知设置', self)
        notifications_action.triggered.connect(self.configure_notifications)
        tools_menu.addAction(notifications_action)
        
        # Help menu
        help_menu = menubar.addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create the toolbar"""
        toolbar = self.addToolBar('主要')
        
        # Add patrol task button
        add_patrol_btn = QPushButton('添加巡检任务')
        add_patrol_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        add_patrol_btn.clicked.connect(self.add_patrol_task)
        toolbar.addWidget(add_patrol_btn)
        
        # Execute patrol button
        execute_patrol_btn = QPushButton('执行巡检')
        execute_patrol_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        execute_patrol_btn.clicked.connect(self.execute_selected_patrol)
        toolbar.addWidget(execute_patrol_btn)
    
    def create_patrol_tab(self):
        """Create the patrol management tab"""
        self.patrol_widget = PatrolTaskWidget()
        self.tab_widget.addTab(self.patrol_widget, "巡检任务")
    
    def create_results_tab(self):
        """Create the patrol results tab"""
        results_widget = QWidget()
        layout = QVBoxLayout(results_widget)
        
        # Results display
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 10))
        layout.addWidget(QLabel("巡检结果:"))
        layout.addWidget(self.results_text)
        
        self.tab_widget.addTab(results_widget, "结果")
    
    def create_variables_tab(self):
        """Create the variables tab"""
        variables_widget = QWidget()
        layout = QVBoxLayout(variables_widget)
        
        # Variables display
        self.variables_text = QTextEdit()
        self.variables_text.setReadOnly(True)
        layout.addWidget(QLabel("变量:"))
        layout.addWidget(self.variables_text)
        
        # Refresh button
        refresh_btn = QPushButton("刷新变量")
        refresh_btn.clicked.connect(self.refresh_variables)
        layout.addWidget(refresh_btn)
        
        self.tab_widget.addTab(variables_widget, "变量")
    
    def create_reports_tab(self):
        """Create the reports tab"""
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)
        
        # Reports controls
        generate_btn = QPushButton("生成报告")
        generate_btn.clicked.connect(self.generate_report)
        layout.addWidget(generate_btn)
        
        edit_report_btn = QPushButton("编辑Word报告")
        edit_report_btn.clicked.connect(self.edit_word_report)
        layout.addWidget(edit_report_btn)
        
        # Reports display
        self.reports_text = QTextEdit()
        self.reports_text.setReadOnly(True)
        layout.addWidget(QLabel("生成的报告:"))
        layout.addWidget(self.reports_text)
        
        self.tab_widget.addTab(reports_widget, "报告")
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Settings display
        self.settings_text = QTextEdit()
        self.settings_text.setReadOnly(True)
        layout.addWidget(QLabel("配置:"))
        layout.addWidget(self.settings_text)
        
        # Load current config
        self.load_config_display()
        
        self.tab_widget.addTab(settings_widget, "设置")
    
    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status labels
        self.status_label = QLabel("就绪")
        self.patrol_status_label = QLabel("巡检: 就绪")
        self.tasks_count_label = QLabel("巡检任务: 0")
        
        self.status_bar.addWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.tasks_count_label)
        self.status_bar.addPermanentWidget(self.patrol_status_label)
    
    def apply_styling(self):
        """Apply custom styling to the interface"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007acc;
            }
            QTextEdit {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
    
    def setup_connections(self):
        """Setup signal/slot connections"""
        # Patrol result callback
        self.patrol_engine.add_result_callback(self.on_patrol_result)
    
    def setup_timer(self):
        """Setup update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # Update every second
    
    def on_patrol_result(self, result):
        """Handle patrol result"""
        # Update results display
        status = "成功" if result.success else "失败"
        result_text = (
            f"[{result.timestamp.strftime('%H:%M:%S')}] "
            f"{result.task_name} - {status}\n"
            f"  网址: {result.website_url}\n"
            f"  状态: {result.status_code}\n"
            f"  响应时间: {result.response_time:.2f}秒\n"
        )
        
        if result.error_message:
            result_text += f"  错误: {result.error_message}\n"
        
        if result.check_results:
            result_text += "  检查结果:\n"
            for check_name, check_result in result.check_results.items():
                check_status = "✓" if check_result.get('success') else "✗"
                result_text += f"    {check_status} {check_name}: {check_result.get('message', '')}\n"
        
        result_text += "\n"
        
        self.results_text.append(result_text)
        
        # Auto-scroll to bottom
        cursor = self.results_text.textCursor()
        cursor.movePosition(cursor.End)
        self.results_text.setTextCursor(cursor)
    
    @pyqtSlot()
    def add_patrol_task(self):
        """Add a new patrol task"""
        if hasattr(self, 'patrol_widget'):
            self.patrol_widget.add_patrol_task()
    
    @pyqtSlot()
    def execute_selected_patrol(self):
        """Execute the currently selected patrol task"""
        if hasattr(self, 'patrol_widget'):
            # Switch to patrol tab if not already there
            patrol_tab_index = 0  # Patrol tab is first
            self.tab_widget.setCurrentIndex(patrol_tab_index)
            
            # Could trigger execution of selected task
            QMessageBox.information(
                self, "提示", 
                "请在巡检任务表格中选择要执行的任务，然后点击'执行'按钮"
            )
    
    @pyqtSlot()
    def configure_notifications(self):
        """Configure notification settings"""
        dialog = NotificationConfigDialog(self)
        dialog.exec_()
    
    @pyqtSlot()
    def generate_report(self):
        """Generate patrol report"""
        # Get recent patrol results
        # This is a placeholder - in a real implementation, you'd get actual results
        self.reports_text.append(f"巡检报告生成已触发 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    @pyqtSlot()
    def edit_word_report(self):
        """Open Word report editor"""
        try:
            from gui.dialogs.word_editor import WordReportEditor
            
            editor = WordReportEditor(self)
            editor.report_saved.connect(self.on_report_saved)
            editor.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开Word报告编辑器:\n{str(e)}")
            self.logger.error(f"Failed to open Word report editor: {e}")
    
    def on_report_saved(self, report_path: str):
        """Handle when a report is saved"""
        self.reports_text.append(f"报告已保存: {report_path}\n")
    
    @pyqtSlot()
    def refresh_variables(self):
        """Refresh variables display"""
        variables = self.variable_manager.get_all_variables_with_metadata()
        
        text = "变量:\n\n"
        for name, data in variables.items():
            value = data['value']
            metadata = data['metadata']
            text += f"名称: {name}\n"
            text += f"类型: {metadata.get('type', '未知')}\n"
            text += f"值: {str(value)[:100]}...\n" if len(str(value)) > 100 else f"值: {value}\n"
            text += f"创建时间: {metadata.get('created_at', '未知')}\n"
            text += "\n"
        
        self.variables_text.setPlainText(text)
    
    def load_config_display(self):
        """Load and display current configuration"""
        config_data = config_manager.get_config_data()
        import json
        config_text = json.dumps(config_data, indent=2)
        self.settings_text.setPlainText(config_text)
    
    def update_status(self):
        """Update status bar information"""
        # Update patrol task count
        task_count = len(self.patrol_engine.tasks)
        self.tasks_count_label.setText(f"巡检任务: {task_count}")
        
        # Update patrol status
        self.patrol_status_label.setText("巡检: 就绪")
        
        # Update variables tab if it's visible
        if self.tab_widget.currentIndex() == 2:  # Variables tab
            self.refresh_variables()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "关于",
            "网站监控和报告系统\n\n"
            "一个用于监控多个网站的综合解决方案，\n"
            "具有自定义报告和通知功能。\n\n"
            "版本: 1.0.0"
        )
    
    def closeEvent(self, event):
        """Handle application close event"""
        event.accept()
        self.logger.info("Application closing")