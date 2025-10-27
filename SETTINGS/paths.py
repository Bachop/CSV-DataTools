# -*- coding: utf-8 -*-
"""
路径工具模块
用于统一管理程序中使用的各种目录路径
"""

import os
import sys

# 导入项目常量
from SETTINGS import LOG_DIR_NAME, PIC_DIR_NAME


# 缓存根目录路径，避免重复计算
_application_root = None


def get_application_root():
    """
    获取应用程序根目录路径
    
    Returns:
        str: 应用程序根目录路径
    """
    global _application_root
    
    if _application_root is not None:
        return _application_root
    
    if getattr(sys, 'frozen', False):
        # 打包后的exe程序，使用exe所在目录作为根目录
        _application_root = os.path.dirname(sys.executable)
    else:
        # Python脚本运行，查找项目根目录
        # 从当前文件开始向上查找包含py目录的目录作为项目根目录
        current_path = os.path.dirname(os.path.abspath(__file__))
        
        # 向上查找最多5级目录，寻找包含py子目录的目录
        for i in range(5):
            if os.path.exists(os.path.join(current_path, 'py')):
                _application_root = current_path
                break
            parent_path = os.path.dirname(current_path)
            # 如果已经到根目录，停止查找
            if parent_path == current_path:
                break
            current_path = parent_path
        
        # 如果没找到包含py的目录，则使用当前文件向上两级作为默认根目录
        if _application_root is None:
            _application_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return _application_root


def get_log_directory():
    """
    获取Log目录路径
    
    Returns:
        str: Log目录路径
    """
    root_path = get_application_root()
    log_dir = os.path.join(root_path, LOG_DIR_NAME)
    return log_dir


def get_pic_directory():
    """
    获取Pic目录路径
    
    Returns:
        str: Pic目录路径
    """
    root_path = get_application_root()
    pic_dir = os.path.join(root_path, PIC_DIR_NAME)
    return pic_dir


def ensure_directory_exists(directory_path):
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory_path (str): 目录路径
    """
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path, exist_ok=True)
        except OSError:
            # 目录可能在检查后被其他进程创建，忽略错误
            pass

def open_log_directory(self):
    """打开Log目录"""
    # 获取Log目录路径
    log_dir = get_log_directory()
    # 确保Log目录存在
    ensure_directory_exists(log_dir)
    
    # 在资源管理器中打开Log目录
    if os.name == 'nt':  # Windows
        # 使用标准的Windows命令行格式
        import subprocess
        subprocess.Popen(['explorer', log_dir], close_fds=True)
    elif os.name == 'posix':  # macOS/Linux
            import subprocess
            subprocess.Popen(['explorer', log_dir], close_fds=True)

def open_pic_directory(self):
    """打开Pic目录"""
    # 获取Pic目录路径
    pic_dir = get_pic_directory()
    # 确保Pic目录存在
    ensure_directory_exists(pic_dir)
    
    # 在资源管理器中打开Pic目录
    if os.name == 'nt':  # Windows
        # 使用标准的Windows命令行格式
        import subprocess
        subprocess.Popen(['explorer', pic_dir], close_fds=True)
    elif os.name == 'posix':  # macOS/Linux
        import subprocess
        subprocess.Popen(['explorer', pic_dir], close_fds=True)
