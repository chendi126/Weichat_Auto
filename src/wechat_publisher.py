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
        self.cover_image = config["wechat"].get("cover_image", "银河快报.png")
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

    def upload_thumb(self, image_path: str = None) -> str:
        """上传封面缩略图素材"""
        if image_path is None:
            image_path = self.cover_image

        token = self._get_access_token()
        # thumb 类型用于封面图
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=thumb"

        files = self._prepare_image(image_path)

        resp = requests.post(url, files=files, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("errcode", 0) != 0:
            raise Exception(f"上传封面失败: {data}")

        return data.get("media_id")

    def _extract_digest(self, content: str) -> str:
        """提取文章摘要，去除 HTML 标签和特殊内容"""
        if not content:
            return ""
        import re
        # 去除 HTML 标签
        text = re.sub(r'<[^>]+>', '', content)
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        # 取前100个字符
        return text[:100]

    def add_draft(self, title: str, content: str, thumb_media_id: str) -> str:
        """新增草稿"""
        token = self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

        # 提取摘要
        digest = self._extract_digest(content)

        article = {
            "title": title,
            "content": content,
            "thumb_media_id": thumb_media_id,
            "author": "太空人",
            "digest": digest,
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
        """发布文章到草稿箱"""
        logger.info(f"开始发布文章: {title}")

        # 上传封面图（使用 thumb 类型）
        thumb_media_id = self.upload_thumb(image_path)

        # 新增草稿（保存到草稿箱）
        draft_id = self.add_draft(title, content, thumb_media_id)

        logger.info(f"文章已保存到草稿箱: {title}, draft_id: {draft_id}")

        return {
            "success": True,
            "draft_id": draft_id,
            "message": "文章已保存到草稿箱，请手动发布"
        }


def publish_article(title: str, content: str) -> dict:
    """发布文章到微信公众号"""
    publisher = WeChatPublisher()
    return publisher.publish(title, content)
