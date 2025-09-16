#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通用工具函数模块
包含各种通用的工具函数
"""

import os
from PyQt5.QtWidgets import QFileDialog


def get_save_filename(parent=None, title="保存文件", directory="", filter_str="所有文件 (*)", default_filename=""):
    """
    获取保存文件的路径
    
    Args:
        parent: 父窗口对象
        title: 对话框标题
        directory: 默认目录
        filter_str: 文件过滤器
        default_filename: 默认文件名
    
    Returns:
        tuple: (文件路径, 选择的过滤器) 如果用户取消则返回空字符串
    """
    if default_filename:
        directory = os.path.join(directory, default_filename) if directory else default_filename
        
    return QFileDialog.getSaveFileName(
        parent, 
        title, 
        directory, 
        filter_str
    )


def get_open_filename(parent=None, title="打开文件", directory="", filter_str="所有文件 (*)"):
    """
    获取打开文件的路径
    
    Args:
        parent: 父窗口对象
        title: 对话框标题
        directory: 默认目录
        filter_str: 文件过滤器
    
    Returns:
        tuple: (文件路径, 选择的过滤器) 如果用户取消则返回空字符串
    """
    return QFileDialog.getOpenFileName(
        parent,
        title,
        directory,
        filter_str
    )


def get_open_filenames(parent=None, title="打开文件", directory="", filter_str="所有文件 (*)"):
    """
    获取打开多个文件的路径
    
    Args:
        parent: 父窗口对象
        title: 对话框标题
        directory: 默认目录
        filter_str: 文件过滤器
    
    Returns:
        tuple: (文件路径列表, 选择的过滤器) 如果用户取消则返回空列表
    """
    return QFileDialog.getOpenFileNames(
        parent,
        title,
        directory,
        filter_str
    )


def generate_related_filename(original_filepath, suffix="", extension=None):
    """
    基于原始文件名生成相关文件名
    
    Args:
        original_filepath (str): 原始文件路径
        suffix (str): 要添加的后缀
        extension (str): 新的文件扩展名（可选，默认保持原扩展名）
    
    Returns:
        str: 生成的相关文件路径
    """
    if not original_filepath:
        return ""
    
    # 获取目录路径
    directory = os.path.dirname(original_filepath)
    
    # 获取文件名（不含路径）
    basename = os.path.basename(original_filepath)
    
    # 分离文件名和扩展名
    name_without_ext, original_ext = os.path.splitext(basename)
    
    # 使用指定扩展名或保持原扩展名
    new_ext = extension if extension is not None else original_ext
    
    # 生成新文件名
    new_filename = f"{name_without_ext}{suffix}{new_ext}"
    
    # 组合完整路径
    return os.path.join(directory, new_filename)


def generate_log_filename(original_filepath, suffix="-筛选", extension=".csv"):
    """
    生成日志相关文件名（用于保存筛选条件等）
    
    Args:
        original_filepath (str): 原始文件路径
        suffix (str): 要添加的后缀
        extension (str): 新的文件扩展名
    
    Returns:
        str: 生成的日志文件路径
    """
    return generate_related_filename(original_filepath, suffix, extension)


def generate_diff_filename(original_filepath, suffix="-diff", extension=".csv"):
    """
    生成差异数据文件名（用于保存处理后的差异数据）
    
    Args:
        original_filepath (str): 原始文件路径
        suffix (str): 要添加的后缀
        extension (str): 新的文件扩展名
    
    Returns:
        str: 生成的差异文件路径
    """
    return generate_related_filename(original_filepath, suffix, extension)