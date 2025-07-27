import os
import requests
import json
from dotenv import load_dotenv
from langchain.tools import tool
import re
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
            "web_search": True #111
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

def get_fallback_price_info(ingredient: str) -> str:
    """提供常见食材的价格信息fallback"""
    # 常见食材价格参考数据库（按地区可能有差异）
    price_db = {
        "鸡蛋": "约5-8元/斤",
        "西红柿": "约3-6元/斤",
        "土豆": "约2-4元/斤",
        "白菜": "约1-3元/斤",
        "胡萝卜": "约2-4元/斤",
        "豆腐": "约3-5元/斤",
        "鸡胸肉": "约12-18元/斤",
        "牛肉": "约35-50元/斤",
        "猪肉": "约15-25元/斤",
        "大米": "约3-6元/斤",
        "面粉": "约3-5元/斤",
        "面条": "约4-8元/斤",
        "食用油": "约8-15元/升",
        "生菜": "约2-4元/斤",
        "黄瓜": "约2-5元/斤",
        "茄子": "约3-6元/斤",
        "青椒": "约3-6元/斤"
    }
    
    # 检查是否包含数据库中的食材
    for food, price in price_db.items():
        if food in ingredient or ingredient in food:
            return f"{ingredient} 价格参考:\n{food}: {price}\n\n注：价格仅供参考，实际价格因地区、季节、品质等因素而异。"
    
    # 默认回复
    return f"抱歉，暂时无法获取 {ingredient} 的准确价格信息。建议您查询当地市场价格或在线购物平台。"

def get_fallback_nutrition_info(food_item: str) -> str:
    """提供常见食物的营养信息fallback"""
    # 常见食物热量数据库
    nutrition_db = {
        "米饭": "每100克约116千卡",
        "面条": "每100克约350千卡（干重）",
        "鸡蛋": "每个约78千卡",
        "西红柿": "每100克约19千卡",
        "鸡胸肉": "每100克约165千卡",
        "牛肉": "每100克约250千卡",
        "豆腐": "每100克约76千卡",
        "白菜": "每100克约17千卡",
        "土豆": "每100克约77千卡",
        "胡萝卜": "每100克约41千卡"
    }
    
    # 复合食物估算
    if "西红柿鸡蛋面" in food_item or "番茄鸡蛋面" in food_item:
        return f"{food_item} 营养估算:\n基于主要成分计算：\n- 面条(100g): 约350千卡\n- 鸡蛋(1个): 约78千卡\n- 西红柿(100g): 约19千卡\n- 食用油等: 约50千卡\n\n总计：约497千卡"
    
    elif "蛋炒饭" in food_item:
        return f"{food_item} 营养估算:\n基于主要成分计算：\n- 米饭(150g): 约174千卡\n- 鸡蛋(1个): 约78千卡\n- 食用油等: 约80千卡\n\n总计：约332千卡"
    
    elif "麻婆豆腐" in food_item:
        return f"{food_item} 营养估算:\n基于主要成分计算：\n- 豆腐(200g): 约152千卡\n- 肉末(50g): 约125千卡\n- 调料油等: 约100千卡\n\n总计：约377千卡"
    
    # 检查是否包含数据库中的基础食材
    for ingredient, calories in nutrition_db.items():
        if ingredient in food_item:
            return f"{food_item} 营养信息:\n{ingredient}: {calories}"
    
    # 默认回复
    return f"抱歉，暂时无法获取 {food_item} 的准确营养信息。建议您查询具体的营养成分表或咨询营养师。"

