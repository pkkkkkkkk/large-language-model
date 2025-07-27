from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from fastapi.responses import StreamingResponse
from app.crawler import crawler_instance
import asyncio
import logging
import json
import random
from pathlib import Path
from fastapi import BackgroundTasks

import asyncio
# 尝试导入RAG链，如果失败则使用备用方案
try:
    from app.rag_chain import get_rag_chain, simple_query
except ImportError as e:
    logging.error(f"导入RAG链失败: {e}")
    # 提供备用函数
    def get_rag_chain():
        def fallback_chain(query):
            return {"output": "系统暂时不可用，请稍后再试"}
        return fallback_chain
    
    def simple_query(question: str) -> str:
        return "系统暂时不可用，请稍后再试"

# 尝试导入内存和用户存储模块
try:
    from app.user_store import load_users, save_users
except ImportError as e:
    logging.error(f"导入 memory 或 user_store 模块失败: {e}")
    # 提供备用
    
    def load_users():
        return {}
    def save_users(users):
        pass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
active_requests = {}
# ====== 原有的请求模型 ======
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class DishRequest(BaseModel):
    dish_name: str
    include_price: bool = True
    include_nutrition: bool = True

class IngredientsRequest(BaseModel):
    ingredients: List[str]
    dietary_requirements: Optional[str] = None

class PriceRequest(BaseModel):
    ingredient: str

class NutritionRequest(BaseModel):
    food_item: str

# ====== 新增的请求模型 ======
class QueryRequest(BaseModel):
    query: str
    username: str
    session_id: Optional[str] = None  # 支持用户记忆绑定


class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

# ====== 原有的响应模型 ======
class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class DishResponse(BaseModel):
    dish_info: str
    price_info: Optional[str] = None
    nutrition_info: Optional[str] = None
    success: bool = True
    error: Optional[str] = None

# ====== 新增密码修改请求模型 ======
class ChangePasswordRequest(BaseModel):
    username: str
    oldPassword: str
    newPassword: str
# 构建RAG Chain，兼容内存参数
class TerminateRequest(BaseModel):
    username: str
    session_id: str

def load_recipe_database():
    """
    从 ../data/recipe.json 加载菜谱数据到内存中。
    """
    try:
        # 从当前文件(routes.py)位置出发，找到父级目录(项目根目录),
        # 然后进入 'data' 文件夹找到 'recipe.json'
        recipe_path = Path(__file__).parent.parent / 'data' / 'recipes.json'
        with open(recipe_path, 'r', encoding='utf-8') as f:
            database = json.load(f)
        print(f"成功加载 {len(database)} 条菜谱到内存中。")
        return database
    except FileNotFoundError:
        print(f"错误：未能找到文件 {recipe_path}。请确认文件路径是否正确。")
        return []
    except Exception as e:
        print(f"加载 recipe.json 时出错: {e}")
        return []

# 在全局变量中保存数据，避免每次请求都重新读取文件
recipe_database = load_recipe_database()
# ====== 新增的基础接口 ======
@router.get("/ping")
async def ping():
    return {"msg": "pong"}


# --- 实现每日推荐功能的接口 ---
@router.get("/api/daily-recommendation")
async def get_daily_recommendation():
    """从数据库中随机选择一道菜谱作为推荐，并附带一张图片。"""
    if not recipe_database:
        raise HTTPException(
            status_code=500, 
            detail="菜谱数据库为空或加载失败。"
        )
    
    # 1. 随机选择一个菜谱
    random_recipe = random.choice(recipe_database)
    dish_name = random_recipe.get('菜谱名称')
    
    # 2. ✅ 为该菜谱搜索图片
    image_url = None
    if dish_name:
        try:
            print(f"为推荐菜品 '{dish_name}' 搜索图片...")
            # 使用爬虫实例获取图片URL列表
            image_urls = crawler_instance.start(dish_name)
            if image_urls:
                # 随机选择一张图片
                image_url = random.choice(image_urls)
                print(f"✅ 成功找到图片: {image_url}")
        except Exception as e:
            logger.error(f"为每日推荐菜品 '{dish_name}' 爬取图片失败: {e}")

    # 3. ✅ 将图片URL添加到返回的JSON中
    random_recipe['imageUrl'] = image_url
    
    print(f"已随机推荐菜谱: {dish_name}")
    return JSONResponse(content=random_recipe)

