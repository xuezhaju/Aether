"""下载进度对话框"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, 
    QProgressBar, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal

from .styles import DOWNLOAD_DIALOG_STYLE


class DownloadDialog(QDialog):
    """下载进度对话框"""
    
    cancelled = pyqtSignal()
    
    def __init__(self, version, parent=None):
        super().__init__(parent)
        self.version = version
        self.is_cancelled = False
        self.init_ui()
        self.setStyleSheet(DOWNLOAD_DIALOG_STYLE)
    
    def init_ui(self):
        self.setWindowTitle(f"正在下载 {self.version}")
        self.setFixedSize(400, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout()
        
        # 标题
        self.title_label = QLabel(f"正在下载 Minecraft {self.version}")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.title_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 状态信息
        self.status_label = QLabel("准备下载...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #aaaaaa; margin-top: 10px;")
        layout.addWidget(self.status_label)
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.on_cancel)
        layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
    
    def update_progress(self, progress):
        """更新进度"""
        self.progress_bar.setValue(progress)
    
    def update_status(self, status):
        """更新状态信息"""
        self.status_label.setText(status)
    
    def on_cancel(self):
        """取消下载"""
        self.is_cancelled = True
        self.cancelled.emit()
        self.reject()
