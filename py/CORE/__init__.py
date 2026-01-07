"""
CORE Package

包含应用程序的核心组件和主窗口模块。

此目录包含主窗口逻辑和其他核心功能模块，
负责协调不同功能模块之间的交互。
"""

from .main_window import MainWindow

# 定义公共接口
__all__ = ['MainWindow']
