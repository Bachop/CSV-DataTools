# -*- coding: utf-8 -*-
"""
批量绘制曲线模块
用于批量绘制选中列的曲线图并添加参考线
"""

import os
import sys
import csv
import numpy as np
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QMessageBox, QProgressDialog,
                             QApplication, QRadioButton, 
                             QButtonGroup, QGroupBox, QCheckBox, QScrollArea,
                             QWidget)
from PyQt5.QtCore import Qt

# 导入项目常量
from SETTINGS import (
    get_pic_directory, ensure_directory_exists, get_unique_filename, get_open_filenames
)

from DATAPROCESS.UI import PlotWindow


class FilterDialog(QDialog):
    """筛选对话框"""
    
    def __init__(self, table, parent=None):
        super().__init__(parent)
        self.table = table
        self.filters = {}  # 存储筛选条件
        self.setWindowTitle("设置筛选条件")
        self.setModal(True)
        self.resize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 创建滚动区域以容纳所有列的筛选输入框
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # 为每列创建筛选输入框
        self.filter_inputs = {}
        for col in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(col)
            header_text = header_item.text() if header_item else f"列{col+1}"
            
            # 创建水平布局放置列名和输入框
            h_layout = QHBoxLayout()
            h_layout.addWidget(QLabel(f"{header_text}:"))
            
            # 创建输入框并设置默认值（如果已有筛选条件）
            line_edit = QLineEdit()
            if col in self.filters:
                line_edit.setText(self.filters[col])
            self.filter_inputs[col] = line_edit
            h_layout.addWidget(line_edit)
            
            scroll_layout.addLayout(h_layout)
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        self.clear_button = QPushButton("清空")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.clear_button.clicked.connect(self.clear_filters)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_filters(self):
        """获取筛选条件"""
        filters = {}
        for col, line_edit in self.filter_inputs.items():
            text = line_edit.text().strip()
            if text:  # 只返回非空的筛选条件
                filters[col] = text
        return filters
    
    def clear_filters(self):
        """清空所有筛选条件"""
        for line_edit in self.filter_inputs.values():
            line_edit.clear()


