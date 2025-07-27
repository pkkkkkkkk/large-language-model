import os
from dotenv import load_dotenv

from langchain_community.chat_models import ChatTongyi
from langchain.schema import HumanMessage

# 加载 .env 文件中的 API 密钥
load_dotenv()

# 初始化模型（会自动读取 DASHSCOPE_API_KEY）
model = ChatTongyi()

# 向模型发送测试信息
messages = [HumanMessage(content="请告诉我一个番茄炒蛋的简单做法")]

try:
    response = model.invoke(messages)
    print("✅ 成功连接模型，返回内容如下：")
    print(response.content)
except Exception as e:
    print("❌ 调用失败，错误信息如下：")
    print(e)
