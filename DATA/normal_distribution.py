# -*- coding: utf-8 -*-
"""
正态分布分析模块
提供绘制正态分布图的功能
"""

import numpy as np
from scipy.stats import norm
from PyQt5.QtWidgets import QMessageBox


def plot_normal_distribution(data_viewer, plot_window_class):
    """
    绘制正态分布图，基于当前选中的列的可见数据。
    
    参数:
    data_viewer: 数据查看器实例，需要实现get_selected_columns和get_visible_data方法
    plot_window_class: PlotWindow类，用于显示图表
    """
    # 获取当前选中的列
    selected_columns = data_viewer.get_selected_columns()
    if not selected_columns:
        QMessageBox.warning(data_viewer, "警告", "请先选择要分析的列")
        return

    # 获取可见数据
    visible_data = data_viewer.get_visible_data()
    if visible_data is None or len(visible_data) == 0:
        QMessageBox.warning(data_viewer, "警告", "没有可用的数据进行分析")
        return

    # 提取选中列的数据
    try:
        data_to_plot = []
        column_labels = []
        for col in selected_columns:
            # 获取列标签
            header_item = data_viewer.table.horizontalHeaderItem(col)
            column_labels.append(header_item.text() if header_item else f"列{col+1}")
            
            # 提取该列的数据
            col_data = visible_data[:, col]
            # 过滤掉非数值数据
            numeric_data = []
            for x in col_data:
                try:
                    numeric_data.append(float(x))
                except (ValueError, TypeError):
                    continue  # 跳过非数值数据
                    
            if numeric_data:
                data_to_plot.append(numeric_data)
        
        if not data_to_plot:
            QMessageBox.warning(data_viewer, "警告", "选中的列中没有有效的数值数据")
            return

        # 准备数据用于PlotWindow显示
        x_data_dict = {}
        y_data_dict = {}
        labels = {}
        
        # 为每条曲线准备数据
        for i, (data, label) in enumerate(zip(data_to_plot, column_labels)):
            # 计算数据的均值和标准差
            mean = np.mean(data)
            std = np.std(data)
            
            # 生成直方图数据（修改为频次而不是比例）
            hist_vals, bin_edges = np.histogram(data, bins=30, density=False)  # 改为density=False
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            # 生成正态分布曲线数据（常规正态分布）- 调整为频次
            # 计算理论频次而不是概率密度
            bin_width = bin_edges[1] - bin_edges[0]
            y_norm = norm.pdf(bin_centers, mean, std) * len(data) * bin_width
            
            # 修改：使用 bar 图形绘制直方图
            x_data_dict[i] = bin_centers
            y_data_dict[i] = hist_vals
            labels[i] = f"{label} 直方图"
            
            # 为正态分布曲线使用不同的索引
            x_data_dict[i + len(data_to_plot)] = bin_centers
            y_data_dict[i + len(data_to_plot)] = y_norm
            labels[i + len(data_to_plot)] = f"{label} 正态分布"

        # 创建并显示图表
        plot_window = plot_window_class()
        # 修改：移除 plot_type 参数，改为使用 kind 参数（假设支持）
        plot_window.plot_multiple(x_data_dict, y_data_dict, labels, "正态分布分析", kind="bar")
        plot_window.show()

    except Exception as e:
        QMessageBox.critical(data_viewer, "错误", f"绘制正态分布时发生错误: {str(e)}")