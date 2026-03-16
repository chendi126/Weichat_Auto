"""文章生成模块"""
import logging
import re
from datetime import datetime
from typing import List, Dict, Any
from jinja2 import Template
from openai import OpenAI
from src.config import get_config

logger = logging.getLogger(__name__)

# 系统提示词
SYSTEM_PROMPT = """你是一个专业的科技新闻编辑，擅长编写100%基于真实素材的科技新闻文章。

【核心原则 - 必须严格遵守】
1. 【最重要】只使用提供的新闻素材中的信息，素材中没有的信息绝对不能添加
2. 【最重要】绝对禁止编造任何新闻内容、数据、事实、数字、日期
3. 如果素材中没有某项信息，必须明确写"信息未提供"
4. 禁止使用"据知情人士透露"、"业内人士表示"等未在素材中提及的内容
5. 当前日期：{{ current_date }}

【可信度要求】
- 每句话都必须有素材依据
- 没有素材的内容绝对不能写
- 保持新闻的客观性和准确性"""

# 用户提示词模板
USER_TEMPLATE = """请根据以下新闻素材，编写一篇100%基于真实素材的科技新闻文章。

【可信度要求 - 必须严格遵守】
【警告】以下规则必须100%遵守，否则文章将被拒绝：
1. 只能使用素材中提供的信息，素材中没有的内容绝对不能添加
2. 绝对禁止编造：数据、事实、数字、日期、机构名称、人物言论
3. star数量、发布时间、发布机构等必须与素材完全一致
4. 如果素材中缺少信息，明确写"信息未提供"
5. 不要添加素材中没有的背景知识或分析

【格式要求】
1. 第一行是文章标题（以 # 开头）
2. 使用 Markdown 格式
3. 文章长度：1000-2000字
4. 当前日期：{{ current_date }}

请根据以下素材写文章，主题：{{ topic }}

【素材】
{{ news_content }}

【重要】素材中的信息可以省略、简化，但绝对不能添加素材中没有的内容！"""


