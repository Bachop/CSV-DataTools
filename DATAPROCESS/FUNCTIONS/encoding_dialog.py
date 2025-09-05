# -*- coding: utf-8 -*-
"""
编码选择模块
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTextEdit, QDialogButtonBox)


class EncodingDialog(QDialog):
    """编码选择对话框"""
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.selected_encoding = None
        self.init_ui()
        self.test_encodings()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("选择文件编码")
        self.setModal(True)
        layout = QVBoxLayout()
        
        # 说明标签
        label = QLabel(f"请选择文件 {os.path.basename(self.file_path)} 的编码:")
        layout.addWidget(label)
        
        # 编码选择下拉框
        self.encoding_combo = QComboBox()
        self.encoding_combo.currentTextChanged.connect(self.on_encoding_changed)
        layout.addWidget(self.encoding_combo)
        
        # 预览文本框
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        layout.addWidget(QLabel("文件预览:"))
        layout.addWidget(self.preview_text)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def test_encodings(self):
        """测试常见编码"""
        # 常见编码列表
        encodings = [
            'utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 
            'latin1', 'ascii', 'big5', 'shift_jis', 'cp932',
            'cp949', 'cp1251', 'cp1252', 'iso-8859-1', 'iso-8859-2'
        ]
        detected = False
        
        # 先添加所有编码到下拉框
        for encoding in encodings:
            self.encoding_combo.addItem(encoding)
        
        # 然后测试哪个编码可以读取文件
        for i, encoding in enumerate(encodings):
            try:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 只读取前1024个字符进行测试
                # 在可以读取的编码后面添加标记
                self.encoding_combo.setItemText(i, f"{encoding} (可读取)")
                if not detected:
                    self.selected_encoding = encoding
                    self.update_preview(encoding)
                    # 设置为当前选中项
                    self.encoding_combo.setCurrentIndex(i)
                    detected = True
            except:
                pass
        
        # 如果没有找到合适的编码，添加一个默认选项
        if not detected:
            self.selected_encoding = 'utf-8'
            self.encoding_combo.setCurrentIndex(0)  # 默认选中第一个
    
    def on_encoding_changed(self, encoding):
        """当编码选择改变时更新预览"""
        # 去除"(可读取)"标记，只保留编码名称
        if " (可读取)" in encoding:
            encoding = encoding.replace(" (可读取)", "")
        self.update_preview(encoding)
    
    def update_preview(self, encoding):
        """更新预览"""
        try:
            with open(self.file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read(500)  # 读取前500个字符作为预览
            self.preview_text.setPlainText(content)
        except Exception as e:
            self.preview_text.setPlainText(f"无法预览: {str(e)}")
    
    def get_selected_encoding(self):
        """获取选择的编码"""
        if self.encoding_combo.count() > 0:
            selected_text = self.encoding_combo.currentText()
            # 去除"(可读取)"标记，只保留编码名称
            if " (可读取)" in selected_text:
                return selected_text.replace(" (可读取)", "")
            return selected_text
        return 'utf-8'