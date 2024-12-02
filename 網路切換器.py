import sys
import subprocess
import ctypes
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSystemTrayIcon, QMenu, QAction, QShortcut
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QRect

class NetworkToggler(QWidget):
    def __init__(self):
        super().__init__()
        self.interface_name = None
        self.initUI()
        self.init_system_tray()
        self.init_shortcuts()

    def initUI(self):
        # 設定視窗
        self.setWindowTitle('網路控制器')
        self.setGeometry(300, 300, 300, 150)  # 更小巧的尺寸
        self.setWindowIcon(QIcon('network_icon.png'))  # 設定應用程式圖示
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: 'Microsoft YaHei', '微軟正黑體', Arial, sans-serif;
            }
            QPushButton {
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 15px;
                margin: 8px;
                background-color: #007BFF;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLabel {
                font-size: 14px;
                margin: 5px;
            }
        """)

        # 主佈局
        layout = QVBoxLayout()

        # 狀態標籤
        self.status_label = QLabel('檢查網路狀態中...')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # 按鈕佈局
        button_layout = QHBoxLayout()

        # 開啟網路按鈕
        self.enable_btn = QPushButton('開啟網路')
        self.enable_btn.setStyleSheet("background-color: #28a745;")  # 綠色背景
        self.enable_btn.clicked.connect(self.enable_network)
        button_layout.addWidget(self.enable_btn)

        # 關閉網路按鈕
        self.disable_btn = QPushButton('關閉網路')
        self.disable_btn.setStyleSheet("background-color: #dc3545;")  # 紅色背景
        self.disable_btn.clicked.connect(self.disable_network)
        button_layout.addWidget(self.disable_btn)

        # 將按鈕佈局加入主佈局
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 定時更新網路狀態
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_network_status)
        self.timer.start(3000)  # 每3秒更新一次

        # 初始更新
        self.update_network_status()

    def init_system_tray(self):
        # 系統托盤圖示
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('network_icon.png'))
        
        # 系統托盤選單
        tray_menu = QMenu()
        
        show_action = QAction("顯示主視窗", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        toggle_action = QAction("切換網路狀態 (F1)", self)
        toggle_action.triggered.connect(self.toggle_network)
        tray_menu.addAction(toggle_action)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def init_shortcuts(self):
        # 快捷鍵 F1 來切換網路
        shortcut = QShortcut(QKeySequence("F1"), self)
        shortcut.activated.connect(self.toggle_network)

    def animate_button(self, button):
        animation = QPropertyAnimation(button, b'geometry')
        animation.setDuration(300)
        animation.setStartValue(button.geometry())
        animation.setEndValue(QRect(button.geometry().x(), button.geometry().y() - 10, button.geometry().width(), button.geometry().height()))
        animation.setLoopCount(2)
        animation.setDirection(QPropertyAnimation.Backward)
        animation.start()

    def get_network_status(self):
        """取得網路狀態"""
        try:
            # 列出所有網路介面
            result = subprocess.run(['netsh', 'interface', 'show', 'interface'], 
                                    capture_output=True, text=True, check=True)
            interfaces = result.stdout.splitlines()
            for line in interfaces:
                if self.interface_name is None and ('已連線' in line or '已啟用' in line):
                    # 嘗試找出預設的網路介面名稱
                    self.interface_name = line.split()[-1]  # 假設介面名稱是最後一部分
                if self.interface_name and self.interface_name in line:
                    if '已連線' in line or '已啟用' in line:
                        return True
                    else:
                        return False
            return False
        except Exception as e:
            print(f'取得網路狀態失敗：{str(e)}')
            return None

    def update_network_status(self):
        """更新網路狀態"""
        status = self.get_network_status()
        
        if status is None:
            self.status_label.setText('無法取得網路狀態')
            self.enable_btn.setEnabled(False)
            self.disable_btn.setEnabled(False)
        elif status:
            self.status_label.setText('網路目前已開啟 🟢')
            self.enable_btn.setEnabled(False)
            self.disable_btn.setEnabled(True)
        else:
            self.status_label.setText('網路目前已關閉 🔴')
            self.enable_btn.setEnabled(True)
            self.disable_btn.setEnabled(False)

    def network_operation(self, enable):
        """透過禁用或啟用 IP 協定來模擬網路的開關狀態，避免無法切換回來的問題"""
        action = 'enabled' if enable else 'disabled'
        try:
            if not self.interface_name:
                print('未找到網路介面，無法進行操作')
                return
            result = subprocess.run(['netsh', 'interface', 'set', 'interface', self.interface_name, 'admin=' + action],
                                    capture_output=True, text=True, check=True)
            if result.returncode == 0:
                # 小延遲讓作業系統有時間更新
                QTimer.singleShot(1000, self.update_network_status)
            else:
                print(f'操作失敗：{result.stderr}')
        except subprocess.CalledProcessError as e:
            print(f'操作失敗：{e.stderr}')
        except Exception as e:
            print(f'操作失敗：{str(e)}')

    def enable_network(self):
        """開啟網路"""
        self.network_operation(True)
        self.status_label.setText('正在開啟網路...')
        self.animate_button(self.enable_btn)

    def disable_network(self):
        """關閉網路"""
        self.network_operation(False)
        self.status_label.setText('正在關閉網路...')
        self.animate_button(self.disable_btn)

    def toggle_network(self):
        """切換網路狀態"""
        status = self.get_network_status()
        if status:
            self.disable_network()
        else:
            self.enable_network()

def is_admin():
    """檢查是否以管理員權限運行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """以管理員權限重新啟動"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)

def main():
    # 確保以管理員權限運行
    run_as_admin()
    
    # 創建應用程式
    app = QApplication(sys.argv)
    app.setApplicationName('網路控制器')
    
    # 創建主視窗
    toggler = NetworkToggler()
    toggler.show()
    
    # 運行應用程式
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()