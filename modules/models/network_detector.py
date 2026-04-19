"""
智能网络检测器 - 检测网络连接状态
"""
import time
import requests


class SmartNetworkDetector:
    def __init__(self):
        self.status = "unknown"
        self.last_check = None
        self.check_interval = 30

    def check_internet(self):
        now = time.time()
        if self.last_check and (now - self.last_check) < self.check_interval:
            return self.status
        self.last_check = now
        test_urls = ["https://www.baidu.com", "https://www.google.com", "https://api.deepseek.com"]
        online_count = 0
        for url in test_urls:
            try:
                response = requests.head(url, timeout=3)
                if response.status_code < 500:
                    online_count += 1
            except:
                continue
        if online_count >= 2:
            self.status = "online"
        elif online_count >= 1:
            self.status = "limited"
        else:
            self.status = "offline"
        return self.status

    def is_online(self):
        status = self.check_internet()
        return status in ["online", "limited"]

    def get_status_message(self):
        status = self.check_internet()
        if status == "online":
            return "✅ 网络连接正常"
        elif status == "limited":
            return "⚠️ 网络连接受限"
        elif status == "offline":
            return "❌ 网络连接断开"
        else:
            return "🔍 检测网络状态..."


network_detector = SmartNetworkDetector()