# -*- coding: utf-8 -*-
"""
状态变量检测模块
用于检测状态变量为特定值时对应的电容值变化情况
"""

import numpy as np
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QSplitter, QDesktopWidget, QWidget,
                             QSizePolicy, QFrame, QApplication, QComboBox,
                             QDialogButtonBox, QAction, QToolButton,
                             QGroupBox, QFileDialog, QStyle, QMenu, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class StatesColumnSelectionDialog(QDialog):
    """状态变量检测列选择对话框"""
    
    def __init__(self, column_names, parent=None):
        super().__init__(parent)
        self.column_names = column_names
        self.state_column = None
        self.sensor_column = None
        
        self.setWindowTitle("状态变量检测 - 列选择")
        self.setModal(True)
        self.resize(600, 200)
        self.center()
        
        self.setup_ui()
    
    def center(self):
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
        """创建UI元素"""
        layout = QVBoxLayout()
        
        # 状态变量列选择
        state_layout = QHBoxLayout()
        state_label = QLabel("状态变量列:")
        self.state_combo = QComboBox()

        for i, name in enumerate(self.column_names):
            self.state_combo.addItem(f"{name} (列{i+1})")  # 添加列索引备注

        state_layout.addWidget(state_label)
        state_layout.addWidget(self.state_combo)

        layout.addLayout(state_layout)
        
        # 传感器值列选择
        sensor_layout = QHBoxLayout()
        sensor_label = QLabel("对应传感器值列:")
        self.sensor_combo = QComboBox()
        
        for i, name in enumerate(self.column_names):
            self.sensor_combo.addItem(f"{name} (列{i+1})")  # 添加列索引备注

        sensor_layout.addWidget(sensor_label)
        sensor_layout.addWidget(self.sensor_combo)

        layout.addLayout(sensor_layout)
        
        # 确定/取消按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def set_defaults(self, state_column=None, sensor_column=None):
        """
        设置默认选中的列
        
        Args:
            state_column (int or str): 状态变量列的索引或列名
            sensor_column (int or str): 传感器值列的索引或列名
        """
        if state_column is not None:
            if isinstance(state_column, int) and 0 <= state_column < self.state_combo.count():
                self.state_combo.setCurrentIndex(state_column)
            elif isinstance(state_column, str) and state_column in self.column_names:
                index = self.column_names.index(state_column)
                self.state_combo.setCurrentIndex(index)
        
        if sensor_column is not None:
            if isinstance(sensor_column, int) and 0 <= sensor_column < self.sensor_combo.count():
                self.sensor_combo.setCurrentIndex(sensor_column)
            elif isinstance(sensor_column, str) and sensor_column in self.column_names:
                index = self.column_names.index(sensor_column)
                self.sensor_combo.setCurrentIndex(index)
    
    def accept(self):
        """确认选择"""
        self.state_column = self.state_combo.currentIndex()
        self.sensor_column = self.sensor_combo.currentIndex()
        
        # 检查是否选择了相同的列
        if self.state_column == self.sensor_column:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "状态变量列和传感器值列不能相同，请重新选择。")
            return
        
        super().accept()


