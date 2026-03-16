# 独立版 AI 科技新闻自动发布工作流 - 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建一个完全脱离 Coze 的 Python 版本，实现每天自动搜索 AI 科技新闻、用 Kimi 写文章并发布到微信公众号。

**Architecture:** 使用 Python 原生方式，通过 APScheduler 实现定时任务，Kimi API 生成文章，直接调用微信 API 发布文章。

**Tech Stack:** Python 3.8+, openai, requests, APScheduler, PyYAML

---

### Task 1: 创建配置文件

**Files:**
- Create: `config.yaml`

**Step 1: 创建 config.yaml**

```yaml
# 微信公众号配置
wechat:
  app_id: "你的AppID"
  app_secret: "你的AppSecret"
  cover_image: "背景.png"

# 定时任务配置
scheduler:
  enabled: true
  hour: 8
  minute: 0
```

**Step 2: 提交**

```bash
git add config.yaml
git commit -m "feat: 添加配置文件 config.yaml"
```

---

### Task 2: 创建 requirements.txt

**Files:**
- Create: `requirements.txt`

**Step 1: 创建 requirements.txt**

```txt
openai>=1.0.0
requests>=2.28.0
PyYAML>=6.0
APScheduler>=3.10.0
```

**Step 2: 提交**

```bash
git add requirements.txt
git commit -m "feat: 添加项目依赖"
```

---

### Task 3: 创建 src/__init__.py

**Files:**
- Create: `src/__init__.py`

**Step 1: 创建空文件**

```python
# AI 科技新闻自动发布工具
```

**Step 2: 提交**

```bash
git add src/__init__.py
git commit -m "feat: 创建 src 模块"
```

---

### Task 4: 创建配置读取模块

**Files:**
- Create: `src/config.py`

**Step 1: 创建 src/config.py**

```python
"""配置管理模块"""
import os
import yaml
from pathlib import Path

_config = None

def get_config() -> dict:
    """获取配置"""
    global _config
    if _config is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config
```

**Step 2: 提交**

```bash
git add src/config.py
git commit -m "feat: 添加配置读取模块"
```

---

### Task 5: 创建新闻搜索模块

**Files:**
- Create: `src/news_searcher.py`

**Step 1: 创建 src/news_searcher.py**

```python
"""新闻搜索模块"""
import logging
from typing import List, Dict, Any
from openai import OpenAI
from src.config import get_config

logger = logging.getLogger(__name__)


def search_news() -> List[Dict[str, Any]]:
    """搜索 AI 和科技新闻"""
    config = get_config()

    # 使用 Kimi 搜索新闻
    client = OpenAI(
        api_key=config["kimi"]["api_key"],
        base_url="https://api.moonshot.cn/v1"
    )

    prompt = """请搜索今天最新的 AI 和科技行业新闻，返回 10 条最重要的新闻。
每条新闻请包含以下信息：
1. 标题
2. 简要摘要（50字以内）
3. 来源网站
4. 发布时间

请用 JSON 格式返回，格式如下：
[{"title": "标题", "summary": "摘要", "source": "来源", "time": "时间"}, ...]"""

    response = client.chat.completions.create(
        model=config["kimi"]["model"],
        messages=[
            {"role": "system", "content": "你是一个科技新闻助手，帮助用户搜索最新的科技新闻。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )

    content = response.choices[0].message.content

    # 解析 JSON
    import json
    import re

    # 尝试提取 JSON 部分
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        try:
            news_list = json.loads(match.group())
            logger.info(f"搜索到 {len(news_list)} 条新闻")
            return news_list
        except json.JSONDecodeError:
            pass

    # 如果解析失败，返回空列表
    logger.warning("新闻解析失败")
    return []
```

**Step 2: 提交**

```bash
git add src/news_searcher.py
git commit -m "feat: 添加新闻搜索模块"
```

---

### Task 6: 创建文章生成模块

**Files:**
- Create: `src/article_writer.py`

**Step 1: 创建 src/article_writer.py**

