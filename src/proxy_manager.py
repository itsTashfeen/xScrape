import os
from typing import Dict
from dotenv import load_dotenv

class ProxyManager:
    def __init__(self):
        load_dotenv()
        self.proxy = self.load_proxy()

    def load_proxy(self) -> Dict:
        return {
            "server": f"http://{os.getenv('PROXY_HOST')}:{os.getenv('PROXY_PORT')}",
            "username": os.getenv('PROXY_USERNAME'),
            "password": os.getenv('PROXY_PASSWORD')
        }

    def get_proxy(self) -> Dict:
        return self.proxy 