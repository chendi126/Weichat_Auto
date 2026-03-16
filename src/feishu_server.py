"""飞书机器人服务器 - 接收消息回调"""
import json
import logging
from flask import Flask, request, jsonify
from src.feishu_bot import FeishuBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = FeishuBot()

# 用于去重的已处理消息ID集合
processed_messages = set()
MAX_CACHE_SIZE = 1000


@app.route("/feishu/", methods=["GET", "POST"])
@app.route("/feishu/callback", methods=["GET", "POST"])
def callback():
    """飞书回调入口"""
    # 验证 URL - 飞书配置事件订阅时会发送 GET 请求
    if request.method == "GET":
        # 飞书会发送 challenge 参数，需要原样返回
        challenge = request.args.get("challenge")
        if challenge:
            return jsonify({"challenge": challenge})
        return jsonify({"status": "ok"})

    # 处理 POST 请求
    try:
        data = request.get_json()
        logger.info(f"收到飞书回调: {json.dumps(data, ensure_ascii=False)[:500]}")

        # 处理事件类型 - v2.0事件格式
        header = data.get("header", {})
        event_type = header.get("event_type", data.get("type", ""))

        # url_verification
        if event_type == "url_verification":
            # URL 验证
            return jsonify({
                "challenge": data.get("challenge")
            })

        elif event_type == "im.message.receive_v1":
            # 事件回调 - v2.0 事件
            event = data.get("event", {})
            message = event.get("message", {})

            logger.info(f"event内容: {json.dumps(event, ensure_ascii=False)[:500]}")

            # 获取消息ID用于去重
            message_id = message.get("message_id", "")

            # 消息去重检查
            if message_id in processed_messages:
                logger.info(f"消息 {message_id} 已处理，跳过")
                return jsonify({"code": 0, "msg": "success"})

            # 添加到已处理集合
            processed_messages.add(message_id)
            # 保持缓存大小
            if len(processed_messages) > MAX_CACHE_SIZE:
                processed_messages.clear()

            # v2.0 消息类型是 message_type
            msg_type = message.get("msg_type") or message.get("message_type", "")
            logger.info(f"消息类型: {msg_type}")

            if msg_type == "text":
                # 文本消息
                user_id = event.get("sender", {}).get("sender_id", {}).get("open_id")
                # v2.0 事件文本在 content 字段
                message_content = message.get("content", "")

                # content 是 JSON 字符串，需要先解析
                try:
                    content_obj = json.loads(message_content)
                    text = content_obj.get("text", "")
                except:
                    text = message_content

                # 去除 @机器人 的前缀
                if "<at id=" in text:
                    import re
                    text = re.sub(r'<at[^>]*>[^<]*</at>', '', text).strip()

                logger.info(f"用户 {user_id} 发送: {text}")

                # 处理消息并回复
                if text:
                    bot.process_message(text, user_id)
            else:
                logger.info(f"不支持的消息类型: {msg_type}")

        return jsonify({"code": 0, "msg": "success"})

    except Exception as e:
        logger.error(f"处理回调失败: {e}")
        return jsonify({"code": 1, "msg": str(e)})


@app.route("/health", methods=["GET"])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # 从配置获取端口
    from src.config import get_config
    config = get_config()
    feishu_config = config.get("feishu", {})
    port = feishu_config.get("port", 5000)

    logger.info(f"飞书机器人服务启动，端口: {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
