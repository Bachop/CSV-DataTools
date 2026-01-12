# -*- coding: utf-8 -*-
"""
绘图窗口模块
"""

import numpy as np
import matplotlib as mpl
import os
import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QLabel, QFrame, QSplitter, QDesktopWidget,
                             QWidget, QSizePolicy, QLineEdit, QFormLayout,QMessageBox)
from PyQt5.QtCore import Qt, QEvent, QPoint
from PyQt5.QtGui import QCursor
import platform

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from SETTINGS import (DEFAULT_WINDOW_SIZE, DEFAULT_DPI,
                      get_pic_directory, ensure_directory_exists,
                      get_save_in_pic, bind_toolbar_save
                      )
from SETTINGS import get_unique_filename

class PlotWindow(QDialog):
    """用于显示曲线的窗口，实现基本的曲线显示和交互功能"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据曲线分析")
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.center()
        
        # 初始化数据变量
        self.x_data_dict = {}
        self.y_data_dict = {}
        self.labels = {}
        
        # 初始化状态变量
        self.drag_start_x = None
        self.selection_start = None
        self.selection_end = None
        self.is_dragging = False
        self.coord_tooltip = None
        self.selected_curves = set()    # 多选功能：选中的曲线集合
        # Shift 临时选择支持
        self.shift_pressed = False
        self.shift_backup_selected = None
        self.shift_temp_selected = set()

        # 曲线上右键标注的点数据结构：列表的每项为 dict {'x','y','curve'}
        self.point_markers = []
        
        # 参考值变量
        self.upper_limit = None
        self.lower_limit = None
        self.reference_values = []
        
        # 工具栏状态变量
        self.toolbar_active = False
        
        # 设置Matplotlib支持中文
        self.setup_matplotlib_chinese_support()
        
        # 设置默认保存路径
        self.setup_default_save_directory()
        
        # 创建UI
        self.setup_ui()
    
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
    
    def setup_ui(self):
        """创建UI元素"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建水平分割器（主容器）
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # 创建垂直分割器（用于两个图表）
        chart_splitter = QSplitter(Qt.Vertical)
        
        # 创建第一个图表区域（包含工具栏和第一个子图）
        self.chart1_container = QWidget()
        chart1_layout = QVBoxLayout(self.chart1_container)
        chart1_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建第一个图表的Matplotlib画布
        self.figure1 = Figure()
        self.canvas1 = FigureCanvas(self.figure1)
        self.canvas1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 添加第一个图表的自定义工具栏（移除移动和放大功能）
        self.toolbar1 = NavigationToolbar(self.canvas1, self)
        # 移除不需要的工具按钮
        actions = self.toolbar1.actions()
        # 通常第一个是Home，第二个是Pan（移动），第三个是Zoom（放大）
        if len(actions) > 2:
            self.toolbar1.removeAction(actions[2])  # 移除Zoom
            self.toolbar1.removeAction(actions[1])  # 移除Pan
        
        # 包装工具栏方法以跟踪状态
        self.wrap_toolbar_methods(self.toolbar1)
        
        # 创建第一个子图
        self.ax1 = self.figure1.add_subplot(111)  # 所有曲线显示在第一个子图
        
        # 设置鼠标事件
        self.canvas1.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas1.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas1.mpl_connect('button_release_event', self.on_mouse_release)
        
        # 将工具栏和画布添加到第一个图表区域
        chart1_layout.addWidget(self.toolbar1)
        chart1_layout.addWidget(self.canvas1)
        
        # 创建第二个图表区域（包含工具栏和第二个子图）
        self.chart2_container = QWidget()
        chart2_layout = QVBoxLayout(self.chart2_container)
        chart2_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建第二个图表的Matplotlib画布
        self.figure2 = Figure()
        self.canvas2 = FigureCanvas(self.figure2)
        self.canvas2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 添加第二个图表的自定义工具栏（移除移动和放大功能）
        self.toolbar2 = NavigationToolbar(self.canvas2, self)
        # 移除不需要的工具按钮
        actions = self.toolbar2.actions()
        # 通常第一个是Home，第二个是Pan（移动），第三个是Zoom（放大）
        if len(actions) > 2:
            self.toolbar2.removeAction(actions[2])  # 移除Zoom
            self.toolbar2.removeAction(actions[1])  # 移除Pan
        
        # 包装工具栏方法以跟踪状态
        self.wrap_toolbar_methods(self.toolbar2)
        
        # 创建第二个子图
        self.ax2 = self.figure2.add_subplot(111)  # 拖拽选定区域曲线显示在第二个子图
        
        # 将工具栏和画布添加到第二个图表区域
        chart2_layout.addWidget(self.toolbar2)
        chart2_layout.addWidget(self.canvas2)
        
        # 将两个图表容器添加到图表分割器
        chart_splitter.addWidget(self.chart1_container)
        chart_splitter.addWidget(self.chart2_container)
        
        # 设置图表分割器的拉伸因子
        chart_splitter.setStretchFactor(0, 1)
        chart_splitter.setStretchFactor(1, 1)
        
        # 创建按钮区域
        self.button_widget = QWidget()
        self.button_layout = QVBoxLayout(self.button_widget)
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        self.button_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.curve_buttons = []  # 存储曲线选择按钮
        
        # 创建参考值输入区域
        self.create_reference_input_area()
        
        # 创建统计信息区域
        self.stats_frame = QFrame()
        self.stats_frame.setFrameShape(QFrame.StyledPanel)
        self.stats_frame.setFrameShadow(QFrame.Raised)
        self.stats_frame.setStyleSheet("background-color: #f5f5f5; border: 1px solid #cccccc;")
        self.stats_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        stats_layout = QVBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        
        self.stats_info = QTextEdit()
        self.stats_info.setReadOnly(True)
        self.stats_info.setStyleSheet("background-color: white; border: 1px solid #dddddd;")
        self.stats_info.setPlaceholderText("左键拖动选择数据区域以显示统计信息")
        self.stats_info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        stats_layout.addWidget(QLabel("选中区域统计:"))
        stats_layout.addWidget(self.stats_info, 1)
        
        # 将按钮区域和统计信息区域添加到右侧分割器
        self.right_splitter = QSplitter(Qt.Vertical)
        self.right_splitter.addWidget(self.button_widget)
        self.right_splitter.addWidget(self.stats_frame)
        self.right_splitter.setSizes([200, 800])
        self.right_splitter.setStretchFactor(0, 1)
        self.right_splitter.setStretchFactor(1, 4)
        
        # 将图表分割器和右侧区域添加到主分割器
        self.main_splitter.addWidget(chart_splitter)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([1000, 800])
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 1)
        
        # 将主分割器添加到主布局
        main_layout.addWidget(self.main_splitter)
        
        # 状态提示
        self.status_label = QLabel("提示: 左键点击并拖动选择数据区域，右键点击显示点坐标", self)
        self.status_label.setStyleSheet("color: gray; font-style: italic; padding: 5px;")
        self.status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.status_label.setMaximumHeight(28)
        main_layout.addWidget(self.status_label)
    
    def create_reference_input_area(self):
        """创建参考值输入区域"""
        # 创建参考值输入框容器
        ref_input_widget = QWidget()
        ref_input_layout = QFormLayout(ref_input_widget)
        ref_input_layout.setContentsMargins(5, 5, 5, 5)
        ref_input_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # 上限输入框
        self.upper_limit_input = QLineEdit()
        self.upper_limit_input.setPlaceholderText("输入上限值")
        self.upper_limit_input.textChanged.connect(self.on_reference_values_changed)
        
        # 下限输入框
        self.lower_limit_input = QLineEdit()
        self.lower_limit_input.setPlaceholderText("输入下限值")
        self.lower_limit_input.textChanged.connect(self.on_reference_values_changed)
        
        # 参考值输入框
        self.reference_values_input = QLineEdit()
        self.reference_values_input.setPlaceholderText("输入参考值，多个值用逗号分隔")
        self.reference_values_input.textChanged.connect(self.on_reference_values_changed)
        
        # 应用按钮
        apply_ref_button = QPushButton("应用参考线")
        apply_ref_button.clicked.connect(self.apply_reference_settings)
        
        # 添加到布局
        ref_input_layout.addRow("上限:", self.upper_limit_input)
        ref_input_layout.addRow("下限:", self.lower_limit_input)
        ref_input_layout.addRow("参考值:", self.reference_values_input)
        ref_input_layout.addRow(apply_ref_button)
        
        # 添加到按钮布局的顶部
        self.button_layout.insertWidget(0, ref_input_widget)
    
    def on_reference_values_changed(self):
        """当参考值输入框内容改变时的处理函数"""
        # 可以在这里添加输入验证逻辑
        pass
    
    def apply_reference_settings(self):
        """应用参考线设置"""
        # 获取上限值
        upper_text = self.upper_limit_input.text().strip()
        self.upper_limit = float(upper_text) if upper_text else None
        
        # 获取下限值
        lower_text = self.lower_limit_input.text().strip()
        self.lower_limit = float(lower_text) if lower_text else None
        
        # 获取参考值
        ref_text = self.reference_values_input.text().strip()
        if ref_text:
            try:
                # 分割并转换参考值
                self.reference_values = [float(x.strip()) for x in ref_text.split(',') if x.strip()]
            except ValueError:
                self.reference_values = []
        else:
            self.reference_values = []
        
        # 重新绘制图表以显示参考线
        self.redraw_plots()
    
    def resizeEvent(self, event):
        """处理窗口大小调整事件"""
        super().resizeEvent(event)
        # 窗口大小调整时可以添加自定义逻辑
        # 例如重新调整图表大小或更新布局
        if hasattr(self, 'canvas1'):
            # 根据窗口大小调整splitter的尺寸
            if hasattr(self, 'main_splitter') and hasattr(self, 'right_splitter'):
                # 获取当前窗口尺寸
                current_width = self.width()
                current_height = self.height()
                
                # 调整主分割器的尺寸比例（左侧70%，右侧30%）
                left_width = int(current_width * 0.7)
                right_width = current_width - left_width
                self.main_splitter.setSizes([left_width, right_width])
                
                # 调整右侧分割器的尺寸比例（按钮区域20%，统计区域80%）
                button_height = int(current_height * 0.2)
                stats_height = current_height - button_height
                self.right_splitter.setSizes([button_height, stats_height])
            
            try:
                self.figure1.tight_layout()
            except Exception:
                pass
            try:
                self.figure2.tight_layout()
            except Exception:
                pass
            self.canvas1.draw()
            if hasattr(self, 'canvas2'):
                self.canvas2.draw()
    
    def setup_matplotlib_chinese_support(self):
        """设置Matplotlib支持中文"""
        # 设置中文字体和解决负号显示问题
        if platform.system() == 'Windows':
            mpl.rcParams['font.sans-serif'] = ['SimHei']
        elif platform.system() == 'Darwin':  # macOS
            mpl.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        else:  # Linux
            mpl.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
        
        mpl.rcParams['axes.unicode_minus'] = False

    def setup_default_save_directory(self):
        """设置默认保存图片的目录为pic"""
        try:
            # 获取pic目录路径
            pic_dir = get_pic_directory()
            
            # 确保pic目录存在
            ensure_directory_exists(pic_dir)
            
            # 设置matplotlib的默认保存目录
            mpl.rcParams['savefig.directory'] = pic_dir
        except Exception:
            # 如果设置失败，保持原有行为
            pass
    
    def set_default_filename(self, filename):
        """设置默认保存图片的文件名"""
        try:
            # 保存原始的save_figure方法
            if not hasattr(self, '_original_save_figure'):
                self._original_save_figure = self.toolbar1.save_figure
            
            # 获取不带扩展名的文件名
            default_filename = os.path.splitext(filename)[0]
            
            # 重写工具栏的save_figure方法以使用自定义文件名
            def custom_save_figure():
                # 保存当前目录
                old_dir = os.getcwd()
                try:
                    # 获取应用程序根目录
                    if getattr(sys, 'frozen', False):
                        # 如果是打包后的exe程序，使用exe所在目录
                        application_path = os.path.dirname(sys.executable)
                    else:
                        # 如果是python脚本运行，使用脚本所在目录
                        application_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    
                    # 创建pic目录路径
                    pic_dir = os.path.join(application_path, 'pic')
                    
                    # 如果pic目录不存在则创建（使用公共工具确保存在）
                    ensure_directory_exists(pic_dir)

                    # 使用 Pic 目录下的保存对话框（不改变当前工作目录）
                    file_path, _ = get_save_in_pic(
                        self.toolbar1,
                        "保存图片",
                        f"{default_filename}.png" if default_filename else "",
                        "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;PDF Files (*.pdf);;SVG Files (*.svg)"
                    )
                    
                    # 如果用户选择了文件路径，则保存图像
                    if file_path:
                        self.figure1.savefig(file_path, dpi=DEFAULT_DPI, bbox_inches='tight')
                finally:
                    # 恢复原来的目录（无论是否更改过）
                    try:
                        os.chdir(old_dir)
                    except Exception:
                        pass
            
            # 替换工具栏的save_figure方法
            self.toolbar1.save_figure = custom_save_figure
        except Exception:
            # 如果设置失败，保持原有行为
            pass
    
    def create_curve_buttons(self):
        """创建曲线选择按钮"""
        # 清除现有按钮
        for button in self.curve_buttons:
            self.button_layout.removeWidget(button)
            button.deleteLater()
        self.curve_buttons.clear()
        
        # 添加"全部曲线"按钮
        all_button = QPushButton("全部曲线")
        all_button.pressed.connect(lambda idx=None: self.on_curve_button_pressed(idx))
        all_button.clicked.connect(lambda checked, idx=None: self.on_curve_button_clicked(idx))
        self.button_layout.addWidget(all_button)
        self.curve_buttons.append(all_button)
        
        # 为每条曲线添加按钮
        for col_idx in sorted(self.y_data_dict.keys()):
            label = self.labels.get(col_idx, f"列{col_idx+1}")
            # 使用默认参数修复闭包问题
            button = QPushButton(label)
            # 使用 pressed 处理 Shift 按住期间的临时选择
            button.pressed.connect(lambda idx=col_idx: self.on_curve_button_pressed(idx))
            # 使用 clicked 处理常规切换（不是 Shift 临时选择）
            button.clicked.connect(lambda checked, idx=col_idx: self.on_curve_button_clicked(idx))
            self.button_layout.addWidget(button)
            self.curve_buttons.append(button)
        
        # 添加弹簧以填充空间
        self.button_layout.addStretch()
        
        # 默认选择全部曲线
        self.select_curve(None)
    
    def select_curve(self, curve_idx):
        """选择要显示的曲线"""
        # 如果curve_idx为None，表示选择全部曲线
        if curve_idx is None:
            # 无论是否按住 Shift，点击全部曲线应显示全部曲线
            self.selected_curves = set(self.y_data_dict.keys())
        else:
            # 非 Shift 模式：单选（仅显示当前点击的曲线）
            if not getattr(self, 'shift_pressed', False):
                self.selected_curves = {curve_idx}
            else:
                # Shift 模式：切换曲线的选中状态
                if curve_idx in self.selected_curves:
                    self.selected_curves.remove(curve_idx)
                else:
                    self.selected_curves.add(curve_idx)
        
        # 更新按钮状态
        for i, button in enumerate(self.curve_buttons):
            if i == 0:  # 全部曲线按钮
                # 如果所有曲线都被选中或者没有曲线被选中，则高亮"全部曲线"按钮
                if len(self.selected_curves) == len(self.y_data_dict.keys()) or len(self.selected_curves) == 0:
                    button.setStyleSheet("background-color: lightblue;")
                else:
                    button.setStyleSheet("")
            elif i > 0:
                # 确保索引在有效范围内
                try:
                    data_keys = sorted(self.y_data_dict.keys())
                    if i-1 < len(data_keys):
                        curve_index = data_keys[i-1]
                        if curve_index in self.selected_curves:
                            button.setStyleSheet("background-color: lightblue;")
                        else:
                            button.setStyleSheet("")
                    else:
                        button.setStyleSheet("")
                except Exception:
                    button.setStyleSheet("")
            else:
                button.setStyleSheet("")
        
        # 根据选择更新功能状态 - 移除限制，使区域选择功能始终可用
        # 无论选择多少条曲线，都要启用区域选择和统计功能
        self.stats_info.setPlaceholderText("左键拖动选择数据区域以显示统计信息")
        
        # 重新绘制图表
        self.redraw_plots()
        try:
            self.update_stats_display()
        except Exception:
            pass

    def on_curve_button_pressed(self, curve_idx):
        """处理曲线按钮按下（支持 Shift 临时选择）"""
        # 如果没有按住 Shift，则不在这里处理（交由 clicked 处理）
        try:
            if not self.shift_pressed:
                return

            # 第一次进入 Shift 临时选择时备份当前选择
            if self.shift_backup_selected is None:
                self.shift_backup_selected = set(self.selected_curves)
                self.shift_temp_selected = set(self.selected_curves)

            # 处理全部曲线按钮
            if curve_idx is None:
                # 切换为全选/全不选临时状态
                if set(self.shift_temp_selected) == set(self.y_data_dict.keys()):
                    self.shift_temp_selected.clear()
                else:
                    self.shift_temp_selected = set(self.y_data_dict.keys())
            else:
                # 切换指定曲线在临时集合中的状态
                if curve_idx in self.shift_temp_selected:
                    self.shift_temp_selected.remove(curve_idx)
                else:
                    self.shift_temp_selected.add(curve_idx)

            # 应用临时选择并刷新
            self.selected_curves = set(self.shift_temp_selected)
            self.update_curve_buttons_style()
            self.redraw_plots()
        except Exception:
            pass

    def on_curve_button_clicked(self, curve_idx):
        """处理曲线按钮点击（常规切换）"""
        # 如果 Shift 正在按下，我们在 pressed 已处理了临时选择，因此忽略 clicked
        if self.shift_pressed:
            return
        self.select_curve(curve_idx)

    def update_curve_buttons_style(self):
        """更新侧边按钮样式以反映当前 selected_curves"""
        try:
            for i, button in enumerate(self.curve_buttons):
                if i == 0:  # 全部曲线按钮
                    if len(self.selected_curves) == len(self.y_data_dict.keys()) or len(self.selected_curves) == 0:
                        button.setStyleSheet("background-color: lightblue;")
                    else:
                        button.setStyleSheet("")
                elif i > 0:
                    try:
                        data_keys = sorted(self.y_data_dict.keys())
                        if i-1 < len(data_keys):
                            curve_index = data_keys[i-1]
                            if curve_index in self.selected_curves:
                                button.setStyleSheet("background-color: lightblue;")
                            else:
                                button.setStyleSheet("")
                        else:
                            button.setStyleSheet("")
                    except Exception:
                        button.setStyleSheet("")
                else:
                    button.setStyleSheet("")
        except Exception:
            pass
        try:
            self.update_stats_display()
        except Exception:
            pass
    
    def redraw_plots(self):
        """重新绘制图表"""
        try:
            colors = ['b-', 'g-', 'r-', 'c-', 'm-', 'y-', 'k-']
            markers = ['o', 's', '^', 'v', 'D', 'p', '*']
            
            # 清除所有子图
            self.ax1.clear()
            self.ax2.clear()
            
            # 如果没有选中任何曲线，则显示所有曲线
            if len(self.selected_curves) == 0:
                # 显示所有曲线
                for i, col_idx in enumerate(self.y_data_dict.keys()):
                    color = colors[i % len(colors)]
                    marker = markers[i % len(markers)]
                    label = self.labels.get(col_idx, f"曲线 {col_idx+1}")
                    
                    self.ax1.plot(
                        self.x_data_dict[col_idx], self.y_data_dict[col_idx], 
                        color, marker=marker, 
                        markevery=max(1, len(self.y_data_dict[col_idx])//20),
                        markersize=5, label=label, picker=3
                    )
                
                self.ax1.set_title("所有曲线")
                self.ax1.set_xlabel("X轴")
                self.ax1.set_ylabel("Y轴")
                self.ax1.legend()
                self.ax1.grid(True)
                self.ax1.ticklabel_format(style='plain', axis='y')
                
                # 清除第二个子图
                self.ax2.set_title("选定区域")
                self.ax2.set_xlabel("X轴")
                self.ax2.set_ylabel("Y轴")
                self.ax2.grid(True)
                self.ax2.ticklabel_format(style='plain', axis='y')
            else:
                # 显示选中的曲线
                selected_labels = []
                # 收集选中曲线的数据用于坐标轴自适应
                selected_x_data = []
                selected_y_data = []
                
                for i, col_idx in enumerate(self.y_data_dict.keys()):
                    color = colors[i % len(colors)]
                    marker = markers[i % len(markers)]
                    label = self.labels.get(col_idx, f"曲线 {col_idx+1}")
                    
                    # 只显示选中的曲线
                    if col_idx in self.selected_curves:
                        self.ax1.plot(
                            self.x_data_dict[col_idx], self.y_data_dict[col_idx], 
                            color, marker=marker,
                            markevery=max(1, len(self.y_data_dict[col_idx])//20),
                            markersize=5, label=label, picker=3, linewidth=2
                        )
                        selected_labels.append(label)
                        # 收集选中曲线的数据
                        selected_x_data.extend(self.x_data_dict[col_idx])
                        selected_y_data.extend(self.y_data_dict[col_idx])
                    # 其他曲线以低透明度显示作为参考
                    else:
                        self.ax1.plot(
                            self.x_data_dict[col_idx], self.y_data_dict[col_idx], 
                            color, marker=marker,
                            markevery=max(1, len(self.y_data_dict[col_idx])//20),
                            markersize=3, label=label, picker=3, alpha=0.3
                        )
                
                # 设置标题
                if len(selected_labels) == 1:
                    self.ax1.set_title(f"曲线: {selected_labels[0]}")
                else:
                    self.ax1.set_title(f"选中 {len(selected_labels)} 条曲线")
                
                self.ax1.set_xlabel("X轴")
                self.ax1.set_ylabel("Y轴")
                self.ax1.legend()
                self.ax1.grid(True)
                # 禁用科学计数法
                self.ax1.ticklabel_format(style='plain', axis='y')
                
                # 根据选中曲线的数据自动调整坐标轴范围
                if selected_x_data and selected_y_data:
                    x_min, x_max = min(selected_x_data), max(selected_x_data)
                    y_min, y_max = min(selected_y_data), max(selected_y_data)
                    x_margin = (x_max - x_min) * 0.05  # 5%边距
                    y_margin = (y_max - y_min) * 0.05  # 5%边距
                    self.ax1.set_xlim(x_min - x_margin, x_max + x_margin)
                    self.ax1.set_ylim(y_min - y_margin, y_max + y_margin)
                
                # 如果只选中了一条曲线且有选择区域，显示在第二个子图
                if len(self.selected_curves) == 1 and self.selection_start is not None and self.selection_end is not None:
                    if list(self.selected_curves)[0] in self.x_data_dict:
                        start_idx = min(self.selection_start, self.selection_end)
                        end_idx = max(self.selection_start, self.selection_end)
                        
                        if (start_idx < len(self.x_data_dict[list(self.selected_curves)[0]]) and 
                            end_idx < len(self.x_data_dict[list(self.selected_curves)[0]]) and
                            end_idx > start_idx):
                            
                            selected_x = self.x_data_dict[list(self.selected_curves)[0]][start_idx:end_idx+1]
                            selected_y = self.y_data_dict[list(self.selected_curves)[0]][start_idx:end_idx+1]
                            
                            if len(selected_y) > 0:
                                # 获取第一个图表中对应曲线的颜色
                                selected_curve_idx = list(self.selected_curves)[0]
                                color_index = list(self.y_data_dict.keys()).index(selected_curve_idx)
                                color = colors[color_index % len(colors)]
                                
                                mean_val = np.mean(selected_y)
                                self.ax2.plot(selected_x, selected_y, f'{color[0]}-', label=selected_labels[0])
                                self.ax2.axhline(y=mean_val, color='r', linestyle='--', label=f'均值: {mean_val:.4f}')
                                self.ax2.set_title(f"选定区域 (曲线: {selected_labels[0]})")
                                self.ax2.set_xlabel("X轴")
                                self.ax2.set_ylabel("Y轴")
                                self.ax2.legend()
                                self.ax2.grid(True)
                                # 禁用科学计数法
                                self.ax2.ticklabel_format(style='plain', axis='y')
                else:
                    self.ax2.set_title("选定区域")
                    self.ax2.set_xlabel("X轴")
                    self.ax2.set_ylabel("Y轴")
                    self.ax2.grid(True)
                    # 禁用科学计数法
                    self.ax2.ticklabel_format(style='plain', axis='y')
            
            # 绘制参考线
            self.draw_reference_lines()

            # 重新绘制之前右键标注的点（及其坐标标签）
            try:
                xlim = self.ax1.get_xlim()
                ylim = self.ax1.get_ylim()
                x_mid = (xlim[0] + xlim[1]) / 2.0
                y_mid = (ylim[0] + ylim[1]) / 2.0
                for m in getattr(self, 'point_markers', []):
                    mx, my = m.get('x'), m.get('y')
                    # 绘制空心圆点作为标注
                    self.ax1.plot([mx], [my], 'o', markerfacecolor='none', markeredgecolor='black', markersize=8, zorder=5)
                    # 文本放置在点的象限（使点成为标签的一个角），优先使用 marker 中的 quadrant
                    quad = m.get('quad')
                    if quad is None:
                        dx = 10 if mx < x_mid else -10
                        dy = 10 if my < y_mid else -10
                    else:
                        sx, sy = quad
                        dx = 10 if sx > 0 else -10
                        dy = 10 if sy > 0 else -10
                    ha = 'left' if dx > 0 else 'right'
                    va = 'bottom' if dy > 0 else 'top'
                    label = m.get('label_text') if m.get('label_text') else self.labels.get(m.get('curve'), f"曲线 {m.get('curve')+1}")
                    txt = f"{label}: x={mx:.4f}, y={my:.4f}"
                    ann = self.ax1.annotate(txt, xy=(mx, my), xytext=(dx, dy), textcoords='offset points',
                                      ha=ha, va=va, bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='black'), zorder=6)
                    # 保存注释对象以便交互检测
                    try:
                        m['annot'] = ann
                    except Exception:
                        m['annot'] = None
            except Exception:
                pass
            
            self.figure1.tight_layout()
            self.canvas1.draw()
            self.figure2.tight_layout()
            self.canvas2.draw()
            try:
                self.update_stats_display()
            except Exception:
                pass
        except Exception:
            pass

    def update_stats_display(self):
        """按照指定格式更新统计信息显示区。

        格式：
        起始点：xx
        结束点：xx
        总计：xx点
        选择x条曲线

        曲线名(列名)：
        最大值：xxx
        最小值：xxx
        均值：xxx
        峰峰值：xxx
        """
        try:
            # 确定要显示统计的曲线
            curves = list(self.selected_curves) if self.selected_curves else list(self.y_data_dict.keys())

            if not curves or not self.x_data_dict:
                self.stats_info.setPlainText("无可用数据")
                return

            # 确定起止索引
            if self.selection_start is not None and self.selection_end is not None:
                start_idx = min(self.selection_start, self.selection_end)
                end_idx = max(self.selection_start, self.selection_end)
            else:
                # 使用第一条曲线作为参考范围
                try:
                    first_key = next(iter(self.x_data_dict))
                    start_idx = 0
                    end_idx = max(0, len(self.x_data_dict[first_key]) - 1)
                except Exception:
                    start_idx = 0
                    end_idx = 0

            total_points = max(0, end_idx - start_idx + 1)

            lines = []
            lines.append(f"起始点：{start_idx}")
            lines.append(f"结束点：{end_idx}")
            lines.append(f"总计：{total_points}点")
            lines.append(f"选择{len(curves)}条曲线")
            lines.append("")

            for col_idx in curves:
                try:
                    label = self.labels.get(col_idx, f"曲线 {col_idx+1}")
                except Exception:
                    label = f"曲线 {col_idx+1}"

                # 获取数据段，确保索引有效
                if col_idx in self.y_data_dict:
                    ydata = self.y_data_dict[col_idx]
                    s = max(0, start_idx)
                    e = min(end_idx, len(ydata) - 1)
                    if e >= s and len(ydata) > 0:
                        seg = np.array(ydata[s:e+1], dtype=float)
                        if seg.size > 0:
                            vmax = np.max(seg)
                            vmin = np.min(seg)
                            vmean = np.mean(seg)
                            vptp = np.ptp(seg)
                            lines.append(f"{label}(列{col_idx+1})：")
                            lines.append(f"最大值：{vmax:.4f}")
                            lines.append(f"最小值：{vmin:.4f}")
                            lines.append(f"均值：{vmean:.4f}")
                            lines.append(f"峰峰值：{vptp:.4f}")
                            lines.append("")
                        else:
                            lines.append(f"{label}(列{col_idx+1})： 无有效数据\n")
                    else:
                        lines.append(f"{label}(列{col_idx+1})： 无有效数据\n")
                else:
                    lines.append(f"{label}(列{col_idx+1})： 无数据\n")

            self.stats_info.setPlainText("\n".join(lines))
        except Exception:
            try:
                self.stats_info.setPlainText("无法计算统计信息")
            except Exception:
                pass
    
    def draw_reference_lines(self):
        """绘制参考线（上限、下限和参考值）"""
        # 绘制上限线
        if self.upper_limit is not None:
            self.ax1.axhline(y=self.upper_limit, color='red', linestyle='--', linewidth=1, 
                            label=f'上限: {self.upper_limit}')
        
        # 绘制下限线
        if self.lower_limit is not None:
            self.ax1.axhline(y=self.lower_limit, color='red', linestyle='--', linewidth=1, 
                            label=f'下限: {self.lower_limit}')
        
        # 绘制参考值线
        for i, ref_val in enumerate(self.reference_values):
            if i == 0:
                self.ax1.axhline(y=ref_val, color='green', linestyle='-.', linewidth=1, 
                                label=f'参考值: {ref_val}')
            else:
                self.ax1.axhline(y=ref_val, color='green', linestyle='-.', linewidth=1)
        
        # 如果添加了参考线，则更新图例
        if self.upper_limit is not None or self.lower_limit is not None or self.reference_values:
            self.ax1.legend()
    
    def plot_multiple(self, x_data_dict, y_data_dict, labels, title="多曲线图"):
        """
        绘制多条曲线
        """
        # 验证数据是否为数值类型
        for col, y_data in y_data_dict.items():
            # 检查y_data是否包含数值数据
            try:
                # 尝试将数据转换为数值类型
                np.array(y_data, dtype=float)
            except (ValueError, TypeError):
                # 显示警告信息
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "警告", f"列 {col+1} 包含非数值数据，无法绘制曲线。\n请先使用数据进制转换功能将数据转换为十进制。")
                return
        
        # 保存数据
        self.x_data_dict = x_data_dict
        self.y_data_dict = y_data_dict
        self.labels = labels
        
        # 清理状态
        self.drag_start_x = None
        self.selection_start = None
        self.selection_end = None
        self.is_dragging = False
        self.stats_info.clear()
        self.stats_info.setPlaceholderText("请选择单条曲线以启用统计功能")
        
        # 创建曲线选择按钮
        self.create_curve_buttons()
        
        # 绘制曲线
        self.redraw_plots()    

    def is_click_on_curve(self, x, y, pixel_threshold=5):
        """检查点击是否在曲线上"""
        if not self.y_data_dict or not self.ax1:
            return False, None, None
        
        try:
            min_dist = float('inf')
            nearest_idx = None
            nearest_curve = None
            
            # 确定要检查的曲线
            curves_to_check = list(self.selected_curves) if self.selected_curves else self.y_data_dict.keys()
            
            # 遍历曲线
            for curve_idx in curves_to_check:
                if curve_idx not in self.x_data_dict:
                    continue
                
                x_data = self.x_data_dict[curve_idx]
                y_data = self.y_data_dict[curve_idx]
                
                # 转换为像素坐标
                points = np.column_stack([x_data, y_data])
                pixels = self.ax1.transData.transform(points)
                
                # 点击位置转换为像素坐标
                click_pixel = self.ax1.transData.transform((x, y))
                click_x_pixel, click_y_pixel = click_pixel
                
                # 计算距离
                distances = np.sqrt((pixels[:, 0] - click_x_pixel)**2 + (pixels[:, 1] - click_y_pixel)**2)
                curve_min_dist = np.min(distances)
                curve_idx_val = np.argmin(distances)
                
                # 更新最小值
                if curve_min_dist < min_dist:
                    min_dist = curve_min_dist
                    nearest_idx = curve_idx_val
                    nearest_curve = curve_idx
            
            return (True, nearest_idx, nearest_curve) if min_dist <= pixel_threshold else (False, None, None)
        except Exception:
            return False, None, None
    
    def show_coord_tooltip(self, x, y, idx, curve_idx):
        """显示坐标提示框"""
        # 保留原有一次性提示功能（用于其他场景），但右键持久标签另行创建
        try:
            label = self.labels.get(curve_idx, f"曲线 {curve_idx+1}")
            tooltip = QLabel(f"{label}: x={x:.4f}, y={y:.4f}", self)
            tooltip.setStyleSheet("""
                background-color: #333333;
                color: #FFFFFF;
                border: 1px solid #666666;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            """)
            tooltip.setWindowFlags(Qt.ToolTip)

            pos = self.mapFromGlobal(QCursor.pos())
            tooltip_width = tooltip.sizeHint().width()
            tooltip_height = tooltip.sizeHint().height()

            x_pos = min(pos.x() + 10, self.width() - tooltip_width - 10)
            y_pos = min(pos.y() + 10, self.height() - tooltip_height - 10)

            tooltip.move(x_pos, y_pos)
            tooltip.show()
            # 自动在短时间后隐藏
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(2500, tooltip.hide)
        except Exception:
            pass

    def _create_persistent_label(self, x, y, idx, curve_idx):
        """创建可点击删除的持久坐标标签并返回 QLabel"""
        try:
            label_text = self.labels.get(curve_idx, f"曲线 {curve_idx+1}") + f": x={x:.4f}, y={y:.4f}"
            lbl = QLabel(label_text, self)
            lbl.setStyleSheet("""
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #666666;
                border-radius: 4px;
                padding: 4px;
            """)
            lbl.setWindowFlags(Qt.Tool)
            lbl.setAttribute(Qt.WA_ShowWithoutActivating)
            # 放置在点附近：将数据坐标转为窗口坐标
            try:
                px, py = self.ax1.transData.transform((x, y))
                # transform to widget coords
                canvas_pos = self.canvas1.mapToGlobal(self.canvas1.rect().topLeft())
                global_x = int(canvas_pos.x() + px)
                global_y = int(canvas_pos.y() + py)
                local_pos = self.mapFromGlobal(QPoint(global_x, global_y))
            except Exception:
                local_pos = self.mapFromGlobal(QCursor.pos())

            tooltip_width = lbl.sizeHint().width()
            tooltip_height = lbl.sizeHint().height()
            x_pos = min(local_pos.x() + 10, self.width() - tooltip_width - 10)
            y_pos = min(local_pos.y() + 10, self.height() - tooltip_height - 10)
            lbl.move(x_pos, y_pos)
            lbl.show()
            # 安装事件过滤器以便点击标签时删除对应标记
            lbl.installEventFilter(self)
            return lbl
        except Exception:
            return None
    
    def hide_coord_tooltip(self):
        """隐藏坐标提示框"""
        try:
            if hasattr(self, 'coord_tooltip') and self.coord_tooltip:
                self.coord_tooltip.hide()
                self.coord_tooltip = None
        except Exception:
            pass

    def eventFilter(self, obj, event):
        """保留 base eventFilter（目前不使用 QLabel 事件过滤）"""
        return super().eventFilter(obj, event)
    
    def wrap_toolbar_methods(self, toolbar):
        """包装工具栏方法以跟踪状态"""
        # 保存原始方法
        original_pan = toolbar.pan
        original_zoom = toolbar.zoom
        
        # 包装pan方法
        def wrapped_pan(*args, **kwargs):
            # 调用原始方法
            result = original_pan(*args, **kwargs)
            # 更新状态
            self.toolbar_active = toolbar._active == 'PAN'
            return result
        
        # 包装zoom方法
        def wrapped_zoom(*args, **kwargs):
            # 调用原始方法
            result = original_zoom(*args, **kwargs)
            # 更新状态
            self.toolbar_active = toolbar._active == 'ZOOM'
            return result
        
        # 替换方法
        toolbar.pan = wrapped_pan
        toolbar.zoom = wrapped_zoom
    
    def on_mouse_press(self, event):
        """处理鼠标按下事件"""
        self.hide_coord_tooltip()
        
        # 如果工具栏处于活动状态，则不处理鼠标事件
        if self.toolbar_active:
            return
        
        # 验证事件
        if not event.inaxes or not self.ax1 or event.xdata is None or event.ydata is None:
            return
        
        # 明示点（用于某些判断使用默认阈值）
        found_marker = self.find_marker_at(event.xdata, event.ydata)
        
        # 右键显示坐标 / 双击空白删除所有标注
        if event.button == 3:  # 右键
            # 对右键操作使用更严格的命中检测阈值，避免在拖拽等情况下误判已有标注
            found_marker_strict = self.find_marker_at(event.xdata, event.ydata, pixel_threshold=4)
            # 右键：如果严格命中已有标注则移除该标注
            if found_marker_strict is not None:
                try:
                    # 在移除标注前删除其 artist/annot，避免完整重绘
                    a = found_marker_strict.get('artist')
                    if a is not None:
                        try:
                            a.remove()
                        except Exception:
                            pass
                    ann = found_marker_strict.get('annot')
                    if ann is not None:
                        try:
                            ann.remove()
                        except Exception:
                            pass
                    try:
                        self.point_markers.remove(found_marker_strict)
                    except Exception:
                        pass
                except Exception:
                    pass
                try:
                    self.canvas1.draw()
                except Exception:
                    pass
                return

            on_curve, idx, curve_idx = self.is_click_on_curve(event.xdata, event.ydata)
            # 如果没有严格命中已有标注，则尝试在曲线上添加新标注
            if (found_marker_strict is None) and on_curve and curve_idx in self.x_data_dict and idx < len(self.x_data_dict[curve_idx]):
                x_data = self.x_data_dict[curve_idx][idx]
                y_data = self.y_data_dict[curve_idx][idx]
                # 添加标注点数据（非重绘方式：直接创建 artist 与注释并保存引用）
                try:
                    marker = {'x': x_data, 'y': y_data, 'curve': curve_idx, 'label_text': None, 'quad': None, 'annot': None, 'artist': None}
                    # 创建点 artist
                    try:
                        artists = self.ax1.plot([x_data], [y_data], 'o', markerfacecolor='none', markeredgecolor='black', markersize=8, zorder=5)
                        if artists:
                            marker['artist'] = artists[0]
                    except Exception:
                        marker['artist'] = None
                    # 创建注释
                    try:
                        xlim = self.ax1.get_xlim()
                        ylim = self.ax1.get_ylim()
                        x_mid = (xlim[0] + xlim[1]) / 2.0
                        y_mid = (ylim[0] + ylim[1]) / 2.0
                        dx = 10 if x_data < x_mid else -10
                        dy = 10 if y_data < y_mid else -10
                        label = marker.get('label_text') if marker.get('label_text') else self.labels.get(curve_idx, f"曲线 {curve_idx+1}")
                        txt = f"{label}: x={x_data:.4f}, y={y_data:.4f}"
                        ann = self.ax1.annotate(txt, xy=(x_data, y_data), xytext=(dx, dy), textcoords='offset points',
                                                ha='left' if dx>0 else 'right', va='bottom' if dy>0 else 'top',
                                                bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='black'), zorder=6)
                        marker['annot'] = ann
                    except Exception:
                        marker['annot'] = None
                    self.point_markers.append(marker)
                except Exception:
                    pass

                try:
                    # 仅重绘 canvas1，避免清除拖拽的临时显示
                    self.canvas1.draw()
                except Exception:
                    pass
            return
        
        # 处理区域选择开始或标签拖拽 - 左键
        if event.button == 1:  # 左键
            # 检查左键双击空白区域以删除所有明示点（功能从右键迁移到左键）
            try:
                on_curve_temp, idx_temp, curve_idx_temp = self.is_click_on_curve(event.xdata, event.ydata)
                if getattr(event, 'dblclick', False) and (not on_curve_temp) and found_marker is None:
                    self.clear_point_markers()
                    return
            except Exception:
                pass

            # 先检测是否点中某个注释文本区域（需要 renderer）以开始标签拖拽
            try:
                renderer = self.canvas1.get_renderer()
                for m in getattr(self, 'point_markers', []):
                    ann = m.get('annot')
                    if ann is None:
                        continue
                    try:
                        bbox = ann.get_window_extent(renderer)
                        # 事件提供的 x,y 是相对于 canvas 的像素坐标
                        ex, ey = event.x, event.y
                        if bbox.contains(ex, ey):
                            # 开始拖拽该标签
                            self.label_dragging = True
                            self.dragging_marker = m
                            return
                        else:
                            # 如果 bbox 检测失败，退而求其次：检查是否点击在标记点附近（像素距离）
                            try:
                                mx, my = m.get('x'), m.get('y')
                                px, py = self.ax1.transData.transform((mx, my))
                                dist = ((px - ex)**2 + (py - ey)**2)**0.5
                                if dist <= 8:  # 8 像素阈值回退检测
                                    self.label_dragging = True
                                    self.dragging_marker = m
                                    return
                            except Exception:
                                pass
                    except Exception:
                        continue
            except Exception:
                pass

            # 否则作为区域选择开始
            self.drag_start_x = event.xdata
            self.is_dragging = False
    
    def find_nearest_index(self, x_target):
        """查找最接近目标x值的数据点索引"""
        if not self.x_data_dict:
            return None
        
        # 使用第一条曲线的数据作为参考
        first_key = next(iter(self.x_data_dict))
        x_data = self.x_data_dict[first_key]
        
        # 找到最接近的索引
        idx = np.abs(np.array(x_data) - x_target).argmin()
        return int(idx)

    def find_marker_at(self, x, y, pixel_threshold=6):
        """查找是否点击到了已有标注点，返回该标注点的 dict 或 None"""
        try:
            if not getattr(self, 'point_markers', None):
                return None
            click_px, click_py = self.ax1.transData.transform((x, y))
            min_dist = float('inf')
            found = None
            for m in self.point_markers:
                mx, my = m.get('x'), m.get('y')
                px, py = self.ax1.transData.transform((mx, my))
                dist = ((px - click_px)**2 + (py - click_py)**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    found = m
            return found if min_dist <= pixel_threshold else None
        except Exception:
            return None
    
    def on_mouse_move(self, event):
        """处理鼠标移动事件"""
        # 如果工具栏处于活动状态，则不处理鼠标事件
        if self.toolbar_active:
            return
        
        # 验证状态
        if (not event.inaxes or not self.ax1 or event.xdata is None or event.button != 1):
            return

        # 如果正在拖拽标签，则更新该标签的象限位置（仅四象限）
        try:
            if getattr(self, 'label_dragging', False) and getattr(self, 'dragging_marker', None):
                m = self.dragging_marker
                # 计算鼠标相对于标记点在像素坐标的偏移
                mx, my = m.get('x'), m.get('y')
                px, py = self.ax1.transData.transform((mx, my))
                # 事件的像素坐标
                ex, ey = event.x, event.y
                sx = 1 if (ex - px) >= 0 else -1
                sy = 1 if (ey - py) >= 0 else -1
                m['quad'] = (sx, sy)
                # 仅更新该标注的注释位置，不触发完整重绘，避免清除选择框
                try:
                    # 更新 annotation（重建或调整）
                    try:
                        if m.get('annot') is not None:
                            try:
                                m['annot'].remove()
                            except Exception:
                                pass
                            m['annot'] = None
                    except Exception:
                        pass
                    try:
                        xlim = self.ax1.get_xlim()
                        ylim = self.ax1.get_ylim()
                        x_mid = (xlim[0] + xlim[1]) / 2.0
                        y_mid = (ylim[0] + ylim[1]) / 2.0
                        dx = 10 if mx < x_mid else -10
                        dy = 10 if my < y_mid else -10
                        label = m.get('label_text') if m.get('label_text') else self.labels.get(m.get('curve'), f"曲线 {m.get('curve')+1}")
                        txt = f"{label}: x={mx:.4f}, y={my:.4f}"
                        ann = self.ax1.annotate(txt, xy=(mx, my), xytext=(dx, dy), textcoords='offset points',
                                                ha='left' if dx>0 else 'right', va='bottom' if dy>0 else 'top',
                                                bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='black'), zorder=6)
                        m['annot'] = ann
                    except Exception:
                        m['annot'] = None
                    # 只重绘 canvas1
                    try:
                        self.canvas1.draw()
                    except Exception:
                        pass
                except Exception:
                    pass
                return
        except Exception:
            pass
        
        # 保存当前坐标轴范围
        if not self.is_dragging:
            self.original_xlim = self.ax1.get_xlim()
            self.original_ylim = self.ax1.get_ylim()
        
        # 检测是否开始拖拽
        if (not self.is_dragging and 
            abs(event.xdata - self.drag_start_x) > 0.01 * (self.ax1.get_xlim()[1] - self.ax1.get_xlim()[0])):
            self.is_dragging = True
            self.selection_start = self.find_nearest_index(self.drag_start_x)
    
        # 拖拽时显示选择区域
        if self.is_dragging:
            self.selection_end = self.find_nearest_index(event.xdata)
        
            # 重绘第一个子图
            try:
                self.ax1.clear()
                colors = ['b-', 'g-', 'r-', 'c-', 'm-', 'y-', 'k-']
                markers = ['o', 's', '^', 'v', 'D', 'p', '*']
            
                # 确定要显示的曲线
                curves_to_display = list(self.selected_curves) if self.selected_curves else list(self.y_data_dict.keys())
            
                # 绘制所有可见曲线
                for i, col_idx in enumerate(self.y_data_dict.keys()):
                    color = colors[i % len(colors)]
                    label = self.labels.get(col_idx, f"曲线 {col_idx+1}")
                
                    if col_idx in curves_to_display:
                        # 显示选中的曲线，保留点标记
                        try:
                            color_char = colors[i % len(colors)][0]
                        except Exception:
                            color_char = 'b'
                        marker = markers[i % len(markers)]
                        try:
                            markevery = max(1, len(self.y_data_dict[col_idx])//20)
                        except Exception:
                            markevery = 1
                        self.ax1.plot(
                            self.x_data_dict[col_idx], 
                            self.y_data_dict[col_idx], 
                            color=color_char, marker=marker, linestyle='-',
                            markevery=markevery, markersize=5, label=label, picker=3,
                            linewidth=2 if col_idx in self.selected_curves else 1
                        )
                    elif not self.selected_curves:
                        # 如果没有选择任何曲线，显示所有曲线（保留点标记）
                        try:
                            color_char = colors[i % len(colors)][0]
                        except Exception:
                            color_char = 'b'
                        marker = markers[i % len(markers)]
                        try:
                            markevery = max(1, len(self.y_data_dict[col_idx])//20)
                        except Exception:
                            markevery = 1
                        self.ax1.plot(
                            self.x_data_dict[col_idx], 
                            self.y_data_dict[col_idx], 
                            color=color_char, marker=marker, linestyle='-',
                            markevery=markevery, markersize=5, label=label, picker=3
                        )
                    else:
                        # 其他曲线以低透明度显示作为参考（保留点标记）
                        try:
                            color_char = colors[i % len(colors)][0]
                        except Exception:
                            color_char = 'b'
                        marker = markers[i % len(markers)]
                        try:
                            markevery = max(1, len(self.y_data_dict[col_idx])//20)
                        except Exception:
                            markevery = 1
                        self.ax1.plot(
                            self.x_data_dict[col_idx], 
                            self.y_data_dict[col_idx], 
                            color=color_char, marker=marker, linestyle='-',
                            markevery=markevery, markersize=3, label=label, picker=3, alpha=0.3
                        )
            
                # 高亮选择区域（如果有）
                if (self.selection_start is not None and self.selection_end is not None):
                    # 确保索引有效
                    start_idx = min(self.selection_start, self.selection_end)
                    end_idx = max(self.selection_start, self.selection_end)
                
                    # 为所有可见曲线高亮选择区域
                    for i, col_idx in enumerate(curves_to_display):
                        if (col_idx in self.x_data_dict and
                            start_idx < len(self.x_data_dict[col_idx]) and 
                            end_idx < len(self.x_data_dict[col_idx]) and
                            start_idx != end_idx):
                            base_color = colors[i % len(colors)][0]  # 获取颜色的第一个字符
                            self.ax1.fill_between(
                                self.x_data_dict[col_idx][start_idx:end_idx+1], 
                                self.y_data_dict[col_idx][start_idx:end_idx+1], 
                                color=base_color, alpha=0.3
                            )

                    # 实时更新选中区域的统计信息，跟随当前显示的曲线
                    try:
                        # 使用统一的统计显示格式更新统计区域
                        try:
                            self.update_stats_display()
                        except Exception:
                            pass
                    except Exception:
                        pass
                
                # 绘制参考线
                self.draw_reference_lines()

                # 在拖拽实时绘制中也重绘持久标注点及其注释，避免标注在拖拽时消失
                try:
                    xlim = self.ax1.get_xlim()
                    ylim = self.ax1.get_ylim()
                    x_mid = (xlim[0] + xlim[1]) / 2.0
                    y_mid = (ylim[0] + ylim[1]) / 2.0
                    for m in getattr(self, 'point_markers', []):
                        mx, my = m.get('x'), m.get('y')
                        # 移除旧的 artist/annotation（如果存在），避免重复绘制
                        try:
                            a = m.get('artist')
                            if a is not None:
                                try:
                                    a.remove()
                                except Exception:
                                    pass
                                m['artist'] = None
                        except Exception:
                            pass
                        try:
                            ann_old = m.get('annot')
                            if ann_old is not None:
                                try:
                                    ann_old.remove()
                                except Exception:
                                    pass
                                m['annot'] = None
                        except Exception:
                            pass

                        # 绘制空心圆点作为标注并保存 artist 引用
                        try:
                            artists = self.ax1.plot([mx], [my], 'o', markerfacecolor='none', markeredgecolor='black', markersize=8, zorder=5)
                            if artists:
                                m['artist'] = artists[0]
                        except Exception:
                            m['artist'] = None

                        # 文本放置在点的象限，优先使用 marker 中的 quadrant
                        quad = m.get('quad')
                        if quad is None:
                            dx = 10 if mx < x_mid else -10
                            dy = 10 if my < y_mid else -10
                        else:
                            sx, sy = quad
                            dx = 10 if sx > 0 else -10
                            dy = 10 if sy > 0 else -10
                        ha = 'left' if dx > 0 else 'right'
                        va = 'bottom' if dy > 0 else 'top'
                        label = m.get('label_text') if m.get('label_text') else self.labels.get(m.get('curve'), f"曲线 {m.get('curve')+1}")
                        txt = f"{label}: x={mx:.4f}, y={my:.4f}"
                        try:
                            ann = self.ax1.annotate(txt, xy=(mx, my), xytext=(dx, dy), textcoords='offset points',
                                              ha=ha, va=va, bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='black'), zorder=6)
                            m['annot'] = ann
                        except Exception:
                            m['annot'] = None
                except Exception:
                    pass
                
                title = "所有曲线" if not self.selected_curves else f"选中 {len(self.selected_curves)} 条曲线"
                self.ax1.set_title(title)
                self.ax1.set_xlabel("X轴")
                self.ax1.set_ylabel("Y轴")
                self.ax1.legend()
                self.ax1.grid(True)
                # 禁用科学计数法
                self.ax1.ticklabel_format(style='plain', axis='y')
                # 恢复坐标轴范围
                if hasattr(self, 'original_xlim') and hasattr(self, 'original_ylim'):
                    self.ax1.set_xlim(self.original_xlim)
                    self.ax1.set_ylim(self.original_ylim)
            
                self.canvas1.draw()
            except Exception:
                pass
    
    def on_mouse_release(self, event):
        """处理鼠标释放事件"""
        # 如果工具栏处于活动状态，则不处理鼠标事件
        if self.toolbar_active:
            return

        # 如果正在拖拽标签，结束标签拖拽
        try:
            if getattr(self, 'label_dragging', False):
                self.label_dragging = False
                self.dragging_marker = None
                return
        except Exception:
            pass

        # 如果没有正在拖拽区域，则忽略
        if not getattr(self, 'is_dragging', False):
            return

        # 计算选择索引范围
        if (self.selection_start is None) or (self.selection_end is None):
            # 重置状态并返回
            self.drag_start_x = None
            self.is_dragging = False
            return

        start_idx = min(self.selection_start, self.selection_end)
        end_idx = max(self.selection_start, self.selection_end)

        # 确定要处理的曲线集合
        curves_to_process = list(self.selected_curves) if self.selected_curves else list(self.y_data_dict.keys())

        # 计算统计信息（均值、峰峰值）
        all_stats = []
        for i, col_idx in enumerate(curves_to_process):
            try:
                if col_idx in self.y_data_dict:
                    y_segment = self.y_data_dict[col_idx][start_idx:end_idx+1]
                    if len(y_segment) > 0:
                        mean_val = np.mean(y_segment)
                        peak_val = np.max(y_segment) - np.min(y_segment)
                        stats_text = f"{self.labels.get(col_idx, f'曲线 {col_idx+1}')}：均值={mean_val:.4f}, 峰峰值={peak_val:.4f}"
                        all_stats.append(stats_text)
            except Exception:
                pass

        # 更新统计信息显示
        try:
            self.update_stats_display()
        except Exception:
            pass

        # 更新第二个子图 - 显示选定区域
        try:
            self.ax2.clear()
            colors = ['b-', 'g-', 'r-', 'c-', 'm-', 'y-', 'k-']

            # 保存当前坐标轴范围
            original_xlim_ax2 = self.ax2.get_xlim()
            original_ylim_ax2 = self.ax2.get_ylim()

            for i, col_idx in enumerate(curves_to_process):
                if (col_idx in self.x_data_dict and col_idx in self.y_data_dict and
                    start_idx < len(self.x_data_dict[col_idx]) and
                    end_idx < len(self.x_data_dict[col_idx]) and
                    end_idx > start_idx):

                    selected_x = self.x_data_dict[col_idx][start_idx:end_idx+1]
                    selected_y = self.y_data_dict[col_idx][start_idx:end_idx+1]

                    if len(selected_y) > 0:
                        color_index = list(self.y_data_dict.keys()).index(col_idx)
                        color = colors[color_index % len(colors)]
                        label = self.labels.get(col_idx, f"曲线 {col_idx+1}")

                        self.ax2.plot(selected_x, selected_y, f'{color[0]}-', label=label)

                        # 只为第一条曲线添加均值线
                        if i == 0:
                            mean_val = np.mean(selected_y)
                            self.ax2.axhline(y=mean_val, color='r', linestyle='--', label=f'均值: {mean_val:.4f}')

            self.ax2.set_title("选定区域")
            self.ax2.set_xlabel("X轴")
            self.ax2.set_ylabel("Y轴")
            self.ax2.legend()
            self.ax2.grid(True)
            self.ax2.ticklabel_format(style='plain', axis='y')

            self.canvas1.draw()
            self.canvas2.draw()
            if hasattr(self, 'original_xlim') and hasattr(self, 'original_ylim'):
                self.ax1.set_xlim(self.original_xlim)
                self.ax1.set_ylim(self.original_ylim)
                self.canvas1.draw()
        except Exception:
            pass
    
        # 重置状态
        self.drag_start_x = None
        self.is_dragging = False

    def keyPressEvent(self, event):
        """捕获 Shift 键按下以进入临时选择模式"""
        try:
            if event.key() == Qt.Key_Shift and not self.shift_pressed:
                self.shift_pressed = True
                # 备份当前选择
                self.shift_backup_selected = set(self.selected_curves)
                self.shift_temp_selected = set(self.selected_curves)
        except Exception:
            pass
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """捕获 Shift 键释放并恢复备份选择"""
        try:
            if event.key() == Qt.Key_Shift and self.shift_pressed:
                self.shift_pressed = False
                # 将按住 Shift 期间的临时选择应用为新的选择
                if self.shift_temp_selected is not None:
                    self.selected_curves = set(self.shift_temp_selected)
                # 清理临时状态
                self.shift_backup_selected = None
                self.shift_temp_selected = set()
                self.update_curve_buttons_style()
                try:
                    self.redraw_plots()
                except Exception:
                    pass
        except Exception:
            pass
        super().keyReleaseEvent(event)

    def clear_point_markers(self):
        """清除所有右键标注的点和提示"""
        try:
            # 清空标注点数据（重绘时将不再绘制）
            self.point_markers = []
            # 隐藏可能存在的一次性提示
            self.hide_coord_tooltip()
            try:
                self.redraw_plots()
            except Exception:
                pass
        except Exception:
            pass

    def closeEvent(self, event):
        """窗口关闭时清理坐标标签等状态"""
        try:
            self.clear_point_markers()
        except Exception:
            pass
        super().closeEvent(event)
    
    def save_figure(self):
        """保存图片"""
        try:
            # 确保保存目录存在
            save_dir = get_pic_directory()
            ensure_directory_exists(save_dir)
            
            # 生成默认文件名
            default_name = "plot.png"
            if hasattr(self, '_last_filename'):
                default_name = self._last_filename
            elif self.labels:
                # 使用第一个标签作为文件名
                first_label = list(self.labels.values())[0] if self.labels else "plot"
                default_name = f"{first_label}.png"
            
            # 构造完整路径并获取唯一文件名
            file_path = os.path.join(save_dir, default_name)
            unique_file_path = get_unique_filename(file_path)
            
            # 保存图片
            self.figure1.savefig(unique_file_path, dpi=DEFAULT_DPI, bbox_inches='tight')
            subplots_file_path = unique_file_path.replace('.png', '_subplot.png')
            self.figure2.savefig(subplots_file_path, dpi=DEFAULT_DPI, bbox_inches='tight')
            
            # 显示保存成功消息
            QMessageBox.information(self, "保存成功", f"图片已保存到:\n{unique_file_path}")
            
            # 更新最后保存的文件名
            self._last_filename = os.path.basename(unique_file_path)
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存图片时出错:\n{str(e)}")
