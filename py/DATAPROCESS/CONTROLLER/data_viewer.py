# -*- coding: utf-8 -*-
"""
数据查看模块
"""

import csv
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QDialog, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QSplitter, QLabel,
                             QAbstractItemView, QComboBox, QTextEdit,
                             QFrame, QListWidget, QListWidgetItem, 
                             QDialogButtonBox, QMessageBox, QDesktopWidget, QWidget,
                             QSizePolicy, QLineEdit, QScrollArea, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QCursor

from SETTINGS import (
    DEFAULT_WINDOW_SIZE, DEFAULT_ENCODING, get_log_directory, ensure_directory_exists,
    get_save_filename, get_open_filenames, get_unique_filename
    )

from DATAPROCESS.FUNCTIONS import (EditableTable,DataConvertDialog,EncodingDialog,
                            ColumnSelectionDialog,StatesLookupWindow,FilterDialog,
                            StatesColumnSelectionDialog,
                            BatchPlotDialog,plot_scatter,SteadyStateDiffDialog,
                            compute_stats_from_selection,compute_diffs,compute_batch_all_results,)
from DATAPROCESS.UI import PlotWindow

class DataViewer(QDialog):
    """数据查看窗口，显示CSV内容并提供数据处理功能"""
    def __init__(self, file_path, parent=None, default_encoding=None):
        super().__init__(parent)
        self.file_path = file_path
        self.encoding = default_encoding if default_encoding else DEFAULT_ENCODING
        self.setWindowTitle(f"数据查看 - {os.path.basename(file_path)}")
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.setAcceptDrops(True)  # 启用拖拽
        self.center()
        
        # 添加快捷键支持
        self.setup_shortcuts()
        
        # 添加修改状态跟踪
        self.modified = False  # 标记文件是否被修改
        
        # 列显示控制相关属性
        self.all_columns_visible = True  # 标记是否显示所有列
        self.visible_columns = set()  # 当前显示的列索引集合
        self.column_mapping = {}  # 显示列索引到原始列索引的映射
        self.original_column_count = 0  # 原始列数
        
        # 防止重复调用的标志
        self.is_converting = False  # 标记是否正在进行数据转换
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 表格显示数据 - 使用可编辑表格
        self.table = EditableTable()
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 连接表格修改信号以跟踪修改状态
        self.table.contentChanged.connect(self.on_content_changed)
        
        # 如果没有指定默认编码，则选择编码
        if not self.encoding:
            if not self.select_encoding():
                # 用户取消了编码选择，直接关闭窗口
                self.reject()
                return
        else:
            # 使用默认编码加载CSV
            if not self.load_csv(file_path):
                # 如果加载失败，让用户重新选择编码
                QMessageBox.critical(self, "错误", f"无法用默认编码({self.encoding})读取文件，请重新选择编码")
                if not self.select_encoding() or not self.load_csv(file_path):
                    self.reject()
                    return
        
        # 功能按钮
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(2, 2, 2, 2)
        btn_layout.setSpacing(3)
        
        # 数据处理按钮
        self.mean_btn = QPushButton("计算均值")
        self.peak_btn = QPushButton("计算峰峰值")
        self.diff_btn = QPushButton("计算差值")  # 添加计算差值按钮
        self.plot_btn = QPushButton("绘制曲线")
        self.batch_plot_btn = QPushButton("批量绘制曲线")  # 添加批量绘制曲线按钮
        self.scatter_btn = QPushButton("绘制散点图")  # 添加散点图按钮
        
        # 添加数据转换按钮
        self.convert_btn = QPushButton("数据进制转换")
        
        # 添加状态变量检测按钮
        self.states_lookup_btn = QPushButton("状态变量检测")
        
        # 添加UID数据处理按钮
        self.uid_analysis_btn = QPushButton("UID数据处理")
        
        # 添加稳态差值计算按钮
        self.steady_state_diff_btn = QPushButton("稳态差值计算")
        
        # 添加保存计算结果按钮
        self.save_calc_result_btn = QPushButton("保存计算结果")
        
        # 添加批量统计量计算结果按钮
        self.batch_calc_result_btn = QPushButton("批量统计量计算")
        
        # 添加筛选按钮
        self.filter_btn = QPushButton("行筛选")
        self.reset_filter_btn = QPushButton("重置筛选")
        
        # 添加筛选条件管理按钮
        self.filter_and_comparison_btn = QPushButton("条件比对筛选")
        
        # 列显示控制按钮
        self.toggle_columns_btn = QPushButton("查看列")

        
        # 表格编辑按钮
        self.save_btn = QPushButton("保存修改")
        
        # 编码按钮
        self.encoding_btn = QPushButton(self.encoding.upper() if self.encoding else "未知编码")
        self.encoding_btn.clicked.connect(self.change_encoding)
        
        btn_layout.addWidget(self.encoding_btn) # 添加编码按钮 
        btn_layout.addSpacing(20)
        btn_layout.addWidget(self.mean_btn) # 添加计算均值按钮 
        btn_layout.addWidget(self.peak_btn) # 添加计算峰峰值按钮 
        btn_layout.addWidget(self.diff_btn) # 添加计算差值按钮 
        btn_layout.addWidget(self.steady_state_diff_btn)  # 添加稳态差值计算按钮
        btn_layout.addWidget(self.save_calc_result_btn)  # 添加保存计算结果按钮
        btn_layout.addWidget(self.batch_calc_result_btn)  # 添加批量统计量计算按钮
        btn_layout.addSpacing(20)
        btn_layout.addWidget(self.convert_btn) # 添加数据转换按钮 
        btn_layout.addSpacing(20)
        btn_layout.addWidget(self.plot_btn) # 添加绘制曲线按钮 
        btn_layout.addWidget(self.batch_plot_btn)  # 添加批量绘制曲线按钮 
        btn_layout.addWidget(self.scatter_btn)  # 添加散点图按钮 
        btn_layout.addWidget(self.states_lookup_btn) # 添加状态变量检测按钮 
        btn_layout.addWidget(self.uid_analysis_btn)  # 添加UID数据处理按钮 
        btn_layout.addSpacing(20)
        btn_layout.addWidget(self.toggle_columns_btn)  # 添加列显示控制按钮 
        btn_layout.addWidget(self.filter_btn)  # 添加筛选按钮 
        btn_layout.addWidget(self.reset_filter_btn)  # 添加重置筛选按钮 
        btn_layout.addWidget(self.filter_and_comparison_btn)  # 添加条件比对筛选按钮 
        btn_layout.addSpacing(20)
        btn_layout.addWidget(self.save_btn)  # 添加保存修改按钮 
        btn_layout.addStretch()
        
        # 右侧按钮区域
        right_widget = QWidget()
        right_widget.setLayout(btn_layout)
        right_widget.setMaximumWidth(150)
        right_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # 分割窗口
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.table)
        splitter.addWidget(right_widget)
        splitter.setSizes([1400, 150])  # 调整分割比例
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        main_layout.addWidget(splitter)
        
        # 状态提示
        self.status_label = QLabel(f"当前编码: {self.encoding} | 提示: 选择数据区域后按Enter计算", self)
        self.status_label.setStyleSheet("color: gray; font-style: italic; padding: 2px;")
        self.status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.status_label.setMaximumHeight(20)
        
        # 创建状态容器
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addWidget(self.status_label)
        
        main_layout.addWidget(status_container)
        
        self.setLayout(main_layout)
        
        # 连接信号
        self.mean_btn.clicked.connect(self.calculate_mean)  # 连接计算均值按钮信号
        self.peak_btn.clicked.connect(self.calculate_peak)  # 连接计算峰峰值按钮信号
        self.save_calc_result_btn.clicked.connect(self.save_calculation_results)  # 连接保存计算结果按钮信号
        self.batch_calc_result_btn.clicked.connect(self.batch_calculate_results)  # 连接批量统计量计算按钮信号
        self.plot_btn.clicked.connect(self.plot_data)  # 连接绘制曲线按钮信号
        self.scatter_btn.clicked.connect(self.plot_scatter)  # 连接散点图按钮信号
        self.diff_btn.clicked.connect(self.calculate_diff)  # 连接计算差值按钮信号
        self.convert_btn.clicked.connect(self.convert_data)  # 连接转换按钮信号
        self.states_lookup_btn.clicked.connect(self.states_lookup)  # 连接状态变量检测按钮信号
        self.uid_analysis_btn.clicked.connect(self.uid_analysis)  # 连接UID数据处理按钮信号
        self.filter_btn.clicked.connect(self.filter_data)  # 连接筛选按钮信号
        self.reset_filter_btn.clicked.connect(self.reset_filter)  # 连接重置筛选按钮信号
        self.filter_and_comparison_btn.clicked.connect(self.filter_and_comparison)  # 连接条件比对筛选按钮信号
        self.batch_plot_btn.clicked.connect(self.batch_plot_data)  # 连接批量绘制曲线按钮信号
        self.steady_state_diff_btn.clicked.connect(self.calculate_steady_state_diff)  # 连接稳态差值计算按钮信号
        self.toggle_columns_btn.clicked.connect(self.toggle_columns)  # 连接列显示控制按钮信号
        self.save_btn.clicked.connect(self.save_to_file)  # 连接保存按钮信号
        self.batch_calc_result_btn.clicked.connect(self.batch_calculate_results)  # 连接批量统计量计算按钮信号
    
    def calculate_steady_state_diff(self):
        """计算稳态差值"""
        # 获取当前所有列名
        column_names = []
        for col in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(col)
            column_names.append(header_item.text() if header_item else f"列{col+1}")
        
        # 创建稳态差值计算对话框
        dialog = SteadyStateDiffDialog(self.table, column_names, self)
        dialog.file_name = os.path.basename(self.file_path)  # 传递文件名用于生成结果文件名
        dialog.exec_()
    
    def batch_plot_data(self):
        """批量绘制选中列的曲线"""
        # 创建并显示批量绘制对话框
        dialog = BatchPlotDialog(self, self)
        dialog.exec_()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.csv'):
                    event.acceptProposedAction()
        super().dragEnterEvent(event)
    
    def dropEvent(self, event: QDropEvent):
        """处理文件拖拽释放事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.csv'):
                    # 创建新的DataViewer窗口来打开拖拽的文件
                    try:
                        viewer = DataViewer(file_path, self.parent(), default_encoding=DEFAULT_ENCODING)
                        viewer.file_path = file_path
                        viewer.show()
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"无法打开文件: {str(e)}")
        super().dropEvent(event)
    
    def center(self):
        """将窗口居中显示"""
        if self.parent():
            # 如果有父窗口，相对于父窗口居中
            parent_geo = self.parent().frameGeometry()
            self.move(
                parent_geo.center().x() - self.width() // 2,
                parent_geo.center().y() - self.height() // 2
            )
        else:
            # 否则相对于屏幕居中
            qr = self.frameGeometry()
            cp = QDesktopWidget().availableGeometry().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())
    
    def setup_shortcuts(self):
        """设置快捷键"""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # Ctrl+S 保存快捷键
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_to_file)
        
    
    def on_content_changed(self):
        """当表格内容被修改时调用"""
        # 检查当前是否已经有修改，如果没有则设置修改标记
        # 如果已经有修改，则仍需要更新标签页标题以确保一致性
        if not self.modified:
            self.modified = True
        
        # 始终更新标签页标题以确保显示正确
        self.update_tab_title()
        
        # 更新状态标签显示
        self.update_status_label()
    
    def update_status_label(self):
        """更新状态标签显示"""
        if self.modified:
            status_text = "未保存"
        else:
            status_text = "已保存修改"
        self.status_label.setText(f"当前编码: {self.encoding} | {status_text} | 提示: 选择数据区域后按Enter计算")
    
    def update_tab_title(self):
        """更新标签页标题"""
        # 获取主窗口引用
        main_window = self.parent()
        if main_window and hasattr(main_window, 'tab_widget'):
            # 查找当前viewer在标签页中的索引
            for i in range(main_window.tab_widget.count()):
                if main_window.tab_widget.widget(i) == self:
                    # 更新标签页标题，使用独立的标签页标题而不是基于文件名
                    if not hasattr(self, 'tab_title'):
                        self.tab_title = os.path.basename(self.file_path)

    def load_csv(self, file_path):
        """使用用户选择的编码加载CSV文件到表格"""
        try:
            with open(file_path, 'r', newline='', encoding=self.encoding, errors='replace') as f:
                reader = csv.reader(f)
                data = list(reader)
                
                if not data:
                    QMessageBox.warning(self, "警告", "CSV文件为空")
                    return False
                
                # 设置表格行列
                self.table.setRowCount(len(data))
                self.table.setColumnCount(len(data[0]) if data[0] else 0)
                
                # 保存原始列数
                self.original_column_count = self.table.columnCount()
                # 初始化可见列集合为所有列
                self.visible_columns = set(range(self.original_column_count))
                # 初始化列映射
                self.column_mapping = {i: i for i in range(self.original_column_count)}
                
                # 填充数据
                for row_idx, row in enumerate(data):
                    for col_idx, item in enumerate(row):
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(item))
                
                # 设置表头
                if self.table.rowCount() > 0 and self.table.columnCount() > 0:
                    header_labels = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(0, col)
                        header_labels.append(item.text() if item else f"列{col+1}")
                    self.table.setHorizontalHeaderLabels(header_labels)
                    self.table.removeRow(0)
                
                return True  # 成功加载
                
        except Exception as e:
            print(f"使用编码 {self.encoding} 读取文件出错: {e}")
            return False
    
    def get_table_data(self):
        """获取表格中所有数据"""
        row_count = self.table.rowCount()
        col_count = self.table.columnCount()
        
        data = []
        # 添加表头
        headers = []
        for col in range(col_count):
            header_item = self.table.horizontalHeaderItem(col)
            headers.append(header_item.text() if header_item else f"列{col+1}")
        data.append(headers)
        
        # 添加数据行
        for row in range(row_count):
            row_data = []
            for col in range(col_count):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        
        return data
    
    def save_to_file(self):
        """将修改后的数据保存回原文件"""
        # 检查是否是新文件（尚未保存过的文件）
        if hasattr(self, 'is_new_file') and self.is_new_file:
            # 新文件使用另存为对话框
            # 使用当前标签页标题作为默认文件名
            default_filename = self.tab_title.rstrip('*') if hasattr(self, 'tab_title') else os.path.basename(self.file_path)
            # 确保文件名以.csv结尾
            if not default_filename.endswith('.csv'):
                default_filename += '.csv'
            
            log_dir = get_log_directory()
            ensure_directory_exists(log_dir)
            default_save_path = os.path.join(log_dir, default_filename)
                
            file_path, _ = get_save_filename(
                self, '保存CSV文件', default_save_path, 'CSV文件 (*.csv);;所有文件 (*)')
            if file_path:
                try:
                    # 获取表格数据
                    data = self.get_table_data()
                    
                    # 如果生成了新的文件路径，提示用户
                    if file_path != file_path:
                        reply = QMessageBox.question(
                            self, 
                            "文件已存在", 
                            f"文件 {os.path.basename(file_path)} 已存在。\n\n是否保存为 {os.path.basename(file_path)}？",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            return  # 用户选择不保存
                    
                    # 写入CSV文件
                    with open(file_path, 'w', newline='', encoding=self.encoding) as f:
                        writer = csv.writer(f)
                        writer.writerows(data)
                    
                    # 更新文件路径和标记
                    old_file_path = self.file_path
                    self.file_path = file_path
                    self.is_new_file = False
                    self.setWindowTitle(f"数据查看 - {os.path.basename(file_path)}")
                    # 重置修改标记
                    
                    # 获取主窗口引用以更新viewers字典
                    # 通过遍历parent链直到找到具有status_bar和viewers属性的对象
                    main_window = None
                    current_parent = self.parent()
                    while current_parent is not None:
                        if hasattr(current_parent, 'status_bar') and hasattr(current_parent, 'viewers'):
                            main_window = current_parent
                            break
                        current_parent = current_parent.parent() if hasattr(current_parent, 'parent') else None
                    
                    if main_window and hasattr(main_window, 'viewers'):
                        # 更新viewers字典
                        if old_file_path in main_window.viewers:
                            main_window.viewers[file_path] = main_window.viewers.pop(old_file_path)
                    
                    # 删除临时文件
                    try:
                        if hasattr(self, 'temp_file_path') and os.path.exists(self.temp_file_path):
                            os.unlink(self.temp_file_path)
                    except Exception as e:
                        print(f"删除临时文件失败: {e}")
                    
                    # 更新标签页标题
                    if main_window and hasattr(main_window, 'tab_widget'):
                        for i in range(main_window.tab_widget.count()):
                            if main_window.tab_widget.widget(i) == self:
                                # 更新标签页标题为保存的文件名（不含*后缀）
                                self.tab_title = os.path.basename(file_path)
                                main_window.tab_widget.setTabText(i, self.tab_title)
                                break
                
                    # 在主窗口状态栏显示保存成功消息
                    if main_window and hasattr(main_window, 'status_bar'):
                        from datetime import datetime
                        current_time = datetime.now().strftime("%H:%M:%S")
                        main_window.status_bar.showMessage(f'保存 {os.path.basename(self.file_path)} 成功 {current_time} @Silver')
                    self.update_status_label()
                except Exception as e:
                    QMessageBox.critical(self, "保存失败", f"保存文件时出错: {str(e)}")
        else:
            # 已有文件直接保存
            if not self.file_path:
                return
            
            try:
                # 获取表格数据
                data = self.get_table_data()
                
                # 写入CSV文件 - 使用self.file_path而不是file_path
                with open(self.file_path, 'w', newline='', encoding=self.encoding) as f:
                    writer = csv.writer(f)
                    writer.writerows(data)
                
                # 获取主窗口引用以更新状态栏
                # 通过遍历parent链直到找到具有status_bar和viewers属性的对象
                main_window = None
                current_parent = self.parent()
                while current_parent is not None:
                    if hasattr(current_parent, 'status_bar') and hasattr(current_parent, 'viewers'):
                        main_window = current_parent
                        break
                    current_parent = current_parent.parent() if hasattr(current_parent, 'parent') else None
                
                if main_window and hasattr(main_window, 'status_bar'):
                    from datetime import datetime
                    current_time = datetime.now().strftime("%H:%M:%S")
                    main_window.status_bar.showMessage(f'保存 {os.path.basename(self.file_path)} 成功 {current_time} @Silver')
                self.update_status_label()
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存文件时出错: {str(e)}")
                
    def get_selected_data(self):
        """获取选中的数值数据，考虑行号作为X轴"""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self, "警告", "请先选择数据区域")
            return None
        
        # 获取行号（作为X轴）- 从1开始而不是从0开始
        row_numbers = []
        for row in range(self.table.rowCount()):
            # 尝试从行标题获取，如果没有则使用行索引+1
            header_item = self.table.verticalHeaderItem(row)
            if header_item and header_item.text():
                try:
                    row_numbers.append(float(header_item.text()))
                except ValueError:
                    row_numbers.append(row + 1)  # 从1开始
            else:
                row_numbers.append(row + 1)  # 从1开始
        
        # 按列组织数据（不再检查是否包含表头，因为表头已经被移除）
        columns = {}
        for rg in selected_ranges:
            for col in range(rg.leftColumn(), rg.rightColumn() + 1):
                # 检查列是否可见
                if self.table.isColumnHidden(col):
                    continue
                    
                if col not in columns:
                    columns[col] = {
                        'x_data': [],
                        'y_data': [],
                        'label': self.table.horizontalHeaderItem(col).text() if self.table.horizontalHeaderItem(col) else f"列{col+1}"
                    }
                
                for row in range(rg.topRow(), rg.bottomRow() + 1):
                    # 检查行是否可见
                    if self.table.isRowHidden(row):
                        continue
                        
                    # 获取X值（行号）
                    try:
                        x_val = float(row_numbers[row])
                    except:
                        x_val = row + 1  # 从1开始
                    
                    # 获取Y值
                    item = self.table.item(row, col)
                    if item:
                        try:
                            y_val = float(item.text())
                            columns[col]['x_data'].append(x_val)
                            columns[col]['y_data'].append(y_val)
                        except (ValueError, TypeError):
                            pass  # 跳过非数值
        
        # 检查是否有有效数据
        valid_columns = {col: data for col, data in columns.items() if data['y_data']}
        if not valid_columns:
            QMessageBox.warning(self, "警告", "选区中没有有效数值数据\n请确保选择的列包含数值数据，或先使用数据进制转换功能")
            return None
        
        return valid_columns
    
    def calculate_mean(self):
        """计算均值（支持多列）"""
        data = self.get_selected_data()
        if data is None:
            return

        stats = compute_stats_from_selection(data)
        if not stats:
            QMessageBox.warning(self, "警告", "未找到可计算的数据")
            return

        results = []
        for col, info in stats.items():
            results.append(f"{info['label']} (列 {col+1}): 均值 = {info['mean']:.4f} (共 {info['count']} 个点)")

        QMessageBox.information(self, "均值计算结果", "\n".join(results))
    
    def calculate_peak(self):
        """计算峰峰值（支持多列）"""
        data = self.get_selected_data()
        if data is None:
            return

        stats = compute_stats_from_selection(data)
        if not stats:
            QMessageBox.warning(self, "警告", "未找到可计算的数据")
            return

        results = []
        for col, info in stats.items():
            results.append(f"{info['label']} (列 {col+1}): 峰峰值 = {info['peak']:.4f} (共 {info['count']} 个点)")

        QMessageBox.information(self, "峰峰值计算结果", "\n".join(results))
    
    def plot_data(self):
        """绘制选中数据的曲线（支持多条曲线）"""
        data = self.get_selected_data()
        if data is None or len(data) == 0:
            QMessageBox.warning(self, "警告", "需要至少1个数据列才能绘制曲线")
            return
        
        # 为每条曲线准备数据
        x_data_dict = {}
        y_data_dict = {}
        labels = {}
        for col, curve_data in data.items():
            x_data_dict[col] = np.array(curve_data['x_data'])
            y_data_dict[col] = np.array(curve_data['y_data'])
            labels[col] = curve_data['label']
        
        # 始终使用独立窗口方式创建曲线窗口
        title = f"曲线图 - {os.path.basename(self.file_path)}"
        self.plot_window = PlotWindow()  # 不再传递父窗口
        self.plot_window.plot_multiple(x_data_dict, y_data_dict, labels, title)
        # 设置默认保存文件名与导入文件名一致
        self.plot_window.set_default_filename(os.path.basename(self.file_path))
        self.plot_window.show()
    
    def convert_data(self):
        """数据进制转换功能"""
        # 检查是否正在进行转换
        if self.is_converting:
            return
            
        # 设置转换标志
        self.is_converting = True
        
        try:
            # 检查是否有选中的单元格
            selected_items = self.table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "警告", "请先选择要转换的数据列")
                return
            
            # 获取选中的列
            selected_columns = set()
            for item in selected_items:
                selected_columns.add(item.column())
            
            # 检查是否只选择了一列
            if len(selected_columns) != 1:
                QMessageBox.warning(self, "警告", "请只选择一列数据进行转换")
                return
            
            selected_col = list(selected_columns)[0]
            
            # 创建转换对话框
            dialog = DataConvertDialog(self.table, selected_col, self)
            dialog.exec_()
        finally:
            # 重置转换标志
            self.is_converting = False
    
    def calculate_diff(self):
        """计算两列差值"""
        # 获取选中的单元格
        selected_items = self.table.selectedItems()

        # 检查是否有选中单元格
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择两列数据进行差值计算")
            return

        # 获取按选择顺序排列的列索引
        selected_columns = []
        seen_columns = set()
        
        for item in selected_items:
            col = item.column()
            if col not in seen_columns:
                selected_columns.append(col)
                seen_columns.add(col)
        
        # 检查是否选择了两列
        if len(selected_columns) != 2:
            QMessageBox.warning(self, "警告", f"请选择两列数据进行差值计算（当前选择了{len(selected_columns)}列）")
            return
        
        # 按照选择顺序确定被减数和减数列
        # 先选中的为被减数(第一个)，后选中的为减数(第二个)
        col1 = selected_columns[0]  # 被减数列
        col2 = selected_columns[1]  # 减数列
        
        # 获取列标题
        header1_item = self.table.horizontalHeaderItem(col1)
        header1_text = header1_item.text() if header1_item else f"列{col1+1}"
        
        header2_item = self.table.horizontalHeaderItem(col2)
        header2_text = header2_item.text() if header2_item else f"列{col2+1}"
        
        # 计算差值并添加新列 (先选中的列 - 后选中的列)
        self.add_diff_column(col1, col2, header1_text, header2_text)
        
        QMessageBox.information(self, "成功", "差值计算完成")
    
    def add_diff_column(self, col1, col2, header1_text, header2_text):
        """添加差值列"""
        # 获取当前列数
        current_col_count = self.table.columnCount()
        
        # 插入新列
        self.table.insertColumn(current_col_count)
        
        # 设置新列标题
        diff_header = f"{header1_text}-{header2_text}差值"
        header_item = QTableWidgetItem(diff_header)
        self.table.setHorizontalHeaderItem(current_col_count, header_item)
        # 收集两列文本值并计算差值（委托给calculate模块）
        col1_vals = []
        col2_vals = []
        for row in range(self.table.rowCount()):
            item1 = self.table.item(row, col1)
            col1_vals.append(item1.text().strip() if item1 else "")
            item2 = self.table.item(row, col2)
            col2_vals.append(item2.text().strip() if item2 else "")

        diffs = compute_diffs(col1_vals, col2_vals)
        for row_idx, diff in enumerate(diffs):
            if diff is None:
                diff_item = QTableWidgetItem("")
            else:
                diff_item = QTableWidgetItem(str(diff))
            self.table.setItem(row_idx, current_col_count, diff_item)

        # 触发内容修改信号
        self.table.contentChanged.emit()
    
    def change_encoding(self):
        """更改文件编码"""
        dialog = EncodingDialog(self.file_path, self)
        
        if dialog.exec_() == QDialog.Accepted:
            new_encoding = dialog.get_selected_encoding()
            old_encoding = self.encoding
            self.encoding = new_encoding
            
            # 更新编码按钮文本
            self.encoding_btn.setText(self.encoding.upper())
            
            # 重新加载文件
            if not self.load_csv(self.file_path):
                QMessageBox.critical(self, "错误", f"无法用新编码({self.encoding})读取文件")
                # 恢复原编码
                self.encoding = old_encoding
                self.encoding_btn.setText(self.encoding.upper() if self.encoding else DEFAULT_ENCODING.upper())
                return
            
            # 更新状态标签
            self.update_status_label()

    def toggle_columns(self):
        """切换列显示模式"""
        if self.all_columns_visible:
            self.select_columns()
        else:
            self.show_all_columns()

    def select_columns(self):
        """选择要显示的列"""
        # 获取当前所有列名（使用表格中的实际列数）
        column_names = []
        for col in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(col)
            column_names.append(header_item.text() if header_item else f"列{col+1}")
        
        # 创建列选择对话框
        dialog = ColumnSelectionDialog(column_names, self.visible_columns, self)
        
        if dialog.exec_() == QDialog.Accepted:
            selected_columns = dialog.get_selected_columns()
            
            if not selected_columns:
                QMessageBox.warning(self, "警告", "至少需要选择一列")
                return
            
            # 更新可见列
            self.visible_columns = selected_columns
            self.update_column_display()
            
            # 更新按钮文本
            self.all_columns_visible = False
            self.toggle_columns_btn.setText("查看全部")

    def show_all_columns(self):
        """显示所有列"""
        # 修改为显示当前表格中的所有列，而不是仅原始列数
        self.visible_columns = set(range(self.table.columnCount()))
        self.update_column_display()
        
        # 更新按钮文本
        self.all_columns_visible = True
        self.toggle_columns_btn.setText("查看列")

    def update_column_display(self):
        """更新表格列显示"""
        # 隐藏所有列
        for col in range(self.table.columnCount()):
            self.table.setColumnHidden(col, True)
        
        # 显示选中的列
        for col in self.visible_columns:
            if col < self.table.columnCount():
                self.table.setColumnHidden(col, False)

    def states_lookup(self):
        """状态变量检测功能"""
        # 获取表头信息
        headers = []
        for col in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(col)
            headers.append(header_item.text() if header_item else f"列{col+1}")
        
        # 弹出列选择对话框，让用户选择状态变量列和传感器值列
        dialog = StatesColumnSelectionDialog(headers, self)
        
        if dialog.exec_() == QDialog.Accepted:
            state_column = dialog.state_column
            sensor_column = dialog.sensor_column
            
            # 获取所有数据
            data = []
            # 添加表头
            header_row = []
            for col in range(self.table.columnCount()):
                header_item = self.table.horizontalHeaderItem(col)
                header_row.append(header_item.text() if header_item else f"列{col+1}")
            data.append(header_row)
            
            # 添加数据行
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # 创建并显示状态变量检测窗口，传递原始文件路径
            try:
                states_window = StatesLookupWindow(data, state_column, sensor_column, self, self.file_path)
                states_window.show()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法创建状态变量检测窗口: {str(e)}")

    def uid_analysis(self):
        """执行UID数据分析"""
        # 导入UID数据处理器对话框
        from DATAPROCESS.FUNCTIONS import UIDDataProcessorDialog
        
        # 创建并显示UID数据处理对话框
        dialog = UIDDataProcessorDialog(self, self)
        dialog.exec_()

    def filter_data(self):
        """数据筛选功能"""
        # 创建筛选对话框
        dialog = FilterDialog(self.table, self)
        if dialog.exec_() == QDialog.Accepted:
            # 获取筛选条件
            filters = dialog.get_filters()
            
            # 应用筛选
            self.apply_filters(filters)
    
    def apply_filters(self, filters):
        """应用筛选条件"""
        if not filters:
            # 如果没有筛选条件，显示所有行
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
            return
        
        # 遍历所有行，检查是否满足筛选条件 
        for row in range(self.table.rowCount()):
            hide_row = False
            
            # 检查每个筛选条件
            for col, filter_text in filters.items():
                if filter_text:  # 如果筛选条件不为空
                    item = self.table.item(row, col)
                    cell_text = item.text() if item else ""
                    
                    # 如果单元格内容不包含筛选文本，则隐藏该行
                    if filter_text not in cell_text:
                        hide_row = True
                        break
            
            # 根据筛选结果隐藏或显示行
            self.table.setRowHidden(row, hide_row)

    def reset_filter(self):
        """重置筛选，显示所有行"""
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)
        # 清除筛选条件
        from DATAPROCESS.FUNCTIONS.filter_comparison import FilterDialog
        FilterDialog.global_filters = {}

    def get_selected_columns(self):
        """获取当前选中的列索引"""
        selected_columns = set()
        selected_ranges = self.table.selectedRanges()
        for rg in selected_ranges:
            for col in range(rg.leftColumn(), rg.rightColumn() + 1):
                # 检查列是否可见
                if not self.table.isColumnHidden(col):
                    selected_columns.add(col)
        return selected_columns

    def plot_scatter(self):
        """
        调用独立的散点图分析模块绘制散点图
        """
        self.scatter_window = plot_scatter(self)

    def filter_and_comparison(self):
        """筛选与对比"""
        # 导入筛选条件管理对话框
        from DATAPROCESS.FUNCTIONS import FilterComparisonDialog
        
        # 创建并显示筛选条件管理对话框
        dialog = FilterComparisonDialog(self, self)
        # 仅显示对话框，功能由对话框内部实现
        dialog.exec_()

    def batch_calculate_results(self):
        """批量统计量计算多个文件的结果"""
        # 获取当前选中的数据
        data = self.get_selected_data()
        if data is None:
            return

        # 获取选中列的信息
        selected_columns = {}
        for col, values in data.items():
            selected_columns[col] = values['label']

        # 选择其他CSV文件
        file_paths, _ = get_open_filenames(
            self,
            "选择要批量统计量计算的CSV文件",
            os.path.dirname(self.file_path),
            "CSV文件 (*.csv)"
        )

        if not file_paths:
            return

        # 委托计算模块计算所有文件的统计量
        all_results = compute_batch_all_results(self.file_path, data, file_paths, selected_columns, encoding=self.encoding)

        # 获取log目录路径并确保目录存在
        log_dir = get_log_directory()
        ensure_directory_exists(log_dir)

        # 生成文件名，带有时间戳
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"批量统计量计算结果-{timestamp}.txt"
        file_path = os.path.join(log_dir, file_name)

        # 写入结果到文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入列信息
                separator = '" "'
                f.write(f"选择列为:\"{separator.join(all_results['column_names'])}\"，共{len(all_results['column_names'])}列\n")

                # 写入文件数量信息
                f.write(f"\n共处理{len(all_results['files'])}个文件\n")

                # 写入均值
                f.write("\n均值：\n")
                for file_info in all_results['files']:
                    mean_values = []
                    for col_name in all_results['column_names']:
                        if col_name in file_info['results']:
                            mean_values.append(f"{file_info['results'][col_name]['mean']:.2f}")
                        else:
                            mean_values.append("N/A")
                    f.write(f"{file_info['name']} {' '.join(mean_values)}\n")

                # 写入峰峰值
                f.write("\n峰峰值：\n")
                for file_info in all_results['files']:
                    peak_values = []
                    for col_name in all_results['column_names']:
                        if col_name in file_info['results']:
                            peak_values.append(f"{file_info['results'][col_name]['peak']:.2f}")
                        else:
                            peak_values.append("N/A")
                    f.write(f"{file_info['name']} {' '.join(peak_values)}\n")

            QMessageBox.information(self, "批量统计量计算完成", f"批量统计量计算结果已保存到: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存文件时出错:\n{str(e)}")

    def save_calculation_results(self):
        """保存计算结果（均值和峰峰值）到txt文件"""
        data = self.get_selected_data()
        if data is None:
            return
        # 使用计算模块计算均值和峰峰值
        stats = compute_stats_from_selection(data)
        results = {}
        for col, info in stats.items():
            results[col] = {
                'label': info.get('label', ''),
                'mean': info.get('mean', 0.0),
                'peak': info.get('peak', 0.0)
            }

        # 获取log目录路径并确保目录存在
        log_dir = get_log_directory()
        ensure_directory_exists(log_dir)

        # 生成文件名
        base_name = os.path.splitext(os.path.basename(self.file_path))[0]
        file_name = f"{base_name}-计算结果.txt"
        file_path = os.path.join(log_dir, file_name)
        
        # 处理重名文件
        unique_file_path = get_unique_filename(file_path)

        # 写入文件
        try:
            with open(unique_file_path, 'w', encoding='utf-8') as f:
                # 写入列信息
                column_names = [values['label'] for values in data.values()]
                separator = '" "'
                f.write(f"选择列为:\"{separator.join(column_names)}\"，共{len(data)}列\n")
                
                # 写入均值（保留2位小数）
                mean_values = [f"{values['mean']:.2f}" for values in results.values()]
                f.write(f"\n均值：{' '.join(mean_values)}\n")
                
                # 写入峰峰值（保留2位小数）
                peak_values = [f"{values['peak']:.2f}" for values in results.values()]
                f.write(f"\n峰峰值：{' '.join(peak_values)}\n")
                
            QMessageBox.information(self, "保存成功", f"计算结果已保存到: {unique_file_path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存文件时出错:\n{str(e)}")