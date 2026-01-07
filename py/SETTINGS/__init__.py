"""
SETTINGS Package

项目配置和常量管理模块。

此目录包含项目的各种配置信息和常量定义，
负责管理应用程序的设置、路径工具和常量值。
"""

from .config import *
from .consts import *
from .paths import *
from .utils import *


# 定义公共接口
__all__ = [
    'config',
    'consts',
    'get_application_root',
    'get_log_directory',
    'get_pic_directory',
    'ensure_directory_exists',
    'get_save_filename',
    'get_open_filename',
    'get_open_filenames',
    'get_unique_filename',
    'generate_related_filename',
    'generate_log_filename',
    'generate_diff_filename',
    'get_save_in_pic',
    'bind_toolbar_save',
    'open_pic_directory',
    'open_log_directory'
]
