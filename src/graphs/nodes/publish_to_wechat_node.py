from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from cozeloop.decorator import observe
import requests

from graphs.state import PublishToWechatInput, PublishToWechatOutput

# 微信公众号配置（从配置文件读取）
from src.config import get_config
_config = get_config()
WECHAT_APP_ID = _config.get("wechat", {}).get("app_id", "")
WECHAT_APP_SECRET = _config.get("wechat", {}).get("app_secret", "")


class WeChatOfficial:
    """微信公众号操作类"""

    def __init__(self):
        self.app_id = WECHAT_APP_ID
        self.app_secret = WECHAT_APP_SECRET
        self.access_token = None
        self._token_expires_at = 0

    def _get_access_token(self) -> str:
        """获取微信公众号access_token"""
        import time

        # 检查 token 是否过期（提前5分钟刷新）
        if self.access_token and time.time() < self._token_expires_at - 300:
            return self.access_token

        # 调用微信 API 获取 token
        url = f"https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if "errcode" in data and data["errcode"] != 0:
                raise Exception(f"获取access_token失败: {data.get('errmsg', '未知错误')}")

            self.access_token = data["access_token"]
            # 微信 token 有效期为 2 小时
            self._token_expires_at = time.time() + data.get("expires_in", 7200)
            return self.access_token
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
        token = self._get_access_token()
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

    @observe
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

    @observe
    def publish_draft(self, media_id: str) -> str:
        """发布草稿"""
        token = self._get_access_token()
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
    desc: 将生成的文章和配图发布到微信公众号（使用微信公众号API）
    integrations: wechat-official-account (直接API)
    """
    ctx = runtime.context

    article_title = state.article_title
    article_content = state.article_content
    # 使用默认图片（背景.png），不再生成图片
    image_url = state.image_url if hasattr(state, 'image_url') and state.image_url else "e:/some_brain_think/pack_project/projects/背景.png"

    try:
        # 初始化微信公众号客户端
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

        # 诊断错误类型
        if "40164" in error_msg or "IP地址不在白名单中" in error_msg or "ip" in error_msg.lower():
            # IP白名单问题
            publish_result = {
                "success": False,
                "error": error_msg,
                "message": (
                    "IP地址不在白名单中（错误码40164）。\n"
                    "解决方法：\n"
                    "1. 登录微信公众平台：https://mp.weixin.qq.com\n"
                    "2. 进入「设置与开发」→「基本配置」→「IP白名单」\n"
                    "3. 添加本机公网IP地址到白名单\n"
                    "4. 保存配置"
                )
            }
        elif "48001" in error_msg or "api 功能未授权" in error_msg:
            # 接口权限问题
            publish_result = {
                "success": False,
                "error": error_msg,
                "message": (
                    "公众号未获得发布接口权限。\n"
                    "解决方法：登录微信公众平台，在「开发者中心」中检查接口权限状态。"
                )
            }
        elif "errcode" in error_msg:
            # 微信API错误
            publish_result = {
                "success": False,
                "error": error_msg,
                "message": f"微信公众号API错误: {e}"
            }
        else:
            # 其他错误
            publish_result = {
                "success": False,
                "error": error_msg,
                "message": f"发布失败: {e}"
            }

    return PublishToWechatOutput(publish_result=publish_result)
