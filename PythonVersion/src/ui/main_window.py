"""主窗口"""
import sys
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QPushButton, QLineEdit,
    QMessageBox, QSplitter, QFrame, QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from .styles import MAIN_STYLE
from .download_dialog import DownloadDialog
from utils.launcher import (
    get_version_list, get_installed_versions, install_version,
    launch_version, is_version_installed
)


class InstallThread(QThread):
    """安装线程"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, version):
        super().__init__()
        self.version = version
        self.is_cancelled = False
    
    def run(self):
        def callback(progress):
            if not self.is_cancelled:
                self.progress_updated.emit(progress)
        
        try:
            install_version(self.version, callback)
            if not self.is_cancelled:
                self.finished_signal.emit(True, f"版本 {self.version} 下载完成！")
        except Exception as e:
            self.finished_signal.emit(False, str(e))
    
    def cancel(self):
        self.is_cancelled = True


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.install_thread = None
        self.versions = []
        self.init_ui()
        self.load_versions()
        self.load_installed()
        self.setStyleSheet(MAIN_STYLE)
    
    def init_ui(self):
        self.setWindowTitle("Aether Launcher - Minecraft 启动器")
        self.setMinimumSize(800, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 标题
        title_label = QLabel("Aether Launcher")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px; color: #00adb5;")
        main_layout.addWidget(title_label)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板 - 版本列表
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        left_layout.addWidget(QLabel("可用版本"))
        
        self.version_list = QListWidget()
        self.version_list.itemDoubleClicked.connect(self.on_version_double_click)
        left_layout.addWidget(self.version_list)
        
        splitter.addWidget(left_panel)
        
        # 右侧面板 - 已安装版本
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        right_layout.addWidget(QLabel("已安装版本"))
        
        self.installed_list = QListWidget()
        self.installed_list.itemDoubleClicked.connect(self.on_installed_double_click)
        right_layout.addWidget(self.installed_list)
        
        # 玩家名输入
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("玩家名:"))
        self.username_input = QLineEdit()
        self.username_input.setText("AetherPlayer")
        name_layout.addWidget(self.username_input)
        right_layout.addLayout(name_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("下载选中版本")
        self.download_btn.clicked.connect(self.on_download)
        button_layout.addWidget(self.download_btn)
        
        self.launch_btn = QPushButton("启动选中版本")
        self.launch_btn.clicked.connect(self.on_launch)
        button_layout.addWidget(self.launch_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_btn)
        
        right_layout.addLayout(button_layout)
        
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setSizes([400, 400])
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def load_versions(self):
        """加载版本列表"""
        self.statusBar().showMessage("正在获取版本列表...")
        try:
            self.versions = get_version_list()
            self.version_list.clear()
            for v in self.versions[:100]:  # 只显示前100个
                type_icon = "📦" if v["type"] == "release" else "🔧"
                item = QListWidgetItem(f"{type_icon} {v['id']} ({v['type']})")
                item.setData(Qt.ItemDataRole.UserRole, v["id"])
                self.version_list.addItem(item)
            self.statusBar().showMessage(f"已加载 {len(self.versions)} 个版本")
        except Exception as e:
            self.statusBar().showMessage(f"加载版本失败: {e}")
            QMessageBox.warning(self, "错误", f"加载版本列表失败:\n{e}")
    
    def load_installed(self):
        """加载已安装版本"""
        try:
            installed = get_installed_versions()
            self.installed_list.clear()
            for v in installed:
                item = QListWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole, v)
                self.installed_list.addItem(item)
        except Exception as e:
            print(f"加载已安装版本失败: {e}")
    
    def on_version_double_click(self, item):
        """双击版本列表开始下载"""
        version_id = item.data(Qt.ItemDataRole.UserRole)
        self.download_version(version_id)
    
    def on_installed_double_click(self, item):
        """双击已安装版本启动"""
        version_id = item.data(Qt.ItemDataRole.UserRole)
        self.launch_version(version_id)
    
    def on_download(self):
        """下载选中版本"""
        current_item = self.version_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个版本")
            return
        
        version_id = current_item.data(Qt.ItemDataRole.UserRole)
        self.download_version(version_id)
    
    def on_launch(self):
        """启动选中版本"""
        current_item = self.installed_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个已安装的版本")
            return
        
        version_id = current_item.data(Qt.ItemDataRole.UserRole)
        self.launch_version(version_id)
    
    def download_version(self, version_id):
        """下载版本"""
        # 检查是否已安装
        if is_version_installed(version_id):
            reply = QMessageBox.question(
                self, "确认",
                f"版本 {version_id} 已存在，是否重新下载？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # 显示下载对话框
        dialog = DownloadDialog(version_id, self)
        dialog.cancelled.connect(self.on_download_cancelled)
        
        # 启动下载线程
        self.install_thread = InstallThread(version_id)
        self.install_thread.progress_updated.connect(dialog.update_progress)
        self.install_thread.status_updated.connect(dialog.update_status)
        self.install_thread.finished_signal.connect(
            lambda success, msg: self.on_download_finished(success, msg, dialog, version_id)
        )
        self.install_thread.start()
        
        dialog.exec()
    
    def on_download_cancelled(self):
        """取消下载"""
        if self.install_thread:
            self.install_thread.cancel()
    
    def on_download_finished(self, success, message, dialog, version_id):
        """下载完成"""
        dialog.close()
        if success:
            QMessageBox.information(self, "成功", message)
            self.load_installed()
        else:
            QMessageBox.critical(self, "错误", f"下载失败:\n{message}")
        self.install_thread = None
    
    def launch_version(self, version_id):
        """启动版本"""
        username = self.username_input.text().strip()
        if not username:
            username = "AetherPlayer"
        
        try:
            self.statusBar().showMessage(f"正在启动 {version_id}...")
            process = launch_version(version_id, username)
            self.statusBar().showMessage(f"游戏已启动: {version_id}")
            
            # 可选：显示游戏输出窗口
            # 这里简单处理，游戏输出会打印到控制台
            
        except Exception as e:
            self.statusBar().showMessage("启动失败")
            QMessageBox.critical(self, "错误", f"启动失败:\n{e}")
    
    def refresh(self):
        """刷新"""
        self.load_versions()
        self.load_installed()
        self.statusBar().showMessage("已刷新")
