"""
基础搜索工具类
"""
import os
import requests
import json
from dotenv import load_dotenv
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class BochaSearchTool:
    """博查搜索工具类"""

    def __init__(self):
        self.api_key = os.getenv("BOCHA_API_KEY")
        print("🔑 BoCha API Key:", self.api_key)
        if not self.api_key:
            logger.warning("缺少 BOCHA_API_KEY，搜索功能将受限")

    def search(self, query: str, search_type: str = "web") -> dict:
        """执行博查搜索"""
        if not self.api_key:
            return {"error": "未配置博查API密钥", "results": []}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "query": query,
            "stream": False,
            "web_search": True
        }

        try:
            endpoint = "https://api.bochaai.com/v1/web-search"
            print("📡 正在发送 BoCha API 请求...")
            print("➡️ 请求内容：", json.dumps(payload, ensure_ascii=False))

            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            print("✅ 收到 BoCha API 响应：", response.text)

            result = response.json()
            # 针对价格搜索，直接提取 data.webPages.value
            if search_type == "price" and "data" in result:
                web_pages = result["data"].get("webPages", {})
                if isinstance(web_pages, dict) and "value" in web_pages:
                    return {"results": web_pages["value"]}
            # 针对营养搜索，同样提取 webPages.value
            if search_type == "nutrition" and "data" in result:
                web_pages = result["data"].get("webPages", {})
                if isinstance(web_pages, dict) and "value" in web_pages:
                    return {"results": web_pages["value"]}
            # 原有通用解析逻辑
            if "data" in result:
                search_results = result["data"]
                if isinstance(search_results, list):
                    return {"results": search_results}
                elif isinstance(search_results, dict) and "results" in search_results:
                    return {"results": search_results["results"]}
                else:
                    return {"results": [search_results]}
            else:
                return {"results": [result] if not isinstance(result, list) else result}

        except requests.RequestException as e:
            logger.error(f"博查搜索请求失败: {e}")
            return {"error": str(e), "results": []}

    def get_ingredient_price(self, ingredient: str) -> dict:
        """获取食材价格信息"""
        query = f"{ingredient} 价格 市场价"
        return self.search(query, "price")

    def get_nutrition_info(self, food_item: str) -> dict:
        """获取营养信息和热量"""
        query = f"{food_item} 营养成分 热量 卡路里"
        return self.search(query, "nutrition")

# 全局初始化博查搜索工具
try:
    bocha_tool = BochaSearchTool()
except Exception as e:
    logger.error(f"初始化博查工具失败: {e}")
    bocha_tool = None