"""
图片搜索工具模块
"""
import logging
import random
from langchain.tools import tool
from ..crawler import crawler_instance  # 导入纯爬虫实例

logger = logging.getLogger(__name__)

@tool
def search_dish_image(dish_name: str) -> str:
    """搜索菜品图片
    
    Args:
        dish_name: 菜品名称
        
    Returns:
        图片URL或错误信息
    """
    print(f"🛠️ 已进入 search_dish_image 工具，搜索菜品：{dish_name}")
    
    try:
        # 使用全局爬虫实例
        image_urls = crawler_instance.start(dish_name)
        
        if image_urls and len(image_urls) > 0:
            # 随机选择一个图片URL
            selected_image = random.choice(image_urls)
            
            result = f"🖼️ 找到 {dish_name} 的图片:\n"
            result += f"图片URL: {selected_image}\n"
            result += f"共找到 {len(image_urls)} 张相关图片"
            
            return result
        else:
            return f"❌ 抱歉，未能找到 {dish_name} 的相关图片"
            
    except Exception as e:
        logger.error(f"搜索菜品图片异常: {e}")
        return f"搜索 {dish_name} 图片时出现异常: {str(e)}"

@tool
def get_multiple_dish_images(dish_name: str, count: int = 3) -> str:
    """获取多张菜品图片
    
    Args:
        dish_name: 菜品名称
        count: 需要的图片数量，默认3张
        
    Returns:
        多个图片URL或错误信息
    """
    print(f"🛠️ 已进入 get_multiple_dish_images 工具，搜索菜品：{dish_name}，数量：{count}")
    
    try:
        # 使用全局爬虫实例
        image_urls = crawler_instance.start(dish_name)
        
        if image_urls and len(image_urls) > 0:
            # 限制返回的图片数量
            selected_images = image_urls[:min(count, len(image_urls))]
            
            result = f"🖼️ 找到 {dish_name} 的图片 ({len(selected_images)} 张):\n\n"
            
            for i, url in enumerate(selected_images, 1):
                result += f"{i}. {url}\n"
            
            result += f"\n📊 总共找到 {len(image_urls)} 张相关图片"
            
            return result
        else:
            return f"❌ 抱歉，未能找到 {dish_name} 的相关图片"
            
    except Exception as e:
        logger.error(f"获取多张菜品图片异常: {e}")
        return f"获取 {dish_name} 图片时出现异常: {str(e)}"