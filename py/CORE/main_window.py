# -*- coding: utf-8 -*-
"""
主窗口模块
"""

import os
import sys
from PyQt5.QtWidgets import (QLabel,QApplication, QMainWindow, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, 
                             QDesktopWidget, QStatusBar, QStackedWidget, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from DATAPROCESS.UI import DataMainWindow
# from SERIALCOM.UI import ComMainWindow

# 导入常量
from SETTINGS import (
    APP_NAME, DEFAULT_MAIN_MENU_SIZE, DEFAULT_WINDOW_SIZE, ICON
    )


class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(APP_NAME)
        self.resize(*DEFAULT_MAIN_MENU_SIZE)
        self.center()
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icon', ICON)
        if not os.path.exists(icon_path):
            # 如果上面的路径不存在，尝试在当前目录下查找图标
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'icon', ICON)
        if not os.path.exists(icon_path):
            # 如果仍然找不到，尝试在sys._MEIPASS中查找（PyInstaller打包后的路径）
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'icon', ICON)
        
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
            # 同时设置应用程序图标
            QApplication.instance().setWindowIcon(icon)
        
        # 设置窗口标志以支持最大化和最小化
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        
        # 创建堆叠窗口部件
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # 创建主菜单界面
        self.create_main_menu()
        
        # 创建功能界面
        self.create_function_windows()
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪 @Silver')
    
    def create_main_menu(self):
        """创建主菜单界面"""
        menu_widget = QWidget()
        main_layout = QVBoxLayout(menu_widget)
        
        # 创建标题
        title_label = QLabel(APP_NAME + " 数据处理工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        main_layout.addWidget(title_label)
        
        # 创建初始界面
        button_layout = QGridLayout()
        
        # CSV数据处理按钮
        self.csv_button = QPushButton('开始') # 当前只启用数据处理功能模块，如后续添加新模块时，需将按钮名与模块名对应
        self.csv_button.setMinimumSize(200, 100)
        self.csv_button.clicked.connect(self.show_csv_window)
        button_layout.addWidget(self.csv_button, 0, 0, Qt.AlignCenter)
        
        # # 串口助手按钮
        # self.serial_button = QPushButton('串口助手')
        # self.serial_button.setMinimumSize(200, 100)
        # self.serial_button.clicked.connect(self.show_com_window)
        # button_layout.addWidget(self.serial_button, 0, 1, Qt.AlignCenter)
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        
        self.stacked_widget.addWidget(menu_widget)
    
    def create_function_windows(self):
        """创建功能窗口"""
        # CSV数据处理窗口
        self.data_window = DataMainWindow()
        self.stacked_widget.addWidget(self.data_window)
        
        # # 串口助手窗口
        # self.com_window = ComMainWindow()
        # self.stacked_widget.addWidget(self.com_window)
    
    def show_main_menu(self):
        """显示主菜单"""
        self.stacked_widget.setCurrentIndex(0)
        self.resize(*DEFAULT_MAIN_MENU_SIZE)
        self.center()

    def show_csv_window(self):
        """显示CSV数据处理窗口"""
        self.stacked_widget.setCurrentIndex(1)
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.center()

    # def show_com_window(self):
    #     """显示串口助手窗口"""
    #     self.stacked_widget.setCurrentIndex(2)
    #     self.resize(*DEFAULT_WINDOW_SIZE)
    #     self.center()
    
    def center(self):
        """将窗口居中显示"""
        # 始终相对于屏幕居中
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())