import json
from typing import Dict
from pathlib import Path

class ProxyManager:
    def __init__(self):
        self.proxy = self.load_proxy()

    def load_proxy(self) -> Dict:
        return {
            "server": "http://brd.superproxy.io:33335",
            "username": "brd-customer-hl_cc04b389-zone-isp_proxy1",
            "password": "xurvd78k1bef"
        }

    def get_proxy(self) -> Dict:
        return self.proxy 