```python
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
SYSTEM_PROMPT = """你是一个专业的科技新闻编辑，擅长编写高质量的科技新闻文章。
文章风格要求：
1. 专业而不晦涩，生动而不浮夸
2. 使用场景代入、数据震撼等方式开头
3. 深度解析技术趋势和影响
4. 聚焦 GitHub 热门项目、AI 大模型动态、科技圈新闻、鸿蒙发展等
5. 文章需要有一个吸引眼球的标题"""

# 用户提示词模板
USER_TEMPLATE = """请根据以下新闻素材，编写一篇高质量的科技新闻文章。

新闻素材：
{{ news_content }}

要求：
1. 第一行是文章标题（以 # 开头）
2. 内容要有深度见解，不能只是简单罗列新闻
3. 使用 Markdown 格式
4. 文章长度控制在 1500-2500 字"""


def write_article(news_list: List[Dict[str, Any]]) -> Dict[str, str]:
    """使用 Kimi 生成文章"""
    config = get_config()

    # 准备新闻内容
    news_text = ""
    for i, news in enumerate(news_list[:10], 1):
        news_text += f"{i}. {news.get('title', '')}\n"
        news_text += f"   摘要: {news.get('summary', '')}\n"
        news_text += f"   来源: {news.get('source', '')}\n"
        news_text += f"   时间: {news.get('time', '')}\n\n"

    # 渲染提示词
    user_prompt = Template(USER_TEMPLATE).render(news_content=news_text)

    # 调用 Kimi
    client = OpenAI(
        api_key=config["kimi"]["api_key"],
        base_url="https://api.moonshot.cn/v1"
    )

    response = client.chat.completions.create(
        model=config["kimi"]["model"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.6,
        max_tokens=8000
    )

    content = response.choices[0].message.content or ""

    # 提取标题和正文
    lines = content.strip().split('\n')
    title = lines[0].replace('#', '').replace('**', '').strip() if lines else "今日科技新闻"
    body = '\n'.join(lines[1:]) if len(lines) > 1 else content

    # 转换为星际风格 HTML
    html = generate_interstellar_html(title, body)

    logger.info(f"文章生成完成: {title}")

    return {
        "title": title,
        "content": html
    }


def generate_interstellar_html(title: str, content: str) -> str:
    """生成星际风格的文章 HTML"""

    # 转换 Markdown 到 HTML
    html_content = markdown_to_html(content)

    # 生成星星装饰
    stars_html = generate_stars()

    html = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%);
            color: #f0e6d3;
            padding: 60px 40px;
            max-width: 800px;
            margin: 0 auto;
            position: relative;
            overflow: hidden;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);">

    {stars_html}

    <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px;
                background: linear-gradient(90deg, transparent, #ffd700, #ff8c00, transparent); opacity: 0.8;"></div>
    <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
                background: linear-gradient(90deg, transparent, #ff6b6b, #ffd700, transparent); opacity: 0.8;"></div>

    <div style="position: relative; z-index: 2;">
        <div style="font-size: 12px; letter-spacing: 8px; color: #ffd700; opacity: 0.6;
                    margin-bottom: 20px; text-transform: uppercase;">
            ◆ Spaceman的Ai圈子 ◆
        </div>

        <h1 style="font-size: 42px; font-weight: 300; margin: 0 0 30px 0; line-height: 1.3;
                   background: linear-gradient(135deg, #ffd700 0%, #ff8c00 50%, #ff6b6b 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   background-clip: text; letter-spacing: 2px;">
            {title}
        </h1>

        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 50px; opacity: 0.7;">
            <div style="height: 1px; width: 80px; background: linear-gradient(90deg, #ffd700, transparent);"></div>
            <div style="font-size: 13px; letter-spacing: 3px; color: #ffd700;">
                {datetime.now().strftime('%Y.%m.%d')}
            </div>
            <div style="height: 1px; width: 80px; background: linear-gradient(90deg, transparent, #ffd700);"></div>
        </div>
    </div>

    <div style="position: relative; z-index: 2; font-size: 18px; line-height: 2;">
        {html_content}
    </div>

    <div style="margin-top: 60px; padding-top: 40px; border-top: 1px solid rgba(255, 215, 0, 0.2);
                display: flex; justify-content: space-between; align-items: center;
                font-size: 12px; color: #ffd700; opacity: 0.5; letter-spacing: 2px;">
        <span>◆ 感谢阅读 ◆</span>
        <span>●●●</span>
    </div>
</div>
"""
    return html


def markdown_to_html(markdown_text: str) -> str:
    """简单的 Markdown 到 HTML 转换"""
    html = markdown_text

    # 标题
    html = re.sub(r'^### (.+)$', r'<h3 style="font-size: 24px; font-weight: 400; margin: 40px 0 20px 0; color: #ffd700;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2 style="font-size: 28px; font-weight: 400; margin: 50px 0 25px 0; color: #ff8c00;">\1</h2>', html, flags=re.MULTILINE)

    # 段落
    html = re.sub(r'\n\n+', '</p><p style="margin: 25px 0; text-align: justify;">', html)

    # 加粗
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color: #ffd700; font-weight: 500;">\1</strong>', html)

    # 列表
    html = re.sub(r'^- (.+)$', r'<li style="margin: 15px 0 15px 30px; list-style: none;"><span style="color: #ffd700;">◆</span> \1</li>', html, flags=re.MULTILINE)

    return f'<p style="margin: 25px 0; text-align: justify;">{html}</p>'


def generate_stars() -> str:
    """生成星星装饰 HTML"""
    positions = [
        (10, 8, 2), (25, 15, 3), (80, 5, 2), (90, 12, 3),
        (5, 20, 2), (95, 25, 2), (15, 30, 3), (85, 35, 2),
        (8, 45, 2), (92, 50, 3), (20, 60, 2), (80, 65, 2),
        (12, 75, 3), (88, 80, 2), (7, 85, 2), (93, 90, 3),
        (18, 92, 2), (82, 95, 2), (30, 10, 2), (70, 15, 3)
    ]

    stars = ""
    for x, y, size in positions:
        opacity = 0.3 + (size * 0.2)
        stars += f'<div style="position: absolute; left: {x}%; top: {y}%; width: {size}px; height: {size}px; background: #ffd700; border-radius: 50%; opacity: {opacity}; box-shadow: 0 0 {size*3}px #ffd700;"></div>'

    return stars
```

