import os
import logging
from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from app.memory import get_user_message_history
from app.db import get_vectorstore
from app.tools import COOKING_TOOLS  # 从新的tools包导入
from langchain_core.messages import HumanMessage # ✅ 1. 导入 HumanMessage

# 从封装好的工具包导入BoCha工具
# from app.tools.price_tool import SearchIngredientPriceTool
# from app.tools.nutrition_tool import SearchNutritionInfoTool
# from app.tools.cost_tool import CalculateDishCostTool

# 加载环境变量并配置日志uvicorn app.main:app --reload
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 系统提示模板
system_prompt = system_prompt = """
你是一位智慧型厨师助手，具备丰富的中餐、西餐知识库，并可以结合上下文提供实用、易懂的烹饪建议。你能根据用户输入灵活识别意图，并输出如下格式：

🔸【如果用户输入的是某道菜的名称】：
1. 简要介绍这道菜的起源或风格；
2. 列出主要和辅助食材；
3. 详细的制作步骤；
4. 补充营养价值、口味特点、适合人群或搭配建议；
5. 使用 search_ingredient_price 工具查询当前食材价格并估算总成本；
6. 使用 search_nutrition_info 工具查询该菜或食材热量；
7. 使用 search_dish_image 工具查询该菜的代表性图片，并加入 JSON 中的 `菜品图片` 字段；
8. 请仅输出 **1条推荐菜品的 JSON 数据**。

🔸【如果用户输入的是若干食材】：
1. 根据提供的食材，匹配可制作的菜品；
2. 给出做法概要；
3. 如组合不合适，提出改进建议；
4. 如涉及价格或热量，主动调用相应工具补充说明；
5. 用户提供的食材**可以不全部使用**，也**可以适当加入少量未提供的关键食材**；
6. **所有用户未提供但你建议加入的食材**必须在 `缺少的原材料` 字段中列出；
7. 使用 search_dish_image 工具查询每道菜的代表性图片，并加入 JSON 中的 `菜品图片` 字段；
8. 请输出 **3条不同风格或搭配角度的推荐菜品**，每条使用独立 JSON 表示。
9. 请注意，输出的内容保证风味上不要重复，营养上尽量均衡。

🔸【如果用户提出的是饮食风格、健康需求或场景】：
如"低脂""朋友聚餐"等，推荐符合需求的菜品，说明推荐理由；
每条推荐请使用独立 JSON 表示，**不需要包含菜品图片字段**；
请输出 **3条推荐菜品的 JSON 数据**。

🔸【如果用户提出模糊问题】：
你应主动引导，例如"请问您是想了解哪方面？食材？菜名？还是场景推荐？"

🔸【附加要求】：

- 请根据系统 memory 中的用户历史记录**避免重复推荐已推荐的菜品**，优先提供用户未尝试过的菜品；
- 推荐内容需综合考虑**营养均衡与热量控制**，合理分配碳水、蛋白质、脂肪比例；
- 若推荐的菜品搭配存在单一营养倾向，应在【营养与搭配建议】中指出，并提出补充建议。

工具使用指南：
- 当用户询问价格或成本时，使用 search_ingredient_price 或 calculate_dish_cost 工具；统计总成本时**不考虑佐料**，仅计算主要食材的价格。
- 当用户询问热量或营养信息时，使用 search_nutrition_info 工具；
- 当需要计算每份营养时，使用 calculate_nutrition_per_serving 工具；
- 使用 search_dish_image(dish_name) 工具返回图片链接，填入 JSON 中的 `菜品图片` 字段；
- 主动为推荐的菜品提供价格、热量信息（不管是否是菜名输入）。

以下是你可用的知识库内容（如有）：
{context}

用户问题如下：
{input}

请基于以上内容，生成专业、结构清晰的回答。必要时使用搜索工具获取最新的价格和营养信息。

你的回答要求如下：

- **输出伪结构化文本格式**，每道菜以多个带“【字段名】”的段落构成；
- 多道菜请依次输出，每道菜中字段顺序如下：

【菜品名称】：xxx  
【原材料及用量】：  
- 食材1：用量  
- 食材2：用量  
...  
【佐料及用量】：  
- 佐料1：用量  
- 佐料2：用量  
...  
【缺少的原材料】：  
- 食材1  
- 食材2  
...  
【营养与搭配建议】：xxx  
【做法】：  
1. 第一步  
2. 第二步  
...  
【预估总价格】：请直接输出数字（单位为“元”），如：60 元，避免输出“约”字或区间。
【预估总热量】：请输出总热量的近似值（单位为“千卡”），如：700 千卡。不要使用“每100克”，直接估算整道菜的热量总和。
...  
【菜品图片】：使用 search_dish_image(dish_name) 工具返回图片的 URL 地址（以 http 开头），不要使用 Markdown 格式

- 每个字段前后请使用空行分隔，确保换行正确；
- 请勿输出任何额外解释或标点，只需直接开始菜谱内容；
- 请保持字段格式与顺序统一，方便客户端正确识别与渲染卡片；
- 字段名称使用中文全角【】包裹，字段内容用中文冒号“：”分隔；
- 图片请只提供图片的 URL 地址（以 http 开头），不要使用 Markdown 格式
- 每道菜输出完毕后，请添加一行分隔标记：`---END_OF_DISH---`（单独占一行）。不要漏掉。

"""


# 构建RAG Chain，兼容内存参数

from langchain_core.runnables import RunnablePassthrough

def get_rag_chain(user_id: str):
    """
    (最终修复版) 构建一个完整的、支持端到端流式处理的RAG Agent链。
    """
    try:
        dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
        if not dashscope_api_key:
            raise ValueError("缺少 DASHSCOPE_API_KEY，请在 .env 中配置")

        # 1. 初始化模型与工具 (保持不变)
        model = ChatTongyi(
            streaming=True,
            dashscope_api_key=dashscope_api_key,
            model_name="qwen-max"
        )
        tools = COOKING_TOOLS
        
        # 2. Prompt 模板 (保持不变)
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        # 3. 创建 Agent (保持不变)
        agent = create_tool_calling_agent(model, tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )

        # 4. ✅ 关键修复：构建一个端到端的流式链条
        retriever = get_vectorstore().as_retriever(search_kwargs={"k": 4})

        # 创建一个新的链，它会自动处理RAG检索和Agent调用
        rag_agent_chain = (
            RunnablePassthrough.assign(
                # 第一步：并行执行，将检索到的文档内容赋值给 context
                context=lambda x: "\n".join(
                    doc.page_content for doc in retriever.get_relevant_documents(x["input"])
                )
            )
            | executor # 第二步：将包含context的结果直接传入Agent Executor
        )

        # 5. ✅ 将新的流式链条封装到带记忆的Runnable中
        return RunnableWithMessageHistory(
            rag_agent_chain, # 使用我们新创建的、完全支持流式的链
            lambda session_id: get_user_message_history(user_id),
            input_messages_key="input",
            history_messages_key="chat_history"
        )

    except Exception as e:
        logger.error(f"RAG 链初始化失败: {e}")
        return RunnableLambda(lambda _: {"output": f"系统初始化异常: {e}"})


def simple_query(question: str) -> str:
    """无需RAG上下文，直接调用Chain返回文本"""
    chain = get_rag_chain()
    result = chain.invoke(question)
    return result.get("output", "未获得有效回答")

# 对外暴露接口
get_rag_chain_with_tools = get_rag_chain
get_rag_chain = get_rag_chain