class CrossFileBatchPlotDialog(QDialog):
    """跨文件批量绘制曲线对话框"""
    
    def __init__(self, data_viewer, selected_columns, parent=None):
        super().__init__(parent)
        self.data_viewer = data_viewer
        self.selected_columns = selected_columns
        self.file_paths = []
        self.file_names = []
        self.filters = {}  # 存储筛选条件
        self.filtered_rows = {}  # 存储每个文件的筛选后行索引
        self.setWindowTitle("跨文件批量绘制曲线")
        self.setModal(True)
        self.resize(500, 300)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 文件选择区域
        file_group = QGroupBox("选择文件")
        file_layout = QVBoxLayout()
        
        # 说明标签
        info_label = QLabel("请选择要对比的CSV文件（当前文件已自动包含）：")
        info_label.setWordWrap(True)
        file_layout.addWidget(info_label)
        
        # 文件选择按钮
        self.select_files_btn = QPushButton("选择文件")
        self.select_files_btn.clicked.connect(self.select_files)
        file_layout.addWidget(self.select_files_btn)
        
        # 已选择文件列表
        self.files_label = QLabel("已选择文件: 无")
        self.files_label.setWordWrap(True)
        file_layout.addWidget(self.files_label)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 行筛选条件
        filter_group = QGroupBox("行筛选条件")
        filter_layout = QVBoxLayout()
        
        filter_info = QLabel("请设置行筛选条件（可选）：")
        filter_layout.addWidget(filter_info)
        
        # 行筛选按钮
        self.filter_btn = QPushButton("设置筛选条件")
        self.filter_btn.clicked.connect(self.set_filters)
        filter_layout.addWidget(self.filter_btn)
        
        # 显示已设置的筛选条件
        self.filter_display = QLabel("当前筛选条件: 无")
        self.filter_display.setWordWrap(True)
        filter_layout.addWidget(self.filter_display)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 参考值设置
        ref_group = QGroupBox("参考线设置")
        ref_layout = QVBoxLayout()
        
        # 上限输入
        upper_layout = QHBoxLayout()
        upper_layout.addWidget(QLabel("上限值:"))
        self.upper_input = QLineEdit()
        self.upper_input.setPlaceholderText("可选，输入数字")
        upper_layout.addWidget(self.upper_input)
        ref_layout.addLayout(upper_layout)
        
        # 下限输入
        lower_layout = QHBoxLayout()
        lower_layout.addWidget(QLabel("下限值:"))
        self.lower_input = QLineEdit()
        self.lower_input.setPlaceholderText("可选，输入数字")
        lower_layout.addWidget(self.lower_input)
        ref_layout.addLayout(lower_layout)
        
        # 参考值输入
        ref_val_layout = QHBoxLayout()
        ref_val_layout.addWidget(QLabel("参考值:"))
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("可选，多个值用逗号分隔，如: 10,20,30")
        ref_val_layout.addWidget(self.ref_input)
        ref_layout.addLayout(ref_val_layout)
        
        ref_group.setLayout(ref_layout)
        layout.addWidget(ref_group)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def select_files(self):
        """选择文件"""
        file_paths, _ = get_open_filenames(
            self,
            "选择要对比的CSV文件",
            os.path.dirname(self.data_viewer.file_path),
            "CSV Files (*.csv)"
        )
        
        if file_paths:
            # 添加当前文件到文件列表开头
            self.file_paths = [self.data_viewer.file_path] + file_paths
            self.file_names = [os.path.splitext(os.path.basename(fp))[0] for fp in self.file_paths]
            self.files_label.setText(f"已选择文件: {', '.join(self.file_names)}")
        else:
            self.file_paths = []
            self.file_names = []
            self.files_label.setText("已选择文件: 无")
    
    def get_reference_values(self):
        """获取参考值设置"""
        upper_limit = None
        lower_limit = None
        reference_values = []
        
        # 获取上限值
        upper_text = self.upper_input.text().strip()
        if upper_text:
            try:
                upper_limit = float(upper_text)
            except ValueError:
                QMessageBox.warning(self, "输入错误", "上限值必须是有效的数字")
                return None, None, None
        
        # 获取下限值
        lower_text = self.lower_input.text().strip()
        if lower_text:
            try:
                lower_limit = float(lower_text)
            except ValueError:
                QMessageBox.warning(self, "输入错误", "下限值必须是有效的数字")
                return None, None, None
        
        # 获取参考值
        ref_text = self.ref_input.text().strip()
        if ref_text:
            try:
                reference_values = [float(x.strip()) for x in ref_text.split(',') if x.strip()]
            except ValueError:
                QMessageBox.warning(self, "输入错误", "参考值必须是用逗号分隔的有效数字")
                return None, None, None
        
        return upper_limit, lower_limit, reference_values
    
    def set_filters(self):
        """设置筛选条件"""
        # 创建筛选对话框
        if self.file_paths:
            # 使用当前DataViewer的表结构创建筛选对话框
            filter_dialog = FilterDialog(self.data_viewer.table, self)
            # 设置已有的筛选条件
            filter_dialog.filters = self.filters
            # 更新输入框的默认值
            for col, filter_text in self.filters.items():
                if col in filter_dialog.filter_inputs:
                    filter_dialog.filter_inputs[col].setText(filter_text)
            
            if filter_dialog.exec_() == QDialog.Accepted:
                # 获取筛选条件
                self.filters = filter_dialog.get_filters()
                # 更新显示
                if self.filters:
                    filter_text = ", ".join([f"列{col+1}:{text}" for col, text in self.filters.items()])
                    self.filter_display.setText(f"当前筛选条件: {filter_text}")
                else:
                    self.filter_display.setText("当前筛选条件: 无")
        else:
            QMessageBox.warning(self, "警告", "请先选择文件")
    
    def apply_filters_to_file(self, file_path):
        """对指定文件应用筛选条件"""
        try:
            # 读取CSV文件
            with open(file_path, 'r', encoding=self.data_viewer.encoding, newline='') as f:
                reader = csv.reader(f)
                data_rows = list(reader)
            
            if len(data_rows) <= 1:
                return []
            
            header_row = data_rows[0]
            data_rows = data_rows[1:]  # 移除标题行
            
            # 如果没有筛选条件，返回所有行索引
            if not self.filters:
                return list(range(len(data_rows)))
            
            # 应用筛选条件
            visible_rows = []
            for row_idx, row in enumerate(data_rows):
                hide_row = False
                
                # 检查每个筛选条件
                for col, filter_text in self.filters.items():
                    if filter_text:  # 如果筛选条件不为空
                        if col < len(row):
                            cell_text = row[col]
                            # 如果单元格内容不包含筛选文本，则隐藏该行
                            if filter_text not in cell_text:
                                hide_row = True
                                break
                
                # 如果不隐藏该行，则添加到可见行列表
                if not hide_row:
                    visible_rows.append(row_idx)
            
            return visible_rows
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用筛选条件到文件 {file_path} 时出错: {str(e)}")
            return list(range(len(data_rows))) if 'data_rows' in locals() else []
    
    def accept(self):
        """确认按钮处理"""
        if not self.file_paths:
            QMessageBox.warning(self, "警告", "请先选择要对比的文件")
            return
        
        upper_limit, lower_limit, reference_values = self.get_reference_values()
        if upper_limit is False:  # 表示有错误
            return
        
        # 执行跨文件批量绘制
        self.cross_file_batch_plot(upper_limit, lower_limit, reference_values)
        super().accept()
    
    def cross_file_batch_plot(self, upper_limit, lower_limit, reference_values):
        """执行跨文件批量绘制"""
        if not self.selected_columns:
            QMessageBox.warning(self, "警告", "没有选中的列")
            return
        
        # 获取pic目录路径
        pic_dir = get_pic_directory()
        if not pic_dir:
            return
        
        # 为每个文件应用筛选条件
        self.filtered_rows = {}
        for file_idx, file_path in enumerate(self.file_paths):
            self.filtered_rows[file_idx] = self.apply_filters_to_file(file_path)
        
        # 创建进度对话框
        total_tasks = len(self.selected_columns)
        progress = QProgressDialog("正在跨文件批量绘制曲线...", "取消", 0, total_tasks, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("跨文件批量绘制进度")
        
        # 为每个选中列绘制曲线（跨文件对比）
        for i, col in enumerate(self.selected_columns):
            if progress.wasCanceled():
                break
            
            progress.setValue(i)
            QApplication.processEvents()  # 处理UI事件
            
            try:
                # 获取列名
                header_item = self.data_viewer.table.horizontalHeaderItem(col)
                col_name = header_item.text() if header_item else f"列{col+1}"
                
                # 准备数据
                x_data_dict = {}
                y_data_dict = {}
                labels = {}
                
                # 从每个文件中读取数据
                for file_idx, file_path in enumerate(self.file_paths):
                    # 读取CSV文件
                    with open(file_path, 'r', encoding=self.data_viewer.encoding, newline='') as f:
                        reader = csv.reader(f)
                        data_rows = list(reader)
                    
                    # 跳过标题行
                    if len(data_rows) <= 1:
                        continue
                    
                    header_row = data_rows[0]
                    data_rows = data_rows[1:]  # 移除标题行
                    
                    # 提取指定列的数据（仅处理筛选后的可见行）
                    y_data = []
                    x_data = []
                    
                    # 只处理筛选后的可见行
                    visible_rows = self.filtered_rows.get(file_idx, list(range(len(data_rows))))
                    for row_idx in visible_rows:
                        if row_idx < len(data_rows):
                            row = data_rows[row_idx]
                            # 检查行是否在当前DataViewer中被隐藏（仅对当前文件有效）
                            if col < len(row) and row[col].strip():
                                try:
                                    y_data.append(float(row[col].strip()))
                                    # 使用行号作为X轴值（从1开始）
                                    x_data.append(row_idx + 1)
                                except ValueError:
                                    # 跳过非数值数据
                                    pass
                    
                    if y_data:
                        x_data_dict[file_idx] = x_data
                        y_data_dict[file_idx] = y_data
                        labels[file_idx] = self.file_names[file_idx]
                
                if not y_data_dict:
                    continue
                
                # 创建绘图窗口
                plot_win = PlotWindow(self)
                plot_win.plot_multiple(x_data_dict, y_data_dict, labels)
                
                # 设置参考值
                plot_win.upper_limit = upper_limit
                plot_win.lower_limit = lower_limit
                plot_win.reference_values = reference_values
                
                # 重新绘制以显示参考线
                plot_win.redraw_plots()
                
                # 保存图片
                image_name = f"跨文件对比_{col_name}.png"
                image_path = os.path.join(pic_dir, image_name)
                # 使用新的避免覆盖的文件名函数
                unique_image_path = get_unique_filename(image_path)
                plot_win.figure1.savefig(unique_image_path, dpi=300, bbox_inches='tight')
                
                # 关闭绘图窗口
                plot_win.close()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"绘制列 {col_name} 时出错: {str(e)}")
        
        progress.setValue(total_tasks)
        QMessageBox.information(self, "完成", f"跨文件批量绘制完成，图片已保存到: {pic_dir}")
    



