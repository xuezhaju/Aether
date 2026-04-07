"""UI 样式表"""

MAIN_STYLE = """
QMainWindow {
    background-color: #1a1a2e;
}

QLabel {
    color: #eeeeee;
    font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC";
}

QPushButton {
    background-color: #0f3460;
    color: #eeeeee;
    border: none;
    border-radius: 5px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #16213e;
}

QPushButton:pressed {
    background-color: #0a1a2a;
}

QListWidget {
    background-color: #16213e;
    color: #eeeeee;
    border: 1px solid #0f3460;
    border-radius: 5px;
    padding: 5px;
    font-size: 13px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 3px;
}

QListWidget::item:selected {
    background-color: #0f3460;
}

QListWidget::item:hover {
    background-color: #1a3a5c;
}

QProgressBar {
    border: 1px solid #0f3460;
    border-radius: 5px;
    text-align: center;
    color: #eeeeee;
}

QProgressBar::chunk {
    background-color: #00adb5;
    border-radius: 4px;
}

QMessageBox {
    background-color: #1a1a2e;
}

QMessageBox QLabel {
    color: #eeeeee;
}

QMessageBox QPushButton {
    min-width: 80px;
}
"""

DOWNLOAD_DIALOG_STYLE = """
QDialog {
    background-color: #1a1a2e;
}

QLabel {
    color: #eeeeee;
}

QProgressBar {
    border: 1px solid #0f3460;
    border-radius: 5px;
    text-align: center;
    color: #eeeeee;
}

QProgressBar::chunk {
    background-color: #00adb5;
    border-radius: 4px;
}
"""
