"""
Main window for the Website Monitoring and Reporting System
"""

import logging
import asyncio
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTextEdit, QStatusBar, QMenuBar, QAction,
    QSplitter, QLabel, QPushButton, QMessageBox, QApplication
)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

from core.monitor import WebsiteMonitor, MonitorResult
from core.auth import AuthenticationManager
from core.variables import VariableManager
from gui.widgets.monitoring_widget import MonitoringWidget
from gui.dialogs.website_config import WebsiteConfigDialog
from gui.dialogs.notification_config import NotificationConfigDialog
from config.settings import config_manager


class MonitoringThread(QThread):
    """Thread for running the monitoring loop"""
    result_signal = pyqtSignal(object)  # MonitorResult
    
    def __init__(self, monitor: WebsiteMonitor):
        super().__init__()
        self.monitor = monitor
        self.loop = None
    
    def run(self):
        """Run the monitoring loop in a separate thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Add result callback
        self.monitor.add_result_callback(self.on_result)
        
        try:
            self.loop.run_until_complete(self.monitor.start_monitoring())
        except Exception as e:
            logging.error(f"Error in monitoring thread: {e}")
        finally:
            if self.loop:
                self.loop.close()
    
    def on_result(self, result: MonitorResult):
        """Handle monitoring result"""
        self.result_signal.emit(result)
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.monitor.stop_monitoring(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.monitor = WebsiteMonitor()
        self.auth_manager = AuthenticationManager()
        self.variable_manager = VariableManager()
        
        # Threading
        self.monitoring_thread: Optional[MonitoringThread] = None
        
        # UI state
        self.is_monitoring = False
        
        self.init_ui()
        self.setup_connections()
        self.setup_timer()
        
        self.logger.info("Main window initialized")
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("网站监控和报告系统")
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
        self.create_monitoring_tab()
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
        
        new_website_action = QAction('添加网站', self)
        new_website_action.setShortcut('Ctrl+N')
        new_website_action.triggered.connect(self.add_website)
        file_menu.addAction(new_website_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Monitoring menu
        monitor_menu = menubar.addMenu('监控')
        
        start_action = QAction('开始监控', self)
        start_action.setShortcut('F5')
        start_action.triggered.connect(self.start_monitoring)
        monitor_menu.addAction(start_action)
        
        stop_action = QAction('停止监控', self)
        stop_action.setShortcut('F6')
        stop_action.triggered.connect(self.stop_monitoring)
        monitor_menu.addAction(stop_action)
        
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
        
        # Start monitoring button
        self.start_btn = QPushButton('开始监控')
        self.start_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_btn.clicked.connect(self.start_monitoring)
        toolbar.addWidget(self.start_btn)
        
        # Stop monitoring button
        self.stop_btn = QPushButton('停止监控')
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        toolbar.addWidget(self.stop_btn)
        
        toolbar.addSeparator()
        
        # Add website button
        add_website_btn = QPushButton('添加网站')
        add_website_btn.clicked.connect(self.add_website)
        toolbar.addWidget(add_website_btn)
    
    def create_monitoring_tab(self):
        """Create the monitoring tab"""
        self.monitoring_widget = MonitoringWidget(self.monitor)
        self.tab_widget.addTab(self.monitoring_widget, "监控")
    
    def create_results_tab(self):
        """Create the results tab"""
        results_widget = QWidget()
        layout = QVBoxLayout(results_widget)
        
        # Results display
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 10))
        layout.addWidget(QLabel("监控结果:"))
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
        self.monitoring_status_label = QLabel("监控: 已停止")
        self.websites_count_label = QLabel("网站: 0")
        
        self.status_bar.addWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.websites_count_label)
        self.status_bar.addPermanentWidget(self.monitoring_status_label)
    
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
        # Monitor result callback
        self.monitor.add_result_callback(self.on_monitoring_result)
    
    def setup_timer(self):
        """Setup update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # Update every second
    
    @pyqtSlot()
    def start_monitoring(self):
        """Start monitoring websites"""
        if self.is_monitoring:
            return
        
        if not self.monitor.websites:
            QMessageBox.warning(self, "警告", "没有配置需要监控的网站!")
            return
        
        try:
            self.monitoring_thread = MonitoringThread(self.monitor)
            self.monitoring_thread.result_signal.connect(self.on_monitoring_result_signal)
            self.monitoring_thread.start()
            
            self.is_monitoring = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            self.status_label.setText("正在启动监控...")
            self.logger.info("Monitoring started")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动监控失败: {e}")
            self.logger.error(f"Failed to start monitoring: {e}")
    
    @pyqtSlot()
    def stop_monitoring(self):
        """Stop monitoring websites"""
        if not self.is_monitoring:
            return
        
        try:
            if self.monitoring_thread:
                self.monitoring_thread.stop_monitoring()
                self.monitoring_thread.wait(5000)  # Wait up to 5 seconds
                
            self.is_monitoring = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
            self.status_label.setText("监控已停止")
            self.logger.info("Monitoring stopped")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止监控失败: {e}")
            self.logger.error(f"Failed to stop monitoring: {e}")
    
    @pyqtSlot(object)
    def on_monitoring_result_signal(self, result: MonitorResult):
        """Handle monitoring result from signal"""
        self.on_monitoring_result(result)
    
    def on_monitoring_result(self, result: MonitorResult):
        """Handle monitoring result"""
        # Update results display
        status = "成功" if result.success else "失败"
        result_text = (
            f"[{result.timestamp.strftime('%H:%M:%S')}] "
            f"{result.website_name} - {status}\n"
            f"  网址: {result.url}\n"
            f"  状态: {result.status_code}\n"
            f"  响应时间: {result.response_time:.2f}秒\n"
        )
        
        if result.error_message:
            result_text += f"  错误: {result.error_message}\n"
        
        result_text += "\n"
        
        self.results_text.append(result_text)
        
        # Auto-scroll to bottom
        cursor = self.results_text.textCursor()
        cursor.movePosition(cursor.End)
        self.results_text.setTextCursor(cursor)
    
    @pyqtSlot()
    def add_website(self):
        """Add a new website for monitoring"""
        dialog = WebsiteConfigDialog(self)
        if dialog.exec_() == dialog.Accepted:
            website_config = dialog.get_config()
            self.monitor.add_website(website_config)
            self.monitoring_widget.refresh_websites()
            self.update_status()
    
    @pyqtSlot()
    def configure_notifications(self):
        """Configure notification settings"""
        dialog = NotificationConfigDialog(self)
        dialog.exec_()
    
    @pyqtSlot()
    def generate_report(self):
        """Generate monitoring report"""
        # Placeholder for report generation
        self.reports_text.append(f"Report generation triggered at {QApplication.instance().property('timestamp')}\n")
    
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
        # Update website count
        website_count = len(self.monitor.websites)
        self.websites_count_label.setText(f"网站: {website_count}")
        
        # Update monitoring status
        status = "运行中" if self.is_monitoring else "已停止"
        self.monitoring_status_label.setText(f"监控: {status}")
        
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
        if self.is_monitoring:
            reply = QMessageBox.question(
                self,
                "确认退出",
                "监控仍在运行中。您确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.stop_monitoring()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
        
        self.logger.info("Application closing")