**Step 2: 提交**

```bash
git add src/article_writer.py
git commit -m "feat: 添加文章生成模块"
```

---

### Task 7: 创建微信公众号发布模块

**Files:**
- Create: `src/wechat_publisher.py`

**Step 1: 创建 src/wechat_publisher.py**

```python
"""微信公众号发布模块"""
import logging
import time
import requests
from pathlib import Path
from src.config import get_config

logger = logging.getLogger(__name__)


class WeChatPublisher:
    """微信公众号发布器"""

    def __init__(self):
        config = get_config()
        self.app_id = config["wechat"]["app_id"]
        self.app_secret = config["wechat"]["app_secret"]
        self.cover_image = config["wechat"].get("cover_image", "背景.png")
        self.access_token = None
        self._token_expires_at = 0

    def _get_access_token(self) -> str:
        """获取 access_token"""
        if self.access_token and time.time() < self._token_expires_at - 300:
            return self.access_token

        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }

        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if "errcode" in data and data["errcode"] != 0:
            raise Exception(f"获取 access_token 失败: {data.get('errmsg')}")

        self.access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 7200)
        return self.access_token

    def _prepare_image(self, image_path: str):
        """准备图片文件"""
        import base64

        path = Path(image_path)
        if not path.exists():
            # 尝试相对路径
            path = Path(__file__).parent.parent / image_path

        if path.exists():
            with open(path, "rb") as f:
                return {"media": ("cover.jpg", f.read())}

        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    def upload_image(self, image_path: str = None) -> str:
        """上传图片素材"""
        if image_path is None:
            image_path = self.cover_image

        token = self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"

        files = self._prepare_image(image_path)

        resp = requests.post(url, files=files, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("errcode", 0) != 0:
            raise Exception(f"上传图片失败: {data}")

        return data.get("media_id")

    def add_draft(self, title: str, content: str, thumb_media_id: str) -> str:
        """新增草稿"""
        token = self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

        article = {
            "title": title,
            "content": content,
            "thumb_media_id": thumb_media_id,
            "author": "AI科技助手",
            "digest": content[:100] if content else "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }

        import json
        json_data = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")

        resp = requests.post(url, data=json_data, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("errcode", 0) != 0:
            raise Exception(f"新增草稿失败: {data}")

        return data.get("media_id")

    def publish_draft(self, media_id: str) -> str:
        """发布草稿"""
        token = self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}"

        resp = requests.post(url, json={"media_id": media_id}, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("errcode", 0) != 0:
            raise Exception(f"发布草稿失败: {data}")

        return data.get("publish_id")

    def publish(self, title: str, content: str, image_path: str = None) -> dict:
        """发布文章"""
        logger.info(f"开始发布文章: {title}")

        # 上传封面图
        thumb_media_id = self.upload_image(image_path)

        # 新增草稿
        draft_id = self.add_draft(title, content, thumb_media_id)

        # 发布草稿
        publish_id = self.publish_draft(draft_id)

        logger.info(f"文章发布成功: {title}, publish_id: {publish_id}")

        return {
            "success": True,
            "draft_id": draft_id,
            "publish_id": publish_id,
            "message": "文章已成功发布到微信公众号"
        }


def publish_article(title: str, content: str) -> dict:
    """发布文章到微信公众号"""
    publisher = WeChatPublisher()
    return publisher.publish(title, content)
```

**Step 2: 提交**

```bash
git add src/wechat_publisher.py
git commit -m "feat: 添加微信公众号发布模块"
```

