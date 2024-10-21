import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtGui import QClipboard
import datetime
import json
from bs4 import BeautifulSoup

class NetworkStatusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.full_ip_display = False
        self.ip_info_data = {}

    def initUI(self):
        self.setWindowTitle("网络状态检测工具")
        self.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()

        # IP信息
        self.ip_info = QLabel("IP 信息：")
        layout.addWidget(self.ip_info)

        # 切换IP显示模式按钮
        toggle_ip_button = QPushButton("切换IP显示模式")
        toggle_ip_button.clicked.connect(self.toggle_ip_display)
        layout.addWidget(toggle_ip_button)

        # 复制IP地址按钮
        copy_ip_button = QPushButton("复制IP地址")
        copy_ip_button.clicked.connect(self.copy_ip_address)
        layout.addWidget(copy_ip_button)

        # 网络自由状态
        self.network_status = QLabel("网络自由状态：")
        layout.addWidget(self.network_status)

        # Google地区
        self.google_region = QLabel("Google地区：")
        layout.addWidget(self.google_region)

        # GitHub连接速度
        self.github_speed = QLabel("GitHub连接速度：")
        layout.addWidget(self.github_speed)

        # 学术机构信息
        self.academic_institution = QLabel("学术机构：")
        layout.addWidget(self.academic_institution)

        # 刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_button)

        self.setLayout(layout)

    def refresh_data(self):
        self.ip_info.setText("获取IP信息中...")
        self.ip_info_data = self.get_ip_info()
        self.update_ip_display()

        self.network_status.setText(f"网络访问状态：{self.check_network_freedom()}")
        self.google_region.setText(f"Google地区：{self.extract_prefdomain_url()}")
        self.github_speed.setText(f"GitHub连接速度：{self.raw_githubusercontent_speed_test():.2f} 毫秒")
        academic_name = self.get_auto_login_name()
        self.academic_institution.setText(f"学术机构：{academic_name if academic_name else '未登录'}")

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
        self.full_ip_display = not self.full_ip_display
        self.update_ip_display()

    def copy_ip_address(self):
        clipboard = QApplication.clipboard()
        if "ip" in self.ip_info_data:
            clipboard.setText(self.ip_info_data['ip'])
        else:
            clipboard.setText(f"国内IP: {self.ip_info_data['domestic_ip']}, 国外IP: {self.ip_info_data['foreign_ip']}")

    def get_ip_info(self):
        try:
            domestic_ip = requests.get('https://4.ipw.cn', timeout=2).text.strip()
            foreign_ip = requests.get('http://ip-api.com/line?fields=query', timeout=2).text.strip()
            def get_ip_details(ip):
                response = requests.get(f'http://ip-api.com/json/{ip}').json()
                return response

            domestic_ip_info = get_ip_details(domestic_ip)
            foreign_ip_info = get_ip_details(foreign_ip)

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

    def check_network_freedom(self):
        urls = [
            'https://www.v2ex.com/generate_204',
            'https://www.youtube.com/generate_204',
            'https://am.i.mullvad.net/ip'
        ]
        success_count = 0

        for url in urls:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code in [204, 200]:
                    success_count += 1
            except requests.exceptions.RequestException:
                continue

        if success_count >= 2:
            return f"自由（{success_count}/{len(urls)}）"
        else:
            return "受限"

    def extract_prefdomain_url(self):
        try:
            content = requests.get('https://www.google.com').text
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
            else:
                return "全球"
        except Exception as e:
            return "获取Google地区时出现错误"

    def raw_githubusercontent_speed_test(self):
        try:
            start = datetime.datetime.now()
            requests.head('https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt')
            end = datetime.datetime.now()
            time_without_proxy = (end - start).total_seconds() * 1000
            return time_without_proxy
        except Exception as e:
            return f"GitHub连接测试出错: {e}"

    def get_auto_login_name(self):
        try:
            response = requests.get(
                'https://login.cnki.net/TopLogin/api/loginapi/IpLoginFlush',
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
            )
            result = json.loads(response.text[1:-1])
            if result.get('IsSuccess'):
                return result.get('ShowName')
            else:
                return None
        except Exception as e:
            return None

# 主程序入口
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NetworkStatusApp()
    window.show()
    sys.exit(app.exec_())