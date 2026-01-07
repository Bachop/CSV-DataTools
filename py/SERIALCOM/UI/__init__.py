"""
SERIALCOM.UI Package

串口通信用户界面模块。

此目录包含串口通信相关的用户界面实现，
如串口主窗口等。
"""

from .com_main_window import ComMainWindow

# 定义公共接口
__all__ = [
    'ComMainWindow'
]