class BatchPlotDialog(QDialog):
    """批量绘制曲线对话框"""
    
    def __init__(self, data_viewer, parent=None):
        super().__init__(parent)
        self.data_viewer = data_viewer
        self.selected_columns = self.get_selected_columns()
        self.setWindowTitle("批量绘制曲线")
        self.setModal(True)
        self.resize(400, 200)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout()
        
        # 添加选择模式（文件内或跨文件）
        mode_group = QGroupBox("选择绘制模式")
        mode_layout = QVBoxLayout()
        
        self.in_file_radio = QRadioButton("文件内批量绘制")
        self.cross_file_radio = QRadioButton("跨文件批量绘制")
        self.in_file_radio.setChecked(True)
        
        mode_layout.addWidget(self.in_file_radio)
        mode_layout.addWidget(self.cross_file_radio)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # 说明标签
        info_label = QLabel("请输入参考线参数，将为每个选中的列单独绘制曲线图：")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 创建输入参数的网格布局
        grid_layout = QHBoxLayout()
        
        # 上限输入
        upper_layout = QVBoxLayout()
        upper_layout.addWidget(QLabel("上限值:"))
        self.upper_input = QLineEdit()
        self.upper_input.setPlaceholderText("可选，输入数字")
        upper_layout.addWidget(self.upper_input)
        
        # 下限输入
        lower_layout = QVBoxLayout()
        lower_layout.addWidget(QLabel("下限值:"))
        self.lower_input = QLineEdit()
        self.lower_input.setPlaceholderText("可选，输入数字")
        lower_layout.addWidget(self.lower_input)
        
        # 参考值输入
        ref_layout = QVBoxLayout()
        ref_layout.addWidget(QLabel("参考值:"))
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("可选，多个值用逗号分隔，如: 10,20,30")
        ref_layout.addWidget(self.ref_input)
        
        # 将三个输入区域添加到水平布局中
        grid_layout.addLayout(upper_layout)
        grid_layout.addLayout(lower_layout)
        grid_layout.addLayout(ref_layout)
        
        # 将水平布局添加到主布局
        layout.addLayout(grid_layout)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_selected_columns(self):
        """获取选中的列索引"""
        selected_columns = set()
        ranges = self.data_viewer.table.selectedRanges()
        for range_ in ranges:
            for col in range(range_.leftColumn(), range_.rightColumn() + 1):
                # 检查列是否可见（筛选后）
                if not self.data_viewer.table.isColumnHidden(col):
                    selected_columns.add(col)
        return sorted(list(selected_columns))
    
    def get_reference_values(self):
        """获取参考值设置"""
        upper_limit = None
        lower_limit = None
        reference_values = []
        
        # 获取上限值
        upper_text = self.upper_input.text().strip()
        if upper_text:
            try:
                upper_limit = float(upper_text)
            except ValueError:
                QMessageBox.warning(self, "输入错误", "上限值必须是有效的数字")
                return None, None, None
        
        # 获取下限值
        lower_text = self.lower_input.text().strip()
        if lower_text:
            try:
                lower_limit = float(lower_text)
            except ValueError:
                QMessageBox.warning(self, "输入错误", "下限值必须是有效的数字")
                return None, None, None
        
        # 获取参考值
        ref_text = self.ref_input.text().strip()
        if ref_text:
            try:
                reference_values = [float(x.strip()) for x in ref_text.split(',') if x.strip()]
            except ValueError:
                QMessageBox.warning(self, "输入错误", "参考值必须是用逗号分隔的有效数字")
                return None, None, None
        
        return upper_limit, lower_limit, reference_values
    
    def accept(self):
        """确认按钮处理"""
        upper_limit, lower_limit, reference_values = self.get_reference_values()
        if upper_limit is False:  # 表示有错误
            return
        
        # 根据选择的模式执行不同的批量绘制
        if self.in_file_radio.isChecked():
            # 执行文件内批量绘制
            self.batch_plot(upper_limit, lower_limit, reference_values)
        else:
            # 执行跨文件批量绘制
            if not self.selected_columns:
                QMessageBox.warning(self, "警告", "请先选择要绘制的列")
                return
            
            # 创建跨文件批量绘制对话框
            cross_file_dialog = CrossFileBatchPlotDialog(self.data_viewer, self.selected_columns, self)
            cross_file_dialog.exec_()
        
        super().accept()
    
    def batch_plot(self, upper_limit, lower_limit, reference_values):
        """执行文件内批量绘制"""
        if not self.selected_columns:
            QMessageBox.warning(self, "警告", "请先选择要绘制的列")
            return

        # 获取文件名（不含扩展名）
        file_name = os.path.splitext(os.path.basename(self.data_viewer.file_path))[0]

        # 获取pic目录路径
        pic_dir = get_pic_directory()
        if not pic_dir:
            return

        # 创建进度对话框
        progress = QProgressDialog("正在批量绘制曲线...", "取消", 0, len(self.selected_columns), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("批量绘制进度")

        # 为每个选中列绘制曲线
        for i, col in enumerate(self.selected_columns):
            if progress.wasCanceled():
                break

            progress.setValue(i)
            QApplication.processEvents()  # 处理UI事件

            try:
                plot_data = self._prepare_plot_data(col)
                if not plot_data["y_data"]:
                    continue

                # 创建绘图窗口并绘制数据
                plot_win = self._create_and_plot_graph(
                    plot_data["x_data"], 
                    plot_data["y_data"], 
                    plot_data["col_name"],
                    upper_limit, 
                    lower_limit, 
                    reference_values
                )

                # 保存图片
                image_name = f"{file_name}_{plot_data['col_name']}.png"
                image_path = os.path.join(pic_dir, image_name)
                # 使用新的避免覆盖的文件名函数
                unique_image_path = get_unique_filename(image_path)
                plot_win.figure1.savefig(unique_image_path, dpi=300, bbox_inches='tight')

                # 关闭绘图窗口
                plot_win.close()

            except Exception as e:
                col_name = plot_data["col_name"] if "plot_data" in locals() else f"列{col+1}"
                QMessageBox.critical(self, "错误", f"绘制列 {col_name} 时出错: {str(e)}")

        progress.setValue(len(self.selected_columns))
        QMessageBox.information(self, "完成", f"批量绘制完成，图片已保存到: {pic_dir}")

    def _prepare_plot_data(self, col):
        """准备绘图数据"""
        # 获取列名
        header_item = self.data_viewer.table.horizontalHeaderItem(col)
        col_name = header_item.text() if header_item else f"列{col + 1}"

        # 生成X轴数据（行号）
        y_data = []
        x_data = []
        for row in range(self.data_viewer.table.rowCount()):
            # 检查行是否可见（筛选后）
            if self.data_viewer.table.isRowHidden(row):
                continue

            item = self.data_viewer.table.item(row, col)
            if item and item.text():
                try:
                    y_data.append(float(item.text()))
                    # 使用行号作为X轴值（从1开始）
                    x_data.append(row + 1)
                except ValueError:
                    # 跳过非数值数据
                    pass

        return {
            "x_data": x_data,
            "y_data": y_data,
            "col_name": col_name
        }

    def _create_and_plot_graph(self, x_data, y_data, col_name, upper_limit, lower_limit, reference_values):
        """创建图表窗口并绘制图形"""
        # 创建绘图窗口
        plot_win = PlotWindow(self)
        
        # 准备绘图数据
        x_data_dict = {0: x_data}  # 使用0作为唯一键
        y_data_dict = {0: y_data}
        labels = {0: col_name}

        # 绘制数据
        plot_win.plot_multiple(x_data_dict, y_data_dict, labels)

        # 设置参考值
        plot_win.upper_limit = upper_limit
        plot_win.lower_limit = lower_limit
        plot_win.reference_values = reference_values

        # 重新绘制以显示参考线
        plot_win.redraw_plots()
        
        return plot_win
        
        progress.setValue(len(self.selected_columns))
        QMessageBox.information(self, "完成", f"批量绘制完成，图片已保存到: {pic_dir}")
