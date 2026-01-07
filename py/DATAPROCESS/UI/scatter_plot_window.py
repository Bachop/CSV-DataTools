# -*- coding: utf-8 -*-
"""
散点图窗口模块
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

# 导入路径工具函数
from SETTINGS import (DEFAULT_WINDOW_SIZE, DEFAULT_DPI,
                      get_pic_directory, ensure_directory_exists,
                      bind_toolbar_save
                      )


class ScatterPlotWindow(QDialog):
    """用于显示散点图的窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("散点图")
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.center()
        
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
        """设置默认保存图片的文件名并绑定到工具栏保存行为"""
        try:
            default_name = os.path.splitext(filename)[0]
            bind_toolbar_save(self.toolbar, self.figure, default_filename=default_name, parent=self)
        except Exception:
            pass

    def setup_ui(self):
        """创建UI元素"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建水平分割器（主容器）
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # 创建图表区域
        chart_container = QWidget()
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建Matplotlib画布
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 添加工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        # 移除不需要的工具按钮
        actions = self.toolbar.actions()
        if len(actions) > 2:
            self.toolbar.removeAction(actions[2])  # 移除Zoom
            self.toolbar.removeAction(actions[1])  # 移除Pan
        
        # 创建单个子图
        self.ax = self.figure.add_subplot(111)  # 只创建一个子图
        
        # 将工具栏和画布添加到图表区域
        chart_layout.addWidget(self.toolbar)
        chart_layout.addWidget(self.canvas)
        
        # 将图表区域添加到主分割器
        self.main_splitter.addWidget(chart_container)
        
        main_layout.addWidget(self.main_splitter)