def write_article(news_list: List[Dict[str, Any]], topic: str = "AI科技新闻") -> Dict[str, str]:
    """使用 MiniMax 生成文章

    Args:
        news_list: 新闻列表
        topic: 文章主题
    """
    config = get_config()
    current_date = datetime.now().strftime("%Y年%m月%d日")

    # 准备新闻内容
    news_text = ""
    for i, news in enumerate(news_list[:10], 1):
        news_text += f"{i}. {news.get('title', '')}\n"
        news_text += f"   摘要: {news.get('summary', '')}\n"
        news_text += f"   来源: {news.get('source', '')}\n"
        news_text += f"   时间: {news.get('time', '')}\n\n"

    # 渲染提示词，传入当前日期
    system_prompt = Template(SYSTEM_PROMPT).render(current_date=current_date)
    user_prompt = Template(USER_TEMPLATE).render(
        news_content=news_text,
        topic=topic,
        current_date=current_date
    )

    # 调用 MiniMax
    mm_config = config.get("minimax", {})
    client = OpenAI(
        api_key=mm_config.get("api_key", ""),
        base_url=mm_config.get("base_url", "https://api.minimax.chat/v1")
    )

    response = client.chat.completions.create(
        model=mm_config.get("model", "abab6.5s-chat"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=8000
    )

    content = response.choices[0].message.content or ""

    # 提取标题和正文
    lines = content.strip().split('\n')
    title = lines[0].replace('#', '').replace('**', '').strip() if lines else "今日科技新闻"
    body = '\n'.join(lines[1:]) if len(lines) > 1 else content

    # 使用 MiniMax 生成7字总结
    summary = generate_summary(title, body)

    # 转换为星际风格 HTML
    html = generate_interstellar_html(title, body, summary)

    logger.info(f"文章生成完成: {title}")

    return {
        "title": title,
        "content": html
    }


def generate_summary(title: str, content: str) -> str:
    """使用 DeepSeek 生成7字文章总结"""
    config = get_config()

    try:
        client = OpenAI(
            api_key=config["deepseek"]["api_key"],
            base_url="https://api.deepseek.com"
        )

        response = client.chat.completions.create(
            model=config["deepseek"]["model"],
            messages=[
                {"role": "system", "content": """你是一个微信公众号标题专家。请根据文章内容生成一个吸引眼球的7字以内的标题总结。

【要求】
1. 标题要简洁有力，能引发好奇
2. 不要车轱辘话，要具体
3. 不要正确的废话，要新颖的角度
4. 只需返回标题，不要任何解释""" },
                {"role": "user", "content": f"文章内容：{content[:800]}..."}
            ],
            temperature=0.3,
            max_tokens=50
        )

        summary = response.choices[0].message.content.strip()
        return summary[:7]  # 限制7字

    except Exception as e:
        logger.warning(f"生成总结失败: {e}")
        return "AI科技前沿"


def generate_interstellar_html(title: str, content: str, summary: str = "AI科技前沿") -> str:
    """生成微信公众号兼容的深色风格 HTML（黑色背景）"""

    # 转换 Markdown 到 HTML（深色模式）
    html_content = markdown_to_html_dark(content)

    # 提取正文前100字作为微信简介（纯文本，去除HTML标签）
    intro_text = re.sub(r'<[^>]+>', '', content)[:100]

    # 使用 section 标签配合内联样式（微信公众号兼容方案）
    html = f"""<!-- 微信简介 -->
<p style="display:none;">{intro_text}</p>

<section style="background-color: #000000; padding: 30px 20px; max-width: 100%; margin: 0 auto;">
    <p style="text-align: center; color: #f48529; font-size: 12px; letter-spacing: 4px; margin-bottom: 30px;">✦ 银 河 快 报 ✦</p>

    <h1 style="text-align: center; font-size: 22px; font-weight: bold; color: #f48529; margin-bottom: 20px; letter-spacing: 2px;">{title}</h1>

    <p style="text-align: center; color: #888888; font-size: 12px; margin-bottom: 30px;">{datetime.now().strftime('%Y.%m.%d')}　｜　{summary}</p>

    <hr style="border: none; border-top: 1px solid #333333; margin: 20px 0;">

    <div style="padding: 0 10px;">
    {html_content}
    </div>

    <hr style="border: none; border-top: 1px solid #333333; margin: 30px 0;">

    <p style="text-align: center; color: #f48529; font-size: 12px;">✦ 感谢阅读 ✦</p>
</section>
"""
    return html


def markdown_to_html_dark(markdown_text: str) -> str:
    """微信公众号深色模式的 Markdown 到 HTML 转换"""
    html = markdown_text

    # 标题 - 橙色，标题间距
    html = re.sub(r'^### (.+)$', r'<h3 style="font-size: 18px; font-weight: bold; color: #f48529; margin-top: 30px; margin-bottom: 16px;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2 style="font-size: 20px; font-weight: bold; color: #f48529; margin-top: 30px; margin-bottom: 16px;">\1</h2>', html, flags=re.MULTILINE)

    # 段落 - 奶油色文字，段落间距
    html = re.sub(r'\n\n+', '</p><p style="color: #f0e6d3; line-height: 1.8; margin-bottom: 16px;">', html)

    # 加粗 - 橙色强调
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color: #f48529;">\1</strong>', html)

    # 列表 - 奶油色，列表项间距
    html = re.sub(r'^- (.+)$', r'<p style="color: #f0e6d3; line-height: 1.8; margin-bottom: 16px;">　🔹　\1</p>', html, flags=re.MULTILINE)

    # 换行
    html = html.replace('\n', '<br>')

    return f'<p style="color: #f0e6d3; line-height: 1.8; margin-bottom: 16px;">{html}</p>'


def write_article_from_tavily(tavily_results: List[Dict[str, Any]], keyword: str) -> Dict[str, str]:
    """使用Tavily搜索结果生成文章"""
    if not tavily_results:
        return {}

    # 准备Tavily搜索内容
    news_text = ""
    for i, news in enumerate(tavily_results[:8], 1):
        title = news.get("title", "")
        content = news.get("content", "")
        url = news.get("url", "")
        news_text += f"{i}. {title}\n"
        news_text += f"   内容: {content}\n"
        if url:
            news_text += f"   来源: {url}\n"
        news_text += "\n"

    # 使用 MiniMax 生成文章
    config = get_config()
    current_date = datetime.now().strftime("%Y年%m月%d日")

    # 使用模板
    system_prompt = Template(SYSTEM_PROMPT).render(current_date=current_date)
    user_prompt = Template(USER_TEMPLATE).render(
        news_content=news_text,
        topic=keyword,
        current_date=current_date
    )

    try:
        # 使用 DeepSeek 生成文章
        ds_config = config.get("deepseek", {})
        client = OpenAI(
            api_key=ds_config.get("api_key", ""),
            base_url=ds_config.get("base_url", "https://api.deepseek.com")
        )

        response = client.chat.completions.create(
            model=ds_config.get("model", "deepseek-chat"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=8000
        )

        content = response.choices[0].message.content or ""

        # 清理思考内容和AI指令残留
        import re

        # 移除各种AI思考/指令残留
        content = re.sub(r'用户要求我.*?\n', '', content)
        content = re.sub(r'让我先.*?\n', '', content)
        content = re.sub(r'现在需要.*?\n', '', content)
        content = re.sub(r'我将按照.*?\n', '', content)
        content = re.sub(r'根据提供的.*?\n', '', content)
        content = re.sub(r'这是一篇.*?\n', '', content)
        content = re.sub(r'以下是.*?\n', '', content)
        content = re.sub(r'^# .*\n', '', content, flags=re.MULTILINE)

        lines = content.split('\n')
        clean_lines = []
        skip = False
        for line in lines:
            if re.match(r'^(思考|think|分析|分析过程|用户要求|让我先|现在需要|我将按照|根据提供|这是一篇|以下是)[：:]', line, re.IGNORECASE):
                skip = True
                continue
            if skip:
                if line.strip() == '' or not re.match(r'^[\s\d\-\*•#]', line):
                    skip = False
                else:
                    continue
            clean_lines.append(line)
        content = '\n'.join(clean_lines)

        # 提取标题和正文
        lines = content.strip().split('\n')

        # 找标题（#开头的行）
        title = None
        body_start_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                title = line.strip().lstrip('#').strip()
                body_start_idx = i + 1
                break

        # 没找到标题就用keyword
        if not title:
            title = keyword
            body_start_idx = 0

        # 提取正文
        body = '\n'.join(lines[body_start_idx:]) if body_start_idx > 0 else content

        # 使用 DeepSeek 生成7字总结
        summary = generate_summary(title, body)

        # 转换为 HTML
        html = generate_interstellar_html(title, body, summary)

        logger.info(f"Tavily文章生成完成: {title}")

        return {
            "title": title,
            "html": html
        }
    except Exception as e:
        logger.error(f"Tavily文章生成失败: {e}")
        return {}

