# -*- coding: utf-8 -*-
"""
UID序列号数据分析模块
用于处理特定格式的数据文件，计算同一序列号下不同状态数据的差值
"""

import sys
import os
import csv
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLabel, 
                             QMessageBox, QDesktopWidget)

# 导入路径工具函数
from SETTINGS import get_log_directory, ensure_directory_exists, get_unique_filename


class UIDDataProcessor:
    """
    UID序列号数据处理器
    处理特定格式的数据文件，计算同一序列号下状态0和状态1数据的差值
    """
    
    def __init__(self, table_data, headers):
        """
        初始化数据处理器
        
        Args:
            table_data: 二维列表，表示表格数据
            headers: 列表，表示表头
        """
        self.table_data = table_data
        self.headers = headers
        
    def process_uid_data(self):
        """
        处理UID序列号数据，计算差值并生成新数据
        
        数据格式要求:
        - 第4列(索引3)为UID序列号
        - 第6列(索引5)为状态变量(0或1)
        - 第7-23列(索引6-22)为状态下的数据
        
        处理逻辑:
        1. 按UID分组数据
        2. 对每个UID，找出最后一个状态0和最后一个状态1对应的数据行
        3. 计算状态1数据减去状态0数据的差值
        4. 在每个UID数据组后插入新行存储差值
        
        Returns:
            tuple: (processed_data, headers) 处理后的数据和表头
        """
        if len(self.headers) < 23:  # 确保有足够的列数
            raise ValueError("数据列数不足，至少需要23列")
            
        # 按UID分组数据
        uid_groups = {}
        for row in self.table_data:
            if len(row) > 3:
                uid = row[3]  # 第4列为UID
                if uid not in uid_groups:
                    uid_groups[uid] = []
                uid_groups[uid].append(row)
        
        # 处理每个UID组
        processed_data = []
        for uid, rows in uid_groups.items():
            # 查找最后一个状态0和状态1的行
            last_state0_row = None
            last_state1_row = None
            
            for row in rows:
                if len(row) > 5:
                    try:
                        state = int(row[5])  # 第6列为状态
                        if state == 0:
                            last_state0_row = row
                        elif state == 1:
                            last_state1_row = row
                    except (ValueError, IndexError):
                        # 状态列不是有效数字，跳过
                        pass
            
            # 如果找到了状态0和状态1的行，则添加这些行和差值行
            if last_state0_row and last_state1_row:
                # 添加状态0和状态1的行
                processed_data.append(last_state0_row)
                processed_data.append(last_state1_row)
                
                # 创建差值行
                diff_row = self._calculate_diff_row(last_state0_row, last_state1_row, last_state1_row)
                processed_data.append(diff_row)
        
        return processed_data, self.headers
    
    def _calculate_diff_row(self, state0_row, state1_row, reference_row):
        """
        计算差值行
        
        Args:
            state0_row: 状态0的数据行
            state1_row: 状态1的数据行
            reference_row: 参考行，用于复制前几列的数据
            
        Returns:
            list: 差值行数据
        """
        # 创建新行，基于参考行
        diff_row = reference_row[:]
        
        # 设置第1列元素为"Diff"
        if len(diff_row) > 0:
            diff_row[0] = "Diff"
        
        # 设置第6列元素为"-"
        if len(diff_row) > 5:
            diff_row[5] = "-"
        
        # 计算第7-23列(索引6-22)的差值 (状态1 - 状态0)
        for i in range(6, min(23, len(state0_row), len(state1_row))):
            try:
                val0 = float(state0_row[i]) if state0_row[i] else 0
                val1 = float(state1_row[i]) if state1_row[i] else 0
                diff_row[i] = str(val1 - val0)
            except (ValueError, IndexError):
                # 如果无法转换为数值，保持原值或设为空
                diff_row[i] = ""
        
        return diff_row


class UIDDataProcessorDialog(QDialog):
    """UID数据处理对话框"""
    
    def __init__(self, data_viewer, parent=None):
        """
        初始化对话框
        
        Args:
            data_viewer: DataViewer实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.data_viewer = data_viewer
        self.setWindowTitle("UID数据处理")
        self.setModal(True)
        self.resize(300, 150)
        self._center()
        self.setup_ui()
    
    def _center(self):
        """将窗口居中显示"""
        if self.parent():
            parent_geo = self.parent().frameGeometry()
            self.move(
                parent_geo.center().x() - self.width() // 2,
                parent_geo.center().y() - self.height() // 2
            )
        else:
            qr = self.frameGeometry()
            cp = QDesktopWidget().availableGeometry().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 说明标签
        info_label = QLabel("此功能将处理UID序列号数据:\n"
                           "1. 按第4列(UID)分组数据\n"
                           "2. 计算每个UID下最后状态1行与最后状态0行的差值\n"
                           "3. 在每个UID组后插入差值行\n"
                           "4. 自动保存到log文件夹，文件名为[原文件名]-diff.csv")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 处理按钮
        self.process_btn = QPushButton("处理并自动保存")
        self.process_btn.clicked.connect(self.process_and_save)
        layout.addWidget(self.process_btn)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        self.setLayout(layout)
    
    def process_and_save(self):
        """处理数据并保存为新文件"""
        try:
            # 修改：增加类型判断，支持列表或DataViewer对象
            if isinstance(self.data_viewer, list):
                table_data = self.data_viewer
            else:
                table_data = self.data_viewer.get_table_data()
            
            # 获取表头（第一行）
            headers = table_data[0]
            
            # 获取数据（从第二行开始）
            data_rows = table_data[1:]
            
            # 处理数据
            processor = UIDDataProcessor(data_rows, headers)
            processed_data, processed_headers = processor.process_uid_data()
            
            # 创建log文件夹（如果不存在）
            log_dir = get_log_directory()
            ensure_directory_exists(log_dir)
            
            # 生成文件名：原文件名-diff.csv
            if hasattr(self.data_viewer, 'file_path') and self.data_viewer.file_path:
                original_filename = os.path.basename(self.data_viewer.file_path)
                name_without_ext = os.path.splitext(original_filename)[0]
                file_name = f"{name_without_ext}-diff.csv"
            else:
                file_name = "processed_data-diff.csv"
                
            file_path = os.path.join(log_dir, file_name)
            # 使用新的避免覆盖的文件名函数
            unique_file_path = get_unique_filename(file_path)
            
            # 保存为新文件
            with open(unique_file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(processed_headers)
                writer.writerows(processed_data)
            
            QMessageBox.information(self, "成功", f"数据已处理并保存到: {unique_file_path}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理数据时出错: {str(e)}")
