# -*- coding: utf-8 -*-
"""
稳态差值计算模块
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QMessageBox, QListWidget, 
                             QListWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt

from SETTINGS.paths import get_log_directory, ensure_directory_exists


class SteadyStateDiffDialog(QDialog):
    """稳态差值计算对话框"""
    def __init__(self, table, column_names, parent=None):
        super().__init__(parent)
        self.table = table
        self.column_names = column_names
        self.setWindowTitle("稳态差值计算")
        self.setModal(True)
        self.resize(400, 500)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 说明标签
        label = QLabel("请选择需要计算稳态差值的列（可多选）:")
        layout.addWidget(label)
        
        # 列表控件
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        
        # 添加列名到列表
        for i, name in enumerate(self.column_names):
            item = QListWidgetItem(f"{name} (列 {i+1})")
            item.setData(Qt.UserRole, i)  # 存储列索引
            self.list_widget.addItem(item)
        
        layout.addWidget(self.list_widget)
        
        # 稳态0点数输入
        layout.addWidget(QLabel("稳态0点数（从第1行向下计数）:"))
        self.steady0_count_edit = QLineEdit()
        self.steady0_count_edit.setText("10")  # 默认值
        layout.addWidget(self.steady0_count_edit)
        
        # 稳态1点数输入
        layout.addWidget(QLabel("稳态1点数（从最后行向上计数）:"))
        self.steady1_count_edit = QLineEdit()
        self.steady1_count_edit.setText("20")  # 默认取20个点
        layout.addWidget(self.steady1_count_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.calculate_btn = QPushButton("计算稳态差值")
        self.cancel_btn = QPushButton("取消")
        self.calculate_btn.clicked.connect(self.calculate_steady_state_diff)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.calculate_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def calculate_steady_state_diff(self):
        """计算稳态差值"""
        try:
            # 获取选中的列
            selected_items = self.list_widget.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "警告", "请至少选择一列进行计算")
                return
            
            selected_columns = [item.data(Qt.UserRole) for item in selected_items]
            
            # 获取稳态点数
            try:
                steady0_count = int(self.steady0_count_edit.text())
                steady1_count = int(self.steady1_count_edit.text())
                
                if steady0_count <= 0 or steady1_count <= 0:
                    QMessageBox.warning(self, "警告", "稳态点数必须大于0")
                    return
            except ValueError:
                QMessageBox.warning(self, "警告", "请输入有效的稳态点数")
                return
            
            # 计算每列的稳态差值
            results = []
            row_count = self.table.rowCount()
            
            if steady0_count + steady1_count > row_count:
                QMessageBox.warning(self, "警告", "稳态点数之和不能超过总行数")
                return
            
            for col in selected_columns:
                # 获取列数据
                column_data = []
                for row in range(row_count):
                    item = self.table.item(row, col)
                    if item and item.text():
                        try:
                            value = float(item.text())
                            column_data.append(value)
                        except ValueError:
                            # 跳过非数值数据
                            pass
                
                if len(column_data) == 0:
                    results.append({
                        'column': col,
                        'column_name': self.column_names[col] if col < len(self.column_names) else f"列{col+1}",
                        'error': '该列没有有效数据'
                    })
                    continue
                
                # 计算稳态0（前steady0_count个点）
                steady0_data = column_data[:steady0_count]
                steady0_avg = sum(steady0_data) / len(steady0_data)
                steady0_min = min(steady0_data)
                steady0_max = max(steady0_data)
                steady0_pp = steady0_max - steady0_min
                
                # 计算稳态1（后steady1_count个点）
                steady1_data = column_data[-steady1_count:]
                steady1_avg = sum(steady1_data) / len(steady1_data)
                steady1_min = min(steady1_data)
                steady1_max = max(steady1_data)
                steady1_pp = steady1_max - steady1_min
                
                # 计算差值
                diff = steady1_avg - steady0_avg
                
                results.append({
                    'column': col,
                    'column_name': self.column_names[col] if col < len(self.column_names) else f"列{col+1}",
                    'steady0_avg': steady0_avg,
                    'steady0_pp': steady0_pp,
                    'steady1_avg': steady1_avg,
                    'steady1_pp': steady1_pp,
                    'diff': diff
                })
            
            # 保存结果到txt文件
            self.save_results_to_file(results, steady0_count, steady1_count)
            
            # 显示成功消息
            QMessageBox.information(self, "成功", f"稳态差值计算完成，结果已保存到log目录")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"计算过程中发生错误: {str(e)}")
    
    def save_results_to_file(self, results, steady0_count, steady1_count):
        """将计算结果保存到txt文件"""
        try:
            # 获取log目录路径并确保目录存在
            log_dir = get_log_directory()
            ensure_directory_exists(log_dir)
            
            # 生成文件名
            base_name = getattr(self.parent(), 'file_name', 'data')
            if base_name.endswith('.csv'):
                base_name = base_name[:-4]
            file_name = f"{base_name}-稳态差值.txt"
            file_path = os.path.join(log_dir, file_name)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("稳态差值计算结果\n")
                f.write("=" * 50 + "\n")
                f.write(f"稳态0点数: {steady0_count}\n")
                f.write(f"稳态1点数: {steady1_count}\n")
                f.write("=" * 50 + "\n\n")
                
                for result in results:
                    f.write(f"列: {result['column_name']} (列 {result['column']+1})\n")
                    if 'error' in result:
                        f.write(f"  错误: {result['error']}\n")
                    else:
                        f.write(f"  稳态0均值: {result['steady0_avg']:.6f}\n")
                        f.write(f"  稳态0峰峰值: {result['steady0_pp']:.6f}\n")
                        f.write(f"  稳态1均值: {result['steady1_avg']:.6f}\n")
                        f.write(f"  稳态1峰峰值: {result['steady1_pp']:.6f}\n")
                        f.write(f"  稳态差值(稳态1均值-稳态0均值): {result['diff']:.6f}\n")
                    f.write("\n")
        except Exception as e:
            raise Exception(f"保存文件时出错: {str(e)}")