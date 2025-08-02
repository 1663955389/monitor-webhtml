"""
Word report editing dialog for modifying generated reports
"""

import logging
import os
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QFileDialog, QMessageBox, QSplitter, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


class WordReportEditor(QDialog):
    """Dialog for editing Word reports with preview and modification capabilities"""
    
    report_saved = pyqtSignal(str)  # Emit path when report is saved
    
    def __init__(self, parent=None, report_path: str = None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.current_report_path = report_path
        self.document = None
        
        self.init_ui()
        
        if report_path and Path(report_path).exists():
            self.load_report(report_path)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Word报告编辑器")
        self.setGeometry(100, 100, 1000, 700)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        self.open_btn = QPushButton("打开报告")
        self.open_btn.clicked.connect(self.open_report)
        toolbar_layout.addWidget(self.open_btn)
        
        self.save_btn = QPushButton("保存报告")
        self.save_btn.clicked.connect(self.save_report)
        self.save_btn.setEnabled(False)
        toolbar_layout.addWidget(self.save_btn)
        
        self.save_as_btn = QPushButton("另存为")
        self.save_as_btn.clicked.connect(self.save_as_report)
        self.save_as_btn.setEnabled(False)
        toolbar_layout.addWidget(self.save_as_btn)
        
        toolbar_layout.addStretch()
        
        self.preview_btn = QPushButton("刷新预览")
        self.preview_btn.clicked.connect(self.refresh_preview)
        self.preview_btn.setEnabled(False)
        toolbar_layout.addWidget(self.preview_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side: Structure and editing
        left_widget = QGroupBox("报告结构编辑")
        left_layout = QVBoxLayout(left_widget)
        
        # Document structure
        structure_label = QLabel("文档结构:")
        left_layout.addWidget(structure_label)
        
        self.structure_table = QTableWidget()
        self.structure_table.setColumnCount(3)
        self.structure_table.setHorizontalHeaderLabels(["类型", "内容", "编辑"])
        self.structure_table.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self.structure_table)
        
        # Content editor
        editor_label = QLabel("内容编辑:")
        left_layout.addWidget(editor_label)
        
        self.content_editor = QTextEdit()
        self.content_editor.setFont(QFont("Arial", 10))
        self.content_editor.setPlaceholderText("选择要编辑的段落或表格...")
        left_layout.addWidget(self.content_editor)
        
        # Edit controls
        edit_controls_layout = QHBoxLayout()
        
        self.update_content_btn = QPushButton("更新内容")
        self.update_content_btn.clicked.connect(self.update_selected_content)
        self.update_content_btn.setEnabled(False)
        edit_controls_layout.addWidget(self.update_content_btn)
        
        self.add_paragraph_btn = QPushButton("添加段落")
        self.add_paragraph_btn.clicked.connect(self.add_paragraph)
        self.add_paragraph_btn.setEnabled(False)
        edit_controls_layout.addWidget(self.add_paragraph_btn)
        
        edit_controls_layout.addStretch()
        left_layout.addLayout(edit_controls_layout)
        
        splitter.addWidget(left_widget)
        
        # Right side: Preview
        right_widget = QGroupBox("文档预览")
        right_layout = QVBoxLayout(right_widget)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 9))
        self.preview_text.setPlaceholderText("文档预览将在这里显示...")
        right_layout.addWidget(self.preview_text)
        
        splitter.addWidget(right_widget)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
        
        # Connect table selection
        self.structure_table.currentCellChanged.connect(self.on_structure_selection_changed)
    
    def open_report(self):
        """Open an existing Word report"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Word报告", "", "Word文档 (*.docx);;所有文件 (*.*)"
        )
        
        if file_path:
            self.load_report(file_path)
    
    def load_report(self, file_path: str):
        """Load a Word report for editing"""
        try:
            self.document = Document(file_path)
            self.current_report_path = file_path
            
            # Update UI state
            self.save_btn.setEnabled(True)
            self.save_as_btn.setEnabled(True)
            self.preview_btn.setEnabled(True)
            self.add_paragraph_btn.setEnabled(True)
            
            # Populate structure table
            self.populate_structure_table()
            
            # Refresh preview
            self.refresh_preview()
            
            self.logger.info(f"Loaded Word report: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载报告文件:\n{str(e)}")
            self.logger.error(f"Failed to load Word report: {e}")
    
    def populate_structure_table(self):
        """Populate the structure table with document elements"""
        if not self.document:
            return
        
        self.structure_table.setRowCount(0)
        
        for i, paragraph in enumerate(self.document.paragraphs):
            row = self.structure_table.rowCount()
            self.structure_table.insertRow(row)
            
            # Determine type
            if paragraph.style.name.startswith('Heading'):
                element_type = f"标题 {paragraph.style.name[-1]}"
            else:
                element_type = "段落"
            
            # Content preview (first 50 chars)
            content = paragraph.text[:50] + "..." if len(paragraph.text) > 50 else paragraph.text
            
            self.structure_table.setItem(row, 0, QTableWidgetItem(element_type))
            self.structure_table.setItem(row, 1, QTableWidgetItem(content))
            
            # Edit button
            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda checked, idx=i: self.edit_paragraph(idx))
            self.structure_table.setCellWidget(row, 2, edit_btn)
        
        # Add tables
        for i, table in enumerate(self.document.tables):
            row = self.structure_table.rowCount()
            self.structure_table.insertRow(row)
            
            content = f"表格 ({len(table.rows)}行 x {len(table.columns)}列)"
            
            self.structure_table.setItem(row, 0, QTableWidgetItem("表格"))
            self.structure_table.setItem(row, 1, QTableWidgetItem(content))
            
            # Edit button
            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda checked, idx=i: self.edit_table(idx))
            self.structure_table.setCellWidget(row, 2, edit_btn)
    
    def edit_paragraph(self, paragraph_index: int):
        """Edit a specific paragraph"""
        if not self.document or paragraph_index >= len(self.document.paragraphs):
            return
        
        paragraph = self.document.paragraphs[paragraph_index]
        self.content_editor.setPlainText(paragraph.text)
        self.current_edit_element = ('paragraph', paragraph_index)
        self.update_content_btn.setEnabled(True)
    
    def edit_table(self, table_index: int):
        """Edit a specific table"""
        if not self.document or table_index >= len(self.document.tables):
            return
        
        table = self.document.tables[table_index]
        
        # Convert table to editable text format
        table_text = ""
        for row in table.rows:
            row_texts = [cell.text for cell in row.cells]
            table_text += "\t".join(row_texts) + "\n"
        
        self.content_editor.setPlainText(table_text)
        self.current_edit_element = ('table', table_index)
        self.update_content_btn.setEnabled(True)
    
    def update_selected_content(self):
        """Update the selected content element"""
        if not hasattr(self, 'current_edit_element'):
            return
        
        new_content = self.content_editor.toPlainText()
        element_type, element_index = self.current_edit_element
        
        try:
            if element_type == 'paragraph':
                paragraph = self.document.paragraphs[element_index]
                paragraph.clear()
                paragraph.add_run(new_content)
                
            elif element_type == 'table':
                table = self.document.tables[element_index]
                lines = new_content.strip().split('\n')
                
                for row_idx, line in enumerate(lines):
                    if row_idx < len(table.rows):
                        cells = line.split('\t')
                        for col_idx, cell_text in enumerate(cells):
                            if col_idx < len(table.columns):
                                table.cell(row_idx, col_idx).text = cell_text.strip()
            
            # Refresh structure and preview
            self.populate_structure_table()
            self.refresh_preview()
            
            QMessageBox.information(self, "成功", "内容已更新")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新内容失败:\n{str(e)}")
    
    def add_paragraph(self):
        """Add a new paragraph to the document"""
        if not self.document:
            return
        
        new_text = self.content_editor.toPlainText()
        if not new_text.strip():
            QMessageBox.warning(self, "警告", "请在编辑框中输入要添加的内容")
            return
        
        # Add new paragraph at the end
        self.document.add_paragraph(new_text)
        
        # Refresh structure and preview
        self.populate_structure_table()
        self.refresh_preview()
        self.content_editor.clear()
        
        QMessageBox.information(self, "成功", "已添加新段落")
    
    def refresh_preview(self):
        """Refresh the document preview"""
        if not self.document:
            return
        
        preview_content = "文档预览:\n\n"
        
        for paragraph in self.document.paragraphs:
            if paragraph.style.name.startswith('Heading'):
                level = paragraph.style.name[-1] if paragraph.style.name[-1].isdigit() else "1"
                prefix = "#" * int(level) + " "
            else:
                prefix = ""
            
            preview_content += prefix + paragraph.text + "\n\n"
        
        # Add tables
        for i, table in enumerate(self.document.tables):
            preview_content += f"[表格 {i+1}]\n"
            for row in table.rows:
                row_text = " | ".join([cell.text for cell in row.cells])
                preview_content += row_text + "\n"
            preview_content += "\n"
        
        self.preview_text.setPlainText(preview_content)
    
    def save_report(self):
        """Save the current report"""
        if not self.document or not self.current_report_path:
            return
        
        try:
            self.document.save(self.current_report_path)
            QMessageBox.information(self, "成功", "报告已保存")
            self.report_saved.emit(self.current_report_path)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
    
    def save_as_report(self):
        """Save the report as a new file"""
        if not self.document:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "另存为", "", "Word文档 (*.docx);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                self.document.save(file_path)
                self.current_report_path = file_path
                QMessageBox.information(self, "成功", f"报告已保存到:\n{file_path}")
                self.report_saved.emit(file_path)
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
    
    def on_structure_selection_changed(self, current_row, current_col, previous_row, previous_col):
        """Handle structure table selection changes"""
        # Could be used to auto-load content for editing
        pass