---

### Task 8: 创建定时任务模块

**Files:**
- Create: `src/scheduler.py`

**Step 1: 创建 src/scheduler.py**

```python
"""定时任务模块"""
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.config import get_config
from src.news_searcher import search_news
from src.article_writer import write_article
from src.wechat_publisher import publish_article

logger = logging.getLogger(__name__)


def run_workflow():
    """执行完整工作流"""
    logger.info("=" * 50)
    logger.info("开始执行工作流")

    try:
        # 1. 搜索新闻
        logger.info("步骤 1: 搜索新闻...")
        news_list = search_news()
        if not news_list:
            logger.warning("未搜索到新闻，跳过本次发布")
            return

        # 2. 生成文章
        logger.info("步骤 2: 生成文章...")
        article = write_article(news_list)

        # 3. 发布到公众号
        logger.info("步骤 3: 发布到公众号...")
        result = publish_article(article["title"], article["content"])

        logger.info(f"工作流执行完成: {result}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"工作流执行失败: {e}", exc_info=True)


def start_scheduler():
    """启动定时任务"""
    config = get_config()
    scheduler_config = config.get("scheduler", {})

    if not scheduler_config.get("enabled", False):
        logger.info("定时任务未启用")
        return

    scheduler = BlockingScheduler()

    # 每天指定时间执行
    trigger = CronTrigger(
        hour=scheduler_config.get("hour", 8),
        minute=scheduler_config.get("minute", 0)
    )

    scheduler.add_job(run_workflow, trigger, name="daily_news_publish")

    logger.info(f"定时任务已启动，每天 {scheduler_config.get('hour')}:{scheduler_config.get('minute'):02d} 执行")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("定时任务已停止")
```

**Step 2: 提交**

```bash
git add src/scheduler.py
git commit -m "feat: 添加定时任务模块"
```

---

### Task 9: 创建入口文件

**Files:**
- Create: `src/main.py`

**Step 1: 创建 src/main.py`

```python
"""AI 科技新闻自动发布 - 主入口"""
import argparse
import logging
import sys
from src.config import get_config
from src.scheduler import start_scheduler, run_workflow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="AI 科技新闻自动发布工具")
    parser.add_argument("--now", action="store_true", help="立即执行一次")
    parser.add_argument("--daemon", action="store_true", help="以守护进程模式运行（定时执行）")

    args = parser.parse_args()

    if args.now:
        # 立即执行
        logger.info("手动执行模式")
        run_workflow()
    elif args.daemon:
        # 定时执行
        logger.info("守护进程模式")
        start_scheduler()
    else:
        # 默认显示帮助
        parser.print_help()


if __name__ == "__main__":
    main()
```

**Step 2: 提交**

```bash
git add src/main.py
git commit -m "feat: 添加主入口文件"
```

---

### Task 10: 创建运行脚本

**Files:**
- Create: `run.sh`

**Step 1: 创建 run.sh**

```bash
#!/bin/bash

# AI 科技新闻自动发布 - 运行脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境（如果有）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 安装依赖（如果需要）
if [ ! -d "node_modules" ] && [ -f "requirements.txt" ]; then
    echo "安装依赖..."
    pip install -r requirements.txt
fi

# 解析参数
MODE=""

while getopts "ndh" opt; do
    case "$opt" in
        n)
            MODE="now"
            ;;
        d)
            MODE="daemon"
            ;;
        h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -n    立即执行一次（手动模式）"
            echo "  -d    以守护进程模式运行（定时执行）"
            echo "  -h    显示帮助"
            echo ""
            echo "示例:"
            echo "  $0 -n          # 手动执行一次"
            echo "  $0 -d          # 启动定时任务"
            exit 0
            ;;
    esac
done

if [ -z "$MODE" ]; then
    echo "请指定运行模式: -n (手动) 或 -d (定时)"
    echo "使用 -h 查看帮助"
    exit 1
fi

# 执行
python src/main.py --$MODE
```

**Step 2: 提交**

```bash
git add run.sh
git commit -m "feat: 添加运行脚本"
```

---

## 实现计划完成

**Plan complete and saved to `docs/plans/2026-03-10-weichatauto-standalone-design.md`.**

### 后续步骤

1. 提交当前代码到 Gitee
2. 你可以在本地测试 `python src/main.py --now`
3. 确认无误后推送到服务器

### 测试命令

```bash
# 本地测试
python src/main.py --now

# 启动定时服务
python src/main.py --daemon
```

**Which approach?**

1. **Subagent-Driven** - 我创建子任务逐步实现并提交
2. **Direct Implementation** - 我直接实现所有文件并一次性提交