"""AI对话模块 - 使用MiniMax API进行智能对话"""
import logging
from openai import OpenAI
from src.config import get_config

logger = logging.getLogger(__name__)


def chat_with_ai(user_message: str, context: str = "") -> str:
    """使用MiniMax API进行智能对话"""
    config = get_config()
    mm_config = config.get("minimax", {})

    api_key = mm_config.get("api_key", "")
    model = mm_config.get("model", "abab6.5s-chat")
    base_url = mm_config.get("base_url", "https://api.minimax.chat/v1")

    if not api_key:
        return "AI配置未找到，请联系管理员"

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        # 构建系统提示
        system_prompt = """你是一个智能助手，名叫"银河快讯"。请遵循以下规则：
1. 用友好、专业的语气回答用户问题
2. 如果用户问的是新闻、科技、股票、投资等问题，可以回答"我帮你搜索一下相关信息"
3. 如果不知道某个具体信息，诚实说明
4. 回答要简洁明了，不要太啰嗦
5. 如果用户需要最新新闻或信息，告诉用户你会帮他搜索

当用户需要搜索新闻时，请回复"好的，我来帮你搜索XX的相关新闻"，其中XX是用户询问的核心关键词。"""

        messages = [{"role": "system", "content": system_prompt}]

        # 添加上下文
        if context:
            messages.append({"role": "assistant", "content": context})

        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        reply = response.choices[0].message.content.strip()
        return reply

    except Exception as e:
        logger.error(f"AI对话失败: {e}")
        return "抱歉，我现在有点忙，请稍后再试"


def chat_with_ai_with_search(user_message: str) -> tuple[str, str]:
    """使用MiniMax API进行对话，自动判断是否需要搜索新闻

    Returns:
        (回复内容, 搜索关键词) - 如果不需要搜索，搜索关键词为空
    """
    config = get_config()
    mm_config = config.get("minimax", {})

    api_key = mm_config.get("api_key", "")
    model = mm_config.get("model", "abab6.5s-chat")
    base_url = mm_config.get("base_url", "https://api.minimax.chat/v1")

    if not api_key:
        return "AI配置未找到，请联系管理员", ""

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        # 构建系统提示，让AI判断是否需要搜索
        system_prompt = """你是一个智能助手。请分析用户的问题，判断是否需要搜索最新新闻或信息。

判断规则：
- 如果用户问的是具体的新闻、事件、动态 → 需要搜索，提取关键词
- 如果用户问的是一般性知识、生活问题 → 不需要搜索
- 如果用户说"帮我找"、"搜索"、"有没有关于" → 需要搜索
- 如果用户问"最新"、"今日新闻" → 需要搜索，关键词"AI"
- 如果用户只是打招呼、闲聊 → 不需要搜索

输出格式：
如果你判断需要搜索，请输出：SEARCH|关键词
如果不需要搜索，请直接回答问题

例如：
用户：帮我找找AI的最新消息
输出：SEARCH|AI

用户：今天天气怎么样
输出：今天我不清楚具体天气情况，建议查看天气预报应用。

用户：你好
输出：你好！有什么我可以帮你的吗？"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=200
        )

        result = response.choices[0].message.content.strip()

        # 判断是否需要搜索
        if result.startswith("SEARCH|"):
            keyword = result.replace("SEARCH|", "").strip()
            logger.info(f"AI判断需要搜索，关键词: {keyword}")
            return "", keyword
        else:
            return result, ""

    except Exception as e:
        logger.error(f"AI对话失败: {e}")
        return "抱歉，我现在有点忙，请稍后再试", ""
