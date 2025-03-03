import sys
import asyncio
import aiohttp
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                            QPushButton, QHBoxLayout, QFrame, QGridLayout,
                            QProgressBar)
from PyQt5.QtGui import QClipboard, QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
import datetime
import json
from bs4 import BeautifulSoup
from functools import partial

class StyledLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 8px;
                color: #212529;
            }
        """)

class StyledButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)

class AsyncWorker(QObject):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.session = None

    async def create_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def get_ip_info(self):
        await self.create_session()
        try:
            async with self.session.get('https://4.ipw.cn', timeout=2) as response:
                domestic_ip = await response.text()
                domestic_ip = domestic_ip.strip()

            async with self.session.get('http://ip-api.com/line?fields=query', timeout=2) as response:
                foreign_ip = await response.text()
                foreign_ip = foreign_ip.strip()

            async def get_ip_details(ip):
                async with self.session.get(f'http://ip-api.com/json/{ip}') as response:
                    return await response.json()

            domestic_ip_info = await get_ip_details(domestic_ip)
            foreign_ip_info = await get_ip_details(foreign_ip)

            if domestic_ip == foreign_ip:
                return {"ip": domestic_ip, "region": f'{domestic_ip_info["regionName"]}, {domestic_ip_info["country"]}'}
            else:
                return {
                    "domestic_ip": domestic_ip,
                    "domestic_region": f'{domestic_ip_info["regionName"]}, {domestic_ip_info["country"]}',
                    "foreign_ip": foreign_ip,
                    "foreign_region": f'{foreign_ip_info["regionName"]}, {foreign_ip_info["country"]}'
                }
        except Exception as e:
            return {"error": f"获取IP地址时出现错误: {e}"}

    async def check_network_freedom(self):
        urls = [
            'https://www.v2ex.com/generate_204',
            'https://www.youtube.com/generate_204',
            'https://am.i.mullvad.net/ip'
        ]
        success_count = 0

        for url in urls:
            for _ in range(2):
                try:
                    async with self.session.get(url, timeout=0.5) as response:
                        if response.status in [204, 200]:
                            success_count += 1
                            break
                except:
                    continue

        return f"自由（{success_count}/{len(urls)}）" if success_count >= 2 else "受限"

    async def extract_prefdomain_url(self):
        try:
            async with self.session.get('https://www.google.com') as response:
                content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            link = soup.find('a', href=lambda href: href and 'setprefdomain' in href)

            if link:
                href = link['href']
                domain = href.split('//')[1].split('/')[0]
                prefdom = href.split('=')[1].split('&')[0]
                if domain == 'www.google.com.hk' and prefdom == 'US':
                    return 'CN'
                else:
                    return prefdom
            return "全球"
        except Exception:
            return "获取Google地区时出现错误"

    async def raw_githubusercontent_speed_test(self):
        try:
            start = datetime.datetime.now()
            async with self.session.head('https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt', timeout=2) as response:
                end = datetime.datetime.now()
                time_without_proxy = (end - start).total_seconds() * 1000
                return f"{time_without_proxy:.2f} 毫秒"
        except Exception as e:
            return f"GitHub连接测试出错: {e}"

    async def get_auto_login_name(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            async with self.session.get('https://login.cnki.net/TopLogin/api/loginapi/IpLoginFlush', headers=headers) as response:
                text = await response.text()
                result = json.loads(text[1:-1])
                if result.get('IsSuccess'):
                    return result.get('ShowName')
                return None
        except Exception:
            return None

    async def run_all_checks(self):
        self.progress.emit("ip_info", "获取IP信息中...")
        ip_info = await self.get_ip_info()
        
        self.progress.emit("network_status", "检查网络状态中...")
        network_status = await self.check_network_freedom()
        
        self.progress.emit("google_region", "检查Google地区中...")
        google_region = await self.extract_prefdomain_url()
        
        self.progress.emit("github_speed", "测试GitHub连接速度中...")
        github_speed = await self.raw_githubusercontent_speed_test()
        
        self.progress.emit("academic", "检查学术机构中...")
        academic_name = await self.get_auto_login_name()

        results = {
            "ip_info": ip_info,
            "network_status": network_status,
            "google_region": google_region,
            "github_speed": github_speed,
            "academic_name": academic_name
        }
        
        await self.close_session()
        self.finished.emit(results)

class WorkerThread(QThread):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.worker.run_all_checks())
        loop.close()

class NetworkStatusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.full_ip_display = False
        self.ip_info_data = {}
        self.worker = None
        self.worker_thread = None

    def initUI(self):
        self.setWindowTitle("网络状态检测工具")
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("网络状态检测工具")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                margin-bottom: 20px;
            }
        """)
        main_layout.addWidget(title)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dcdde1;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # 创建网格布局用于信息显示
        grid = QGridLayout()
        grid.setSpacing(10)

        # IP信息区域
        ip_frame = QFrame()
        ip_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        ip_layout = QVBoxLayout(ip_frame)
        
        self.ip_info = StyledLabel()
        ip_layout.addWidget(self.ip_info)

        button_layout = QHBoxLayout()
        toggle_ip_button = StyledButton("切换IP显示模式")
        copy_ip_button = StyledButton("复制IP地址")
        toggle_ip_button.clicked.connect(self.toggle_ip_display)
        copy_ip_button.clicked.connect(self.copy_ip_address)
        button_layout.addWidget(toggle_ip_button)
        button_layout.addWidget(copy_ip_button)
        ip_layout.addLayout(button_layout)

        grid.addWidget(ip_frame, 0, 0, 1, 2)

        # 其他信息区域
        self.network_status = StyledLabel()
        self.google_region = StyledLabel()
        self.github_speed = StyledLabel()
        self.academic_institution = StyledLabel()

        grid.addWidget(self.network_status, 1, 0)
        grid.addWidget(self.google_region, 1, 1)
        grid.addWidget(self.github_speed, 2, 0)
        grid.addWidget(self.academic_institution, 2, 1)

        main_layout.addLayout(grid)

        # 刷新按钮
        self.refresh_button = StyledButton("刷新")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 6px;
                font-weight: bold;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_data)
        main_layout.addWidget(self.refresh_button)

        self.setLayout(main_layout)

    def refresh_data(self):
        self.refresh_button.setEnabled(False)
        self.progress_bar.setMaximum(0)  # 设置为循环进度条
        self.progress_bar.show()
        
        self.ip_info.setText("获取IP信息中...")
        self.network_status.setText("正在刷新...")
        self.google_region.setText("正在刷新...")
        self.github_speed.setText("正在刷新...")
        self.academic_institution.setText("正在刷新...")

        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()

        self.worker = AsyncWorker()
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.handle_results)
        
        self.worker_thread = WorkerThread(self.worker)
        self.worker_thread.start()

    def update_progress(self, component, message):
        if component == "ip_info":
            self.ip_info.setText(message)
        elif component == "network_status":
            self.network_status.setText(message)
        elif component == "google_region":
            self.google_region.setText(message)
        elif component == "github_speed":
            self.github_speed.setText(message)
        elif component == "academic":
            self.academic_institution.setText(message)

    def handle_results(self, results):
        self.ip_info_data = results["ip_info"]
        self.update_ip_display()
        
        self.network_status.setText(f"网络访问状态：{results['network_status']}")
        self.google_region.setText(f"Google地区：{results['google_region']}")
        self.github_speed.setText(f"GitHub连接速度：{results['github_speed']}")
        academic_name = results['academic_name']
        self.academic_institution.setText(f"学术机构：{academic_name if academic_name else '未登录'}")
        
        self.progress_bar.hide()
        self.refresh_button.setEnabled(True)

    def update_ip_display(self):
        if "error" in self.ip_info_data:
            self.ip_info.setText(self.ip_info_data["error"])
        else:
            if "ip" in self.ip_info_data:
                ip_display = self.mask_ip(self.ip_info_data['ip']) if not self.full_ip_display else self.ip_info_data['ip']
                self.ip_info.setText(f"IP地址：{ip_display}（{self.ip_info_data['region']}）")
            else:
                domestic_ip_display = self.mask_ip(self.ip_info_data['domestic_ip']) if not self.full_ip_display else self.ip_info_data['domestic_ip']
                foreign_ip_display = self.mask_ip(self.ip_info_data['foreign_ip']) if not self.full_ip_display else self.ip_info_data['foreign_ip']
                self.ip_info.setText(f"IP地址（面向国内网站）：{domestic_ip_display}（{self.ip_info_data['domestic_region']}）\n"
                                     f"IP地址（面向国外网站）：{foreign_ip_display}（{self.ip_info_data['foreign_region']}）")

    def mask_ip(self, ip):
        parts = ip.split('.')
        return '.'.join(parts[:2] + ['*', '*'])

    def toggle_ip_display(self):
        if not self.ip_info_data:
            return
        self.full_ip_display = not self.full_ip_display
        self.update_ip_display()

    def copy_ip_address(self):
        clipboard = QApplication.clipboard()
        if "ip" in self.ip_info_data:
            clipboard.setText(self.ip_info_data['ip'])
        else:
            clipboard.setText(f"国内IP: {self.ip_info_data['domestic_ip']}, 国外IP: {self.ip_info_data['foreign_ip']}")

# 主程序入口
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NetworkStatusApp()
    window.refresh_data()
    window.show()
    sys.exit(app.exec_())