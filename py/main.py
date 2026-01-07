# -*- coding: utf-8 -*-
"""
CSV数据处理程序 - 主程序模块
"""

import sys
import warnings
import os

# 过滤特定的弃用警告
warnings.filterwarnings("ignore", message="sipPyTypeDict() is deprecated", category=DeprecationWarning)

# 设置matplotlib后端
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# 导入项目常量
from SETTINGS import ICON

from CORE import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icon', ICON)
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 创建并显示主窗口
    main_window = MainWindow()
    main_window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()