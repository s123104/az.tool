import sys
import ctypes
import os
import wmi
import winreg as reg
import subprocess
import logging
import socket
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSystemTrayIcon, QMenu, QAction, QStyle
)
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QRect, pyqtSignal, QThread
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
import keyboard  # 用於全局快捷鍵

# Configure logging
def get_log_file_path():
    """
    獲取日誌文件的路徑，確保寫入到用戶可寫的目錄。
    優先使用應用程式所在目錄，若不可寫，則使用用戶的 AppData 目錄。
    """
    try:
        if getattr(sys, 'frozen', False):
            # 如果是打包後的應用程式，使用可執行文件所在目錄
            application_path = Path(sys.executable).parent
        else:
            # 如果是腳本運行，使用腳本所在目錄
            application_path = Path(__file__).parent
        log_file = application_path / 'network_toggler.log'
        # 嘗試創建文件以確保有寫入權限
        with open(log_file, 'a'):
            pass
        return str(log_file)
    except Exception as e:
        # 如果應用程式目錄不可寫，使用 AppData 目錄
        appdata = os.getenv('APPDATA')
        log_dir = Path(appdata) / 'NetworkToggler'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'network_toggler.log'
        return str(log_file)

logging.basicConfig(
    filename=get_log_file_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def resource_path(relative_path):
    """獲取資源文件的絕對路徑，支持打包後的路徑"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def add_to_startup():
    """將應用程式添加到 Windows 啟動項目"""
    try:
        exe_path = os.path.abspath(sys.executable)
        logging.info(f"Executable Path: {exe_path}")  # Debug
        registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER,
                                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                                    0, reg.KEY_READ)
        try:
            existing_value, regtype = reg.QueryValueEx(registry_key, "NetworkToggler")
            if existing_value == exe_path:
                reg.CloseKey(registry_key)
                logging.info("NetworkToggler 已經在啟動項目中")
                return
        except FileNotFoundError:
            pass
        reg.CloseKey(registry_key)

        registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER,
                                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                                    0, reg.KEY_WRITE)
        reg.SetValueEx(registry_key, "NetworkToggler", 0, reg.REG_SZ, exe_path)
        reg.CloseKey(registry_key)
        logging.info("已成功添加到啟動項目")
    except Exception as e:
        logging.error(f"添加到啟動項目失敗：{e}")

class HotkeyListener(QThread):
    toggle_network_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        # 設置全局快捷鍵
        keyboard.add_hotkey('ctrl+f1', self.emit_toggle_network)
        keyboard.wait()

    def emit_toggle_network(self):
        self.toggle_network_signal.emit()

class SingleInstance:
    """確保應用程式只運行一個實例"""
    def __init__(self, key):
        self.key = key
        self.server = QLocalServer()
        self.is_running = False

        # 移除任何現有的同名 socket
        if self.server.isListening():
            self.server.close()

        if self.server.listen(self.key):
            # 沒有現有實例
            self.server.newConnection.connect(self.handle_new_connection)
        else:
            # 已有實例在運行
            self.is_running = True

    def handle_new_connection(self):
        """處理來自其他實例的連接請求"""
        socket = self.server.nextPendingConnection()
        socket.waitForReadyRead(1000)
        # 可以在這裡處理其他實例發來的訊息
        socket.disconnectFromServer()

class NetworkToggler(QWidget):
    def __init__(self):
        super().__init__()
        self.is_network_blocked = False  # 初始狀態為網路未被阻止
        self.initUI()
        self.init_system_tray()
        self.init_global_shortcuts()
        self.wmi_interface = wmi.WMI()

    def initUI(self):
        # 獲取圖示的絕對路徑
        icon_path = resource_path(os.path.join('img', 'internet.png'))
        if not os.path.exists(icon_path):
            icon_path = resource_path('app.ico')  # 使用另一個圖示或預設圖示

        # 設定視窗
        self.setWindowTitle('網路控制器')
        self.setGeometry(300, 300, 300, 150)
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
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
            QPushButton:pressed {
                background-color: #003f7f;
                padding-top: 12px;
                padding-bottom: 8px;
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
        self.enable_btn.setCursor(QCursor(Qt.PointingHandCursor))  # 設置手指游標
        button_layout.addWidget(self.enable_btn)

        # 關閉網路按鈕
        self.disable_btn = QPushButton('關閉網路')
        self.disable_btn.setStyleSheet("background-color: #dc3545;")  # 紅色背景
        self.disable_btn.clicked.connect(self.disable_network)
        self.disable_btn.setCursor(QCursor(Qt.PointingHandCursor))  # 設置手指游標
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

        # 列出所有網路介面，便於確認
        self.list_all_adapters()

    def list_all_adapters(self):
        """列出所有網路介面名稱"""
        try:
            adapters = self.wmi_interface.Win32_NetworkAdapter()
            for adapter in adapters:
                logging.info(f"Adapter Name: {adapter.Name}, NetEnabled: {adapter.NetEnabled}, NetConnectionStatus: {adapter.NetConnectionStatus}")
        except Exception as e:
            logging.error(f'列出網路介面失敗：{e}')

    def init_system_tray(self):
        # 獲取圖示的絕對路徑
        icon_path = resource_path(os.path.join('img', 'internet.png'))
        if not os.path.exists(icon_path):
            icon_path = resource_path('app.ico')  # 使用另一個圖示或預設圖示

        # 系統托盤圖示
        self.tray_icon = QSystemTrayIcon(self)
        if icon_path and os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))  # 使用預設圖示

        # 系統托盤選單
        tray_menu = QMenu()

        show_action = QAction("顯示主視窗", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        toggle_action = QAction("切換網路狀態 (Ctrl+F1)", self)
        toggle_action.triggered.connect(self.toggle_network)
        tray_menu.addAction(toggle_action)

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # 當托盤圖示被激活時處理（例如，左鍵單擊顯示主視窗）
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        """處理托盤圖示的激活事件"""
        if reason == QSystemTrayIcon.Trigger:
            # 左鍵單擊顯示主視窗
            self.show()

    def init_global_shortcuts(self):
        self.hotkey_listener = HotkeyListener()
        self.hotkey_listener.toggle_network_signal.connect(self.toggle_network)
        self.hotkey_listener.start()

    def animate_button(self, button):
        animation = QPropertyAnimation(button, b'geometry')
        animation.setDuration(300)
        animation.setStartValue(button.geometry())
        animation.setEndValue(QRect(button.geometry().x(), button.geometry().y() - 10, button.geometry().width(), button.geometry().height()))
        animation.setLoopCount(2)
        animation.setDirection(QPropertyAnimation.Backward)
        animation.start()

    def get_primary_adapter(self):
        """自動掃描並獲取主要網路介面"""
        try:
            adapters = self.wmi_interface.Win32_NetworkAdapter(NetEnabled=True, NetConnectionStatus=2)
            if not adapters:
                return None
            # 根據特定名稱過濾，或返回第一個
            for adapter in adapters:
                if "Ethernet" in adapter.Name or "Wi-Fi" in adapter.Name:
                    return adapter
            # 如果沒有特定名稱，返回第一個
            return adapters[0]
        except Exception as e:
            logging.error(f'掃描網路介面失敗：{e}')
            return None

    def get_network_status(self):
        """取得網路狀態，嘗試連接到 Google DNS 以確認"""
        try:
            socket.setdefaulttimeout(3)
            host = socket.gethostbyname("8.8.8.8")
            s = socket.create_connection((host, 53), 2)
            s.close()
            return True
        except Exception as e:
            logging.error(f'網路連接測試失敗：{e}')
            return False

    def update_network_status(self):
        """更新網路狀態"""
        status = self.get_network_status()

        if status is None:
            self.status_label.setText('無法取得網路狀態')
            self.enable_btn.setEnabled(False)
            self.disable_btn.setEnabled(False)
            self.is_network_blocked = False
        elif status:
            self.status_label.setText('網路目前已開啟 🟢')
            self.enable_btn.setEnabled(False)
            self.disable_btn.setEnabled(True)
            self.is_network_blocked = False
        else:
            self.status_label.setText('網路目前已關閉 🔴')
            self.enable_btn.setEnabled(True)
            self.disable_btn.setEnabled(False)
            self.is_network_blocked = True

    def network_operation(self, block):
        """透過防火牆規則來阻止或允許網路連接"""
        try:
            # 獲取應用程式的完整路徑
            program_path = sys.executable
            logging.info(f"Program Path: {program_path}")  # Debug

            # 定義規則名稱
            allow_rule_name = "AllowNetworkToggler"
            block_rule_name = "BlockAllOutbound"

            if block:
                # 先刪除可能存在的舊規則，防止重複
                subprocess.run(
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     f'name={allow_rule_name}', 'dir=out'],
                    capture_output=True, text=True, check=False,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                subprocess.run(
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     f'name={block_rule_name}', 'dir=out'],
                    capture_output=True, text=True, check=False,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                logging.info("已刪除舊的 AllowNetworkToggler 和 BlockAllOutbound 規則")

                # 添加允許 NetworkToggler.exe 的出站規則
                allow_rule = [
                    'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                    f'name={allow_rule_name}',
                    'dir=out',
                    'action=allow',
                    f'program="{program_path}"',
                    'enable=yes',
                    'profile=any'  # Apply to all profiles
                ]
                subprocess.run(
                    allow_rule,
                    capture_output=True, text=True, check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                logging.info("已添加 AllowNetworkToggler 規則")

                # 添加防火牆規則，阻止所有出站流量
                block_rule = [
                    'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                    f'name={block_rule_name}',
                    'dir=out',
                    'action=block',
                    'enable=yes',
                    'profile=any'
                ]
                subprocess.run(
                    block_rule,
                    capture_output=True, text=True, check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                logging.info("已添加 BlockAllOutbound 規則")

                self.is_network_blocked = True
            else:
                # 刪除阻止所有出站流量的規則
                subprocess.run(
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     f'name={block_rule_name}', 'dir=out'],
                    capture_output=True, text=True, check=False,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                logging.info("已刪除 BlockAllOutbound 規則")

                # 刪除允許 NetworkToggler.exe 的規則
                subprocess.run(
                    ['netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                     f'name={allow_rule_name}', 'dir=out'],
                    capture_output=True, text=True, check=False,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                logging.info("已刪除 AllowNetworkToggler 規則")

                self.is_network_blocked = False

            # 更新狀態
            self.update_network_status()
            # 顯示通知
            self.show_notification(block)
        except subprocess.CalledProcessError as e:
            logging.error(f'操作失敗：{e.stderr}')
            self.status_label.setText('操作失敗')
        except Exception as e:
            logging.error(f'操作失敗：{e}')
            self.status_label.setText('操作失敗')

    def show_notification(self, block):
        """顯示網路狀態切換的通知"""
        if block:
            title = "網路狀態"
            message = "網路已被阻止 ❌"
        else:
            title = "網路狀態"
            message = "網路已被允許 ✅"
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 3000)

    def enable_network(self):
        """允許網路連接"""
        self.network_operation(False)
        self.status_label.setText('正在允許網路...')
        self.animate_button(self.enable_btn)

    def disable_network(self):
        """阻止網路連接"""
        self.network_operation(True)
        self.status_label.setText('正在阻止網路...')
        self.animate_button(self.disable_btn)

    def toggle_network(self):
        """切換網路狀態"""
        # 根據當前的 is_network_blocked 狀態來切換
        if self.is_network_blocked:
            self.enable_network()
        else:
            self.disable_network()

    def closeEvent(self, event):
        """覆寫關閉事件，使應用程式最小化到系統托盤，且不顯示通知"""
        event.ignore()
        self.hide()
        # 不顯示通知
        # 如果需要，可以在這裡添加其他處理，例如記錄
        logging.info("應用程式已最小化到系統托盤")

    def exit_app(self):
        """退出應用程式"""
        logging.info("退出應用程式。")
        QApplication.quit()

def main():
    # 創建應用程式
    app = QApplication(sys.argv)
    app.setApplicationName('網路控制器')

    # 確保只運行一個實例
    single = SingleInstance("NetworkTogglerUniqueKey")
    if single.is_running:
        logging.info("已有一個 NetworkToggler 實例在運行中。退出新啟動的實例。")
        sys.exit(0)

    # 確保以管理員權限運行
    if not ctypes.windll.shell32.IsUserAnAdmin():
        logging.info("非管理員權限，嘗試以管理員權限重新啟動。")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join([f'"{arg}"' for arg in sys.argv]), None, 1
        )
        sys.exit(0)

    # 添加到啟動項目
    add_to_startup()

    # 創建主視窗
    toggler = NetworkToggler()
    toggler.show()

    # 運行應用程式
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
