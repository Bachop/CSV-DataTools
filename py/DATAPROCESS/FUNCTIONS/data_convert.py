# -*- coding: utf-8 -*-
"""
数据转换模块
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QMessageBox, QTableWidgetItem)


class DataConvertDialog(QDialog):
    """数据转换对话框"""
    def __init__(self, table, selected_col, parent=None):
        super().__init__(parent)
        self.table = table
        self.selected_col = selected_col
        self.setWindowTitle("数据进制转换")
        self.setModal(True)
        self.resize(400, 250)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 获取选中列的信息
        header_item = self.table.horizontalHeaderItem(self.selected_col)
        header_text = header_item.text() if header_item else f"列{self.selected_col+1}"
        
        # 说明标签
        label = QLabel(f"将对第{self.selected_col+1}列: {header_text} 进行转换")
        layout.addWidget(label)
        
        # # 转换模式选择
        # layout.addWidget(QLabel("转换模式:"))
        # self.convert_mode = QComboBox()
        # self.convert_mode.addItems(["普通模式", "CAN模式"])
        # layout.addWidget(self.convert_mode)
        
        # 源进制和目标进制
        layout.addWidget(QLabel("源进制:"))
        self.source_base = QComboBox()
        self.source_base.addItems(["2进制", "4进制", "8进制", "10进制", "16进制"])
        self.source_base.setCurrentText("16进制")  # 设置默认选中16进制
        layout.addWidget(self.source_base)
        
        layout.addWidget(QLabel("目标进制:"))
        self.target_base = QComboBox()
        self.target_base.addItems(["2进制", "4进制", "8进制", "10进制", "16进制"])
        self.target_base.setCurrentText("10进制")  # 默认转换为10进制
        layout.addWidget(self.target_base)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("开始转换")
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self.convert)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def convert(self):
        """执行转换操作"""
        try:
            # # 获取转换模式
            # mode = self.convert_mode.currentText()
            
            # 获取源进制和目标进制
            base_map = {"2进制": 2, "4进制": 4, "8进制": 8, "10进制": 10, "16进制": 16}
            source_base = base_map.get(self.source_base.currentText(), 16)
            target_base = base_map.get(self.target_base.currentText(), 10)
            
            # 获取当前列数
            current_col_count = self.table.columnCount()
            
            # 为转换结果添加新列
            # 每行数据会被拆分为多个值，我们先处理第一行来确定需要多少新列
            sample_item = self.table.item(0, self.selected_col)
            if not sample_item:
                QMessageBox.warning(self, "警告", "选中列无数据")
                return
                
            sample_data = sample_item.text().strip()
            values = sample_data.split()

            new_columns_needed = len(values)
            
            # # 根据模式确定新列数
            # if mode == "CAN模式":
            #     # 检查是否是偶数个值
            #     if len(values) % 2 != 0:
            #         QMessageBox.warning(self, "警告", "数据不是偶数个，无法两两组合")
            #         return
            #     new_columns_needed = len(values) // 2
            # else:  # 正常模式
            #     new_columns_needed = len(values)
            
            # 添加新列
            for i in range(new_columns_needed):
                self.table.insertColumn(current_col_count + i)
                header_item = QTableWidgetItem(f"转换列{self.selected_col+1}_{i+1}")
                self.table.setHorizontalHeaderItem(current_col_count + i, header_item)
            
            # 对每一行进行转换
            for row in range(self.table.rowCount()):
                item = self.table.item(row, self.selected_col)
                if not item:
                    continue
                    
                data = item.text().strip()
                if not data:
                    continue
                    
                values = data.split()

                converted_values = []

                for value in values:
                    try:
                        decimal_val = int(value, source_base)
                        # 转换为目标进制
                        if target_base == 2:
                            converted_val = bin(decimal_val)[2:]  # 去掉'0b'前缀
                        elif target_base == 8:
                            converted_val = oct(decimal_val)[2:]  # 去掉'0o'前缀
                        elif target_base == 16:
                            converted_val = hex(decimal_val)[2:].upper()  # 去掉'0x'前缀并转为大写
                        else:  # target_base == 10
                            converted_val = str(decimal_val)
                        converted_values.append(converted_val)
                    except ValueError:
                        converted_values.append("0")  # 转换失败时默认为0
                
                # # 根据模式处理数据
                # if mode == "CAN模式":
                #     # 确保有偶数个值
                #     if len(values) % 2 != 0:
                #         continue  # 跳过无效行
                # converted_values = []
                
                # if mode == "CAN模式":
                #     # 两两组合并转换
                #     for i in range(0, len(values), 2):
                #         # 组合两个值（高位在前）
                #         try:
                #             # 先转换为十进制
                #             high_val = int(values[i], source_base)
                #             low_val = int(values[i+1], source_base)
                #             # 组合成16位值（高8位+低8位）
                #             combined_val = (high_val << 8) + low_val
                #             # 转换为目标进制
                #             if target_base == 2:
                #                 converted_val = bin(combined_val)[2:]  # 去掉'0b'前缀
                #             elif target_base == 8:
                #                 converted_val = oct(combined_val)[2:]  # 去掉'0o'前缀
                #             elif target_base == 16:
                #                 converted_val = hex(combined_val)[2:].upper()  # 去掉'0x'前缀并转为大写
                #             else:  # target_base == 10
                #                 converted_val = str(combined_val)
                #             converted_values.append(converted_val)
                #         except ValueError:
                #             converted_values.append("0")  # 转换失败时默认为0
                # else:  # 正常模式
                #     # 直接转换每个值
                #     for value in values:
                #         try:
                #             decimal_val = int(value, source_base)
                #             # 转换为目标进制
                #             if target_base == 2:
                #                 converted_val = bin(decimal_val)[2:]  # 去掉'0b'前缀
                #             elif target_base == 8:
                #                 converted_val = oct(decimal_val)[2:]  # 去掉'0o'前缀
                #             elif target_base == 16:
                #                 converted_val = hex(decimal_val)[2:].upper()  # 去掉'0x'前缀并转为大写
                #             else:  # target_base == 10
                #                 converted_val = str(decimal_val)
                #             converted_values.append(converted_val)
                #         except ValueError:
                #             converted_values.append("0")  # 转换失败时默认为0
                
                # 将转换结果写入新列
                for i, converted_val in enumerate(converted_values):
                    new_item = QTableWidgetItem(converted_val)
                    self.table.setItem(row, current_col_count + i, new_item)
            
            # 发射内容变化信号，通知数据已修改
            self.table.contentChanged.emit()
            
            QMessageBox.information(self, "成功", f"转换完成，新增{new_columns_needed}列")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"转换过程中发生错误: {str(e)}")
        finally:
            # 无论成功与否都关闭对话框
            self.accept()  # 接受对话框并关闭窗口