# app/db.py

import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from functools import lru_cache # ✅ 1. 导入 lru_cache

load_dotenv()
dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")

@lru_cache(maxsize=1) # ✅ 2. 添加缓存装饰器
def get_vectorstore():
    print("--- 正在从磁盘加载向量数据库 (此消息应只在服务启动时出现一次) ---")
    embedding = DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=dashscope_api_key
    )

    return FAISS.load_local(
        folder_path="vectorstore",
        embeddings=embedding,
        index_name="recipe",
        allow_dangerous_deserialization=True
    )