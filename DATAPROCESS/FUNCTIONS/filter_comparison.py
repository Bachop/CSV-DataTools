# -*- coding: utf-8 -*-
"""
筛选条件保存与对比模块
提供保存筛选结果和基于筛选条件对比数据的功能
"""

import sys
import os
import csv
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,QFileDialog,
                             QPushButton, QLabel, QLineEdit, QTextEdit, QTableWidgetItem,
                             QMessageBox, QGroupBox, QListWidget, QListWidgetItem,
                             QCheckBox, QComboBox, QApplication,QTableWidget,QAbstractItemView)
from PyQt5.QtCore import Qt

# 导入路径工具函数
from SETTINGS import get_log_directory, ensure_directory_exists


class FilterComparisonDialog(QDialog):
    """筛选条件保存与对比对话框"""
    
    def __init__(self, data_viewer, parent=None):
        super().__init__(parent)
        self.data_viewer = data_viewer
        self.filter_records = []  # 存储筛选记录
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("筛选条件管理")
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        # 添加说明标签
        info_label = QLabel("筛选条件管理功能：\n"
                           "1. 保存筛选条件：将当前筛选后的数据保存为筛选条件文件\n"
                           "2. 对比特定筛选：导入筛选条件文件，对比数据表中的匹配项")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        self.save_filter_btn = QPushButton("保存筛选条件")
        self.save_filter_btn.clicked.connect(self.save_filter_conditions)
        
        self.compare_filter_btn = QPushButton("对比特定筛选")
        self.compare_filter_btn.clicked.connect(self.compare_filter_conditions)
        
        button_layout.addWidget(self.save_filter_btn)
        button_layout.addWidget(self.compare_filter_btn)
        
        layout.addLayout(button_layout)
        
        # 显示筛选记录的表格
        self.records_table = QTableWidget()
        self.records_table.setColumnCount(3)
        self.records_table.setHorizontalHeaderLabels(["日期", "时间", "UID序列号"])
        self.records_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.records_table)
        
        self.setLayout(layout)
    
    def save_filter_conditions(self):
        """保存当前筛选条件到CSV文件"""
        # 检查是否有数据
        if self.data_viewer.table.rowCount() == 0:
            QMessageBox.warning(self, "警告", "当前没有数据可以保存")
            return
        
        # 获取可见行数据
        visible_rows = []
        for row in range(self.data_viewer.table.rowCount()):
            if not self.data_viewer.table.isRowHidden(row):
                visible_rows.append(row)
        
        if not visible_rows:
            QMessageBox.warning(self, "警告", "当前没有可见数据可以保存")
            return
        
        # 检查列数是否足够
        if self.data_viewer.table.columnCount() < 4:
            QMessageBox.warning(self, "警告", "数据列数不足，至少需要4列")
            return
        
        # 提取第2列(日期)、第3列(时间)、第4列(UID)的数据
        filter_data = []
        headers = ["日期", "时间", "UID序列号"]  # 对应第2、3、4列的列名
        filter_data.append(headers)
        
        for row in visible_rows:
            row_data = []
            # 第2列(索引1)为日期
            date_item = self.data_viewer.table.item(row, 1)
            date_value = date_item.text() if date_item else ""
            
            # 第3列(索引2)为时间
            time_item = self.data_viewer.table.item(row, 2)
            time_value = time_item.text() if time_item else ""
            
            # 第4列(索引3)为UID序列号
            uid_item = self.data_viewer.table.item(row, 3)
            uid_value = uid_item.text() if uid_item else ""
            
            row_data.extend([date_value, time_value, uid_value])
            filter_data.append(row_data)
        
        # 确定保存路径
        base_name = os.path.splitext(os.path.basename(self.data_viewer.file_path))[0]
        file_name = f"{base_name}-筛选.csv"
        
        # 获取Log目录路径
        log_dir = get_log_directory()
        ensure_directory_exists(log_dir)
        
        save_path = os.path.join(log_dir, file_name)
        
        # 保存为CSV文件
        try:
            with open(save_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(filter_data)
            
            QMessageBox.information(self, "保存成功", f"筛选条件已保存到: {save_path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存筛选条件时出错: {str(e)}")
    
    def compare_filter_conditions(self):
        """对比特定筛选条件"""
        # 选择筛选条件文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择筛选条件文件', '', 'CSV文件 (*.csv);;所有文件 (*)')
        
        if not file_path:
            return
        
        # 读取筛选条件文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                records = list(reader)
                
            if len(records) < 2:  # 至少需要标题行和一行数据
                QMessageBox.warning(self, "警告", "筛选条件文件数据不足")
                return
                
            # 跳过标题行，保存筛选记录
            self.filter_records = records[1:]  # 保存除标题行外的所有记录
            
            # 显示筛选记录
            self.show_filter_records(records[0], self.filter_records)
            
            # 在当前数据表中查找匹配行
            self.apply_filter_comparison()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取筛选条件文件时出错: {str(e)}")
    
    def show_filter_records(self, headers, records):
        """在表格中显示筛选记录"""
        self.records_table.clear()
        self.records_table.setRowCount(len(records))
        self.records_table.setColumnCount(len(headers))
        self.records_table.setHorizontalHeaderLabels(headers)
        
        for row_idx, row_data in enumerate(records):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(cell_data)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 设置为不可编辑
                self.records_table.setItem(row_idx, col_idx, item)
        
        self.records_table.resizeColumnsToContents()
    
    def apply_filter_comparison(self):
        """应用筛选条件对比，隐藏不匹配的行"""
        if not self.filter_records:
            return
        
        # 检查当前表格列数
        if self.data_viewer.table.columnCount() < 4:
            QMessageBox.warning(self, "警告", "当前数据表列数不足，无法进行对比")
            return
        
        # 遍历所有行，检查是否匹配筛选条件
        matched_count = 0
        for row in range(self.data_viewer.table.rowCount()):
            # 获取当前行的第2、3、4列数据（日期、时间、UID）
            date_item = self.data_viewer.table.item(row, 1)
            time_item = self.data_viewer.table.item(row, 2)
            uid_item = self.data_viewer.table.item(row, 3)
            
            date_value = date_item.text() if date_item else ""
            time_value = time_item.text() if time_item else ""
            uid_value = uid_item.text() if uid_item else ""
            
            # 检查是否匹配任一筛选记录
            matched = False
            for record in self.filter_records:
                # record格式: [日期, 时间, UID]
                if len(record) >= 3 and (date_value, time_value, uid_value) == (record[0], record[1], record[2]):
                    matched = True
                    matched_count += 1
                    break
            
            # 根据匹配结果隐藏或显示行
            self.data_viewer.table.setRowHidden(row, not matched)
        
        QMessageBox.information(self, "筛选完成", f"筛选完成，找到 {matched_count} 条匹配记录")