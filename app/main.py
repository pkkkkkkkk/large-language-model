from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router  # routes.py 中定义了 router = APIRouter()

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AI Recipe Generator")
app.include_router(router)  # 注册路由

# 允许跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")