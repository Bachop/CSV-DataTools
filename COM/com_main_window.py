# -*- coding: utf-8 -*-
"""
串口助手主窗口模块

依赖库:
- pyserial: 用于串口通信功能
"""

import sys
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QDesktopWidget, QStatusBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import serial.tools.list_ports
import os


class ComMainWindow(QWidget):
    """串口助手主窗口类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建顶部按钮布局
        top_layout = QHBoxLayout()
        self.back_button = QPushButton("返回主菜单")
        self.back_button.clicked.connect(self.back_to_main)
        top_layout.addWidget(self.back_button)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)
        
        # 创建串口选择区域
        com_selection_layout = QHBoxLayout()
        
        # 串口选择标签
        com_label = QLabel("选择串口:")
        com_selection_layout.addWidget(com_label)
        
        # 串口下拉选框
        self.combo_box = QComboBox()
        com_selection_layout.addWidget(self.combo_box)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_ports)
        com_selection_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(com_selection_layout)
        
        # 添加占位符
        placeholder_label = QLabel("串口助手功能正在开发中...")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 20px;")
        main_layout.addWidget(placeholder_label)
        
        # 状态栏
        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)
        self.status_bar.showMessage('就绪 @Silver')
        
        # 初始化串口列表（在status_bar创建后再调用）
        self.refresh_ports()
    
    def back_to_main(self):
        """返回主菜单"""
        # 通过父级关系找到主窗口并切换到主菜单
        # self.parent()返回QStackedWidget，需要再往上找一层才是主窗口
        stacked_widget = self.parent()
        if stacked_widget:
            main_window = stacked_widget.parent()
            if main_window and hasattr(main_window, 'show_main_menu'):
                main_window.show_main_menu()
    
    def refresh_ports(self):
        """刷新串口列表"""
        # 清空现有选项
        self.combo_box.clear()
        
        # 获取可用串口列表
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.combo_box.addItem(f"{port.device} - {port.description}")
        
        if not ports:
            self.combo_box.addItem("未找到可用串口")
            self.status_bar.showMessage('未找到可用串口 @Silver')
        else:
            self.status_bar.showMessage(f'找到 {len(ports)} 个可用串口 @Silver')
    
