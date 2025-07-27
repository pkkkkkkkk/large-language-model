# app/memory.py
from langchain_core.chat_history import InMemoryChatMessageHistory

# 用户独立聊天历史存储：一个用户一个 InMemoryChatMessageHistory
user_message_history_store = {}

def get_user_message_history(user_id: str):
    if user_id not in user_message_history_store:
        print(f"🔄 为新用户 {user_id} 创建聊天历史")
        user_message_history_store[user_id] = InMemoryChatMessageHistory()
    return user_message_history_store[user_id]