class StatesLookupWindow(QDialog):
    """状态变量检测窗口"""
    
    def __init__(self, data, state_column, capacitor_column, parent=None):
        super().__init__(parent)
        self.data = data
        self.state_column = state_column
        self.capacitor_column = capacitor_column
        
        # 获取状态列和电容列的数据
        self.state_data = [float(row[self.state_column]) for row in self.data[1:] if row[self.state_column]]
        self.capacitor_data = [float(row[self.capacitor_column]) for row in self.data[1:] if row[self.capacitor_column]]
        
        # 分析状态数据，找出连续为1的段
        self.state_segments = self._find_state_segments()
        
        # 初始化当前段的x_range
        self.current_segment_x_range = []
        
        self.setWindowTitle("状态变量检测")
        self.resize(1600, 900)  # 调整默认大小以适应不同分辨率
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)  # 支持最大化最小化
        
        # 初始化Matplotlib支持中文
        self.setup_matplotlib_chinese_support()
        
        # 居中显示窗口
        self.center()
        
        # 创建UI
        self.setup_ui()
        
        # 如果有状态段，显示第一个
        if self.state_segments:
            self.show_segment(0)
        
        # 在显示后强制刷新界面
        self.show()
        self.raise_()
        self.activateWindow()
    
    def center(self):
        """将窗口居中显示"""
        # 始终相对于屏幕居中
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def setup_matplotlib_chinese_support(self):
        """设置Matplotlib支持中文"""
        import matplotlib as mpl
        # 检测操作系统
        system = QApplication.instance().platformName() if QApplication.instance() else ""
        
        # 设置中文字体
        if system == "windows":
            mpl.rcParams['font.sans-serif'] = ['SimHei']  # Windows黑体
        elif system == "darwin":  # macOS
            mpl.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        else:  # Linux
            mpl.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
        
        # 解决负号显示问题
        mpl.rcParams['axes.unicode_minus'] = False
    
    def _find_state_segments(self):
        """
        查找状态数据中连续为1的段
        返回: [{"start": 起始索引, "end": 结束索引, "length": 长度}, ...]
        """
        segments = []
        if not self.state_data:
            return segments
            
        start = None
        for i, value in enumerate(self.state_data):
            # 检查是否是状态1的开始
            if value == 1 and start is None:
                start = i
            # 检查是否是状态1的结束
            elif value != 1 and start is not None:
                segments.append({
                    "start": start,
                    "end": i - 1,
                    "length": i - start
                })
                start = None
        
        # 处理最后一个段
        if start is not None:
            segments.append({
                "start": start,
                "end": len(self.state_data) - 1,
                "length": len(self.state_data) - start
            })
            
        return segments
    
    def setup_ui(self):
        """创建UI元素"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 减小边距以适应小分辨率
        main_layout.setSpacing(5)

        # 创建主水平分割器
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)  # 防止子控件被压缩到不可见

        # 左侧图表区域 - 使用垂直分割器
        left_widget = QSplitter(Qt.Vertical)
        left_widget.setChildrenCollapsible(False)  # 防止子控件被压缩到不可见

        # 第一个splitter - 显示所有数据曲线
        chart1_container = QWidget()
        chart1_layout = QVBoxLayout(chart1_container)
        chart1_layout.setContentsMargins(2, 2, 2, 2)
        chart1_layout.setSpacing(2)

        self.figure1 = Figure(figsize=(5, 3), dpi=100)  # 设置合适的默认大小
        self.canvas1 = FigureCanvas(self.figure1)
        self.canvas1.setMinimumSize(200, 150)  # 设置最小尺寸
        chart1_layout.addWidget(self.canvas1)

        # 第二个splitter - 显示当前选中段及其左右30个点
        chart2_container = QWidget()
        chart2_layout = QVBoxLayout(chart2_container)
        chart2_layout.setContentsMargins(2, 2, 2, 2)
        chart2_layout.setSpacing(2)

        self.figure2 = Figure(figsize=(5, 3), dpi=100)  # 设置合适的默认大小
        self.canvas2 = FigureCanvas(self.figure2)
        self.canvas2.setMinimumSize(200, 150)  # 设置最小尺寸
        chart2_layout.addWidget(self.canvas2)

        # 添加到左侧分割器
        left_widget.addWidget(chart1_container)
        left_widget.addWidget(chart2_container)
        left_widget.setSizes([400, 400])  # 设置合理的默认大小比例

        # 右侧控件区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(3, 3, 3, 3)
        right_layout.setSpacing(5)

        # 状态段选择下拉按钮
        segment_group = QGroupBox("状态段选择")
        segment_layout = QVBoxLayout(segment_group)

        # 创建下拉按钮
        self.segment_dropdown = QToolButton()
        self.segment_dropdown.setText("选择状态段")
        self.segment_dropdown.setPopupMode(QToolButton.InstantPopup)
        self.segment_dropdown.setToolButtonStyle(Qt.ToolButtonTextOnly)

        # 创建下拉菜单
        self.segment_menu = QMenu(self.segment_dropdown)
        self.segment_dropdown.setMenu(self.segment_menu)

        # 创建状态段菜单项
        self.segment_actions = []
        for i, segment in enumerate(self.state_segments):
            action = QAction(f"状态段 {i+1}(连1点数: {segment['length']})", self)
            action.triggered.connect(lambda checked, x=i: self.show_segment(x))
            self.segment_menu.addAction(action)
            self.segment_actions.append(action)

        segment_layout.addWidget(self.segment_dropdown)

        # 统计信息区域
        stats_group = QGroupBox("状态统计量")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_label = QTextEdit()
        self.stats_label.setReadOnly(True)
        self.stats_label.setAlignment(Qt.AlignTop)
        self.stats_label.setHtml("请选择一个状态段以查看统计信息")
        self.stats_label.setMinimumSize(200, 400)  # 设置最小尺寸
        self.stats_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        stats_layout.addWidget(self.stats_label)

        # 添加到右侧布局
        right_layout.addWidget(segment_group)
        right_layout.addWidget(stats_group)
        right_layout.addStretch()

        # 添加到主分割器
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([850, 350])  # 设置主分割器的默认大小比例

        main_layout.addWidget(main_splitter)

        # 创建图表子图
        self.ax1_cap = self.figure1.add_subplot(211)  # 电容值曲线
        self.ax1_state = self.figure1.add_subplot(212)  # 状态变量曲线

        self.ax2_cap = self.figure2.add_subplot(211)  # 选中段及周边电容值曲线
        self.ax2_state = self.figure2.add_subplot(212)  # 选中段及周边状态变量曲线

        # 连接鼠标事件
        self.canvas1.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas2.mpl_connect('button_press_event', self.on_mouse_press)
        
        # 初始化状态变量
        self.coord_tooltip = None

        # 在设置完UI后刷新画布
        self.figure1.tight_layout()
        self.figure2.tight_layout()
    
    def is_click_on_curve(self, x, y, ax, x_data, y_data, pixel_threshold=5):
        """检查点击是否在曲线上"""
        if not x_data or not ax:
            return False, None
        
        try:
            # 转换为像素坐标
            points = np.column_stack([x_data, y_data])
            pixels = ax.transData.transform(points)
            
            # 点击位置转换为像素坐标
            click_pixel = ax.transData.transform((x, y))
            click_x_pixel, click_y_pixel = click_pixel
            
            # 计算距离
            distances = np.sqrt((pixels[:, 0] - click_x_pixel)**2 + (pixels[:, 1] - click_y_pixel)**2)
            min_dist = np.min(distances)
            nearest_idx = np.argmin(distances)
            
            return (True, nearest_idx) if min_dist <= pixel_threshold else (False, None)
        except Exception:
            return False, None
    
    def show_coord_tooltip(self, x, y):
        """显示坐标提示框"""
        self.hide_coord_tooltip()
        
        try:
            from PyQt5.QtWidgets import QLabel
            from PyQt5.QtGui import QCursor
            
            self.coord_tooltip = QLabel(f"x={x:.0f}, y={y:.4f}", self)
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
        if not event.inaxes or event.xdata is None or event.ydata is None:
            return
        
        # 右键显示坐标
        if event.button == 3:  # 右键
            # 判断是哪个图表被点击
            if event.inaxes == self.ax1_cap:
                # 第一个图表的电容值曲线
                on_curve, idx = self.is_click_on_curve(event.xdata, event.ydata, 
                                                       self.ax1_cap, 
                                                       list(range(len(self.capacitor_data))), 
                                                       self.capacitor_data)
                if on_curve and idx < len(self.capacitor_data):
                    x_data = idx
                    y_data = self.capacitor_data[idx]
                    self.show_coord_tooltip(x_data, y_data)
            elif event.inaxes == self.ax1_state:
                # 第一个图表的状态变量曲线
                on_curve, idx = self.is_click_on_curve(event.xdata, event.ydata, 
                                                       self.ax1_state, 
                                                       list(range(len(self.state_data))), 
                                                       self.state_data)
                if on_curve and idx < len(self.state_data):
                    x_data = idx
                    y_data = self.state_data[idx]
                    self.show_coord_tooltip(x_data, y_data)
            elif event.inaxes == self.ax2_cap:
                # 获取当前显示的段数据
                if hasattr(self, 'current_segment_x_range'):
                    # 第二个图表的电容值曲线
                    on_curve, idx = self.is_click_on_curve(event.xdata, event.ydata, 
                                                           self.ax2_cap, 
                                                           self.current_segment_x_range, 
                                                           [self.capacitor_data[i] for i in self.current_segment_x_range])
                    if on_curve and idx < len(self.current_segment_x_range):
                        x_data = self.current_segment_x_range[idx]
                        y_data = self.capacitor_data[x_data]
                        self.show_coord_tooltip(x_data, y_data)
            elif event.inaxes == self.ax2_state:
                # 获取当前显示的段数据
                if hasattr(self, 'current_segment_x_range'):
                    # 第二个图表的状态变量曲线
                    on_curve, idx = self.is_click_on_curve(event.xdata, event.ydata, 
                                                           self.ax2_state, 
                                                           self.current_segment_x_range, 
                                                           [self.state_data[i] for i in self.current_segment_x_range])
                    if on_curve and idx < len(self.current_segment_x_range):
                        x_data = self.current_segment_x_range[idx]
                        y_data = self.state_data[x_data]
                        self.show_coord_tooltip(x_data, y_data)
            return
    
    def show_segment(self, segment_index):
        """显示指定状态段的数据"""
        if not self.state_segments or segment_index >= len(self.state_segments):
            return
            
        segment = self.state_segments[segment_index]
        
        # 更新下拉按钮文本
        self.segment_dropdown.setText(f"状态段 {segment_index+1} (连1点数: {segment['length']})")
        
        # 更新菜单项的选中状态
        for i, action in enumerate(self.segment_actions):
            if i == segment_index:
                action.setFont(QFont(action.font().family(), action.font().pointSize(), QFont.Bold))
            else:
                action.setFont(QFont(action.font().family(), action.font().pointSize(), QFont.Normal))
        
        # 绘制第一个splitter - 所有数据
        self._plot_all_data()
        
        # 绘制第二个splitter - 当前段及其周边数据
        self._plot_segment_data(segment)
        
        # 计算并显示统计信息
        self._calculate_and_show_stats(segment)
    
    def _plot_all_data(self):
        """绘制所有数据曲线"""
        # 清除之前的绘图
        self.ax1_cap.clear()
        self.ax1_state.clear()
        
        # 绘制电容值曲线
        self.ax1_cap.plot(self.capacitor_data, 'b-', linewidth=1, label='传感器值')
        self.ax1_cap.set_title("传感器值曲线", fontsize=10)
        self.ax1_cap.set_ylabel("传感器值", fontsize=9)
        self.ax1_cap.grid(True)
        self.ax1_cap.legend(fontsize=9)
        self.ax1_cap.tick_params(labelsize=8)
        # 禁用科学计数法
        self.ax1_cap.ticklabel_format(style='plain', axis='y')
        
        # 绘制状态变量曲线
        self.ax1_state.plot(self.state_data, 'r-', linewidth=1, label='状态变量')
        self.ax1_state.set_title("状态变量曲线", fontsize=10)
        self.ax1_state.set_xlabel("数据点", fontsize=9)
        self.ax1_state.set_ylabel("状态值", fontsize=9)
        self.ax1_state.grid(True)
        self.ax1_state.legend(fontsize=9)
        self.ax1_state.tick_params(labelsize=8)
        # 禁用科学计数法
        self.ax1_state.ticklabel_format(style='plain', axis='y')
        
        # 标注状态段
        for i, segment in enumerate(self.state_segments):
            self.ax1_state.axvspan(segment["start"], segment["end"], 
                                   alpha=0.3, color='yellow', 
                                   label=f"状态段{i+1}")
        
        if len(self.state_segments) > 0:
            self.ax1_state.legend(fontsize=9)
        self.canvas1.draw()
    
    def _plot_segment_data(self, segment):
        """绘制指定段及其周边数据"""
        # 清除之前的绘图
        self.ax2_cap.clear()
        self.ax2_state.clear()
        
        # 计算左右两侧连续0点的数量
        left_zeros = self._count_consecutive_zeros(segment["start"] - 1, -1, -1)
        right_zeros = self._count_consecutive_zeros(segment["end"] + 1, len(self.state_data), 1)
        
        # 确定实际要显示的点数（取两侧连续0点数量的最小值，最多30个点）
        display_points = min(30, left_zeros, right_zeros) if left_zeros > 0 and right_zeros > 0 else min(left_zeros, right_zeros, 30)
        
        # 计算显示范围
        start_idx = max(0, segment["start"] - display_points)
        end_idx = min(len(self.capacitor_data) - 1, segment["end"] + display_points)
        
        # 提取数据
        x_range = list(range(start_idx, end_idx + 1))
        cap_values = self.capacitor_data[start_idx:end_idx + 1]
        state_values = self.state_data[start_idx:end_idx + 1]
        
        # 保存当前显示的x_range，用于鼠标点击检测
        self.current_segment_x_range = x_range
        
        # 绘制电容值曲线
        self.ax2_cap.plot(x_range, cap_values, 'b-', linewidth=1, marker='o', markersize=2, label='传感器值')
        self.ax2_cap.set_title(f"状态段 {self.state_segments.index(segment)+1} 及周边数据 (点 {start_idx} 到 {end_idx})", fontsize=10)
        self.ax2_cap.set_ylabel("传感器值", fontsize=9)
        self.ax2_cap.grid(True)
        
        # 用不同颜色标示状态段
        self.ax2_cap.axvspan(segment["start"], segment["end"], 
                             alpha=0.3, color='yellow', label="选中状态段")
        self.ax2_cap.legend(fontsize=9)
        self.ax2_cap.tick_params(labelsize=8)
        # 禁用科学计数法
        self.ax2_cap.ticklabel_format(style='plain', axis='y')
        
        # 绘制状态变量曲线
        self.ax2_state.plot(x_range, state_values, 'r-', linewidth=1, marker='o', markersize=2, label='状态变量')
        self.ax2_state.set_title("状态变量", fontsize=10)
        self.ax2_state.set_xlabel("数据点", fontsize=9)
        self.ax2_state.set_ylabel("状态值", fontsize=9)
        self.ax2_state.grid(True)
        self.ax2_state.set_ylim(min(state_values) - 0.5, max(state_values) + 0.5)
        
        # 用不同颜色标示状态段
        self.ax2_state.axvspan(segment["start"], segment["end"], 
                               alpha=0.3, color='yellow', label="选中状态段")
        self.ax2_state.legend(fontsize=9)
        self.ax2_state.tick_params(labelsize=8)
        # 禁用科学计数法
        self.ax2_state.ticklabel_format(style='plain', axis='y')
        
        self.canvas2.draw()
    
    def _count_consecutive_zeros(self, start_idx, end_idx, step):
        """
        计算从start_idx开始，以step方向，连续为0的点的数量
        Args:
            start_idx: 起始索引
            end_idx: 结束索引
            step: 方向步长 (-1表示向左，1表示向右)
        Returns:
            连续为0的点的数量
        """
        count = 0
        i = start_idx
        
        while (step == -1 and i >= end_idx) or (step == 1 and i < end_idx):
            if 0 <= i < len(self.state_data) and self.state_data[i] == 0:
                count += 1
                i += step
            else:
                break
                
        return count
    
    def _calculate_and_show_stats(self, segment):
        """计算并显示统计信息"""
        # 计算状态为1时的统计数据
        state_1_caps = self.capacitor_data[segment["start"]:segment["end"] + 1]
        state_1_min = min(state_1_caps)
        state_1_max = max(state_1_caps)
        state_1_mean = np.mean(state_1_caps)
        state_1_pp = state_1_max - state_1_min
        
        # 计算左右两侧连续0点的数量
        left_zeros = self._count_consecutive_zeros(segment["start"] - 1, -1, -1)
        right_zeros = self._count_consecutive_zeros(segment["end"] + 1, len(self.state_data), 1)
        
        # 确定实际用于统计的点数（取两侧连续0点数量的最小值，最多30个点）
        stat_points = min(30, left_zeros, right_zeros) if left_zeros > 0 and right_zeros > 0 else min(left_zeros, right_zeros, 30)
        
        # 计算左边0值时的统计数据
        left_start = max(0, segment["start"] - stat_points)
        left_end = segment["start"]
        left_caps = self.capacitor_data[left_start:left_end] if left_end > left_start else []
        
        if left_caps:
            left_min = min(left_caps)
            left_max = max(left_caps)
            left_mean = np.mean(left_caps)
            left_pp = left_max - left_min
        else:
            left_min = left_max = left_mean = left_pp = 0
        
        # 计算右边0值时的统计数据
        right_start = segment["end"] + 1
        right_end = min(len(self.capacitor_data), segment["end"] + 1 + stat_points)
        right_caps = self.capacitor_data[right_start:right_end] if right_end > right_start else []
        
        if right_caps:
            right_min = min(right_caps)
            right_max = max(right_caps)
            right_mean = np.mean(right_caps)
            right_pp = right_max - right_min
        else:
            right_min = right_max = right_mean = right_pp = 0
        
        # 显示统计信息
        stats_text = f"""<b>状态段信息:</b><br>
起始点: {segment['start']}<br>
结束点: {segment['end']}<br>
段长: {segment['length']}<br><br>

<b>连1段:</b><br>
最小值: {state_1_min:.4f}<br>
最大值: {state_1_max:.4f}<br>
均值: {state_1_mean:.4f}<br>
峰峰值: {state_1_pp:.4f}<br><br>

<b>左侧0段(左侧共{left_zeros}点, 实统计{stat_points}点):</b><br>
最小值: {left_min:.4f}<br>
最大值: {left_max:.4f}<br>
均值: {left_mean:.4f}<br>
峰峰值: {left_pp:.4f}<br><br>

<b>右侧0段 (右侧共{right_zeros}点, 实统计{stat_points}点):</b><br>
最小值: {right_min:.4f}<br>
最大值: {right_max:.4f}<br>
均值: {right_mean:.4f}<br>
峰峰值: {right_pp:.4f}"""
        
        self.stats_label.setHtml(stats_text)