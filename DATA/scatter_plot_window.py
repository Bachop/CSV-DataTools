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


class ScatterPlotWindow(QDialog):
    """用于显示散点图的窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("散点图")
        self.resize(1600, 900)
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
        # 通常第一个是Home，第二个是Pan（移动），第三个是Zoom（放大）
        if len(actions) > 2:
            self.toolbar.removeAction(actions[2])  # 移除Zoom
            self.toolbar.removeAction(actions[1])  # 移除Pan
        
        # 创建单个子图
        self.ax = self.figure.add_subplot(111)  # 只创建一个子图
        
        # 将工具栏和画布添加到图表区域
        chart_layout.addWidget(self.toolbar)
        chart_layout.addWidget(self.canvas)
        
        chart_layout.addWidget(self.canvas)
        
        # 将图表区域添加到主分割器
        self.main_splitter.addWidget(chart_container)
        
        main_layout.addWidget(self.main_splitter)