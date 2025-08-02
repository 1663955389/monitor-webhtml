"""
Widget for displaying and managing website monitoring
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSlot
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.monitor import WebsiteMonitor

class MonitoringWidget(QWidget):
    """Widget for monitoring websites display and management"""
    
    def __init__(self, monitor: 'WebsiteMonitor'):
        super().__init__()
        self.monitor = monitor
        self.init_ui()
        self.refresh_websites()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("已配置的网站")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_websites)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Websites table
        self.websites_table = QTableWidget()
        self.websites_table.setColumnCount(7)
        self.websites_table.setHorizontalHeaderLabels([
            "名称", "网址", "状态", "间隔(秒)", "最近检查", "响应时间", "操作"
        ])
        
        # Configure table
        header = self.websites_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Interval
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Last Check
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Response Time
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Actions
        
        self.websites_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.websites_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.websites_table)
        
        # Bottom controls
        controls_layout = QHBoxLayout()
        
        self.check_now_btn = QPushButton("立即检查选中项")
        self.check_now_btn.clicked.connect(self.check_selected_website)
        controls_layout.addWidget(self.check_now_btn)
        
        self.remove_btn = QPushButton("删除选中项")
        self.remove_btn.clicked.connect(self.remove_selected_website)
        controls_layout.addWidget(self.remove_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
    
    def refresh_websites(self):
        """Refresh the websites table"""
        websites = self.monitor.websites
        self.websites_table.setRowCount(len(websites))
        
        for row, (name, config) in enumerate(websites.items()):
            # Name
            self.websites_table.setItem(row, 0, QTableWidgetItem(name))
            
            # URL
            url_item = QTableWidgetItem(config.url)
            url_item.setToolTip(config.url)  # Show full URL on hover
            self.websites_table.setItem(row, 1, url_item)
            
            # Status (enabled/disabled)
            status = "启用" if config.enabled else "禁用"
            status_item = QTableWidgetItem(status)
            if config.enabled:
                status_item.setBackground(Qt.green)
            else:
                status_item.setBackground(Qt.gray)
            self.websites_table.setItem(row, 2, status_item)
            
            # Check interval
            self.websites_table.setItem(row, 3, QTableWidgetItem(str(config.check_interval)))
            
            # Last check time (placeholder for now)
            self.websites_table.setItem(row, 4, QTableWidgetItem("从未"))
            
            # Response time (placeholder for now)
            self.websites_table.setItem(row, 5, QTableWidgetItem("N/A"))
            
            # Actions (placeholder for now)
            self.websites_table.setItem(row, 6, QTableWidgetItem("编辑 | 删除"))
        
        # Update button states
        self.update_button_states()
    
    def update_button_states(self):
        """Update button enabled/disabled states"""
        has_websites = len(self.monitor.websites) > 0
        has_selection = len(self.websites_table.selectedItems()) > 0
        
        self.check_now_btn.setEnabled(has_selection)
        self.remove_btn.setEnabled(has_selection)
    
    @pyqtSlot()
    def check_selected_website(self):
        """Check the selected website now"""
        current_row = self.websites_table.currentRow()
        if current_row < 0:
            return
        
        website_name = self.websites_table.item(current_row, 0).text()
        
        # This would trigger an immediate check
        # For now, just show a message
        QMessageBox.information(
            self,
            "检查网站",
            f"触发立即检查: {website_name}"
        )
    
    @pyqtSlot()
    def remove_selected_website(self):
        """Remove the selected website"""
        current_row = self.websites_table.currentRow()
        if current_row < 0:
            return
        
        website_name = self.websites_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"您确定要从监控中删除 '{website_name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.monitor.remove_website(website_name)
            self.refresh_websites()
    
    def update_website_status(self, website_name: str, last_check: str, response_time: str):
        """Update a website's status in the table"""
        for row in range(self.websites_table.rowCount()):
            name_item = self.websites_table.item(row, 0)
            if name_item and name_item.text() == website_name:
                self.websites_table.setItem(row, 4, QTableWidgetItem(last_check))
                self.websites_table.setItem(row, 5, QTableWidgetItem(response_time))
                break