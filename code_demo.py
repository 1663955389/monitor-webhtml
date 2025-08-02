"""
演示新功能的关键代码片段
"""

# ========== 段落删除功能 ==========

def populate_structure_table(self):
    """填充结构表格，现在包含删除按钮"""
    # ... 段落处理 ...
    
    # 编辑按钮
    edit_btn = QPushButton("编辑")
    edit_btn.clicked.connect(lambda checked, idx=i: self.edit_paragraph(idx))
    self.structure_table.setCellWidget(row, 2, edit_btn)
    
    # 🆕 删除按钮
    delete_btn = QPushButton("删除")
    delete_btn.clicked.connect(lambda checked, idx=i: self.delete_paragraph(idx))
    delete_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
    self.structure_table.setCellWidget(row, 3, delete_btn)

def delete_paragraph(self, paragraph_index: int):
    """🆕 删除指定段落"""
    # 确认删除
    reply = QMessageBox.question(
        self, "确认删除", 
        f"确定要删除第 {paragraph_index + 1} 个段落吗？",
        QMessageBox.Yes | QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        # 从文档中删除段落
        paragraph = self.document.paragraphs[paragraph_index]
        p = paragraph._element
        p.getparent().remove(p)
        
        # 刷新界面
        self.populate_structure_table()
        self.refresh_preview()


# ========== 变量系统 ==========

def update_selected_content(self):
    """更新选中内容，现在支持变量替换"""
    new_content = self.content_editor.toPlainText()
    
    # 🆕 应用变量替换
    substituted_content = self.variable_manager.substitute_variables(new_content)
    
    # 更新文档内容
    paragraph.clear()
    paragraph.add_run(substituted_content)

def refresh_variables_list(self):
    """🆕 刷新可用变量列表"""
    self.variables_list.clear()
    
    variables = self.variable_manager.get_all_variables_with_metadata()
    
    for var_name, var_info in variables.items():
        var_type = var_info.get('metadata', {}).get('type', 'unknown')
        var_value = var_info.get('value', '')
        
        # 创建显示文本
        if var_type == 'image':
            display_text = f"${{{var_name}}} [图片] - {var_value}"
        elif var_type == 'text':
            preview = str(var_value)[:30] + "..." if len(str(var_value)) > 30 else str(var_value)
            display_text = f"${{{var_name}}} [文本] - {preview}"
        # ...

def _populate_variables_from_results(self, results):
    """🆕 从巡检结果生成变量"""
    for result in results:
        # 生成安全的变量名
        safe_task_name = "".join(c for c in result.task_name if c.isalnum() or c in ('_',))
        safe_url = result.website_url.replace("://", "_").replace("/", "_")...
        
        # 存储截图变量
        if result.screenshot_path:
            var_name = f"screenshot_{safe_task_name}_{safe_url}"
            self.variable_manager.set_variable(
                var_name, result.screenshot_path, "image", 
                f"页面截图来源: {result.website_url}"
            )
        
        # 存储XPath提取的值
        if result.check_results:
            for check_name, check_result in result.check_results.items():
                if check_result.get('extracted_value'):
                    var_name = f"extracted_{safe_check_name}_{safe_task_name}"
                    self.variable_manager.set_variable(
                        var_name, check_result['extracted_value'], "text",
                        f"提取值来源: {check_name} ({result.website_url})"
                    )


# ========== 用户界面增强 ==========

def init_ui(self):
    """初始化UI，现在包含变量支持"""
    # ...
    
    # 🆕 文档结构表格增加删除列
    self.structure_table = QTableWidget()
    self.structure_table.setColumnCount(4)  # 增加删除列
    self.structure_table.setHorizontalHeaderLabels(["类型", "内容", "编辑", "删除"])
    
    # 🆕 内容编辑器提示变量语法
    editor_label = QLabel("内容编辑 (支持变量: ${变量名}):")
    self.content_editor.setPlaceholderText("选择要编辑的段落或表格...\n支持变量语法: ${变量名}")
    
    # 🆕 变量相关按钮和列表
    self.insert_variable_btn = QPushButton("插入变量")
    self.insert_variable_btn.clicked.connect(self.show_variable_selector)
    
    # 🆕 可用变量列表
    variables_label = QLabel("可用变量:")
    self.variables_list = QListWidget()
    self.variables_list.itemDoubleClicked.connect(self.insert_selected_variable)


# ========== 变量使用示例 ==========

# 用户在编辑器中输入：
"""
巡检报告

网站状态：${status_主网站巡检_https___example_com}
响应时间：${response_time_主网站巡检_https___example_com}
用户数量：${extracted_用户数量检查_主网站巡检}

页面截图：${screenshot_主网站巡检_https___example_com}
"""

# 系统自动替换为：
"""
巡检报告

网站状态：成功
响应时间：2.34秒
用户数量：1,234 用户

页面截图：/reports/screenshots/example_com_20250102_143052.png
"""