"""
搜索工具模块
"""
import re
import json
import logging
from langchain.tools import tool
from .base_search import bocha_tool
from .fallback_data import get_fallback_price_info, get_fallback_nutrition_info

logger = logging.getLogger(__name__)

@tool
def search_ingredient_price(ingredient: str) -> str:
    """搜索食材价格信息
    
    Args:
        ingredient: 食材名称
        
    Returns:
        价格信息字符串
    """
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
    """搜索食物营养信息和热量
    
    Args:
        food_item: 食物名称
        
    Returns:
        营养信息字符串
    """
    print("🛠️ 已进入 search_nutrition_info 工具")
    if not bocha_tool:
        return get_fallback_nutrition_info(food_item)
    
    try:
        result = bocha_tool.get_nutrition_info(food_item)
        print("📞 调用了 bocha_tool.get_nutrition_info:", json.dumps(result, ensure_ascii=False, indent=2))
        
        if result.get("error"):
            logger.warning(f"博查搜索失败，使用fallback: {result['error']}")
            return get_fallback_nutrition_info(food_item)
        
        results = result.get("results", [])
        if not results:
            return get_fallback_nutrition_info(food_item)
        
        # 解析营养信息
        nutrition_info = []
        calorie_pattern = r'(\d+(?:\.\d+)?)\s*(?:千卡|卡路里|kcal|大卡|cal)'
        
        for item in results[:3]:
            # 处理不同的响应格式
            if isinstance(item, dict):
                title = item.get("title", "") or item.get("name", "")
                snippet = item.get("snippet", "") or item.get("content", "") or item.get("description", "")
            else:
                title = str(item)
                snippet = str(item)
            
            # 提取热量信息
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