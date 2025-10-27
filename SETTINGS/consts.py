# -*- coding: utf-8 -*-
"""
项目常量配置文件
用于集中管理项目中使用的各种常量值
"""

# 应用程序信息常量
APP_NAME = "CSV-DataTools"
ICON = "CSV-DataTools.ico"

# 界面相关常量
DEFAULT_MAIN_MENU_SIZE = (800, 600)
DEFAULT_WINDOW_SIZE = (1600, 900)

DEFAULT_BUTTON_SIZE = (200, 30)

# 文件相关常量
DEFAULT_ENCODING = "utf-8"
SUPPORTED_ENCODINGS = [
    "utf-8", "gbk", "gb2312", "ascii", "latin-1", 
    "cp936", "big5", "shift_jis", "utf-16"
]

TEMP_DIR_NAME = "temp"
DEFAULT_SAVE_DIR_NAME = "pic"
LOG_DIR_NAME = "Log"
PIC_DIR_NAME = "Pic"

# 文件类型过滤器
CSV_FILE_FILTER = "CSV文件 (*.csv)"
ALL_FILE_FILTER = "所有文件 (*)"
IMAGE_FILE_FILTER = "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)"

# 图表相关常量
DEFAULT_DPI = 300
MATPLOTLIB_CHINESE_SUPPORT = True

# 状态栏相关常量
DEFAULT_STATUS_MESSAGE = "就绪 @Silver"