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
                             QWidget, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
import platform

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class PlotWindow(QDialog):
    """用于显示曲线的窗口，实现基本的曲线显示和交互功能"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据曲线分析")
        self.resize(1600, 900)
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
        chart1_container = QWidget()
        chart1_layout = QVBoxLayout(chart1_container)
        chart1_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建Matplotlib画布
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 添加自定义工具栏（移除移动和放大功能）
        self.toolbar = NavigationToolbar(self.canvas, self)
        # 移除不需要的工具按钮
        actions = self.toolbar.actions()
        # 通常第一个是Home，第二个是Pan（移动），第三个是Zoom（放大）
        if len(actions) > 2:
            self.toolbar.removeAction(actions[2])  # 移除Zoom
            self.toolbar.removeAction(actions[1])  # 移除Pan
        
        # 创建子图
        self.ax1 = self.figure.add_subplot(211)  # 所有曲线显示在第一个子图
        self.ax2 = self.figure.add_subplot(212)  # 拖拽选定区域曲线显示在第二个子图
        
        # 设置鼠标事件
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        
        # 将工具栏和画布添加到第一个图表区域
        chart1_layout.addWidget(self.toolbar)
        chart1_layout.addWidget(self.canvas)
        
        # 将第一个图表区域添加到图表分割器
        chart_splitter.addWidget(chart1_container)
        
        # 设置图表分割器的拉伸因子
        chart_splitter.setStretchFactor(0, 1)
        
        # 创建按钮区域
        self.button_widget = QWidget()
        self.button_layout = QVBoxLayout(self.button_widget)
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        self.button_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.curve_buttons = []  # 存储曲线选择按钮
        
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
    
    def resizeEvent(self, event):
        """处理窗口大小调整事件"""
        super().resizeEvent(event)
        # 窗口大小调整时可以添加自定义逻辑
        # 例如重新调整图表大小或更新布局
        if hasattr(self, 'canvas'):
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
            
            self.canvas.draw()
    
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
            # 获取应用程序根目录
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe程序，使用exe所在目录
                application_path = os.path.dirname(sys.executable)
            else:
                # 如果是python脚本运行，使用脚本所在目录
                application_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 创建pic目录路径
            pic_dir = os.path.join(application_path, 'pic')
            
            # 如果pic目录不存在则创建
            if not os.path.exists(pic_dir):
                os.makedirs(pic_dir)
            
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
                self._original_save_figure = self.toolbar.save_figure
            
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
                    
                    # 如果pic目录不存在则创建
                    if not os.path.exists(pic_dir):
                        os.makedirs(pic_dir)
                    
                    # 切换到pic目录
                    os.chdir(pic_dir)
                    
                    # 创建自定义文件对话框
                    from PyQt5.QtWidgets import QFileDialog
                    file_path, _ = QFileDialog.getSaveFileName(
                        self.toolbar,
                        "保存图片",
                        os.path.join(pic_dir, default_filename),  # 使用自定义文件名作为默认文件名
                        "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;PDF Files (*.pdf);;SVG Files (*.svg)",
                        "PNG Files (*.png)"
                    )
                    
                    # 如果用户选择了文件路径，则保存图像
                    if file_path:
                        self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                finally:
                    # 恢复原来的目录
                    os.chdir(old_dir)
            
            # 替换工具栏的save_figure方法
            self.toolbar.save_figure = custom_save_figure
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
        all_button.clicked.connect(lambda: self.select_curve(None))
        self.button_layout.addWidget(all_button)
        self.curve_buttons.append(all_button)
        
        # 为每条曲线添加按钮
        for col_idx in sorted(self.y_data_dict.keys()):
            label = self.labels.get(col_idx, f"列{col_idx+1}")
            # 使用默认参数修复闭包问题
            button = QPushButton(label)
            button.clicked.connect(lambda checked, idx=col_idx: self.select_curve(idx))
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
            # 如果已经选择了全部曲线，则清空选择
            if len(self.selected_curves) == len(self.y_data_dict.keys()) or len(self.selected_curves) == 0:
                self.selected_curves.clear()
            else:
                # 否则选择所有曲线
                self.selected_curves = set(self.y_data_dict.keys())
        else:
            # 切换曲线的选中状态
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
            
            self.figure.tight_layout()
            self.canvas.draw()
        except Exception:
            pass
    
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
        self.hide_coord_tooltip()
        
        try:
            label = self.labels.get(curve_idx, f"曲线 {curve_idx+1}")
            self.coord_tooltip = QLabel(f"{label}: x={x:.4f}, y={y:.4f}", self)
            self.coord_tooltip.setStyleSheet("""
                background-color: #333333;
                color: #FFFFFF;
                border: 1px solid #666666;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
            """)
            self.coord_tooltip.setWindowFlags(Qt.ToolTip)
            
            # 定位提示框
            pos = self.mapFromGlobal(QCursor.pos())
            tooltip_width = self.coord_tooltip.sizeHint().width()
            tooltip_height = self.coord_tooltip.sizeHint().height()
            
            x_pos = min(pos.x() + 10, self.width() - tooltip_width - 10)
            y_pos = min(pos.y() + 10, self.height() - tooltip_height - 10)
            
            self.coord_tooltip.move(x_pos, y_pos)
            self.coord_tooltip.show()
        except Exception:
            pass
    
    def hide_coord_tooltip(self):
        """隐藏坐标提示框"""
        if self.coord_tooltip:
            try:
                self.coord_tooltip.hide()
                self.coord_tooltip = None
            except:
                self.coord_tooltip = None
    
    def on_mouse_press(self, event):
        """处理鼠标按下事件"""
        self.hide_coord_tooltip()
        
        # 验证事件
        if not event.inaxes or not self.ax1 or event.xdata is None or event.ydata is None:
            return
        
        # 右键显示坐标
        if event.button == 3:  # 右键
            on_curve, idx, curve_idx = self.is_click_on_curve(event.xdata, event.ydata)
            if on_curve and curve_idx in self.x_data_dict and idx < len(self.x_data_dict[curve_idx]):
                x_data = self.x_data_dict[curve_idx][idx]
                y_data = self.y_data_dict[curve_idx][idx]
                self.show_coord_tooltip(x_data, y_data, idx, curve_idx)
            return
        
        # 处理区域选择开始 - 左键
        if event.button == 1:  # 左键
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
    
    def on_mouse_move(self, event):
        """处理鼠标移动事件"""
        # 验证状态
        if (not self.drag_start_x or 
            not event.inaxes or not self.ax1 or event.xdata is None or event.button != 1):
            return
        
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
            
                # 确定要显示的曲线
                curves_to_display = list(self.selected_curves) if self.selected_curves else list(self.y_data_dict.keys())
            
                # 绘制所有可见曲线
                for i, col_idx in enumerate(self.y_data_dict.keys()):
                    color = colors[i % len(colors)]
                    label = self.labels.get(col_idx, f"曲线 {col_idx+1}")
                
                    if col_idx in curves_to_display:
                        # 显示选中的曲线
                        self.ax1.plot(
                            self.x_data_dict[col_idx], 
                            self.y_data_dict[col_idx], 
                            color, label=label, picker=3, linewidth=2 if col_idx in self.selected_curves else 1
                        )
                    elif not self.selected_curves:
                        # 如果没有选择任何曲线，显示所有曲线
                        self.ax1.plot(
                            self.x_data_dict[col_idx], 
                            self.y_data_dict[col_idx], 
                            color, label=label, picker=3
                        )
                    else:
                        # 其他曲线以低透明度显示作为参考
                        self.ax1.plot(
                            self.x_data_dict[col_idx], 
                            self.y_data_dict[col_idx], 
                            color, label=label, picker=3, alpha=0.3
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
            
                self.canvas.draw()
            except Exception:
                pass
    
    def on_mouse_release(self, event):
        """处理鼠标释放事件"""
        # 验证状态
        if (not self.drag_start_x or event.button != 1 or not self.is_dragging or 
            not event.inaxes or not self.ax1 or event.xdata is None):
            return
    
        # 获取选择区域
        self.selection_end = self.find_nearest_index(event.xdata)
    
        # 确定要处理的曲线
        curves_to_process = list(self.selected_curves) if self.selected_curves else list(self.y_data_dict.keys())
    
        if (self.selection_start is not None and self.selection_end is not None and curves_to_process):
            start_idx = min(self.selection_start, self.selection_end)
            end_idx = max(self.selection_start, self.selection_end)
        
            # 收集所有曲线的统计信息
            all_stats = []
        
            for col_idx in curves_to_process:
                if (col_idx in self.x_data_dict and col_idx in self.y_data_dict and
                    start_idx < len(self.x_data_dict[col_idx]) and 
                    end_idx < len(self.x_data_dict[col_idx]) and
                    end_idx > start_idx):
                
                    # 获取选中区域数据
                    x_data = self.x_data_dict[col_idx]
                    y_data = self.y_data_dict[col_idx]

                    # 确保索引有效
                    selected_x = x_data[start_idx:end_idx+1]
                    selected_y = y_data[start_idx:end_idx+1]
                
                    if len(selected_y) > 0:
                        try:
                            # 计算统计量
                            mean_val = np.mean(selected_y)
                            peak_val = np.max(selected_y) - np.min(selected_y)
                            label = self.labels.get(col_idx, f"曲线 {col_idx+1}")
                            
                            # 添加到统计信息列表
                            stats_text = (
                                f"曲线: {label}\n"
                                f"选中点数: {len(selected_y)}\n"
                                f"均值: {mean_val:.4f}\n"
                                f"峰峰值: {peak_val:.4f}\n"
                                f"最大值: {np.max(selected_y):.4f}\n"
                                f"最小值: {np.min(selected_y):.4f}\n"
                            )
                            all_stats.append(stats_text)
                        except Exception:
                            pass
        
            # 更新统计信息显示
            if all_stats:
                self.stats_info.setPlainText("\n".join(all_stats))
            else:
                self.stats_info.setPlainText("选定区域无有效数据")
        
            # 更新第二个子图 - 显示选定区域
            try:
                self.ax2.clear()
                colors = ['b-', 'g-', 'r-', 'c-', 'm-', 'y-', 'k-']
                
                # 保存当前坐标轴范围
                original_xlim_ax2 = self.ax2.get_xlim()
                original_ylim_ax2 = self.ax2.get_ylim()
                
                # 为所有可见曲线绘制选定区域
                for i, col_idx in enumerate(curves_to_process):
                    if (col_idx in self.x_data_dict and col_idx in self.y_data_dict and
                        start_idx < len(self.x_data_dict[col_idx]) and 
                        end_idx < len(self.x_data_dict[col_idx]) and
                        end_idx > start_idx):
                    
                        selected_x = self.x_data_dict[col_idx][start_idx:end_idx+1]
                        selected_y = self.y_data_dict[col_idx][start_idx:end_idx+1]
                    
                        if len(selected_y) > 0:
                            color = colors[i % len(colors)]
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
                # 禁用科学计数法
                self.ax2.ticklabel_format(style='plain', axis='y')
            
                self.figure.tight_layout()
                self.canvas.draw()
                
                # 恢复第一个子图的坐标轴范围
                if hasattr(self, 'original_xlim') and hasattr(self, 'original_ylim'):
                    self.ax1.set_xlim(self.original_xlim)
                    self.ax1.set_ylim(self.original_ylim)
                    self.canvas.draw()
            except Exception:
                pass
    
        # 重置状态
        self.drag_start_x = None
        self.is_dragging = False