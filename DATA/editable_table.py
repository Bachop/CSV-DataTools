# -*- coding: utf-8 -*-
"""
可编辑表格模块
"""

import numpy as np
from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QAbstractItemView, 
                             QMenu, QApplication, QInputDialog, QMessageBox,
                             QHeaderView)
from PyQt5.QtCore import Qt, QItemSelection, QItemSelectionModel, QItemSelectionRange, pyqtSignal


class EditableTable(QTableWidget):
    """可编辑的表格，支持右键菜单和优化的撤销/重做功能"""
    
    # 添加自定义信号
    contentChanged = pyqtSignal()
    
    # 撤销/重做命令类
    class EditCommand:
        """基础编辑命令类"""
        def undo(self, table):
            pass
        
        def redo(self, table):
            pass

    class CellChangeCommand(EditCommand):
        """单元格内容变化命令"""
        def __init__(self, row, col, old_text, new_text):
            self.row = row
            self.col = col
            self.old_text = old_text
            self.new_text = new_text
        
        def undo(self, table):
            if self.row < table.rowCount() and self.col < table.columnCount():
                item = table.item(self.row, self.col)
                if item:
                    item.setText(self.old_text)
                else:
                    table.setItem(self.row, self.col, QTableWidgetItem(self.old_text))
        
        def redo(self, table):
            if self.row < table.rowCount() and self.col < table.columnCount():
                item = table.item(self.row, self.col)
                if item:
                    item.setText(self.new_text)
                else:
                    table.setItem(self.row, self.col, QTableWidgetItem(self.new_text))
    
    class InsertRowCommand(EditCommand):
        """插入行命令"""
        def __init__(self, row):
            self.row = row
        
        def undo(self, table):
            if self.row < table.rowCount():
                table.removeRow(self.row)
        
        def redo(self, table):
            table.insertRow(self.row)
            # 为新行添加默认数据
            for col in range(table.columnCount()):
                table.setItem(self.row, col, QTableWidgetItem(""))
    
    class InsertColumnCommand(EditCommand):
        """插入列命令"""
        def __init__(self, col):
            self.col = col
        
        def undo(self, table):
            if self.col < table.columnCount():
                table.removeColumn(self.col)
        
        def redo(self, table):
            table.insertColumn(self.col)
            # 为新列添加默认数据
            for row in range(table.rowCount()):
                table.setItem(row, self.col, QTableWidgetItem(""))
    
    class DeleteRowCommand(EditCommand):
        """删除行命令"""
        def __init__(self, row, row_data):
            self.row = row
            self.row_data = row_data
        
        def undo(self, table):
            table.insertRow(self.row)
            # 恢复行数据
            for col, text in enumerate(self.row_data):
                if col < table.columnCount():
                    table.setItem(self.row, col, QTableWidgetItem(text))
        
        def redo(self, table):
            if self.row < table.rowCount():
                table.removeRow(self.row)
    
    class DeleteColumnCommand(EditCommand):
        """删除列命令"""
        def __init__(self, col, col_data, header_text):
            self.col = col
            self.col_data = col_data
            self.header_text = header_text
        
        def undo(self, table):
            table.insertColumn(self.col)
            # 恢复列标题
            header_item = QTableWidgetItem(self.header_text)
            table.setHorizontalHeaderItem(self.col, header_item)
            # 恢复列数据
            for row, text in enumerate(self.col_data):
                if row < table.rowCount():
                    table.setItem(row, self.col, QTableWidgetItem(text))
        
        def redo(self, table):
            if self.col < table.columnCount():
                table.removeColumn(self.col)
    
    class PasteCommand(EditCommand):
        """粘贴命令"""
        def __init__(self, start_row, start_col, old_data, new_data):
            self.start_row = start_row
            self.start_col = start_col
            self.old_data = old_data
            self.new_data = new_data
        
        def undo(self, table):
            # 恢复旧数据
            for row_idx, row_data in enumerate(self.old_data):
                for col_idx, text in enumerate(row_data):
                    row_pos = self.start_row + row_idx
                    col_pos = self.start_col + col_idx
                    if row_pos < table.rowCount() and col_pos < table.columnCount():
                        item = table.item(row_pos, col_pos)
                        if item:
                            item.setText(text)
                        else:
                            table.setItem(row_pos, col_pos, QTableWidgetItem(text))
        
        def redo(self, table):
            # 应用新数据
            for row_idx, row_data in enumerate(self.new_data):
                for col_idx, text in enumerate(row_data):
                    row_pos = self.start_row + row_idx
                    col_pos = self.start_col + col_idx
                    # 确保行和列存在
                    while row_pos >= table.rowCount():
                        table.setRowCount(row_pos + 1)
                    while col_pos >= table.columnCount():
                        table.setColumnCount(col_pos + 1)
                    # 设置单元格值
                    item = table.item(row_pos, col_pos)
                    if item:
                        item.setText(text)
                    else:
                        table.setItem(row_pos, col_pos, QTableWidgetItem(text))
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # 撤消/重做命令栈
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 50  # 减少历史记录数以提高性能
        
        # 用于跟踪单元格更改
        self._current_item = None
        self._current_text = ""
        
        # 自定义信号连接
        self.cellValueChanged = None  # 用于存储回调函数
        
        # 连接信号以跟踪更改
        self.itemChanged.connect(self.on_item_changed)
        self.currentItemChanged.connect(self.on_current_item_changed)
        
        # 列选择顺序跟踪
        self.column_selection_order = []  # 记录列选择顺序
        self.current_selection_start = None  # 当前选择的起始列
        self.drag_start_position = None  # 拖拽起始位置

        # 添加水平和垂直表头的右键菜单策略
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        # 修改表头右键菜单连接到统一的菜单方法
        self.horizontalHeader().customContextMenuRequested.connect(self.show_context_menu)
        self.verticalHeader().customContextMenuRequested.connect(self.show_context_menu)
        
        # 启用自定义选择行为
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            # 获取点击的列
            column = self.columnAt(event.pos().x())
            if column >= 0:  # 点击在有效列上
                self.current_selection_start = column
                # 如果点击的列不在当前选择中，则清空选择顺序
                if not self.isColumnSelected(column):
                    self.column_selection_order.clear()
                    self.column_selection_order.append(column)
                else:
                    # 如果点击的列已在选择中，移到列表末尾（表示重新选择）
                    if column in self.column_selection_order:
                        self.column_selection_order.remove(column)
                    self.column_selection_order.append(column)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，实现自定义拖拽选择"""
        if event.buttons() & Qt.LeftButton and self.drag_start_position:
            # 获取当前位置
            current_pos = event.pos()
            
            # 计算选择区域
            start_row = self.rowAt(self.drag_start_position.y())
            start_col = self.columnAt(self.drag_start_position.x())
            end_row = self.rowAt(current_pos.y())
            end_col = self.columnAt(current_pos.x())
            
            # 确保行和列索引有效
            if start_row >= 0 and start_col >= 0 and end_row >= 0 and end_col >= 0:
                # 确定选择范围的边界
                top = min(start_row, end_row)
                bottom = max(start_row, end_row)
                left = min(start_col, end_col)
                right = max(start_col, end_col)
                
                # 创建只包含可见单元格的选择
                self.selectVisibleCells(top, left, bottom, right)
        
        super().mouseMoveEvent(event)
    
    def selectVisibleCells(self, top_row, left_col, bottom_row, right_col):
        """选择指定范围内的可见单元格"""
        # 清除当前选择
        self.clearSelection()
        
        # 创建选择模型
        selection_model = self.selectionModel()
        
        # 遍历指定范围内的所有单元格
        for row in range(top_row, bottom_row + 1):
            for col in range(left_col, right_col + 1):
                # 检查行和列是否可见
                if not self.isRowHidden(row) and not self.isColumnHidden(col):
                    # 选择可见的单元格
                    model_index = self.model().index(row, col)
                    selection_model.select(model_index, QItemSelectionModel.Select)
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.drag_start_position:
            # 获取释放位置的列
            release_column = self.columnAt(event.pos().x())
            start_column = self.columnAt(self.drag_start_position.x())
            
            # 如果是拖拽选择（起始和结束位置不同）
            if start_column >= 0 and release_column >= 0 and start_column != release_column:
                # 确定拖拽方向
                if start_column < release_column:
                    # 从左到右拖拽
                    first_col, last_col = start_column, release_column
                else:
                    # 从右到左拖拽
                    first_col, last_col = release_column, start_column
                
                # 清空当前选择顺序并按拖拽方向添加列
                self.column_selection_order.clear()
                
                # 只添加可见的列到选择顺序中
                for col in range(first_col, last_col + 1):
                    if not self.isColumnHidden(col):
                        self.column_selection_order.append(col)
            
            self.drag_start_position = None
        
        super().mouseReleaseEvent(event)
    
    def isColumnSelected(self, column):
        """检查列是否被选择"""
        return column in [item.column() for item in self.selectedItems()]
    
    def get_selection_order(self):
        """获取列选择顺序"""
        # 过滤掉已不存在的列和隐藏的列
        valid_columns = [col for col in self.column_selection_order 
                        if col < self.columnCount() and not self.isColumnHidden(col)]
        return valid_columns
    
    def on_current_item_changed(self, current, previous):
        """当当前单元格改变时调用"""
        if current:
            self._current_item = current
            self._current_text = current.text()
        else:
            self._current_item = None
            self._current_text = ""

    def on_item_changed(self, item):
        """当表格项发生变化时调用"""
        # 只有当变化来自用户编辑时才记录命令
        if self._current_item is item and item.text() != self._current_text:
            row = item.row()
            col = item.column()
            command = self.CellChangeCommand(row, col, self._current_text, item.text())
            self.push_command(command)
            # 更新当前文本
            self._current_text = item.text()
            
            # 只有在实际内容变化时发射信号
            # 发射单元格值变化信号
            if hasattr(self, 'cellValueChanged') and self.cellValueChanged is not None:
                self.cellValueChanged(row, col, item.text())
            
            # 发射内容变化信号
            self.contentChanged.emit()
        elif self._current_item is item:
            # 更新当前文本以保持同步
            self._current_text = item.text()
    
    def keyPressEvent(self, event):
        """处理键盘事件，支持Ctrl+Z和Ctrl+Y快捷键"""
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Z:
            self.undo()
            return
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Y:
            self.redo()
            return
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_A:
            self.selectAll()
            # 清空选择顺序并添加所有列
            self.column_selection_order.clear()
            self.column_selection_order = list(range(self.columnCount()))
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
            self.copy_selection()
            return
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
            self.paste_from_clipboard()
            return
        elif event.key() == Qt.Key_Delete:
            self.delete_selected_items()
            return
        super().keyPressEvent(event)
    
    def delete_selected_items(self):
        """删除选中的项目"""
        selected_items = self.selectedItems()
        if not selected_items:
            return
            
        # 记录更改命令
        for item in selected_items:
            row, col = item.row(), item.column()
            if item.text():  # 只有当单元格有内容时才记录命令
                command = self.CellChangeCommand(row, col, item.text(), "")
                self.push_command(command)
                item.setText("")
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        # 检查是否在水平表头区域点击
        if self.horizontalHeader().underMouse():
            # 获取点击的列索引
            column = self.horizontalHeader().logicalIndexAt(pos)
            if column >= 0:
                # 选中整列
                self.selectColumn(column)
        # 检查是否在垂直表头区域点击
        elif self.verticalHeader().underMouse():
            # 获取点击的行索引
            row = self.verticalHeader().logicalIndexAt(pos)
            if row >= 0:
                # 选中整行
                self.selectRow(row)
        
        # 创建统一的右键菜单
        menu = QMenu(self)
        
        # 检查是否在水平表头区域点击
        if self.horizontalHeader().underMouse():
            self._add_horizontal_header_actions(menu, pos)
        # 检查是否在垂直表头区域点击
        elif self.verticalHeader().underMouse():
            self._add_vertical_header_actions(menu, pos)
        # 否则是在表格单元格区域点击
        else:
            self._add_cell_actions(menu)
        
        menu.exec_(self.mapToGlobal(pos))

    def _add_cell_actions(self, menu):
        """添加单元格右键菜单项"""
        # 添加菜单项
        actions = [
            ("复制", self.copy_selection),
            ("剪切", self.cut_selection),
            ("粘贴", self.paste_from_clipboard),
            None,  # 分隔符
            ("在下方插入行", lambda: self.insert_row_at(self.currentRow())),
            ("在右侧插入列", lambda: self.insert_column_at(self.currentColumn())),
            None,  # 分隔符
            ("删除所在行", lambda: self.delete_row_at(self.currentRow())),
            ("删除所在列", lambda: self.delete_column_at(self.currentColumn())),
            None,  # 分隔符
            ("撤销", self.undo),
            ("重做", self.redo)
        ]
        
        for action in actions:
            if action is None:
                menu.addSeparator()
            else:
                name, func = action
                qaction = menu.addAction(name)
                # 设置快捷键提示和状态
                if name == "撤销":
                    qaction.setShortcut("Ctrl+Z")
                    qaction.setEnabled(len(self.undo_stack) > 0)
                    qaction.triggered.connect(func)
                elif name == "重做":
                    qaction.setShortcut("Ctrl+Y")
                    qaction.setEnabled(len(self.redo_stack) > 0)
                    qaction.triggered.connect(func)
                else:
                    qaction.triggered.connect(func)

    def _add_horizontal_header_actions(self, menu, pos):
        """添加水平表头右键菜单项"""
        # 获取点击的列索引
        column = self.horizontalHeader().logicalIndexAt(pos)
        if column < 0:
            return
            
        # 添加修改列名选项
        rename_action = menu.addAction("修改列名")
        rename_action.triggered.connect(lambda: self.rename_column(column))
        
        # 添加其他通用选项
        menu.addSeparator()
        insert_action = menu.addAction("在右侧插入列")
        insert_action.triggered.connect(lambda: self.insert_column_at(column))
        
        delete_action = menu.addAction("删除该列")
        delete_action.triggered.connect(lambda: self.delete_column_at(column))
        
        menu.addSeparator()
        
        # 添加通用操作
        self._add_common_actions(menu)

    def _add_vertical_header_actions(self, menu, pos):
        """添加垂直表头右键菜单项"""
        # 获取点击的行索引
        row = self.verticalHeader().logicalIndexAt(pos)
        if row < 0:
            return
            
        # 添加行操作选项
        insert_action = menu.addAction("在下方插入行")
        insert_action.triggered.connect(lambda: self.insert_row_at(row))
        
        delete_action = menu.addAction("删除该行")
        delete_action.triggered.connect(lambda: self.delete_row_at(row))
        
        menu.addSeparator()
        
        # 添加通用操作
        self._add_common_actions(menu)

    def _add_common_actions(self, menu):
        """添加通用操作菜单项"""
        # 添加复制、剪切、粘贴操作
        copy_action = menu.addAction("复制")
        copy_action.triggered.connect(self.copy_selection)
        
        cut_action = menu.addAction("剪切")
        cut_action.triggered.connect(self.cut_selection)
        
        paste_action = menu.addAction("粘贴")
        paste_action.triggered.connect(self.paste_from_clipboard)
        
        menu.addSeparator()
        
        # 添加撤销/重做操作
        undo_action = menu.addAction("撤销")
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setEnabled(len(self.undo_stack) > 0)
        undo_action.triggered.connect(self.undo)
        
        redo_action = menu.addAction("重做")
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setEnabled(len(self.redo_stack) > 0)
        redo_action.triggered.connect(self.redo)

    def rename_column(self, column):
        """修改列名"""
        if column < 0 or column >= self.columnCount():
            return
            
        # 获取当前列名
        header_item = self.horizontalHeaderItem(column)
        current_name = header_item.text() if header_item else f"列{column+1}"
        
        # 弹出输入对话框
        new_name, ok = QInputDialog.getText(self, "修改列名", "请输入新的列名:", text=current_name)
        
        if ok and new_name:
            # 检查新列名是否与当前列名相同
            if new_name == current_name:
                return
                
            # 检查新列名是否为空
            if not new_name.strip():
                QMessageBox.warning(self, "警告", "列名不能为空！")
                return
                
            # 更新列名
            if not header_item:
                header_item = QTableWidgetItem(new_name)
                self.setHorizontalHeaderItem(column, header_item)
            else:
                header_item.setText(new_name)

    def paste_from_clipboard(self):
        """从剪贴板粘贴数据"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if not mime_data.hasText():
            return
            
        # 获取剪贴板文本
        text = mime_data.text()
        if not text:
            return
            
        # 解析剪贴板数据
        rows = text.split('\n')
        # 移除最后的空行（如果有的话）
        if rows and not rows[-1]:
            rows.pop()
            
        if not rows:
            return
            
        # 获取当前选中的起始单元格
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            start_row, start_col = 0, 0
        else:
            start_row = selected_ranges[0].topRow()
            start_col = selected_ranges[0].leftColumn()
            
        # 准备旧数据和新数据
        old_data = []
        new_data = []
        for row_idx, row in enumerate(rows):
            cols = row.split('\t')
            old_row_data = []
            new_row_data = []
            for col_idx, value in enumerate(cols):
                row_pos = start_row + row_idx
                col_pos = start_col + col_idx
                # 保存旧值
                old_item = self.item(row_pos, col_pos) if row_pos < self.rowCount() and col_pos < self.columnCount() else None
                old_row_data.append(old_item.text() if old_item else "")
                new_row_data.append(value)
            old_data.append(old_row_data)
            new_data.append(new_row_data)
        
        # 执行粘贴操作
        command = self.PasteCommand(start_row, start_col, old_data, new_data)
        command.redo(self)
        self.push_command(command)

    def copy_selection(self):
        """复制选中区域到剪贴板"""
        selected_items = self.selectedItems()
        if not selected_items:
            return
            
        # 按行和列组织数据
        data_dict = {}
        for item in selected_items:
            row, col = item.row(), item.column()
            if row not in data_dict:
                data_dict[row] = {}
            data_dict[row][col] = item.text()
            
        # 获取选区范围
        rows = sorted(data_dict.keys())
        if not rows:
            return
            
        cols = set()
        for row_data in data_dict.values():
            cols.update(row_data.keys())
        cols = sorted(cols)
        
        # 构建制表符分隔的文本
        lines = []
        for row in rows:
            row_data = data_dict.get(row, {})
            line = "\t".join(row_data.get(col, "") for col in cols)
            lines.append(line)
            
        text = "\n".join(lines)
        
        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def cut_selection(self):
        """剪切选中区域"""
        self.copy_selection()  # 先复制
        
        # 然后清空选中单元格的内容
        selected_items = self.selectedItems()
        for item in selected_items:
            row, col = item.row(), item.column()
            command = self.CellChangeCommand(row, col, item.text(), "")
            self.push_command(command)
            item.setText("")
    
    def push_command(self, command):
        """将命令推送到撤销栈，并清空重做栈"""
        self.undo_stack.append(command)
        # 限制撤销历史记录数量
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        # 清空重做栈
        self.redo_stack.clear()
    
    def undo(self):
        """撤销上一个操作"""
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo(self)
            self.redo_stack.append(command)
            # 限制重做历史记录数量
            if len(self.redo_stack) > self.max_history:
                self.redo_stack.pop(0)
    
    def redo(self):
        """重做上一个操作"""
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.redo(self)
            self.undo_stack.append(command)
            # 限制撤销历史记录数量
            if len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)
    
    def insert_row_at(self, row):
        """在指定行下面插入新行"""
        if row >= -1:  # 允许在第0行之前插入
            command = self.InsertRowCommand(row + 1)
            command.redo(self)
            self.push_command(command)
            # 发射内容变化信号
            self.contentChanged.emit()
    
    def insert_column_at(self, col):
        """在指定列右边插入新列"""
        if col >= -1:  # 允许在第0列之前插入
            command = self.InsertColumnCommand(col + 1)
            command.redo(self)
            self.push_command(command)
            # 发射内容变化信号
            self.contentChanged.emit()
    
    def delete_row_at(self, row):
        """删除指定行"""
        if row >= 0 and row < self.rowCount():
            # 保存行数据以支持撤销
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            
            command = self.DeleteRowCommand(row, row_data)
            command.redo(self)
            self.push_command(command)
    
    def delete_column_at(self, col):
        """删除指定列"""
        if col >= 0 and col < self.columnCount():
            # 保存列数据和标题以支持撤销
            col_data = []
            for row in range(self.rowCount()):
                item = self.item(row, col)
                col_data.append(item.text() if item else "")
            
            header_item = self.horizontalHeaderItem(col)
            header_text = header_item.text() if header_item else f"列{col+1}"
            
            command = self.DeleteColumnCommand(col, col_data, header_text)
            command.redo(self)
            self.push_command(command)