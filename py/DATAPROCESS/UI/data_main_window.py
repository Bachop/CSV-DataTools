# -*- coding: utf-8 -*-
"""
CSV数据处理主窗口模块
"""

import os
import sys
import csv
from functools import partial

from PyQt5.QtWidgets import (QInputDialog,QLineEdit,QApplication, QAbstractItemView, QMainWindow, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, 
                             QTabWidget, QDesktopWidget, QStatusBar, QMenu, QAction, QTabBar,
                             QScrollBar, QStyle, QFrame)
from PyQt5.QtCore import Qt, QRect, QPoint, QMimeData, pyqtSignal, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent, QDragLeaveEvent, QPainter, QDrag, QIcon

from SETTINGS import (
                                                APP_NAME, DEFAULT_WINDOW_SIZE, CSV_FILE_FILTER, ALL_FILE_FILTER,
                                                DEFAULT_BUTTON_SIZE, ICON,
                                                get_log_directory, ensure_directory_exists, 
                                                open_log_directory, open_pic_directory, get_open_filenames
                                            ) 

class DraggableTabBar(QTabBar):
    """支持拖拽排序的标签栏"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.drag_start_pos = None
        self.drag_drop_pos = None
        self.drag_tab_index = -1
        self.main_window = None

    def setMainWindow(self, main_window):
        """设置主窗口引用"""
        self.main_window = main_window

    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.drag_tab_index = self.tabAt(self.drag_start_pos)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and self.drag_start_pos is not None:
            # 计算鼠标移动距离
            distance = (event.pos() - self.drag_start_pos).manhattanLength()
            if distance >= QApplication.startDragDistance():
                self.start_drag()
        super().mouseMoveEvent(event)

    def start_drag(self):
        """开始拖拽操作"""
        if self.drag_tab_index == -1:
            return
            
        # 创建MIME数据
        mime_data = QMimeData()
        mime_data.setData('application/x-tab-index', str(self.drag_tab_index).encode())
        
        # 创建拖拽对象
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # 开始拖拽操作，允许在整个屏幕范围内拖拽
        drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        if event.mimeData().hasFormat('application/x-tab-index'):
            event.acceptProposedAction()
            self.drag_drop_pos = event.pos()
            self.update()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """处理拖拽移动事件"""
        if event.mimeData().hasFormat('application/x-tab-index'):
            event.acceptProposedAction()
            self.drag_drop_pos = event.pos()
            self.update()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        """处理拖拽离开事件"""
        self.drag_drop_pos = None
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        """处理拖拽释放事件"""
        if event.mimeData().hasFormat('application/x-tab-index'):
            # 获取源标签页索引
            source_index_data = event.mimeData().data('application/x-tab-index')
            source_index = int(source_index_data.data().decode())
            
            # 获取目标标签页索引
            target_index = self.tabAt(event.pos())
            
            # 如果目标位置有效且不等于源位置，则移动标签页
            if target_index != -1 and target_index != source_index:
                self.move_tab(source_index, target_index)
                event.acceptProposedAction()
            
            self.drag_drop_pos = None
            self.update()
        else:
            super().dropEvent(event)

    def move_tab(self, source_index, target_index):
        """移动标签页"""
        # 获取父级QTabWidget
        tab_widget = self.parent()
        if not tab_widget:
            return
            
        # 获取widget和标签信息
        widget = tab_widget.widget(source_index)
        text = tab_widget.tabText(source_index)
        icon = tab_widget.tabIcon(source_index)
        tooltip = tab_widget.tabToolTip(source_index)
        whats_this = tab_widget.tabWhatsThis(source_index)
        
        # 根据拖拽方向调整目标索引
        # 如果从前往后拖拽，插入到目标标签页之后
        # 如果从后往前拖拽，插入到目标标签页之前
        if source_index < target_index:
            target_index += 1
            
        # 移除源标签页
        tab_widget.removeTab(source_index)
        
        # 在新位置插入标签页
        # 修正：由于移除了源标签页，如果从前往后拖拽，需要调整目标索引
        if source_index < target_index:
            target_index -= 1
            
        tab_widget.insertTab(target_index, widget, icon, text)
        tab_widget.setTabToolTip(target_index, tooltip)
        tab_widget.setTabWhatsThis(target_index, whats_this)
        
        # 设置为当前标签页
        tab_widget.setCurrentIndex(target_index)

    def paintEvent(self, event):
        """处理绘制事件"""
        super().paintEvent(event)
        
        # 绘制拖拽指示器
        if self.drag_drop_pos:
            painter = QPainter(self)
            painter.setPen(Qt.red)
            painter.setBrush(Qt.NoBrush)
            
            # 获取当前鼠标下的标签页
            tab_index = self.tabAt(self.drag_drop_pos)
            if tab_index != -1:
                rect = self.tabRect(tab_index)
                painter.drawRect(rect)


class TabScrollBar(QScrollBar):
    """自定义标签页滚动条 - 放置在标签页上方"""
    def __init__(self, tab_widget, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.tab_widget = tab_widget
        self.setMinimumHeight(12)  # 设置最小高度
        self.setMaximumHeight(15)  # 设置最大高度
        
        # 设置滚动条样式，增强可见性
        self.setStyleSheet("""
            QScrollBar:horizontal {
                border: 1px solid #cccccc;
                background: #f0f0f0;
                height: 10px;
                margin: 0px 20px 0 20px;
            }
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #888888, stop:1 #666666);
                border: 1px solid #555555;
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #666666, stop:1 #444444);
            }
            QScrollBar::add-line:horizontal {
                border: 1px solid #cccccc;
                background: #e0e0e0;
                width: 20px;
                subcontrol-position: right;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:horizontal {
                border: 1px solid #cccccc;
                background: #e0e0e0;
                width: 20px;
                subcontrol-position: left;
                subcontrol-origin: margin;
            }
            QScrollBar::add-line:horizontal:hover, QScrollBar::sub-line:horizontal:hover {
                background: #d0d0d0;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        # 初始化范围
        self.setRange(0, max(0, tab_widget.count() - 1))
        self.setSingleStep(1)
        self.setPageStep(3)  # 一次滚动3个标签页
        
        # 连接标签页变化信号
        tab_widget.tabBar().tabMoved.connect(self.update_range)
        tab_widget.tabCloseRequested.connect(self.update_range)
        tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # 定时器用于延迟更新
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._delayed_update)
        
        # 批量操作标志
        self.batch_operation = False
        self.pending_updates = 0
        
        # 初始化时强制更新一次
        self.update_range()
        
    def update_range(self):
        """更新滚动条范围"""
        # 如果正在进行批量操作，累积更新请求
        if self.batch_operation:
            self.pending_updates += 1
            return
            
        # 直接更新而不使用定时器，确保即时响应
        self._immediate_update()
    
    def _immediate_update(self):
        """立即更新滚动条范围"""
        count = self.tab_widget.count()
        new_max = max(0, count - 1)
        
        # 只有当范围发生变化时才更新
        if self.maximum() != new_max:
            self.setRange(0, new_max)
        
        if count > 0:
            current_index = self.tab_widget.currentIndex()
            if 0 <= current_index < count:
                self.setValue(current_index)
            else:
                self.setValue(min(self.value(), new_max))
        else:
            self.setValue(0)
            
        # 强制刷新显示
        self.update()
    
    def _delayed_update(self):
        """延迟更新滚动条范围（保持兼容性）"""
        self._immediate_update()
        # 重置批量操作标志
        self.batch_operation = False
        self.pending_updates = 0
    
    def start_batch_operation(self):
        """开始批量操作"""
        self.batch_operation = True
        self.pending_updates = 0
    
    def end_batch_operation(self):
        """结束批量操作并执行更新"""
        self.batch_operation = False
        # 无论是否有累积的更新请求，都需要在批量操作结束时刷新一次范围
        # 这样可以覆盖批量添加标签时未触发 update_range 的情况
        self._immediate_update()
        # 重置待处理更新计数
        self.pending_updates = 0
    
    def on_tab_changed(self, index):
        """响应标签页切换"""
        if 0 <= index <= self.maximum():
            self.setValue(index)
    
    def sliderChange(self, change):
        """处理滑块变化"""
        super().sliderChange(change)
        if change == QScrollBar.SliderValueChange:
            # 切换到对应的标签页
            tab_index = self.value()
            if 0 <= tab_index < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(tab_index)
                
    def wheelEvent(self, event):
        """处理鼠标滚轮事件"""
        # 增强滚轮滚动效果
        delta = event.angleDelta().y()
        step = 1 if delta > 0 else -1
        current_value = self.value()
        new_value = current_value - step
        
        if 0 <= new_value <= self.maximum():
            self.setValue(new_value)
            # 同步切换标签页
            self.tab_widget.setCurrentIndex(new_value)
        
        event.accept()


class DataMainWindow(QMainWindow):
    """CSV数据处理主窗口类"""
    request_resize = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化UI（UI中会创建并赋值 `self.tab_scrollbar`）
        self.init_ui()
        self.viewers = {}  # 存储已打开的查看器
        self.setAcceptDrops(True)  # 启用拖拽
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(APP_NAME)
        self.resize(*DEFAULT_WINDOW_SIZE)
        self.center()
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icon', ICON)
        if not os.path.exists(icon_path):
            # 如果上面的路径不存在，尝试在当前目录下查找图标
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'icon', ICON)
        if not os.path.exists(icon_path):
            # 如果仍然找不到，尝试在sys._MEIPASS中查找（PyInstaller打包后的路径）
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'icon', ICON)
        
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setWindowIcon(icon)
            # 同时设置应用程序图标
            QApplication.instance().setWindowIcon(icon)
        
        # 设置窗口标志以支持最大化和最小化
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        # 启用拖拽
        self.setAcceptDrops(True)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(2)  # 减少间距
        main_layout.setContentsMargins(5, 5, 5, 5)  # 设置边距
        
        # 创建顶部按钮布局
        top_layout = QHBoxLayout()
        self.back_button = QPushButton("返回主菜单")
        self.back_button.clicked.connect(self.back_to_main)
        top_layout.addWidget(self.back_button)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 创建按钮
        self.open_btn = QPushButton('导入CSV文件(支持拖拽导入)')
        self.open_btn.clicked.connect(self.open_file)
        self.open_btn.setFixedHeight(30)  # 设置导入按钮高度
        button_layout.addWidget(self.open_btn, 1)  # 添加扩展因子，让按钮填满可用空间
        
        # 添加Log目录按钮
        self.log_dir_btn = QPushButton('Log目录')
        self.log_dir_btn.clicked.connect(open_log_directory)
        self.log_dir_btn.setFixedSize(*DEFAULT_BUTTON_SIZE)  # 设置Log目录按钮大小
        button_layout.addWidget(self.log_dir_btn)  # 不添加扩展因子，保持固定宽度
        
        # 添加Pic目录按钮
        self.pic_dir_btn = QPushButton('Pic目录')
        self.pic_dir_btn.clicked.connect(open_pic_directory)
        self.pic_dir_btn.setFixedSize(*DEFAULT_BUTTON_SIZE)  # 设置Pic目录按钮大小
        button_layout.addWidget(self.pic_dir_btn)  # 不添加扩展因子，保持固定宽度
        
        main_layout.addLayout(button_layout)

        # 创建标签页容器（包含滚动条和标签页）
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        # 使用自定义的可拖拽标签栏
        draggable_tab_bar = DraggableTabBar(self.tab_widget)
        draggable_tab_bar.setMainWindow(self)  # 设置主窗口引用
        self.tab_widget.setTabBar(draggable_tab_bar)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)  # 连接标签页切换信号
        self.tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.show_tab_context_menu)
        
        # 禁用标签页双击编辑功能
        self.tab_widget.tabBarDoubleClicked.connect(self.ignore_tab_double_click)
        
        # 添加标签页滚动条（放在标签页上方）
        self.tab_scrollbar = TabScrollBar(self.tab_widget)
        tab_layout.addWidget(self.tab_scrollbar)
        tab_layout.addWidget(self.tab_widget)
        
        main_layout.addWidget(tab_container)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪 @Silver')
    
    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        # 请求主窗口调整大小
        self.request_resize.emit(*DEFAULT_WINDOW_SIZE)
    
    def back_to_main(self):
        """返回主菜单"""
        # 通过父级关系找到主窗口并切换到主菜单
        # self.parent()返回QStackedWidget，需要再往上找一层才是主窗口
        stacked_widget = self.parent()
        if stacked_widget:
            main_window = stacked_widget.parent()
            if main_window and hasattr(main_window, 'show_main_menu'):
                main_window.show_main_menu()
    def ignore_tab_double_click(self, index):
        """忽略标签页双击事件"""
        # 空实现，用于禁用默认的双击编辑行为
        pass
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith('.csv'):
                        event.acceptProposedAction()
                        return
        # 处理标签页拖拽
        elif event.mimeData().hasFormat('application/x-tab-index'):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        """处理拖拽移动事件"""
        # 处理标签页拖拽
        if event.mimeData().hasFormat('application/x-tab-index'):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event: QDropEvent):
        """处理文件拖拽释放事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = []
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith('.csv'):
                        file_paths.append(file_path)
            
            if file_paths:
                self.open_files(file_paths)
        # 处理标签页拖拽释放
        elif event.mimeData().hasFormat('application/x-tab-index'):
            # 这里可以添加将标签页拖出窗口创建新窗口的逻辑（如果需要）
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
    
    def show_tab_context_menu(self, position):
        """显示标签页右键菜单"""
        # 创建右键菜单
        context_menu = QMenu(self)
        
        # 添加菜单项
        new_tab_action = QAction("新建标签页", self)
        new_tab_action.triggered.connect(self.new_tab)
        context_menu.addAction(new_tab_action)
        
        close_tab_action = QAction("关闭标签页", self)
        close_tab_action.triggered.connect(lambda: self.close_current_tab())
        context_menu.addAction(close_tab_action)
        
        close_others_action = QAction("关闭其他标签页", self)
        close_others_action.triggered.connect(self.close_other_tabs)
        context_menu.addAction(close_others_action)
        
        close_all_action = QAction("关闭全部标签页", self)
        close_all_action.triggered.connect(self.close_all_tabs)
        context_menu.addAction(close_all_action)
        
        # 添加重命名功能
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(self.rename_tab)
        context_menu.addAction(rename_action)
        
        # 添加在资源管理器中查看功能
        show_in_explorer_action = QAction("在资源管理器中查看", self)
        show_in_explorer_action.triggered.connect(self.show_in_explorer)
        context_menu.addAction(show_in_explorer_action)
        
        # 显示菜单
        context_menu.exec_(self.tab_widget.mapToGlobal(position))
    
    def show_in_explorer(self):
        """在资源管理器中显示文件"""
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "警告", "没有选中的标签页")
            return
            
        current_widget = self.tab_widget.widget(current_index)
        if not current_widget:
            QMessageBox.warning(self, "警告", "无法获取当前标签页")
            return
            
        if not hasattr(current_widget, 'file_path'):
            QMessageBox.warning(self, "警告", "当前标签页没有文件路径信息")
            return
            
        file_path = current_widget.file_path
        if not file_path:
            QMessageBox.warning(self, "警告", "文件路径为空")
            return
            
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", f"文件不存在: {file_path}")
            return
        
        # 在资源管理器中显示文件
        try:
            if os.name == 'nt':  # Windows
                # 使用标准的Windows命令行格式
                import subprocess
                # 确保路径使用双反斜杠或原始字符串
                normalized_path = os.path.normpath(file_path)
                subprocess.Popen(f'explorer /select,"{normalized_path}"', shell=True)
            elif os.name == 'posix':  # macOS/Linux
                import subprocess
                subprocess.Popen(['xdg-open', os.path.dirname(file_path)])
        except Exception as e:
            # 如果第一种方法失败，尝试备用方法
            try:
                if os.name == 'nt':  # Windows
                    # 备用方法：直接打开文件所在目录
                    import subprocess
                    normalized_path = os.path.normpath(file_path)
                    subprocess.Popen(f'explorer "{os.path.dirname(normalized_path)}"', shell=True)
                elif os.name == 'posix':  # macOS/Linux
                    import subprocess
                    subprocess.Popen(['xdg-open', os.path.dirname(file_path)])
            except Exception as e2:
                QMessageBox.critical(self, "错误", f"无法在资源管理器中显示文件: {str(e)}\n备用方法也失败: {str(e2)}")
    def rename_tab(self):
        """重命名当前标签页文件"""
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            return
            
        current_widget = self.tab_widget.widget(current_index)
        if not current_widget or not hasattr(current_widget, 'file_path'):
            return
            
        # 获取当前文件路径
        old_file_path = current_widget.file_path
        if not os.path.exists(old_file_path):
            QMessageBox.warning(self, "警告", "文件不存在，无法重命名")
            return
            
        # 获取当前文件名（不含路径）
        old_filename = os.path.basename(old_file_path)
        old_name, old_ext = os.path.splitext(old_filename)
        
        # 弹出输入对话框获取新文件名
        from PyQt5.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, "重命名文件", "请输入新文件名:", text=old_name)
        
        if ok and new_name:
            # 确保文件名包含扩展名
            if not new_name.endswith(old_ext):
                new_name += old_ext
                
            # 构造新文件路径
            new_file_path = os.path.join(os.path.dirname(old_file_path), new_name)
            
            # 检查新文件名是否与原文件名相同
            if new_name == old_filename:
                return
                
            # 检查目标文件是否已存在
            if os.path.exists(new_file_path):
                reply = QMessageBox.question(self, "确认", 
                                           f"文件 '{new_name}' 已存在，是否覆盖？",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            
            try:
                # 重命名文件
                os.rename(old_file_path, new_file_path)
                
                # 更新viewer中的文件路径
                current_widget.file_path = new_file_path
                
                # 更新标签页标题（使用独立的标签页标题）
                if hasattr(current_widget, 'tab_title'):
                    # 如果已经有独立的标签页标题，则更新它
                    current_widget.tab_title = new_name
                else:
                    # 否则创建独立的标签页标题
                    current_widget.tab_title = new_name
                
                self.tab_widget.setTabText(current_index, new_name)
                
                # 更新viewers字典
                if old_file_path in self.viewers:
                    self.viewers[new_file_path] = self.viewers.pop(old_file_path)
                
                # 更新窗口标题
                current_widget.setWindowTitle(f"数据查看 - {new_name}")
                
                # 如果是新文件，同时更新temp_file_path属性
                if hasattr(current_widget, 'temp_file_path'):
                    current_widget.temp_file_path = new_file_path
                
                self.status_bar.showMessage(f'文件已重命名为: {new_name} @Silver')
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名文件失败: {str(e)}")

    def new_tab(self):
        """新建空白标签页"""
        # 先让用户输入文件名
        from PyQt5.QtWidgets import QInputDialog
        file_name, ok = QInputDialog.getText(self, "新建文件", "请输入文件名:", text="新建文件")
        
        if not ok or not file_name:
            return  # 用户取消或未输入文件名
            
        # 确保文件名以.csv结尾
        if not file_name.endswith('.csv'):
            file_name += '.csv'
        
        # 获取Log目录路径并创建文件
        log_dir = get_log_directory()
        ensure_directory_exists(log_dir)
        temp_file_path = os.path.join(log_dir, file_name)
        
        # 检查临时文件是否已存在，如果存在则添加序号
        base_name, ext = os.path.splitext(file_name)
        counter = 1
        while os.path.exists(temp_file_path):
            temp_file_path = os.path.join(log_dir, f"{base_name}_{counter}{ext}")
            counter += 1
        
        # 创建一个空的CSV文件，只包含表头行
        with open(temp_file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 只写入表头行，让Qt自动处理列标题
            writer.writerow(["1"])
            writer.writerow([""])
        
        # 动态导入DataViewer
        from DATAPROCESS.CONTROLLER import DataViewer
                    
        # 创建DataViewer实例
        viewer = DataViewer(temp_file_path, self, default_encoding='utf-8')
        viewer.file_path = temp_file_path
        viewer.is_new_file = True  # 标记为新文件
        viewer.temp_file_path = temp_file_path  # 保存临时文件路径，用于后续删除
        viewer.tab_title = file_name  # 初始化标签页标题
        
        # 添加标签页并同步滚动条
        tab_index = self.add_tab_with_scroll_sync(viewer, file_name)
        self.tab_widget.setCurrentIndex(tab_index)
        self.viewers[temp_file_path] = viewer
        self.status_bar.showMessage(f'已创建新文件: {file_name} @Silver')

    def close_current_tab(self):
        """关闭当前标签页"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)
    
    def close_other_tabs(self):
        """关闭其他标签页"""
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            return
            
        # 获取当前标签页的文件路径
        current_widget = self.tab_widget.widget(current_index)
        current_file_path = None
        if current_widget and hasattr(current_widget, 'file_path'):
            current_file_path = current_widget.file_path
        
        # 关闭所有其他标签页
        for i in range(self.tab_widget.count() - 1, -1, -1):
            if i != current_index:
                self.close_tab(i)
    
    def close_all_tabs(self):
        """关闭所有标签页"""
        for i in range(self.tab_widget.count() - 1, -1, -1):
            self.close_tab(i)
    
    def open_files(self, file_paths):
        """打开多个CSV文件"""
        # 开始批量操作模式
        if self.tab_scrollbar:
            self.tab_scrollbar.start_batch_operation()
        
        success_count = 0
        error_count = 0
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            # 更新状态栏显示进度
            self.status_bar.showMessage(f'正在导入文件 ({i+1}/{total_files}): {os.path.basename(file_path)} @Silver')
            QApplication.processEvents()  # 处理界面事件，确保状态栏更新显示
            
            # 检查文件是否已打开
            if file_path in self.viewers:
                self.status_bar.showMessage(f'文件已在标签页中: {os.path.basename(file_path)} @Silver')
                # 切换到对应的标签页
                for j in range(self.tab_widget.count()):
                    if self.tab_widget.widget(j).file_path == file_path:
                        self.tab_widget.setCurrentIndex(j)
                        # 同步滚动条
                        if self.tab_scrollbar:
                            self.tab_scrollbar.setValue(j)
                        break
                continue
            
            # 打开新的数据查看窗口作为标签页
            try:
                from DATAPROCESS.CONTROLLER import DataViewer

                # 创建DataViewer实例，传入默认编码utf-8
                viewer = DataViewer(file_path, self, default_encoding='utf-8')
                # 为viewer添加file_path属性，以便在关闭标签页时使用
                viewer.file_path = file_path
                tab_title = os.path.basename(file_path)
                
                # 添加标签页（在批量操作期间不触发滚动条更新）
                tab_index = self.tab_widget.addTab(viewer, tab_title)
                self.viewers[file_path] = viewer
                success_count += 1
                
                # 只在最后一个文件时设置为当前标签页
                if file_path == file_paths[-1]:
                    self.tab_widget.setCurrentIndex(tab_index)
                    
            except Exception as e:
                error_count += 1
                QMessageBox.critical(self, "错误", f"无法打开文件 {os.path.basename(file_path)}: {str(e)}")
        
        # 结束批量操作模式并更新滚动条
        if self.tab_scrollbar:
            self.tab_scrollbar.end_batch_operation()
        
        # 强制处理所有待处理的事件，确保UI完全更新
        QApplication.processEvents()
        
        # 显示批量导入结果
        if success_count > 0:
            self.status_bar.showMessage(f'成功导入 {success_count} 个文件 @Silver')
        if error_count > 0:
            self.status_bar.showMessage(f'导入完成: {success_count} 成功, {error_count} 失败 @Silver')

    def open_file(self):
        """打开CSV文件"""
        # 使用getOpenFileNames支持多文件选择（使用封装函数）
        file_paths, _ = get_open_filenames(
            self, '选择CSV文件', '', f'{CSV_FILE_FILTER};;{ALL_FILE_FILTER}')  # 使用常量设置文件过滤器
        
        if file_paths:
            self.open_files(file_paths)
    
    
    def center(self):
        """将窗口居中显示"""
        # 始终相对于屏幕居中
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def close_tab(self, index):
        """关闭标签页"""
        widget = self.tab_widget.widget(index)
        if widget and hasattr(widget, 'file_path'):
            file_path = widget.file_path
            if file_path in self.viewers:
                del self.viewers[file_path]
        self.remove_tab_with_scroll_sync(index)

    def edit_tab_title(self, index):
        """编辑标签页标题"""
        if index < 0:
            return
            
        widget = self.tab_widget.widget(index)
        if not widget or not hasattr(widget, 'tab_title'):
            return
            
        # 获取当前标签页标题
        old_title = self.tab_widget.tabText(index)
        
        # 弹出输入对话框获取新标题
        from PyQt5.QtWidgets import QInputDialog
        new_title, ok = QInputDialog.getText(self, "重命名标签页", "请输入新标题:", text=old_title)
        
        if ok and new_title:
            # 更新标签页标题
            self.tab_widget.setTabText(index, new_title)
            
            # 更新viewer中的标签页标题
            widget.tab_title = new_title
            
            # 更新窗口标题
            widget.setWindowTitle(f"数据查看 - {new_title}")
            
            self.status_bar.showMessage(f'标签页已重命名为: {new_title} @Silver')

    def on_tab_changed(self, index):
        """标签页切换时的处理"""
        # 同步滚动条位置
        if self.tab_scrollbar and 0 <= index < self.tab_widget.count():
            self.tab_scrollbar.setValue(index)
            
        # 更新状态栏信息
        if index >= 0:
            tab_text = self.tab_widget.tabText(index)
            self.status_bar.showMessage(f'当前标签页: {tab_text} @Silver')
        else:
            self.status_bar.showMessage('就绪 @Silver')

    def sync_scrollbar_with_tabs(self):
        """同步滚动条与标签页数量"""
        if self.tab_scrollbar:
            self.tab_scrollbar.update_range()

    def add_tab_with_scroll_sync(self, widget, title):
        """添加标签页并同步滚动条"""
        tab_index = self.tab_widget.addTab(widget, title)
        self.sync_scrollbar_with_tabs()
        return tab_index

    def remove_tab_with_scroll_sync(self, index):
        """移除标签页并同步滚动条"""
        self.tab_widget.removeTab(index)
        self.sync_scrollbar_with_tabs()