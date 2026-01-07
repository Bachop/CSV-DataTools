#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
通用工具函数模块
包含各种通用的工具函数
"""

import os
import re
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

def get_unique_filename(filepath):
    """
    获取唯一的文件名，如果文件已存在则添加序号
    
    Args:
        filepath (str): 原始文件路径
    
    Returns:
        str: 唯一的文件路径
    """
    # 如果文件不存在，直接返回原路径
    if not os.path.exists(filepath):
        return filepath
    
    # 分离目录、文件名和扩展名
    directory = os.path.dirname(filepath)
    basename = os.path.basename(filepath)
    name, ext = os.path.splitext(basename)
    
    # 查找文件名中是否已经包含序号模式 (数字)
    # 匹配类似 "filename(1)" 或 "filename(2)" 的模式
    pattern = re.compile(r'^(.*)\((\d+)\)$')
    match = pattern.match(name)
    
    if match:
        # 如果已经有序号，提取基础文件名和当前序号
        base_name = match.group(1)
        counter = int(match.group(2))
    else:
        # 如果没有序号，基础文件名为当前文件名，序号从1开始
        base_name = name
        counter = 1
    
    # 循环查找第一个不存在的文件名
    while True:
        new_filename = f"{base_name}({counter}){ext}"
        new_filepath = os.path.join(directory, new_filename)
        if not os.path.exists(new_filepath):
            return new_filepath
        counter += 1

def get_save_in_pic(parent=None, title="保存文件", default_filename="", filter_str="所有文件 (*)"):
    """
    在 Pic 目录下打开保存文件对话框并返回选择的路径。

    会确保 Pic 目录存在，不修改当前工作目录。
    返回与 `QFileDialog.getSaveFileName` 相同的格式： (filepath, selected_filter)
    """
    try:
        from .paths import get_pic_directory, ensure_directory_exists

        pic_dir = get_pic_directory()
        ensure_directory_exists(pic_dir)

        default_path = os.path.join(pic_dir, default_filename) if default_filename else pic_dir
        return get_save_filename(parent, title, default_path, filter_str)
    except Exception:
        # 如果发生错误，退回到通用保存对话框调用
        return get_save_filename(parent, title, default_filename, filter_str)


def bind_toolbar_save(toolbar, figure, default_filename="", parent=None, filter_str="PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;PDF Files (*.pdf);;SVG Files (*.svg)", dpi=None):
    """
    将一个自定义的保存行为绑定到 Matplotlib 的 `NavigationToolbar` 的 `save_figure` 方法。

    Args:
        toolbar: Matplotlib NavigationToolbar 实例（toolbar.save_figure 将被替换）
        figure: Matplotlib Figure 实例，用于保存图片
        default_filename: 保存对话框的默认文件名（不包含路径）
        parent: 对话框父窗口
        filter_str: 文件过滤器字符串，传递给保存对话框
        dpi: 保存时使用的 DPI，若为 None 则使用 SETTINGS.consts.DEFAULT_DPI

    Operations: 
        会先保存原始的 `save_figure` 到 `toolbar._original_save_figure`（若不存在），
        并替换为一个调用 `get_save_in_pic` 的函数，使用 `get_unique_filename` 避免覆盖。
        不会改变当前工作目录。
    """
    try:
        from .paths import get_pic_directory, ensure_directory_exists
        from . import get_save_in_pic, get_unique_filename
        from SETTINGS.consts import DEFAULT_DPI as CONST_DEFAULT_DPI
    except Exception:
        from SETTINGS import get_save_in_pic, get_unique_filename
        from SETTINGS.consts import DEFAULT_DPI as CONST_DEFAULT_DPI

    if not hasattr(toolbar, '_original_save_figure'):
        try:
            toolbar._original_save_figure = toolbar.save_figure
        except Exception:
            toolbar._original_save_figure = None

    def _custom_save():
        try:
            # 打开 Pic 目录下的保存对话框（不切换 cwd）
            file_path, _ = get_save_in_pic(parent or toolbar, "保存图片", default_filename, filter_str)
            if file_path:
                unique_path = get_unique_filename(file_path)
                save_dpi = dpi if dpi is not None else CONST_DEFAULT_DPI
                try:
                    figure.savefig(unique_path, dpi=save_dpi, bbox_inches='tight')
                except Exception:
                    # 尝试使用原 toolbar 的保存方法作为回退
                    if hasattr(toolbar, '_original_save_figure') and toolbar._original_save_figure:
                        try:
                            toolbar._original_save_figure()
                        except Exception:
                            pass
        except Exception:
            # 保持静默失败以不影响 UI
            pass

    try:
        toolbar.save_figure = _custom_save
    except Exception:
        # 忽略不可替换的情况
        pass