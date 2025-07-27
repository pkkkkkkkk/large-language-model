"""
备用数据模块 - 当API不可用时提供基础数据
"""
import logging

logger = logging.getLogger(__name__)

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
        "青椒": "约3-6元/斤",
        "洋葱": "约2-4元/斤",
        "韭菜": "约3-5元/斤",
        "菠菜": "约3-5元/斤",
        "芹菜": "约2-4元/斤",
        "冬瓜": "约1-3元/斤",
        "南瓜": "约2-4元/斤",
        "萝卜": "约1-3元/斤"
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
        "胡萝卜": "每100克约41千卡",
        "生菜": "每100克约16千卡",
        "黄瓜": "每100克约16千卡",
        "茄子": "每100克约24千卡",
        "青椒": "每100克约22千卡",
        "洋葱": "每100克约40千卡",
        "菠菜": "每100克约23千卡",
        "芹菜": "每100克约16千卡"
    }
    
    # 复合食物估算
    composite_foods = {
        "西红柿鸡蛋面": {
            "ingredients": [
                ("面条", "100g", 350),
                ("鸡蛋", "1个", 78),
                ("西红柿", "100g", 19),
                ("食用油等", "", 50)
            ],
            "total": 497
        },
        "番茄鸡蛋面": {
            "ingredients": [
                ("面条", "100g", 350),
                ("鸡蛋", "1个", 78),
                ("西红柿", "100g", 19),
                ("食用油等", "", 50)
            ],
            "total": 497
        },
        "蛋炒饭": {
            "ingredients": [
                ("米饭", "150g", 174),
                ("鸡蛋", "1个", 78),
                ("食用油等", "", 80)
            ],
            "total": 332
        },
        "麻婆豆腐": {
            "ingredients": [
                ("豆腐", "200g", 152),
                ("肉末", "50g", 125),
                ("调料油等", "", 100)
            ],
            "total": 377
        }
    }
    
    # 检查复合食物
    for dish_name, dish_data in composite_foods.items():
        if dish_name in food_item:
            result = f"{food_item} 营养估算:\n基于主要成分计算：\n"
            for ingredient, amount, calories in dish_data["ingredients"]:
                if amount:
                    result += f"- {ingredient}({amount}): 约{calories}千卡\n"
                else:
                    result += f"- {ingredient}: 约{calories}千卡\n"
            result += f"\n总计：约{dish_data['total']}千卡"
            return result
    
    # 检查是否包含数据库中的基础食材
    for ingredient, calories in nutrition_db.items():
        if ingredient in food_item:
            return f"{food_item} 营养信息:\n{ingredient}: {calories}"
    
    # 默认回复
    return f"抱歉，暂时无法获取 {food_item} 的准确营养信息。建议您查询具体的营养成分表或咨询营养师。"