# ====== 密码修改接口实现 ======
@router.post("/api/change-password")
async def change_password(req: ChangePasswordRequest):
    """修改用户密码接口"""
    try:
        # 加载用户数据
        users = load_users()
        
        # 验证用户是否存在
        if req.username not in users:
            return {"success": False, "message": "用户不存在"}
        
        # 验证旧密码是否正确
        if users[req.username] != req.oldPassword:
            return {"success": False, "message": "旧密码错误"}
        
        # # 验证新密码长度
        # if len(req.newPassword) < 6:
        #     return {"success": False, "message": "密码长度至少6位"}
        
        # 更新密码
        users[req.username] = req.newPassword
        save_users(users)
        
        logger.info(f"用户 {req.username} 密码修改成功")
        return {"success": True, "message": "密码修改成功"}
    
    except Exception as e:
        logger.error(f"密码修改失败: {e}", exc_info=True)
        return {"success": False, "message": "密码修改失败"}

# # ====== 新增的生成菜谱接口 ======
# @router.post("/api/ask")
# async def ask_recipe(request: QueryRequest) -> dict:
#     try:
#         # ✅ 获取用户 session_id 或 fallback 为默认 ID
#         session_id = request.session_id if hasattr(request, "session_id") and request.session_id else request.username

#         # ✅ 每个用户独立的 rag_chain 实例（含对话记忆）
#         rag_chain = get_rag_chain(session_id)

#         # ✅ 统一调用入口：invoke({input})
#         result = rag_chain.invoke({"input": request.query}, config={"configurable": {"session_id": request.session_id}})

#         # ✅ 提取返回结果
#         if isinstance(result, dict):
#             answer = result.get("answer") or result.get("output") or str(result)
#         else:
#             answer = str(result)

#         return {"answer": answer}

#     except Exception as e:
#         logger.error(f"生成菜谱失败: {e}")
#         return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/api/ask")
async def ask_recipe_streaming_final(request: QueryRequest):
    """
    处理用户请求，通过解析Agent事件流，实现真正的流式响应。
    """
    async def stream_generator():
        try:
            """异步生成器，用于解析 LangChain 事件流并产生文本块。"""
            session_id = request.session_id or request.username
            rag_chain = get_rag_chain(session_id)
            cancel_event = asyncio.Event()
            active_requests[session_id] = {"cancel_event": cancel_event}
            # 使用 astream_events V1 版本来获取结构化的事件流
            # astream_events 会提供关于Agent执行过程的详细信息
            async for event in rag_chain.astream_events(
                {"input": request.query},
                config={"configurable": {"session_id": session_id}},
                version="v1"
            ):
                if cancel_event.is_set():  # 检查是否触发终止
                    logger.info(f"请求被终止: session_id={session_id}")
                    return  # 退出生成器
                kind = event["event"]

                # 我们只关心由大模型（Chat Model）实时生成的文本块
                if kind == "on_chat_model_stream":
                    # 提取内容块
                    content = event["data"]["chunk"].content
                    if content:
                        # 如果内容非空，则将其发送给前端
                        logger.debug(f"Yielding content chunk: {content}")
                        yield content
                        await asyncio.sleep(0.01) # 短暂休眠，防止CPU占用过高
                # (可选) 您也可以在这里处理其他类型的事件，比如工具的开始和结束
                elif kind == "on_tool_start":
                    logger.info(f"Tool started: {event['name']} with args {event['data'].get('input')}")
                elif kind == "on_tool_end":
                   logger.info(f"Tool ended: {event['name']} with output {event['data'].get('output')}")
        finally:
            # ✅ 确保资源释放
            if session_id in active_requests:
                del active_requests[session_id]

    return StreamingResponse(stream_generator(), media_type='text/plain')
# ====== 新增终止接口 ======
@router.post("/api/terminate")
async def terminate_request(req: TerminateRequest):
    session_id = req.session_id
    if session_id in active_requests:
        active_requests[session_id]["cancel_event"].set()  # 触发终止
        del active_requests[session_id]  # 清理资源
        return {"success": True}
    return {"success": False}
# ====== 新增的用户认证接口 ======
@router.post("/api/register")
async def register_user(req: RegisterRequest):
    """用户注册接口"""
    try:
        users = load_users()
        if req.username in users:
            return {"success": False, "message": "该用户名已存在"}
        users[req.username] = req.password
        save_users(users)
        return {"success": True, "message": "注册成功"}
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        return {"success": False, "message": "注册失败"}

@router.post("/api/login")
async def login_user(req: LoginRequest):
    """用户登录接口"""
    try:
        users = load_users()
        if req.username not in users:
            return {"success": False, "message": "用户不存在"}
        if users[req.username] != req.password:
            return {"success": False, "message": "密码错误"}
        return {"success": True, "message": "登录成功"}
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        return {"success": False, "message": "登录失败"}

# ====== 原有的会话管理 ======
sessions = {}

def get_or_create_session(session_id: str = None):
    """获取或创建会话"""
    if not session_id:
        session_id = f"session_{len(sessions) + 1}"
    
    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "rag_chain": get_rag_chain()
        }
    
    return session_id, sessions[session_id]

