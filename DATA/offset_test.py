"""
offset_test.py

这是一个用于比较标准文件与待测文件之间数据偏移程度的Python脚本。
核心功能是根据列6的值（0、1、-）将数据分为三类，分别计算列7-列23数据与标准文件对应类别的MAE。

使用方法:
1. 导入标准文件和多个待测文件
2. 点击偏移检测按钮进行分析
3. 结果将保存到txt文件中
"""

import numpy as np
import os
import csv
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLabel)
from PyQt5.QtCore import Qt

class OffsetTestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("偏移检测工具")
        self.resize(1000, 600)
        
        self.standard_file = None
        self.test_files = []
        self.standard_data = {}
        self.test_data = {}
        
        self.init_ui()
    
    def init_ui(self):
        # 主布局
        layout = QVBoxLayout()
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        
        self.standard_btn = QPushButton("选择标准文件")
        self.standard_btn.clicked.connect(self.select_standard_file)
        file_layout.addWidget(self.standard_btn)
        
        self.test_btn = QPushButton("选择待测文件(可多选)")
        self.test_btn.clicked.connect(self.select_test_files)
        file_layout.addWidget(self.test_btn)
        
        self.detect_btn = QPushButton("偏移检测")
        self.detect_btn.clicked.connect(self.offset_detection)
        self.detect_btn.setEnabled(False)
        file_layout.addWidget(self.detect_btn)
        
        file_layout.addStretch()
        
        # 文件信息显示
        self.file_info_label = QLabel("请先选择标准文件和待测文件")
        layout.addWidget(self.file_info_label)
        
        # 数据显示表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["文件名", "类别", "数据点数", "MAE", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        layout.addLayout(file_layout)
        self.setLayout(layout)
    
    def select_standard_file(self):
        """选择标准文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择标准文件", "", "CSV文件 (*.csv);;所有文件 (*)")
        
        if file_path:
            self.standard_file = file_path
            self.update_file_info()
            self.check_ready_for_detection()
    
    def select_test_files(self):
        """选择待测文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择待测文件", "", "CSV文件 (*.csv);;所有文件 (*)")
        
        if file_paths:
            self.test_files = file_paths
            self.update_file_info()
            self.check_ready_for_detection()
    
    def update_file_info(self):
        """更新文件信息显示"""
        info_text = ""
        if self.standard_file:
            info_text += f"标准文件: {os.path.basename(self.standard_file)}\n"
        if self.test_files:
            info_text += f"待测文件数量: {len(self.test_files)}\n"
            for i, file in enumerate(self.test_files):
                info_text += f"  {i+1}. {os.path.basename(file)}\n"
        
        self.file_info_label.setText(info_text)
    
    def check_ready_for_detection(self):
        """检查是否可以进行偏移检测"""
        self.detect_btn.setEnabled(bool(self.standard_file and self.test_files))
    
    def load_csv_data(self, file_path):
        """加载CSV文件数据"""
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    # 确保每行至少有23列
                    if len(row) >= 23:
                        data.append(row)
            return data
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件 {file_path} 失败: {str(e)}")
            return None
    
    def classify_data(self, data):
        """根据列6的值将数据分类"""
        classified = {'0': [], '1': [], '-': []}
        
        # 跳过表头行
        for row in data[1:]:  # 假设第一行是表头
            if len(row) >= 23:
                # 获取第6列的值（索引为5）
                col6_value = row[5].strip() if row[5] else ''
                
                # 根据第6列的值分类
                if col6_value in ['0', '1', '-']:
                    # 提取第7-23列的数据（索引为6-22）
                    row_data = []
                    for i in range(6, 23):  # 第7列到第23列
                        try:
                            row_data.append(float(row[i]) if row[i] else 0.0)
                        except ValueError:
                            row_data.append(0.0)  # 如果无法转换为浮点数，则使用0.0
                    classified[col6_value].append(row_data)
        
        return classified
    
    def calculate_mae(self, standard_data, test_data):
        """计算平均绝对误差(MAE)"""
        if len(standard_data) == 0 or len(test_data) == 0:
            return float('inf')  # 如果没有数据，返回无穷大
        
        # 转换为numpy数组
        std_array = np.array(standard_data)
        test_array = np.array(test_data)
        
        # 计算每个数据点的MAE
        errors = np.abs(std_array - test_array)
        mae = np.mean(errors)
        
        return mae
    
    def offset_detection(self):
        """执行偏移检测"""
        # 清空表格
        self.table.setRowCount(0)
        
        # 加载标准文件数据
        standard_raw_data = self.load_csv_data(self.standard_file)
        if standard_raw_data is None:
            return
        
        # 分类标准文件数据
        self.standard_data = self.classify_data(standard_raw_data)
        
        # 为每个待测文件进行检测
        results = []
        for test_file in self.test_files:
            # 加载待测文件数据
            test_raw_data = self.load_csv_data(test_file)
            if test_raw_data is None:
                continue
            
            # 分类待测文件数据
            test_classified_data = self.classify_data(test_raw_data)
            
            # 对每个类别计算MAE
            file_result = {
                'file_name': os.path.basename(test_file),
                'categories': {}
            }
            
            row_position = self.table.rowCount()
            for category in ['0', '1', '-']:
                std_data = self.standard_data[category]
                test_data = test_classified_data[category]
                
                # 添加到表格
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QTableWidgetItem(os.path.basename(test_file)))
                self.table.setItem(row_position, 1, QTableWidgetItem(category))
                self.table.setItem(row_position, 2, QTableWidgetItem(f"{len(test_data)}"))
                
                if len(std_data) > 0 and len(test_data) > 0:
                    # 为了计算MAE，需要确保数据长度一致，取较短的长度
                    min_len = min(len(std_data), len(test_data))
                    std_data_truncated = std_data[:min_len]
                    test_data_truncated = test_data[:min_len]
                    
                    mae = self.calculate_mae(std_data_truncated, test_data_truncated)
                    file_result['categories'][category] = mae
                    self.table.setItem(row_position, 3, QTableWidgetItem(f"{mae:.6f}"))
                    self.table.setItem(row_position, 4, QTableWidgetItem("完成"))
                else:
                    file_result['categories'][category] = float('inf')
                    self.table.setItem(row_position, 3, QTableWidgetItem("无数据"))
                    self.table.setItem(row_position, 4, QTableWidgetItem("无匹配数据"))
                
                row_position += 1
            
            results.append(file_result)
        
        # 保存结果到txt文件
        self.save_results_to_txt(results)
        QMessageBox.information(self, "完成", "偏移检测完成，结果已保存到result.txt文件中")
    
    def save_results_to_txt(self, results):
        """将结果保存到txt文件"""
        try:
            with open('result.txt', 'w', encoding='utf-8') as f:
                f.write("偏移检测结果报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"标准文件: {os.path.basename(self.standard_file)}\n")
                f.write(f"待测文件数量: {len(self.test_files)}\n\n")
                
                for result in results:
                    f.write(f"待测文件: {result['file_name']}\n")
                    for category in ['0', '1', '-']:
                        mae = result['categories'].get(category, float('inf'))
                        if mae == float('inf'):
                            f.write(f"  类别 {category}: 无匹配数据\n")
                        else:
                            f.write(f"  类别 {category}: MAE = {mae:.6f}\n")
                    f.write("\n")
            
            print("结果已保存到result.txt文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存结果失败: {str(e)}")


def main():
    """主函数"""
    import sys
    app = QApplication(sys.argv)
    dialog = OffsetTestDialog()
    dialog.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()