@tool
def search_ingredient_price(ingredient: str) -> str:
    """搜索食材价格信息"""
    print("🛠️ 已进入 search_ingredient_price 工具")
    if not bocha_tool:
        return get_fallback_price_info(ingredient)

    try:
        result = bocha_tool.get_ingredient_price(ingredient)
        print("📞 调用了 bocha_tool.get_ingredient_price:", json.dumps(result, ensure_ascii=False, indent=2))

        if result.get("error"):
            logger.warning(f"博查搜索失败，使用fallback: {result['error']}")
            return get_fallback_price_info(ingredient)

        results = result.get("results", [])
        if not results:
            return get_fallback_price_info(ingredient)

        # 解析价格信息
        price_info = []
        price_pattern = r'(\d+(?:\.\d+)?)\s*(?:元|块|¥|人民币|块钱)'
        for item in results[:3]:
            if isinstance(item, dict):
                title = item.get("name", item.get("title", ""))
                snippet = item.get("snippet", item.get("description", ""))
            else:
                title = snippet = str(item)
            
            prices = re.findall(price_pattern, snippet)
            if prices:
                price_info.append(f"• {title[:50]}...: {prices[0]}元")
            else:
                price_info.append(f"• {title[:80]}... 无价格信息")

        if price_info:
            return f"🔍 {ingredient} 价格信息:\n" + "\n".join(price_info)
        else:
            return get_fallback_price_info(ingredient)

    except Exception as e:
        logger.error(f"搜索价格信息异常: {e}")
        return get_fallback_price_info(ingredient)

@tool
def search_nutrition_info(food_item: str) -> str:
    """搜索食物营养信息和热量"""
    if not bocha_tool:
        return get_fallback_nutrition_info(food_item)
    
    try:
        result = bocha_tool.get_nutrition_info(food_item)
        
        if result.get("error"):
            logger.warning(f"博查搜索失败，使用fallback: {result['error']}")
            return get_fallback_nutrition_info(food_item)
        
        results = result.get("results", [])
        if not results:
            return get_fallback_nutrition_info(food_item)
        
        # 解析营养信息
        nutrition_info = []
        for item in results[:3]:
            # 处理不同的响应格式
            if isinstance(item, dict):
                title = item.get("title", "") or item.get("name", "")
                snippet = item.get("snippet", "") or item.get("content", "") or item.get("description", "")
            else:
                title = str(item)
                snippet = str(item)
            
            # 提取热量信息
            calorie_pattern = r'(\d+(?:\.\d+)?)\s*(?:千卡|卡路里|kcal|大卡|cal)'
            calories = re.findall(calorie_pattern, snippet)
            
            if calories:
                nutrition_info.append(f"• {title[:50]}...: {calories[0]}千卡")
            elif title or snippet:
                content = title or snippet
                nutrition_info.append(f"• {content[:100]}...")
        
        if nutrition_info:
            return f"🥗 {food_item} 营养信息:\n" + "\n".join(nutrition_info)
        else:
            return get_fallback_nutrition_info(food_item)
    
    except Exception as e:
        logger.error(f"搜索营养信息异常: {e}")
        return get_fallback_nutrition_info(food_item)

@tool
def calculate_dish_cost(ingredients: str) -> str:
    """计算菜品成本"""
    try:
        # 将字符串分割成列表
        ingredients_list = [ing.strip() for ing in ingredients.split(',') if ing.strip()]
        
        total_cost = 0
        cost_details = []
        
        for ingredient in ingredients_list:
            # 搜索每种食材的价格
            price_info = search_ingredient_price(ingredient)
            
            # 简单的价格提取逻辑
            price_match = re.search(r'(\d+(?:\.\d+)?)\s*元', price_info)
            if price_match:
                price = float(price_match.group(1))
                total_cost += price
                cost_details.append(f"{ingredient}: {price}元")
            else:
                cost_details.append(f"{ingredient}: 价格信息不全")
        
        result = f"菜品成本估算:\n"
        result += "\n".join(cost_details)
        result += f"\n\n预估总成本: {total_cost:.2f}元"
        
        return result
    
    except Exception as e:
        return f"计算菜品成本时出现异常: {str(e)}"

# 导出工具列表，方便其他模块导入
COOKING_TOOLS = [
    search_ingredient_price,
    search_nutrition_info,
    calculate_dish_cost
]

# 导出工具类，方便直接使用
__all__ = [
    'BochaSearchTool',
    'search_ingredient_price',
    'search_nutrition_info',
    'calculate_dish_cost',
    'COOKING_TOOLS'
]