# ====== 原有的聊天接口 ======
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """通用聊天接口"""
    try:
        session_id, session = get_or_create_session(request.session_id)
        
        # 记录用户输入
        session["history"].append({"role": "user", "content": request.message})
        
        # 调用RAG链获取回答
        rag_chain = session["rag_chain"]
        result = rag_chain(request.message)
        
        # 提取回答
        if isinstance(result, dict):
            response_text = result.get("output", "抱歉，我无法理解您的问题")
        else:
            response_text = str(result)
        
        # 记录助手回答
        session["history"].append({"role": "assistant", "content": response_text})
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            success=True
        )
        
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        return ChatResponse(
            response="抱歉，处理您的请求时出现错误",
            session_id=request.session_id,
            success=False,
            error=str(e)
        )

# ====== 原有的菜品相关接口 ======
@router.post("/dish", response_model=DishResponse)
async def get_dish_info(request: DishRequest):
    """获取菜品详细信息"""
    try:
        # 构建查询
        query_parts = [f"详细介绍{request.dish_name}的制作方法"]
        
        if request.include_price:
            query_parts.append("包括食材价格和成本估算")
        
        if request.include_nutrition:
            query_parts.append("包括热量和营养信息")
        
        query = "，".join(query_parts)
        
        # 获取回答
        response = simple_query(query)
        
        return DishResponse(
            dish_info=response,
            success=True
        )
        
    except Exception as e:
        logger.error(f"获取菜品信息失败: {e}")
        return DishResponse(
            dish_info="",
            success=False,
            error=str(e)
        )

@router.post("/recommend")
async def recommend_dishes(request: IngredientsRequest):
    """根据食材推荐菜品"""
    try:
        ingredients_str = "、".join(request.ingredients)
        query = f"我有这些食材：{ingredients_str}，请推荐可以制作的菜品"
        
        if request.dietary_requirements:
            query += f"，要求：{request.dietary_requirements}"
        
        query += "，包括制作方法、价格和营养信息"
        
        response = simple_query(query)
        
        return {
            "recommendations": response,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"推荐菜品失败: {e}")
        return {
            "recommendations": "",
            "success": False,
            "error": str(e)
        }

@router.post("/price")
async def get_price(request: PriceRequest):
    """获取食材价格"""
    try:
        query = f"{request.ingredient}的当前市场价格是多少？"
        response = simple_query(query)
        
        return {
            "ingredient": request.ingredient,
            "price_info": response,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"获取价格失败: {e}")
        return {
            "ingredient": request.ingredient,
            "price_info": "",
            "success": False,
            "error": str(e)
        }

@router.post("/nutrition")
async def get_nutrition(request: NutritionRequest):
    """获取营养信息"""
    try:
        query = f"{request.food_item}的营养成分和热量是多少？"
        response = simple_query(query)
        
        return {
            "food_item": request.food_item,
            "nutrition_info": response,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"获取营养信息失败: {e}")
        return {
            "food_item": request.food_item,
            "nutrition_info": "",
            "success": False,
            "error": str(e)
        }

# ====== 原有的系统管理接口 ======
@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "厨师助手API正常运行"}

@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """获取会话历史"""
    try:
        if session_id in sessions:
            return {
                "session_id": session_id,
                "history": sessions[session_id]["history"],
                "success": True
            }
        else:
            return {
                "session_id": session_id,
                "history": [],
                "success": False,
                "error": "会话不存在"
            }
    except Exception as e:
        logger.error(f"获取会话历史失败: {e}")
        return {
            "session_id": session_id,
            "history": [],
            "success": False,
            "error": str(e)
        }
    
@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """清除会话"""
    try:
        if session_id in sessions:
            del sessions[session_id]
            return {"message": f"会话 {session_id} 已清除", "success": True}
        else:
            return {"message": "会话不存在", "success": False}
    except Exception as e:
        logger.error(f"清除会话失败: {e}")
        return {"message": "清除会话失败", "success": False, "error": str(e)}

# ====== 错误处理 ======
# 注意：exception_handler 应该在 FastAPI 应用实例上设置，而不是在 APIRouter 上
# 这些错误处理器应该在 main.py 或 __init__.py 中的 FastAPI 应用实例上注册

# 如果需要在路由级别处理错误，可以使用装饰器或者在具体的路由函数中处理
async def handle_http_exception(request, exc):
    return {
        "success": False,
        "error": exc.detail,
        "status_code": exc.status_code
    }

async def handle_general_exception(request, exc):
    logger.error(f"未处理的异常: {exc}")
    return {
        "success": False,
        "error": "内部服务器错误",
        "status_code": 500
    }