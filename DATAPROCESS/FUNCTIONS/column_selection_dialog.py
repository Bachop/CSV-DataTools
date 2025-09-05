# -*- coding: utf-8 -*-
"""
列选择模块
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem, 
                             QDialogButtonBox, QAbstractItemView)
from PyQt5.QtCore import Qt


class ColumnSelectionDialog(QDialog):
    """列选择对话框"""
    def __init__(self, column_names, selected_columns=None, parent=None):
        super().__init__(parent)
        self.column_names = column_names
        self.selected_columns = selected_columns or set(range(len(column_names)))
        self.setWindowTitle("选择要显示的列")
        self.setModal(True)
        self.resize(300, 600)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 说明标签
        label = QLabel("请选择要显示的列（可多选）:")
        layout.addWidget(label)
        
        # 列表控件
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        
        # 添加列名到列表
        for i, name in enumerate(self.column_names):
            item = QListWidgetItem(f"{name} (列 {i+1})")
            item.setData(Qt.UserRole, i)  # 存储列索引
            if i in self.selected_columns:
                item.setSelected(True)
            self.list_widget.addItem(item)
        
        layout.addWidget(self.list_widget)
        
        # 全选/全不选按钮
        select_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.select_none_btn = QPushButton("全不选")
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_none_btn.clicked.connect(self.select_none)
        select_layout.addWidget(self.select_all_btn)
        select_layout.addWidget(self.select_none_btn)
        layout.addLayout(select_layout)
        
        # 确定/取消按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def select_all(self):
        """全选所有列"""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(True)
    
    def select_none(self):
        """取消选择所有列"""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(False)
    
    def get_selected_columns(self):
        """获取选中的列索引集合"""
        selected_items = self.list_widget.selectedItems()
        return {item.data(Qt.UserRole) for item in selected_items}