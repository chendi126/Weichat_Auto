"""GitHub 热门项目文章生成模块"""
import logging
import re
from datetime import datetime
from typing import List, Dict, Any
from openai import OpenAI
from src.config import get_config
from src.github_trending import get_github_raw_data

logger = logging.getLogger(__name__)

# 系统提示词
SYSTEM_PROMPT = """你是一个专业的科技编辑，擅长介绍开源项目和编程技术。

【核心原则】
1. 只使用提供的JSON数据中的信息，不要添加任何数据中没有的内容
2. 绝对不要编造项目描述、功能或star数量
3. 如果数据中没有某项信息，明确说明"数据未提供"而不是猜测
4. 项目名称、描述、star数必须与JSON数据完全一致

文章风格要求：
1. 专业而不晦涩，生动而不浮夸
2. 重点介绍项目的功能、特点和适用场景（基于JSON数据）
3. 让读者快速了解这些项目的价值
4. 直接生成微信公众号兼容的HTML格式，只需纯HTML结构，不需要设置颜色
5. 项目名称要准确，不要编造"""


def write_github_article(project_list: List[Dict[str, Any]]) -> Dict[str, str]:
    """使用 DeepSeek 生成 GitHub 热门项目文章"""
    config = get_config()

    # 获取原始JSON数据
    raw_data = get_github_raw_data()

    # 提取URL映射
    project_urls = {}
    if raw_data:
        import json
        try:
            projects = json.loads(raw_data)
            for p in projects:
                name = p.get("name", "")
                url = p.get("url", "")
                if name and url:
                    # 只保留项目名称部分（owner/name -> name）
                    short_name = name.split("/")[-1] if "/" in name else name
                    project_urls[short_name] = url
        except:
            pass

    if not raw_data:
        logger.warning("未获取到GitHub数据，使用备用数据")
        raw_data = str(project_list[:10])

    current_date = datetime.now().strftime("%Y年%m月%d日")

    # 用户提示词 - 直接传原始JSON给DeepSeek处理
    user_prompt = f"""以下是上周 GitHub 热门项目的真实JSON数据，请严格按照数据内容生成文章。

【重要规则】
- 只能使用JSON数据中提供的信息，不要添加任何数据中没有的内容
- 不要编造项目的功能描述，必须基于数据中的信息
- star数量、fork数、描述等必须与数据完全一致
- 如果数据中缺少某些信息，直接写"信息未提供"

开头写这样一句话："你好！这是上周GitHub的热门项目，来看看世界发生了什么变化。"
不要添加"当然可以，以下是..."的报头，也不要在结尾写任何额外帮助的话语。
生成微信公众号兼容的纯HTML格式，不需要设置任何颜色样式，只需要HTML标签结构。

JSON数据：
{raw_data}

当前日期：{current_date}"""

    # 调用 DeepSeek
    client = OpenAI(
        api_key=config["deepseek"]["api_key"],
        base_url="https://api.deepseek.com"
    )

    response = client.chat.completions.create(
        model=config["deepseek"]["model"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=8000
    )

    content = response.choices[0].message.content or ""

    # 清理思考内容和AI指令残留
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

    # 提取标题 - 找#开头的行
    lines = content.strip().split('\n')
    title = None
    body_start_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            title = line.strip().lstrip('#').strip()
            body_start_idx = i + 1
            break

    # 没找到标题就用默认
    if not title:
        title = "GitHub 热门项目"

    # 提取正文
    body = '\n'.join(lines[body_start_idx:]) if body_start_idx > 0 else content

    # 使用 DeepSeek 生成7字总结
    summary = generate_summary(title, body)

    # 转换为 HTML
    html = generate_github_html(title, body, summary, project_urls)

    logger.info(f"GitHub 文章生成完成: {title}")

    return {
        "title": title,
        "content": html
    }


def generate_summary(title: str, content: str) -> str:
    """使用 DeepSeek 生成7字项目总结"""
    config = get_config()

    try:
        client = OpenAI(
            api_key=config["deepseek"]["api_key"],
            base_url="https://api.deepseek.com"
        )

        response = client.chat.completions.create(
            model=config["deepseek"]["model"],
            messages=[
                {"role": "system", "content": """你是一个微信公众号标题专家。请根据项目内容生成一个吸引眼球的7字以内的标题总结。

【要求】
1. 标题要简洁有力，能引发好奇
2. 不要车轱辘话，要具体
3. 不要正确的废话，要新颖的角度
4. 只需返回标题，不要任何解释""" },
                {"role": "user", "content": f"项目内容：{content[:800]}..."}
            ],
            temperature=0.3,
            max_tokens=50
        )

        summary = response.choices[0].message.content.strip()
        return summary[:7]

    except Exception as e:
        logger.warning(f"生成总结失败: {e}")
        return "开源项目精选"


def generate_github_html(title: str, content: str, summary: str = "开源项目精选", project_urls: dict = None) -> str:
    """生成 GitHub 文章 HTML - 标准公众号排版"""

    # 检查是否已经是HTML格式
    if content.strip().startswith('<'):
        # AI已经生成了HTML，清理并添加基本布局
        html_content = content

        # 移除所有原有的颜色样式
        html_content = re.sub(r'\s+color="[^"]*"', '', html_content)
        html_content = re.sub(r"\s+color='[^']*'", '', html_content)

        # 移除行内style属性中的颜色
        html_content = re.sub(r'style="[^"]*color[^"]*"', '', html_content)

        # 清理空的style属性
        html_content = re.sub(r'style=""', '', html_content)

        # 按公众号规范设置排版
        html_content = re.sub(r'<h2([^>]*)>', r'<h2\1 style="font-size: 22px; font-weight: bold; margin-top: 24px; margin-bottom: 12px;">', html_content)
        html_content = re.sub(r'<h3([^>]*)>', r'<h3\1 style="font-size: 18px; font-weight: bold; margin-top: 20px; margin-bottom: 10px;">', html_content)
        html_content = re.sub(r'<p([^>]*)>', r'<p\1 style="font-size: 15px; line-height: 1.75; margin-bottom: 16px; text-align: justify;">', html_content)

        # 修复AI生成的错误链接格式并添加GitHub链接
        if project_urls:
            for project_name, url in project_urls.items():
                pattern = rf'{re.escape(project_name)}"\s*target="_blank">([^<]+)'
                replacement = f'<a href="{url}" target="_blank" style="color: #0079d3;">\\1</a>'
                html_content = re.sub(pattern, replacement, html_content)

                simple_pattern = rf'({re.escape(project_name)})'
                simple_replacement = f'<a href="{url}" target="_blank" style="color: #0079d3;">\\1</a>'
                html_content = re.sub(simple_pattern, simple_replacement, html_content)
    else:
        # 还是Markdown，转换为HTML
        html_content = markdown_to_html_github(content, project_urls)

    # 提取正文前100字作为微信简介（纯文本，去除HTML标签）
    intro_text = re.sub(r'<[^>]+>', '', content)[:100]

    # 标准公众号排版
    html = f"""
<!-- 微信简介 -->
<p style="display:none;">{intro_text}</p>

<section style="padding: 20px 15px; max-width: 100%; margin: 0 auto;">
    <h1 style="text-align: center; font-size: 22px; font-weight: bold; color: #333333; margin-bottom: 8px;">{title}</h1>

    <p style="text-align: center; color: #666666; font-size: 14px; margin-bottom: 20px;">{datetime.now().strftime('%Y.%m.%d')}　｜　{summary}</p>

    <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 15px 0;">

    <div style="padding: 0 5px;">
    {html_content}
    </div>

    <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 20px 0;">
</section>
"""
    return html


def markdown_to_html_github(markdown_text: str, project_urls: dict = None) -> str:
    """Markdown 到 HTML 转换 - 标准公众号排版"""
    html = markdown_text

    # 标题 - 按公众号规范
    html = re.sub(r'^### (.+)$', r'<h3 style="font-size: 18px; font-weight: bold; color: #333333; margin-top: 24px; margin-bottom: 12px;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2 style="font-size: 22px; font-weight: bold; color: #333333; margin-top: 28px; margin-bottom: 14px;">\1</h2>', html, flags=re.MULTILINE)

    # 段落 - 15px字号，行高1.75，两端对齐
    html = re.sub(r'\n\n+', '</p><p style="font-size: 15px; line-height: 1.75; margin-bottom: 16px; text-align: justify; color: #333333;">', html)

    # 加粗
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color: #333333;">\1</strong>', html)

    # 列表 - 15px字号，两端对齐
    html = re.sub(r'^- (.+)$', r'<p style="font-size: 15px; line-height: 1.75; margin-bottom: 16px; text-align: justify; color: #333333;">　🔹　\1</p>', html, flags=re.MULTILINE)

    # 检测GitHub链接并为项目名称添加跳转
    if project_urls:
        for project_name, url in project_urls.items():
            pattern = rf'(<p style="[^>]*>　🔹　)({re.escape(project_name)})'
            replacement = rf'\1<a href="{url}" target="_blank" style="color: #0079d3;">\2</a>'
            html = re.sub(pattern, replacement, html)

    # 换行
    html = html.replace('\n', '<br>')

    return f'<p style="font-size: 15px; line-height: 1.75; margin-bottom: 16px; text-align: justify; color: #333333;">{html}</p>'
