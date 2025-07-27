"""
计算工具模块
"""
import re
import logging
from langchain.tools import tool
from .search_tools import search_ingredient_price

logger = logging.getLogger(__name__)

@tool
def calculate_dish_cost(ingredients: str) -> str:
    """计算菜品成本
    
    Args:
        ingredients: 食材清单，用逗号分隔
        
    Returns:
        成本计算结果字符串
    """
    print("🛠️ 已进入 calculate_dish_cost 工具")
    try:
        # 将字符串分割成列表
        ingredients_list = [ing.strip() for ing in ingredients.split(',') if ing.strip()]
        
        if not ingredients_list:
            return "请提供有效的食材清单"
        
        total_cost = 0
        cost_details = []
        
        for ingredient in ingredients_list:
            print(f"🔍 正在查询 {ingredient} 的价格...")
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
        
        result = f"📊 菜品成本估算:\n"
        result += "\n".join(cost_details)
        
        if total_cost > 0:
            result += f"\n\n💰 预估总成本: {total_cost:.2f}元"
        else:
            result += "\n\n💰 由于部分食材价格信息缺失，无法计算准确总成本"
        
        result += "\n\n📝 注：价格仅供参考，实际成本可能因地区、季节、品质等因素而异"
        
        return result
    
    except Exception as e:
        logger.error(f"计算菜品成本异常: {e}")
        return f"计算菜品成本时出现异常: {str(e)}"

@tool 
def calculate_nutrition_per_serving(food_item: str, servings: int = 1) -> str:
    """计算每份食物的营养信息
    
    Args:
        food_item: 食物名称
        servings: 份数，默认为1
        
    Returns:
        每份营养信息字符串
    """
    print("🛠️ 已进入 calculate_nutrition_per_serving 工具")
    try:
        from .search_tools import search_nutrition_info
        
        # 获取基础营养信息
        base_nutrition = search_nutrition_info(food_item)
        
        if servings <= 0:
            return "份数必须大于0"
        
        # 提取热量数字
        calorie_pattern = r'(\d+(?:\.\d+)?)\s*千卡'
        calories = re.findall(calorie_pattern, base_nutrition)
        
        if calories:
            # 计算每份热量
            total_calories = float(calories[0])
            per_serving_calories = total_calories / servings
            
            result = f"🍽️ {food_item} 营养分析:\n"
            result += f"总热量: {total_calories}千卡\n"
            result += f"份数: {servings}份\n"
            result += f"每份热量: {per_serving_calories:.1f}千卡\n\n"
            result += "详细信息:\n" + base_nutrition
            
            return result
        else:
            return f"🍽️ {food_item} 营养信息:\n份数: {servings}份\n\n" + base_nutrition
            
    except Exception as e:
        logger.error(f"计算每份营养信息异常: {e}")
        return f"计算每份营养信息时出现异常: {str(e)}"