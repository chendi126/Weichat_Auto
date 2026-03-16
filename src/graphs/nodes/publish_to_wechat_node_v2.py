from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from cozeloop.decorator import observe
import requests

from graphs.state import PublishToWechatInput, PublishToWechatOutput


class WeChatOfficial:
    """微信公众号操作类"""

    def __init__(self):
        # 从配置文件读取凭证
        from src.config import get_config
        config = get_config()
        wechat_config = config.get("wechat", {})
        self.app_id = wechat_config.get("app_id", "")
        self.app_secret = wechat_config.get("app_secret", "")
        self.access_token = self._get_access_token()

    def _get_access_token(self) -> str:
        """获取微信公众号access_token"""
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"

        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()

            if "access_token" in data:
                return data["access_token"]
            else:
                raise Exception(f"获取access_token失败: {data}")

        except Exception as e:
            raise Exception(f"获取微信公众号access_token失败: {e}")

    def _is_base64(self, s: str) -> bool:
        """判断字符串是否为base64编码"""
        try:
            import base64
            t = s.strip().replace("\n", "")
            base64.b64decode(t, validate=True)
            return True
        except Exception:
            return False

    def _prepare_media_files(self, image_url: str):
        """准备图片文件"""
        files = None
        f_to_close = None
        import base64
        import os

        if image_url.startswith("http://") or image_url.startswith("https://"):
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()
            files = {"media": ("image.jpg", resp.content)}
        elif image_url.startswith("data:"):
            b64 = image_url.split(",", 1)[1] if "," in image_url else ""
            data = base64.b64decode(b64)
            files = {"media": ("image.jpg", data)}
        elif self._is_base64(image_url):
            data = base64.b64decode(image_url.strip().replace("\n", ""), validate=True)
            files = {"media": ("image.jpg", data)}
        else:
            if not os.path.isfile(image_url):
                raise FileNotFoundError(image_url)
            f_to_close = open(image_url, "rb")
            files = {"media": f_to_close}

        return files, f_to_close

    @observe
    def upload_permanent_image(self, image_url: str) -> Dict[str, Any]:
        """上传永久图片"""
        token = self.access_token
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
        files, f_to_close = self._prepare_media_files(image_url)
        try:
            r = requests.post(url, files=files, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            raise Exception(f"上传永久图片异常: {e}")
        finally:
            if f_to_close:
                try:
                    f_to_close.close()
                except Exception:
                    pass
        if data.get("errcode", 0) != 0:
            raise Exception(f"上传永久图片失败: {data}")
        return {"media_id": data.get("media_id"), "url": data.get("url")}

    def add_draft(self, title: str, content: str, thumb_media_id: str) -> str:
        """新增草稿"""
        token = self.access_token
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

        article = {
            "title": title,
            "content": content,
            "thumb_media_id": thumb_media_id,
            "author": "银河系的AI生活",
            "digest": content[:100],
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }

        import json
        try:
            json_data = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
            r = requests.post(url, data=json_data, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            raise Exception(f"新增草稿异常: {e}")
        if data.get("errcode", 0) != 0:
            raise Exception(f"新增草稿失败: {data}")
        media_id = data.get("media_id")
        if not media_id:
            raise Exception(f"新增草稿失败: {data}")
        return media_id

    def publish_draft(self, media_id: str) -> str:
        """发布草稿"""
        token = self.access_token
        url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={token}"
        try:
            r = requests.post(url, json={"media_id": media_id}, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            raise Exception(f"发布草稿异常: {e}")
        if data.get("errcode", 0) != 0:
            raise Exception(f"发布草稿失败: {data}")
        publish_id = data.get("publish_id")
        if not publish_id:
            raise Exception(f"发布草稿失败: {data}")
        return publish_id


def publish_to_wechat_node(state: PublishToWechatInput, config: RunnableConfig, runtime: Runtime[Context]) -> PublishToWechatOutput:
    """
    title: 发布到微信公众号
    desc: 将生成的文章和配图发布到微信公众号
    integrations: wechat-official-account
    """
    ctx = runtime.context

    article_title = state.article_title
    article_content = state.article_content
    image_url = state.image_url

    try:
        # 初始化微信公众号客户端（直接使用凭证）
        wechat = WeChatOfficial()

        # 上传图片素材
        perm_img = wechat.upload_permanent_image(image_url)

        # 新增草稿
        draft_media_id = wechat.add_draft(
            title=article_title,
            content=article_content,
            thumb_media_id=perm_img["media_id"]
        )

        # 发布草稿
        publish_id = wechat.publish_draft(draft_media_id)

        publish_result = {
            "success": True,
            "draft_media_id": draft_media_id,
            "publish_id": publish_id,
            "message": "文章已成功发布到微信公众号"
        }
    except Exception as e:
        error_msg = str(e)
        # 检查是否是 IP 白名单问题
        if "40164" in error_msg or "not in whitelist" in error_msg:
            publish_result = {
                "success": False,
                "error": error_msg,
                "message": "IP地址未在微信公众号白名单中。请在微信公众平台后台添加以下IP到白名单：115.191.1.173, 101.126.95.49"
            }
        else:
            publish_result = {
                "success": False,
                "error": error_msg,
                "message": f"发布失败: {e}"
            }

    return PublishToWechatOutput(publish_result=publish_result)
