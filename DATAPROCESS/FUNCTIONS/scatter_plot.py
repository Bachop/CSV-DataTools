# -*- coding: utf-8 -*-
"""
散点图绘制模块
"""
import os

import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QMessageBox
from DATAPROCESS.UI import ScatterPlotWindow

def plot_scatter(data_viewer):
    """
    根据选中数据绘制散点图
    
    参数:
    - data_viewer: DataViewer实例，包含选中的数据和表格
    
    功能说明:
    - 以选中数据所在列的表头为横坐标标签
    - 以选中数据所在行的第4列(索引为3)元素作为系列名
    - 绘制散点图
    """
    # 获取选中区域
    selected_ranges = data_viewer.table.selectedRanges()
    if not selected_ranges:
        QMessageBox.warning(data_viewer, "警告", "请先选择数据区域")
        return None
    
    # 检查是否存在第4列(索引为3)
    if data_viewer.table.columnCount() < 4:
        QMessageBox.warning(data_viewer, "警告", "该文件不可用此功能")
        return None
    
    # 获取选中区域的数据
    scatter_data = {}
    
    # 遍历所有选中区域
    for rg in selected_ranges:
        # 遍历选中的列
        for col in range(rg.leftColumn(), rg.rightColumn() + 1):
            # 跳过隐藏列
            if data_viewer.table.isColumnHidden(col):
                continue
            
            # 获取列标题作为X轴标签
            header_item = data_viewer.table.horizontalHeaderItem(col)
            x_label = header_item.text() if header_item else f"列{col+1}"
            
            # 遍历选中的行
            for row in range(rg.topRow(), rg.bottomRow() + 1):
                # 跳过隐藏行
                if data_viewer.table.isRowHidden(row):
                    continue
                
                # 获取第4列(索引为3)作为系列名
                series_item = data_viewer.table.item(row, 3)  # 第4列
                series_name = series_item.text() if series_item and series_item.text() else f"行{row+1}"
                
                # 获取当前单元格的值作为Y值
                item = data_viewer.table.item(row, col)
                if not item or not item.text():
                    continue
                
                try:
                    y_value = float(item.text())
                except (ValueError, TypeError):
                    continue  # 跳过非数值数据
                
                # 组织数据结构
                if series_name not in scatter_data:
                    scatter_data[series_name] = {
                        'x_labels': [],  # 列标题
                        'y_values': [],
                        'x_positions': [],
                        'series_labels': []  # 第4列的值，用作标签
                    }
                
                scatter_data[series_name]['x_labels'].append(x_label)
                scatter_data[series_name]['y_values'].append(y_value)
                scatter_data[series_name]['x_positions'].append(col)
                scatter_data[series_name]['series_labels'].append(series_name)  # 使用series_name作为标签
    
    # 检查是否有有效数据
    if not scatter_data:
        QMessageBox.warning(data_viewer, "警告", "选区中没有有效数值数据")
        return None
    
    # 创建散点图窗口
    plot_window = ScatterPlotWindow()
    plot_window.setWindowTitle(f"散点图 - {data_viewer.file_path.split('/')[-1]}")
    
    # 清空之前的图表
    plot_window.ax.clear()
    
    # 存储散点图数据，用于事件处理
    plot_window.scatter_data = scatter_data
    
    # 绘制散点图
    colors = plt.cm.Set1(np.linspace(0, 1, len(scatter_data)))  # 为不同系列分配颜色
    
    # 存储绘制的散点和标签
    plot_window.scatter_plots = []
    plot_window.annotations = {}
    
    # 优化性能：使用集合存储所有点的坐标
    plot_window.all_points = {}  # 用字典存储所有点的信息，提高查找效率
    
    for i, (series_name, data) in enumerate(scatter_data.items()):
        x_positions = data['x_positions']
        y_values = data['y_values']
        labels = data['series_labels']  # 使用第4列的值作为标签
        
        # 转换为numpy数组以提高性能
        x_array = np.array(x_positions)
        y_array = np.array(y_values)
        
        # 绘制散点，关闭picker以提高性能，改用自定义事件处理
        scatter = plot_window.ax.scatter(x_array, y_array, label=series_name, color=colors[i], s=60, alpha=0.7)
        plot_window.scatter_plots.append({
            'scatter': scatter,
            'x_positions': x_array,
            'y_values': y_array,
            'labels': labels,
            'series_index': i
        })
        
        # 存储每个点的信息，用于快速查找
        for j in range(len(x_positions)):
            point_key = (x_positions[j], y_values[j])
            plot_window.all_points[point_key] = {
                'label': labels[j],
                'series_index': i
            }
    
    # 设置图表属性
    plot_window.ax.set_xlabel('列')
    plot_window.ax.set_ylabel('数值')
    plot_window.ax.set_title('散点图')
    # 不再显示图例
    # plot_window.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plot_window.ax.grid(True, alpha=0.3)
    
    # 设置x轴刻度标签
    all_cols = set()
    all_labels = []
    for data in scatter_data.values():
        for pos, label in zip(data['x_positions'], data['x_labels']):
            if pos not in all_cols:
                all_cols.add(pos)
                all_labels.append((pos, label))
    
    # 按位置排序
    all_labels.sort()
    positions = [pos for pos, _ in all_labels]
    labels = [label for _, label in all_labels]
    
    if positions:
        plot_window.ax.set_xticks(positions)
        plot_window.ax.set_xticklabels(labels, rotation=45, ha='right')
    
    # 连接鼠标点击事件（使用更高效的事件处理）
    def on_click(event):
        # 只处理鼠标右键点击事件
        if event.button != 3:  # 3表示右键
            return
            
        # 确保点击在图形区域内
        if event.inaxes != plot_window.ax:
            return
            
        # 获取点击位置
        click_x, click_y = event.xdata, event.ydata
        
        # 查找最近的点
        min_distance = float('inf')
        closest_point = None
        
        # 遍历所有点，找到最近的点
        for (x, y), info in plot_window.all_points.items():
            distance = np.sqrt((x - click_x)**2 + (y - click_y)**2)
            if distance < min_distance:
                min_distance = distance
                closest_point = (x, y)
        
        # 如果最近的点在合理范围内，则显示/隐藏标签
        if min_distance < 0.1:  # 阈值可根据需要调整
            point_key = closest_point
            
            # 如果标签已存在则移除，否则创建新标签
            if point_key in plot_window.annotations:
                # 移除标签
                annotation = plot_window.annotations.pop(point_key)
                annotation.remove()
            else:
                # 创建新标签
                label = plot_window.all_points[point_key]['label']
                ann = plot_window.ax.annotate(label, point_key, xytext=(5, 5), 
                                             textcoords='offset points', fontsize=8,
                                             bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
                plot_window.annotations[point_key] = ann
                    
            # 刷新画布
            plot_window.canvas.draw()
    
    # 连接鼠标点击事件
    plot_window.canvas.mpl_connect('button_press_event', on_click)
    
    # 调整布局
    plot_window.figure.tight_layout()
    
    # 设置默认保存文件名与导入文件名一致
    plot_window.set_default_filename(os.path.basename(data_viewer.file_path))
    
    # 刷新画布
    plot_window.canvas.draw()
    
    # 显示窗口
    plot_window.show()
    plot_window.raise_()
    plot_window.activateWindow()
    
    return plot_window