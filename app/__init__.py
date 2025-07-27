# app/__init__.py 或 main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="厨师助手API",
    description="一个智能的厨师助手API，提供菜谱生成、食材推荐等功能",
    version="1.0.0"
)

# 导入路由
from app.routes import router
app.include_router(router)

# 在 FastAPI 应用实例上设置异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP异常: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "内部服务器错误",
            "status_code": 500
        }
    )

# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("厨师助手API启动成功")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("厨师助手API正在关闭")

# 根路径
@app.get("/")
async def root():
    return {
        "message": "欢迎使用厨师助手API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)