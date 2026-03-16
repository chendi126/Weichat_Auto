"""飞书机器人模块 - 接收用户消息并搜索新闻"""
import logging
import json
import time
import hashlib
import hmac
import base64
from typing import Optional
import requests
from src.config import get_config
from src.news_searcher import search_news
from src.article_writer import write_article, write_article_from_tavily

logger = logging.getLogger(__name__)

# 缓存最后一次生成的文章
_last_article_cache = {}


class FeishuBot:
    """飞书机器人"""

    def __init__(self):
        config = get_config()
        feishu_config = config.get("feishu", {})
        self.app_id = feishu_config.get("app_id", "")
        self.app_secret = feishu_config.get("app_secret", "")
        self.token = None
        self.token_expires = 0

    def get_tenant_access_token(self) -> Optional[str]:
        """获取 tenant_access_token"""
        # 检查 token 是否过期
        if self.token and time.time() < self.token_expires:
            return self.token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        try:
            resp = requests.post(url, json=data, timeout=10)
            result = resp.json()

            if result.get("code") == 0:
                self.token = result.get("tenant_access_token")
                # 提前5分钟过期
                self.token_expires = time.time() + result.get("expire", 7200) - 300
                return self.token
            else:
                logger.error(f"获取token失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取token异常: {e}")
            return None

    def send_message(self, receive_id: str, content: str, msg_type: str = "text") -> bool:
        """发送消息"""
        token = self.get_tenant_access_token()
        if not token:
            return False

        url = "https://open.feishu.cn/open-apis/im/v1/messages"
        params = {
            "receive_id_type": "open_id"
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 根据消息类型构建 content
        if msg_type == "text":
            msg_content = {"text": content}
            content_str = json.dumps(msg_content, ensure_ascii=False)
        elif msg_type == "interactive":
            # interactive 类型直接传字典
            content_str = json.dumps(content, ensure_ascii=False)
        else:
            msg_content = {"text": content}
            content_str = json.dumps(msg_content, ensure_ascii=False)

        data = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": content_str
        }

        try:
            logger.info(f"发送消息 params={params}, data={data}")
            resp = requests.post(url, params=params, headers=headers, json=data, timeout=30)
            logger.info(f"响应状态码: {resp.status_code}")
            result = resp.json()
            logger.info(f"响应内容: {result}")

            if result.get("code") == 0:
                logger.info(f"消息发送成功到 {receive_id}")
                return True
            else:
                logger.error(f"消息发送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return False

    def send_text_message(self, receive_id: str, text: str) -> bool:
        """发送文本消息"""
        return self.send_message(receive_id, text, "text")

    def send_card_message(self, receive_id: str, title: str, content: str) -> bool:
        """发送卡片消息"""
        card = {
            "config": {
                "update_multi": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        }
        return self.send_message(receive_id, card, "interactive")

    def process_message(self, user_message: str, user_id: str) -> str:
        """处理用户消息，返回回复内容"""
        logger.info(f"开始处理消息: {user_message}, user_id: {user_id}")
        user_message = user_message.strip()

        # 帮助指令
        if user_message in ["帮助", "help", "?", "？"]:
            return """🤖 银河快讯机器人

使用方法：
• 输入关键词搜索新闻，如：AI新闻、科技动态
• 输入"最新"获取今日AI新闻
• 输入"GitHub"获取热门开源项目
• 输入"发布+关键词"搜索并发布到公众号草稿箱
• 直接问我问题，我会帮你搜索并回答

示例：发布 AI新闻"""

        # 发布到公众号草稿箱
        if user_message.startswith("发布") or "发布到公众号" in user_message or user_message == "发布":
            # 检查是否有缓存的文章
            cached = _last_article_cache.get(user_id)

            # 如果说"发布"或"发布到公众号"且有缓存，直接发布刚才的文章
            if (user_message in ["发布", "发布到公众号"] or user_message == "发布") and cached:
                return self.publish_cached_article(cached, user_id)

            # 否则提取关键词搜索
            keyword = user_message.replace("发布", "").replace("到公众号", "").replace("公众号", "").strip()
            if keyword:
                return self.publish_to_wechat(keyword, user_id)
            else:
                self.send_text_message(user_id, "请输入要发布的关键词，如：发布 AI新闻")
                return "需要关键词"

        # 最新新闻
        if user_message in ["最新", "今日新闻", "新闻"]:
            return self.get_latest_news(user_id)

        # GitHub 热门
        if user_message in ["GitHub", "github", "开源", "热门项目"]:
            return self.get_github_trending(user_id)

        # 简化处理：直接用用户消息作为关键词搜索
        try:
            from src.tavily_search import search_with_tavily, format_tavily_results

            # 清理关键词，去掉"搜索"、"帮我找"等词
            import re
            search_keyword = re.sub(r'^(搜索|帮我找|找|查找|有没有|帮我|请问|问一下)\s*', '', user_message)
            search_keyword = search_keyword.strip()

            if not search_keyword or len(search_keyword) < 2:
                self.send_text_message(user_id, "请输入要搜索的关键词，如：AI新闻、科技动态")
                return "需要关键词"

            # 发送搜索消息
            self.send_text_message(user_id, f"好的，我来帮你搜索「{search_keyword}」的相关信息...")

            # 优先使用 Tavily 搜索（更智能的AI搜索）
            tavily_results = search_with_tavily(search_keyword)
            if tavily_results:
                # 使用 Tavily 搜索结果生成文章
                article = write_article_from_tavily(tavily_results, search_keyword)
                if article:
                    title = article.get("title", search_keyword)
                    html = article.get("html", "")
                    import re
                    text_content = re.sub(r'<[^>]+>', '', html)[:800]
                    # 保存到缓存
                    _last_article_cache[user_id] = {"title": title, "html": html}
                    self.send_card_message(user_id, f"📰 {title}", text_content + "...")
                    return "已发送"

            # 如果 Tavily 没结果，回退到 NewsNow
            news_list = search_news(search_keyword)
            if news_list:
                # 生成文章
                article = write_article(news_list)
                title = article.get("title", search_keyword)
                html = article.get("html", "")

                import re
                text_content = re.sub(r'<[^>]+>', '', html)[:800]

                # 保存到缓存
                _last_article_cache[user_id] = {"title": title, "html": html}

                # 发送卡片消息
                self.send_card_message(user_id, f"📰 {title}", text_content + "...")
                return "已发送"
            else:
                # 没搜到相关新闻
                self.send_text_message(user_id, f"抱歉，暂时没有找到关于「{search_keyword}」的相关信息。")
                return "无结果"

        except Exception as e:
            logger.error(f"AI处理失败: {e}")
            # 如果AI失败，回退到简单的关键词匹配
            return self._fallback_process(user_message, user_id)

    def _fallback_process(self, user_message: str, user_id: str) -> str:
        """备用处理方式"""
        # 技术关键词
        tech_keywords = ["AI", "人工智能", "大模型", "GPT", "ChatGPT", "OpenAI", "科技", "芯片", "算法", "智能", "数码", "手机", "电脑", "互联网", "英伟达", "微软", "Google", "Meta", "特斯拉", "电动车", "汽车", "自动驾驶", "鸿蒙", "华为", "苹果", "小米", "OPPO", "vivo", "三星", "显卡", "CPU", "GPU", "处理器", "新能源", "电池", "光伏", "SpaceX", "火箭", "卫星", "股票", "投资", "理财"]

        has_keyword = any(kw in user_message for kw in tech_keywords)

        if has_keyword:
            return self.search_and_reply(user_message, user_id)
        else:
            replies = [
                "你好！我是银河快讯机器人，你可以让我帮你搜索新闻或解答问题哦~",
                "你可以问我任何问题，我会尽力帮你搜索相关信息",
            ]
            import random
            self.send_text_message(user_id, random.choice(replies))
            return "友好回复"

    def get_latest_news(self, user_id: str) -> str:
        """获取最新AI新闻"""
        self.send_text_message(user_id, "🔍 正在搜索最新AI新闻，请稍候...")

        try:
            # 搜索新闻
            news_list = search_news()
            if not news_list:
                self.send_text_message(user_id, "抱歉，暂时没有找到相关新闻。")
                return "无新闻"

            # 生成文章
            article = write_article(news_list)
            title = article.get("title", "AI科技新闻")
            html = article.get("html", "")

            # 提取纯文本内容（用于飞书消息）
            import re
            text_content = re.sub(r'<[^>]+>', '', html)[:500]

            # 发送标题
            self.send_card_message(user_id, f"📰 {title}", text_content + "...")

            return "已发送"
        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
            self.send_text_message(user_id, f"获取新闻失败: {str(e)}")
            return "失败"

    def get_github_trending(self, user_id: str) -> str:
        """获取GitHub热门项目"""
        self.send_text_message(user_id, "🔍 正在获取GitHub热门项目，请稍候...")

        try:
            from src.github_trending import search_github_official
            from src.github_writer import write_github_article

            # 获取热门项目
            projects = search_github_official("")
            if not projects:
                self.send_text_message(user_id, "抱歉，暂时没有获取到热门项目。")
                return "无项目"

            # 生成文章
            article = write_github_article(projects)
            title = article.get("title", "GitHub热门项目")
            html = article.get("html", "")

            # 提取纯文本
            import re
            text_content = re.sub(r'<[^>]+>', '', html)[:500]

            self.send_card_message(user_id, f"⭐ {title}", text_content + "...")

            return "已发送"
        except Exception as e:
            logger.error(f"获取GitHub热门失败: {e}")
            self.send_text_message(user_id, f"获取热门项目失败: {str(e)}")
            return "失败"

    def search_and_reply(self, keyword: str, user_id: str) -> str:
        """搜索关键词新闻"""
        self.send_text_message(user_id, f"🔍 正在搜索「{keyword}」相关新闻，请稍候...")

        try:
            # 搜索新闻
            news_list = search_news(keyword)
            if not news_list:
                self.send_text_message(user_id, f"抱歉，暂时没有找到关于「{keyword}」的新闻。")
                return "无新闻"

            # 生成文章
            article = write_article(news_list)
            title = article.get("title", keyword)
            html = article.get("html", "")

            # 提取纯文本
            import re
            text_content = re.sub(r'<[^>]+>', '', html)[:500]

            self.send_card_message(user_id, f"📰 {title}", text_content + "...")

            return "已发送"
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            self.send_text_message(user_id, f"搜索失败: {str(e)}")
            return "失败"

    def publish_to_wechat(self, keyword: str, user_id: str) -> str:
        """搜索新闻并发布到微信公众号草稿箱"""
        self.send_text_message(user_id, f"📝 正在搜索「{keyword}」并发布到公众号草稿箱，请稍候...")

        try:
            # 使用 Tavily 搜索
            tavily_results = search_with_tavily(keyword)
            if tavily_results:
                article = write_article_from_tavily(tavily_results, keyword)
            else:
                # 回退到 NewsNow
                news_list = search_news(keyword)
                if not news_list:
                    self.send_text_message(user_id, f"抱歉，暂时没有找到关于「{keyword}」的新闻。")
                    return "无新闻"
                article = write_article(news_list)

            if not article:
                self.send_text_message(user_id, f"抱歉，文章生成失败。")
                return "生成失败"

            title = article.get("title", keyword)
            html = article.get("html", "")

            # 保存到缓存
            _last_article_cache[user_id] = {"title": title, "html": html}

            # 发布到微信公众号草稿箱
            from src.wechat_publisher import WeChatPublisher
            wechat = WeChatPublisher()

            result = wechat.publish(title, html)

            if result.get("success"):
                self.send_text_message(user_id, f"✅ 文章已发布到公众号草稿箱！\n\n标题：{title}\n请前往公众号后台确认发布。")
                logger.info(f"文章已发布到草稿箱: {title}")
                return "已发布"
            else:
                error_msg = result.get("message", "未知错误")
                self.send_text_message(user_id, f"❌ 发布失败：{error_msg}")
                return "发布失败"

        except Exception as e:
            logger.error(f"发布失败: {e}")
            self.send_text_message(user_id, f"发布失败: {str(e)}")
            return "失败"

    def publish_cached_article(self, cached: dict, user_id: str) -> str:
        """发布缓存的文章到公众号"""
        title = cached.get("title", "")
        html = cached.get("html", "")

        if not title or not html:
            self.send_text_message(user_id, "没有找到缓存的文章，请先搜索后再发布。")
            return "无缓存"

        self.send_text_message(user_id, f"📝 正在发布刚才的文章到公众号草稿箱，请稍候...")

        try:
            from src.wechat_publisher import WeChatPublisher
            wechat = WeChatPublisher()

            result = wechat.publish(title, html)

            if result.get("success"):
                self.send_text_message(user_id, f"✅ 文章已发布到公众号草稿箱！\n\n标题：{title}\n请前往公众号后台确认发布。")
                logger.info(f"文章已发布到草稿箱: {title}")
                return "已发布"
            else:
                error_msg = result.get("message", "未知错误")
                self.send_text_message(user_id, f"❌ 发布失败：{error_msg}")
                return "发布失败"

        except Exception as e:
            logger.error(f"发布失败: {e}")
            self.send_text_message(user_id, f"发布失败: {str(e)}")
            return "失败"


def verify_signature(timestamp: str, sign: str, secret: str) -> bool:
    """验证飞书签名"""
    try:
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        expected_sign = base64.b64encode(hmac_code).decode("utf-8")
        return expected_sign == sign
    except Exception as e:
        logger.error(f"签名验证失败: {e}")
        return False
