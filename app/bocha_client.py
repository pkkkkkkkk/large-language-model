# app/bocha_client.py
import os, requests, logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class BochaClient:
    def __init__(self):
        self.api_key = os.getenv("BOCHA_API_KEY")
        self.endpoint = "https://api.bochaai.com/v1/web-search"
        if not self.api_key:
            logger.warning("缺少 BOCHA_API_KEY")

    def _search(self, query: str) -> dict:
        headers = {"Authorization":f"Bearer {self.api_key}", "Content-Type":"application/json"}
        payload = {"query": query, "stream": False, "web_search": True}
        try:
            r = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"BoCha 请求失败: {e}")
            return {}

    def get_price_pages(self, ingredient: str) -> list:
        data = self._search(f"{ingredient} 价格 市场价")
        return data.get("data", {}).get("webPages", {}).get("value", [])

    def get_nutrition_pages(self, food_item: str) -> list:
        data = self._search(f"{food_item} 营养成分 热量 卡路里")
        return data.get("data", {}).get("webPages", {}).get("value", [])
