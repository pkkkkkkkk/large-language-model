import os
import json
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from dotenv import load_dotenv
load_dotenv()


# 加载 DashScope 向量模型
embedding = DashScopeEmbeddings(
    model="text-embedding-v1",
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
)

# 加载菜谱 JSON 数据
with open("data/recipes.json", "r", encoding="utf-8") as f:
    recipes = json.load(f)

# 构造 Document（直接把每条 JSON 全内容序列化为字符串）
documents = []
for recipe in recipes:
    content = json.dumps(recipe, ensure_ascii=False, indent=2)  # ✅ 保留中文，格式美观
    documents.append(Document(page_content=content))  # ❗只用 page_content，不加 metadata

# 构建 FAISS 向量库
vectorstore = FAISS.from_documents(documents, embedding)

# 保存
vectorstore.save_local("vectorstore", index_name="recipe")

print("✅ 全 JSON 内容已写入向量库并保存")
