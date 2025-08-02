"""
Patrol management widget for the main window (巡检管理组件)
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QMenu, QLabel, QFrame,
    QSplitter, QTextEdit, QGroupBox, QProgressBar, QComboBox, QDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon, QPixmap, QPainter

from core.patrol import PatrolEngine, PatrolTask, PatrolResult, PatrolFrequency, PatrolCheck, PatrolType
from gui.dialogs.patrol_config import PatrolTaskConfigDialog
from gui.dialogs.word_editor import WordReportEditor
from reports.generator import ReportGenerator


class PatrolExecutionThread(QThread):
    """Thread for executing patrol tasks"""
    
    task_started = pyqtSignal(str)  # task_name
    task_completed = pyqtSignal(str, list)  # task_name, results
    task_failed = pyqtSignal(str, str)  # task_name, error_message
    result_received = pyqtSignal(object)  # PatrolResult
    
    def __init__(self, patrol_engine: PatrolEngine, task_name: str):
        super().__init__()
        self.patrol_engine = patrol_engine
        self.task_name = task_name
        self.is_cancelled = False
    
    def run(self):
        """Execute the patrol task"""
        try:
            self.task_started.emit(self.task_name)
            
            # Add result callback
            self.patrol_engine.add_result_callback(self.on_result)
            
            # Execute the patrol task
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                results = loop.run_until_complete(
                    self.patrol_engine.execute_patrol_task(self.task_name)
                )
                if not self.is_cancelled:
                    self.task_completed.emit(self.task_name, results)
            finally:
                loop.close()
                
        except Exception as e:
            if not self.is_cancelled:
                self.task_failed.emit(self.task_name, str(e))
    
    def on_result(self, result: PatrolResult):
        """Handle individual patrol result"""
        if not self.is_cancelled:
            self.result_received.emit(result)
    
    def cancel(self):
        """Cancel the execution"""
        self.is_cancelled = True


class PatrolTaskWidget(QWidget):
    """Widget for managing patrol tasks"""
    
    task_execution_requested = pyqtSignal(str)  # task_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.patrol_engine = PatrolEngine()
        self.report_generator = ReportGenerator()
        
        # Execution state
        self.execution_threads: Dict[str, PatrolExecutionThread] = {}
        self.task_results: Dict[str, List[PatrolResult]] = {}
        self.last_generated_reports: Dict[str, str] = {}  # Track last generated report paths
        
        self.setup_ui()
        self.setup_timers()
        
        # Load sample tasks for demo
        self.load_sample_tasks()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        
        # Header section
        header_layout = QHBoxLayout()
        
        title_label = QLabel("巡检任务管理")
        title_label.setFont(QFont("", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Task management buttons
        self.add_task_button = QPushButton("添加巡检任务")
        self.add_task_button.clicked.connect(self.add_patrol_task)
        header_layout.addWidget(self.add_task_button)
        
        self.edit_task_button = QPushButton("编辑任务")
        self.edit_task_button.clicked.connect(self.edit_patrol_task)
        self.edit_task_button.setEnabled(False)
        header_layout.addWidget(self.edit_task_button)
        
        self.delete_task_button = QPushButton("删除任务")
        self.delete_task_button.clicked.connect(self.delete_patrol_task)
        self.delete_task_button.setEnabled(False)
        header_layout.addWidget(self.delete_task_button)
        
        header_layout.addWidget(QLabel("|"))  # Separator
        
        # Report management buttons
        self.open_word_editor_button = QPushButton("自定义报告编辑器")
        self.open_word_editor_button.clicked.connect(self.open_word_editor)
        header_layout.addWidget(self.open_word_editor_button)
        
        layout.addLayout(header_layout)
        
        # Main splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Tasks table
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(8)
        self.tasks_table.setHorizontalHeaderLabels([
            "任务名称", "状态", "网站数量", "检查项", "频率", "下次执行", "上次执行", "操作"
        ])
        
        # Configure table
        header = self.tasks_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionResizeMode(5, QHeaderView.Interactive)
        header.setSectionResizeMode(6, QHeaderView.Interactive)
        
        self.tasks_table.setColumnWidth(1, 80)
        self.tasks_table.setColumnWidth(2, 80)
        self.tasks_table.setColumnWidth(3, 80)
        
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.tasks_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tasks_table.customContextMenuRequested.connect(self.show_context_menu)
        
        splitter.addWidget(self.tasks_table)
        
        # Results section
        results_widget = self.create_results_widget()
        splitter.addWidget(results_widget)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
    
    def create_results_widget(self) -> QWidget:
        """Create the results display widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Results header
        header_layout = QHBoxLayout()
        
        results_label = QLabel("执行结果")
        results_label.setFont(QFont("", 12, QFont.Bold))
        header_layout.addWidget(results_label)
        
        header_layout.addStretch()
        
        # Results filter
        self.results_filter = QComboBox()
        self.results_filter.addItems(["全部", "成功", "失败", "最近执行"])
        self.results_filter.currentTextChanged.connect(self.filter_results)
        header_layout.addWidget(QLabel("筛选:"))
        header_layout.addWidget(self.results_filter)
        
        # Generate report button
        self.generate_report_button = QPushButton("生成报告")
        self.generate_report_button.clicked.connect(self.generate_current_report)
        self.generate_report_button.setEnabled(False)
        header_layout.addWidget(self.generate_report_button)
        
        # Edit report button
        self.edit_report_button = QPushButton("编辑报告")
        self.edit_report_button.clicked.connect(self.edit_current_report)
        self.edit_report_button.setEnabled(False)
        header_layout.addWidget(self.edit_report_button)
        
        layout.addLayout(header_layout)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "任务名称", "网站", "状态", "执行时间", "响应时间", "状态码", "错误信息"
        ])
        
        # Configure results table
        results_header = self.results_table.horizontalHeader()
        results_header.setStretchLastSection(True)
        results_header.setSectionResizeMode(0, QHeaderView.Interactive)
        results_header.setSectionResizeMode(1, QHeaderView.Interactive)
        results_header.setSectionResizeMode(2, QHeaderView.Fixed)
        results_header.setSectionResizeMode(3, QHeaderView.Interactive)
        results_header.setSectionResizeMode(4, QHeaderView.Fixed)
        results_header.setSectionResizeMode(5, QHeaderView.Fixed)
        
        self.results_table.setColumnWidth(2, 80)
        self.results_table.setColumnWidth(4, 100)
        self.results_table.setColumnWidth(5, 80)
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.results_table)
        
        return widget
    
    def setup_timers(self):
        """Setup timers for periodic updates"""
        # Refresh timer for task list
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_tasks_display)
        self.refresh_timer.start(30000)  # 30 seconds
        
        # Check for scheduled tasks
        self.schedule_timer = QTimer()
        self.schedule_timer.timeout.connect(self.check_scheduled_tasks)
        self.schedule_timer.start(60000)  # 1 minute
    
    def load_sample_tasks(self):
        """Load sample patrol tasks for demonstration"""
        
        # Sample task 1
        sample_task1 = PatrolTask(
            name="主网站巡检",
            description="检查主网站的基本功能和内容",
            websites=["https://httpbin.org/get", "https://httpbin.org/status/200"],
            frequency=PatrolFrequency.DAILY,
            start_time="09:00"
        )
        
        # Add content check
        sample_task1.checks.append(PatrolCheck(
            name="页面标题检查",
            type=PatrolType.CONTENT_CHECK,
            target="title",
            expected_value="httpbin",
            description="检查页面标题是否包含httpbin"
        ))
        
        # Add API check
        sample_task1.checks.append(PatrolCheck(
            name="API状态检查",
            type=PatrolType.API_CHECK,
            target="/status/200",
            expected_value="200",
            description="检查API接口状态"
        ))
        
        self.patrol_engine.add_patrol_task(sample_task1)
        
        # Sample task 2
        sample_task2 = PatrolTask(
            name="API接口巡检",
            description="检查关键API接口的可用性",
            websites=["https://httpbin.org/json", "https://httpbin.org/xml"],
            frequency=PatrolFrequency.WEEKLY,
            start_time="08:00"
        )
        
        sample_task2.checks.append(PatrolCheck(
            name="JSON响应检查",
            type=PatrolType.API_CHECK,
            target="/json",
            expected_value="application/json",
            description="检查JSON API响应格式"
        ))
        
        self.patrol_engine.add_patrol_task(sample_task2)
        
        # Refresh display
        self.refresh_tasks_display()
    
    def refresh_tasks_display(self):
        """Refresh the tasks table display"""
        tasks = self.patrol_engine.list_patrol_tasks()
        
        self.tasks_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # Task name
            name_item = QTableWidgetItem(task.name)
            name_item.setData(Qt.UserRole, task.name)
            self.tasks_table.setItem(row, 0, name_item)
            
            # Status
            status_text = "启用" if task.enabled else "禁用"
            status_item = QTableWidgetItem(status_text)
            if task.enabled:
                status_item.setBackground(QBrush(QColor(144, 238, 144)))  # Light green
            else:
                status_item.setBackground(QBrush(QColor(255, 182, 193)))  # Light red
            self.tasks_table.setItem(row, 1, status_item)
            
            # Website count
            website_count_item = QTableWidgetItem(str(len(task.websites)))
            self.tasks_table.setItem(row, 2, website_count_item)
            
            # Check count
            check_count_item = QTableWidgetItem(str(len(task.checks)))
            self.tasks_table.setItem(row, 3, check_count_item)
            
            # Frequency
            freq_map = {
                PatrolFrequency.DAILY: "每日",
                PatrolFrequency.MULTIPLE_DAILY: "每日多次",
                PatrolFrequency.WEEKLY: "每周",
                PatrolFrequency.MONTHLY: "每月",
                PatrolFrequency.CUSTOM: "自定义"
            }
            freq_text = freq_map.get(task.frequency, "未知")
            freq_item = QTableWidgetItem(freq_text)
            self.tasks_table.setItem(row, 4, freq_item)
            
            # Next run
            if task.next_run:
                next_run_text = task.next_run.strftime("%Y-%m-%d %H:%M")
            else:
                next_run = self.patrol_engine.calculate_next_run_time(task)
                next_run_text = next_run.strftime("%Y-%m-%d %H:%M")
            next_run_item = QTableWidgetItem(next_run_text)
            self.tasks_table.setItem(row, 5, next_run_item)
            
            # Last run
            if task.last_run:
                last_run_text = task.last_run.strftime("%Y-%m-%d %H:%M")
            else:
                last_run_text = "从未执行"
            last_run_item = QTableWidgetItem(last_run_text)
            self.tasks_table.setItem(row, 6, last_run_item)
            
            # Actions
            actions_widget = self.create_actions_widget(task.name)
            self.tasks_table.setCellWidget(row, 7, actions_widget)
    
    def create_actions_widget(self, task_name: str) -> QWidget:
        """Create actions widget for a task row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        
        # Execute button
        execute_button = QPushButton("执行")
        execute_button.setMaximumSize(60, 25)
        execute_button.clicked.connect(lambda: self.execute_patrol_task(task_name))
        layout.addWidget(execute_button)
        
        # Check if task is currently executing
        if task_name in self.execution_threads:
            execute_button.setText("执行中...")
            execute_button.setEnabled(False)
        
        layout.addStretch()
        
        return widget
    
    def on_selection_changed(self):
        """Handle table selection changes"""
        selected_rows = set()
        for item in self.tasks_table.selectedItems():
            selected_rows.add(item.row())
        
        has_selection = len(selected_rows) > 0
        self.edit_task_button.setEnabled(has_selection and len(selected_rows) == 1)
        self.delete_task_button.setEnabled(has_selection)
        
        # Update results display for selected task
        if len(selected_rows) == 1:
            row = list(selected_rows)[0]
            task_name_item = self.tasks_table.item(row, 0)
            if task_name_item:
                task_name = task_name_item.data(Qt.UserRole)
                self.display_task_results(task_name)
                has_results = task_name in self.task_results and len(self.task_results[task_name]) > 0
                self.generate_report_button.setEnabled(has_results)
                # Enable edit report button only if there's a recently generated report
                has_report = task_name in self.last_generated_reports
                self.edit_report_button.setEnabled(has_report)
        else:
            self.generate_report_button.setEnabled(False)
            self.edit_report_button.setEnabled(False)
    
    def show_context_menu(self, position):
        """Show context menu for tasks table"""
        item = self.tasks_table.itemAt(position)
        if not item:
            return
        
        task_name_item = self.tasks_table.item(item.row(), 0)
        task_name = task_name_item.data(Qt.UserRole)
        
        menu = QMenu(self)
        
        execute_action = menu.addAction("立即执行")
        execute_action.triggered.connect(lambda: self.execute_patrol_task(task_name))
        
        edit_action = menu.addAction("编辑任务")
        edit_action.triggered.connect(self.edit_patrol_task)
        
        menu.addSeparator()
        
        duplicate_action = menu.addAction("复制任务")
        duplicate_action.triggered.connect(lambda: self.duplicate_patrol_task(task_name))
        
        delete_action = menu.addAction("删除任务")
        delete_action.triggered.connect(self.delete_patrol_task)
        
        menu.addSeparator()
        
        view_results_action = menu.addAction("查看执行历史")
        view_results_action.triggered.connect(lambda: self.view_task_history(task_name))
        
        # Add edit report option if recent report exists
        if task_name in self.last_generated_reports:
            menu.addSeparator()
            edit_report_action = menu.addAction("编辑最近报告")
            edit_report_action.triggered.connect(lambda: self.edit_report_for_task(task_name))
        
        # Disable execute if already running
        if task_name in self.execution_threads:
            execute_action.setEnabled(False)
        
        menu.exec_(self.tasks_table.mapToGlobal(position))
    
    def add_patrol_task(self):
        """Add a new patrol task"""
        dialog = PatrolTaskConfigDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                task = dialog.get_task()
                self.patrol_engine.add_patrol_task(task)
                self.refresh_tasks_display()
                QMessageBox.information(self, "成功", f"巡检任务 '{task.name}' 已添加")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加任务失败: {str(e)}")
    
    def edit_patrol_task(self):
        """Edit selected patrol task"""
        selected_rows = set(item.row() for item in self.tasks_table.selectedItems())
        if len(selected_rows) != 1:
            return
        
        row = list(selected_rows)[0]
        task_name_item = self.tasks_table.item(row, 0)
        task_name = task_name_item.data(Qt.UserRole)
        
        task = self.patrol_engine.get_patrol_task(task_name)
        if not task:
            QMessageBox.warning(self, "错误", "找不到指定的巡检任务")
            return
        
        dialog = PatrolTaskConfigDialog(task, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                updated_task = dialog.get_task()
                # Remove old task and add updated one
                self.patrol_engine.remove_patrol_task(task_name)
                self.patrol_engine.add_patrol_task(updated_task)
                self.refresh_tasks_display()
                QMessageBox.information(self, "成功", f"巡检任务 '{updated_task.name}' 已更新")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新任务失败: {str(e)}")
    
    def delete_patrol_task(self):
        """Delete selected patrol tasks"""
        selected_rows = set(item.row() for item in self.tasks_table.selectedItems())
        if not selected_rows:
            return
        
        task_names = []
        for row in selected_rows:
            task_name_item = self.tasks_table.item(row, 0)
            if task_name_item:
                task_names.append(task_name_item.data(Qt.UserRole))
        
        if not task_names:
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 {len(task_names)} 个巡检任务吗？\n\n" + "\n".join(task_names),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for task_name in task_names:
                self.patrol_engine.remove_patrol_task(task_name)
                # Cancel execution if running
                if task_name in self.execution_threads:
                    self.execution_threads[task_name].cancel()
                    del self.execution_threads[task_name]
                # Remove results
                if task_name in self.task_results:
                    del self.task_results[task_name]
            
            self.refresh_tasks_display()
            QMessageBox.information(self, "成功", f"已删除 {len(task_names)} 个巡检任务")
    
    def duplicate_patrol_task(self, task_name: str):
        """Duplicate a patrol task"""
        task = self.patrol_engine.get_patrol_task(task_name)
        if not task:
            return
        
        # Create copy with new name
        import copy
        new_task = copy.deepcopy(task)
        new_task.name = f"{task.name} - 副本"
        new_task.created_at = datetime.now()
        new_task.last_run = None
        new_task.next_run = None
        new_task.run_count = 0
        
        dialog = PatrolTaskConfigDialog(new_task, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                final_task = dialog.get_task()
                self.patrol_engine.add_patrol_task(final_task)
                self.refresh_tasks_display()
                QMessageBox.information(self, "成功", f"已复制巡检任务 '{final_task.name}'")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"复制任务失败: {str(e)}")
    
    def execute_patrol_task(self, task_name: str):
        """Execute a patrol task"""
        if task_name in self.execution_threads:
            QMessageBox.information(self, "提示", f"任务 '{task_name}' 正在执行中")
            return
        
        task = self.patrol_engine.get_patrol_task(task_name)
        if not task:
            QMessageBox.warning(self, "错误", f"找不到任务 '{task_name}'")
            return
        
        if not task.enabled:
            reply = QMessageBox.question(
                self, "确认执行",
                f"任务 '{task_name}' 当前被禁用，是否仍要执行？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Create and start execution thread
        thread = PatrolExecutionThread(self.patrol_engine, task_name)
        thread.task_started.connect(self.on_task_started)
        thread.task_completed.connect(self.on_task_completed)
        thread.task_failed.connect(self.on_task_failed)
        thread.result_received.connect(self.on_result_received)
        thread.finished.connect(lambda: self.cleanup_thread(task_name))
        
        self.execution_threads[task_name] = thread
        thread.start()
        
        # Refresh display to show "executing" status
        self.refresh_tasks_display()
    
    @pyqtSlot(str)
    def on_task_started(self, task_name: str):
        """Handle task execution start"""
        self.logger.info(f"Started patrol task: {task_name}")
        # Initialize results list for this task
        if task_name not in self.task_results:
            self.task_results[task_name] = []
    
    @pyqtSlot(str, list)
    def on_task_completed(self, task_name: str, results: List[PatrolResult]):
        """Handle task execution completion"""
        self.logger.info(f"Completed patrol task: {task_name}, {len(results)} results")
        
        # Store results
        if task_name not in self.task_results:
            self.task_results[task_name] = []
        self.task_results[task_name].extend(results)
        
        # Keep only recent results (last 100)
        self.task_results[task_name] = self.task_results[task_name][-100:]
        
        # Show completion message
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        
        QMessageBox.information(
            self, "执行完成",
            f"巡检任务 '{task_name}' 执行完成\n\n"
            f"总计: {total_count} 个网站\n"
            f"成功: {success_count} 个\n"
            f"失败: {total_count - success_count} 个"
        )
        
        # Refresh displays
        self.refresh_tasks_display()
        self.display_task_results(task_name)
    
    @pyqtSlot(str, str)
    def on_task_failed(self, task_name: str, error_message: str):
        """Handle task execution failure"""
        self.logger.error(f"Patrol task failed: {task_name}, error: {error_message}")
        
        QMessageBox.critical(
            self, "执行失败",
            f"巡检任务 '{task_name}' 执行失败:\n\n{error_message}"
        )
        
        self.refresh_tasks_display()
    
    @pyqtSlot(object)
    def on_result_received(self, result: PatrolResult):
        """Handle individual patrol result"""
        # Update real-time display if this task is selected
        selected_rows = set(item.row() for item in self.tasks_table.selectedItems())
        if len(selected_rows) == 1:
            row = list(selected_rows)[0]
            task_name_item = self.tasks_table.item(row, 0)
            if task_name_item and task_name_item.data(Qt.UserRole) == result.task_name:
                self.add_result_to_display(result)
    
    def cleanup_thread(self, task_name: str):
        """Clean up execution thread"""
        if task_name in self.execution_threads:
            del self.execution_threads[task_name]
        self.refresh_tasks_display()
    
    def display_task_results(self, task_name: str):
        """Display results for a specific task"""
        results = self.task_results.get(task_name, [])
        
        # Apply filter
        filter_text = self.results_filter.currentText()
        if filter_text == "成功":
            results = [r for r in results if r.success]
        elif filter_text == "失败":
            results = [r for r in results if not r.success]
        elif filter_text == "最近执行":
            # Last 10 results
            results = results[-10:] if len(results) > 10 else results
        
        self.populate_results_table(results)
    
    def populate_results_table(self, results: List[PatrolResult]):
        """Populate the results table with data"""
        self.results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # Task name
            task_item = QTableWidgetItem(result.task_name)
            self.results_table.setItem(row, 0, task_item)
            
            # Website URL
            url_item = QTableWidgetItem(result.website_url)
            self.results_table.setItem(row, 1, url_item)
            
            # Status
            status_text = "成功" if result.success else "失败"
            status_item = QTableWidgetItem(status_text)
            if result.success:
                status_item.setBackground(QBrush(QColor(144, 238, 144)))  # Light green
            else:
                status_item.setBackground(QBrush(QColor(255, 182, 193)))  # Light red
            self.results_table.setItem(row, 2, status_item)
            
            # Execution time
            time_item = QTableWidgetItem(result.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            self.results_table.setItem(row, 3, time_item)
            
            # Response time
            if result.response_time is not None:
                response_time_text = f"{result.response_time:.2f}s"
            else:
                response_time_text = "N/A"
            response_time_item = QTableWidgetItem(response_time_text)
            self.results_table.setItem(row, 4, response_time_item)
            
            # Status code
            if result.status_code is not None:
                status_code_text = str(result.status_code)
            else:
                status_code_text = "N/A"
            status_code_item = QTableWidgetItem(status_code_text)
            self.results_table.setItem(row, 5, status_code_item)
            
            # Error message
            error_item = QTableWidgetItem(result.error_message or "")
            self.results_table.setItem(row, 6, error_item)
    
    def add_result_to_display(self, result: PatrolResult):
        """Add a single result to the display (for real-time updates)"""
        current_row_count = self.results_table.rowCount()
        self.results_table.insertRow(current_row_count)
        
        # Populate the new row
        self.populate_results_table([result])
        
        # Scroll to the new row
        self.results_table.scrollToBottom()
    
    def filter_results(self):
        """Apply results filter"""
        selected_rows = set(item.row() for item in self.tasks_table.selectedItems())
        if len(selected_rows) == 1:
            row = list(selected_rows)[0]
            task_name_item = self.tasks_table.item(row, 0)
            if task_name_item:
                task_name = task_name_item.data(Qt.UserRole)
                self.display_task_results(task_name)
    
    def generate_current_report(self):
        """Generate report for currently selected task"""
        selected_rows = set(item.row() for item in self.tasks_table.selectedItems())
        if len(selected_rows) != 1:
            return
        
        row = list(selected_rows)[0]
        task_name_item = self.tasks_table.item(row, 0)
        task_name = task_name_item.data(Qt.UserRole)
        
        results = self.task_results.get(task_name, [])
        if not results:
            QMessageBox.information(self, "提示", "该任务还没有执行结果")
            return
        
        try:
            # Generate patrol Word report with enhanced features
            report_path = self.report_generator.generate_patrol_word_report(
                patrol_results=results,
                task_name=task_name
            )
            
            # Store the path for editing functionality
            self.last_generated_reports[task_name] = report_path
            
            # Update button states
            self.edit_report_button.setEnabled(True)
            
            QMessageBox.information(
                self, "报告生成成功",
                f"巡检报告已生成:\n{report_path}\n\n您可以点击'编辑报告'按钮来自定义报告内容。"
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成报告失败: {str(e)}")
    
    def edit_current_report(self):
        """Edit the most recently generated report for selected task"""
        selected_rows = set(item.row() for item in self.tasks_table.selectedItems())
        if len(selected_rows) != 1:
            return
        
        row = list(selected_rows)[0]
        task_name_item = self.tasks_table.item(row, 0)
        task_name = task_name_item.data(Qt.UserRole)
        
        # Get the most recent report path for this task
        report_path = self.last_generated_reports.get(task_name)
        if not report_path or not Path(report_path).exists():
            # No recent report, try to generate one first
            reply = QMessageBox.question(
                self, "无报告文件",
                "找不到该任务的报告文件。是否要先生成报告？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.generate_current_report()
                # After generation, try again
                report_path = self.last_generated_reports.get(task_name)
                if not report_path:
                    return
            else:
                return
        
        try:
            # Open Word report editor
            editor = WordReportEditor(parent=self, report_path=report_path)
            editor.report_saved.connect(lambda path: self._on_report_saved(task_name, path))
            editor.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开报告编辑器失败: {str(e)}")
    
    def _on_report_saved(self, task_name: str, report_path: str):
        """Handle report saved event"""
        self.last_generated_reports[task_name] = report_path
        QMessageBox.information(self, "成功", "报告已保存！")
    
    def edit_report_for_task(self, task_name: str):
        """Edit report for a specific task (helper method for context menu)"""
        # Select the task in the table first
        for row in range(self.tasks_table.rowCount()):
            item = self.tasks_table.item(row, 0)
            if item and item.data(Qt.UserRole) == task_name:
                self.tasks_table.selectRow(row)
                break
        
        # Then call the main edit method
        self.edit_current_report()
    
    def open_word_editor(self):
        """Open Word editor for custom report editing"""
        try:
            # Open Word editor without any specific report
            editor = WordReportEditor(parent=self)
            editor.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开自定义报告编辑器失败: {str(e)}")
    
    def view_task_history(self, task_name: str):
        """View execution history for a task"""
        # This could open a detailed history dialog
        QMessageBox.information(
            self, "执行历史",
            f"任务 '{task_name}' 的详细执行历史功能正在开发中"
        )
    
    def check_scheduled_tasks(self):
        """Check for tasks that should be executed according to schedule"""
        current_time = datetime.now()
        
        for task in self.patrol_engine.list_patrol_tasks():
            if not task.enabled:
                continue
            
            # Calculate next run time if not set
            if not task.next_run:
                task.next_run = self.patrol_engine.calculate_next_run_time(task)
            
            # Check if it's time to run
            if task.next_run <= current_time:
                # Execute the task
                self.logger.info(f"Executing scheduled task: {task.name}")
                self.execute_patrol_task(task.name)
                
                # Update next run time
                task.next_run = self.patrol_engine.calculate_next_run_time(task)