#!/usr/bin/env python3
"""
多平台消息推送机器人
=====================
功能:
  1. 统一接口, 一套代码同时推送至 企业微信 / 钉钉 / 飞书
  2. 支持文本、Markdown、图片、文件、卡片消息
  3. 消息模板引擎 (Jinja2)
  4. 发送队列 + 失败重试
  5. Webhook触发器 (可接收HTTP请求转消息推送)

使用场景:
  - 系统告警通知
  - 业务数据日报推送
  - CI/CD构建结果通知
  - 客户服务提醒

技术栈: Python + requests + Flask + jinja2
"""

import json
import time
import hashlib
import hmac
import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue
from threading import Thread
from urllib.parse import quote

import requests
from jinja2 import Template


# ============================================================
# 日志
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MultiBot")


# ============================================================
# 平台定义
# ============================================================

class Platform(Enum):
    WECOM = "wecom"        # 企业微信
    DINGTALK = "dingtalk"  # 钉钉
    FEISHU = "feishu"      # 飞书


@dataclass
class BotConfig:
    """机器人配置"""
    platform: Platform
    webhook_url: str
    secret: str = ""          # 签名密钥 (企业微信/钉钉)
    at_mobiles: list = field(default_factory=list)
    at_all: bool = False


# ============================================================
# 消息类型
# ============================================================

@dataclass
class Message:
    """统一消息体"""
    title: str = ""
    content: str = ""
    msg_type: str = "text"     # text, markdown, image, file, card
    image_path: str = ""
    file_path: str = ""
    card_data: dict = field(default_factory=dict)
    at_mobiles: list = field(default_factory=list)
    at_all: bool = False


# ============================================================
# 签名工具
# ============================================================

class SignUtils:
    """各平台签名算法"""

    @staticmethod
    def wecom_sign(timestamp: str, secret: str) -> str:
        """企业微信签名"""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    @staticmethod
    def dingtalk_sign(timestamp: str, secret: str) -> str:
        """钉钉签名"""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = base64.b64encode(hmac_code).decode("utf-8")
        return quote(sign)

    @staticmethod
    def feishu_sign(timestamp: str, secret: str) -> str:
        """飞书签名"""
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")


# ============================================================
# 平台适配器
# ============================================================

class BaseAdapter:
    """平台适配器基类"""

    def __init__(self, config: BotConfig):
        self.config = config

    def send(self, msg: Message) -> bool:
        raise NotImplementedError

    def _post(self, payload: dict) -> bool:
        try:
            resp = requests.post(
                self.config.webhook_url,
                json=payload,
                timeout=10,
            )
            result = resp.json()
            logger.info(f"[{self.config.platform.value}] 发送成功: {result}")
            return True
        except Exception as e:
            logger.error(f"[{self.config.platform.value}] 发送失败: {e}")
            return False


class WecomAdapter(BaseAdapter):
    """企业微信机器人适配器"""

    def send(self, msg: Message) -> bool:
        url = self.config.webhook_url

        if self.config.secret:
            timestamp = str(int(time.time()))
            sign = SignUtils.wecom_sign(timestamp, self.config.secret)
            url = f"{url}&timestamp={timestamp}&sign={sign}"

        payload = {"msgtype": msg.msg_type}

        if msg.msg_type == "text":
            payload["text"] = {
                "content": msg.content,
                "mentioned_mobile_list": msg.at_mobiles or self.config.at_mobiles,
            }

        elif msg.msg_type == "markdown":
            payload["markdown"] = {"content": msg.content}

        elif msg.msg_type == "image":
            payload["image"] = {
                "base64": self._image_to_base64(msg.image_path),
                "md5": self._file_md5(msg.image_path),
            }

        elif msg.msg_type == "file":
            # 企业微信文件需要先上传获取media_id
            payload["file"] = {"media_id": self._upload_file(msg.file_path)}

        elif msg.msg_type == "news":
            payload["news"] = {"articles": msg.card_data.get("articles", [])}

        try:
            resp = requests.post(url, json=payload, timeout=10)
            result = resp.json()
            if result.get("errcode") == 0:
                logger.info("[企业微信] 发送成功")
                return True
            else:
                logger.error(f"[企业微信] 发送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"[企业微信] 异常: {e}")
            return False

    def _image_to_base64(self, path: str) -> str:
        import base64 as b64
        with open(path, "rb") as f:
            return b64.b64encode(f.read()).decode()

    def _file_md5(self, path: str) -> str:
        return hashlib.md5(Path(path).read_bytes()).hexdigest()

    def _upload_file(self, path: str) -> str:
        upload_url = self.config.webhook_url.replace(
            "webhook/send", "webhook/upload_media"
        ).split("?")[0] + f"?key={self.config.webhook_url.split('key=')[1].split('&')[0]}&type=file"
        with open(path, "rb") as f:
            resp = requests.post(upload_url, files={"media": f})
        return resp.json().get("media_id", "")


class DingtalkAdapter(BaseAdapter):
    """钉钉机器人适配器"""

    def send(self, msg: Message) -> bool:
        url = self.config.webhook_url

        if self.config.secret:
            timestamp = str(int(time.time() * 1000))
            sign = SignUtils.dingtalk_sign(timestamp, self.config.secret)
            url = f"{url}&timestamp={timestamp}&sign={sign}"

        payload = {"msgtype": msg.msg_type}

        if msg.msg_type == "text":
            payload["text"] = {"content": msg.content}
            at = {"atMobiles": msg.at_mobiles or self.config.at_mobiles,
                  "isAtAll": msg.at_all or self.config.at_all}
            payload["at"] = at

        elif msg.msg_type == "markdown":
            payload["markdown"] = {
                "title": msg.title,
                "text": msg.content,
            }

        elif msg.msg_type == "link":
            payload["link"] = {
                "title": msg.card_data.get("title", ""),
                "text": msg.card_data.get("text", ""),
                "messageUrl": msg.card_data.get("url", ""),
                "picUrl": msg.card_data.get("pic_url", ""),
            }

        elif msg.msg_type == "actionCard":
            payload["actionCard"] = {
                "title": msg.title,
                "text": msg.content,
                "btns": msg.card_data.get("btns", []),
            }

        return self._post(payload)


class FeishuAdapter(BaseAdapter):
    """飞书机器人适配器"""

    def send(self, msg: Message) -> bool:
        if self.config.secret:
            timestamp = str(int(time.time()))
            sign = SignUtils.feishu_sign(timestamp, self.config.secret)
            payload = {
                "timestamp": timestamp,
                "sign": sign,
                "msg_type": msg.msg_type,
            }
        else:
            payload = {"msg_type": msg.msg_type}

        if msg.msg_type == "text":
            payload["content"] = {"text": msg.content}

        elif msg.msg_type == "interactive":
            payload["card"] = msg.card_data
            payload["msg_type"] = "interactive"

        elif msg.msg_type == "image":
            payload["content"] = {"image_key": self._upload_image(msg.image_path)}

        return self._post(payload)

    def _upload_image(self, path: str) -> str:
        return ""


# ============================================================
# 消息模板引擎
# ============================================================

class MessageTemplate:
    """消息模板"""

    def __init__(self, template_str: str):
        self.template = Template(template_str)

    def render(self, **kwargs) -> str:
        return self.template.render(**kwargs)


# 内置模板
TEMPLATES = {
    "alert": MessageTemplate("""
## ⚠️ 系统告警

**告警时间**: {{ time }}
**告警级别**: {{ level }}
**告警内容**: {{ message }}
**影响范围**: {{ scope }}
{% if detail %}
**详细信息**: {{ detail }}
{% endif %}
""".strip()),

    "daily_report": MessageTemplate("""
## 📊 日报 {{ date }}

{% for item in items %}
- **{{ item.name }}**: {{ item.value }} {{ item.unit }}
{% endfor %}

> 自动生成于 {{ gen_time }}
""".strip()),

    "deploy_notify": MessageTemplate("""
## 🚀 部署通知

**项目**: {{ project }}
**版本**: {{ version }}
**环境**: {{ env }}
**状态**: {{ status }}
**耗时**: {{ duration }}

[查看详情]({{ url }})
""".strip()),
}


# ============================================================
# 消息调度器
# ============================================================

class MessageDispatcher:
    """消息分发器 (支持多平台群发 + 失败重试)"""

    def __init__(self, max_retries: int = 3, retry_delay: float = 5.0):
        self.adapters: dict[Platform, BaseAdapter] = {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.queue = Queue()
        self._worker = Thread(target=self._process_queue, daemon=True)
        self._worker.start()

    def register(self, config: BotConfig):
        """注册平台机器人"""
        adapter_map = {
            Platform.WECOM: WecomAdapter,
            Platform.DINGTALK: DingtalkAdapter,
            Platform.FEISHU: FeishuAdapter,
        }
        adapter_cls = adapter_map.get(config.platform)
        if adapter_cls:
            self.adapters[config.platform] = adapter_cls(config)
            logger.info(f"已注册: {config.platform.value}")

    def send(self, msg: Message, platforms: list[Platform] = None):
        """发送消息到指定平台 (默认全平台)"""
        targets = platforms or list(self.adapters.keys())
        for platform in targets:
            self.queue.put((platform, msg))

    def broadcast(self, msg: Message):
        """全平台广播"""
        self.send(msg, platforms=None)

    def _process_queue(self):
        """后台处理发送队列"""
        while True:
            platform, msg = self.queue.get()
            adapter = self.adapters.get(platform)
            if not adapter:
                continue

            for attempt in range(1, self.max_retries + 1):
                if adapter.send(msg):
                    break
                logger.warning(f"[{platform.value}] 第 {attempt} 次重试...")
                time.sleep(self.retry_delay * attempt)


# ============================================================
# Flask Webhook触发器
# ============================================================

def create_webhook_server(dispatcher: MessageDispatcher, host: str = "0.0.0.0",
                          port: int = 5000):
    """创建Webhook触发服务"""
    from flask import Flask, request, jsonify

    app = Flask(__name__)

    @app.route("/webhook/<platform>", methods=["POST"])
    def webhook_handler(platform: str):
        """接收HTTP请求转消息推送"""
        data = request.get_json(force=True, silent=True) or {}

        platform_map = {
            "wecom": Platform.WECOM,
            "dingtalk": Platform.DINGTALK,
            "feishu": Platform.FEISHU,
        }
        target = platform_map.get(platform)
        if not target:
            return jsonify({"error": f"未知平台: {platform}"}), 400

        msg = Message(
            title=data.get("title", "Webhook消息"),
            content=data.get("content", request.get_data(as_text=True)),
            msg_type=data.get("msg_type", "text"),
        )
        dispatcher.send(msg, platforms=[target])
        return jsonify({"status": "ok"}), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "platforms": [p.value for p in dispatcher.adapters.keys()],
            "queue_size": dispatcher.queue.qsize(),
        })

    logger.info(f"Webhook服务启动: http://{host}:{port}")
    app.run(host=host, port=port)


# ============================================================
# 命令行入口
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="多平台消息推送机器人",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 发送文本消息
  python multi_bot.py --wecom https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx \\
      --msg "服务器CPU超过90%"

  # 发送Markdown消息
  python multi_bot.py --dingtalk https://oapi.dingtalk.com/robot/send?access_token=xxx \\
      --secret SECxxx --markdown --title "日报" --msg "## 今日数据"

  # 启动Webhook服务
  python multi_bot.py --server --wecom https://xxx --dingtalk https://xxx

  # 从配置文件加载
  python multi_bot.py --config bots.json
        """
    )

    parser.add_argument("--wecom", help="企业微信Webhook URL")
    parser.add_argument("--dingtalk", help="钉钉Webhook URL")
    parser.add_argument("--feishu", help="飞书Webhook URL")
    parser.add_argument("--wecom-secret", help="企业微信签名密钥")
    parser.add_argument("--dingtalk-secret", help="钉钉签名密钥")
    parser.add_argument("--feishu-secret", help="飞书签名密钥")
    parser.add_argument("--msg", help="消息内容")
    parser.add_argument("--title", help="消息标题")
    parser.add_argument("--markdown", action="store_true", help="发送Markdown消息")
    parser.add_argument("--template", choices=list(TEMPLATES.keys()),
                        help="使用内置模板")
    parser.add_argument("--at-mobiles", nargs="*", help="@指定手机号")
    parser.add_argument("--at-all", action="store_true", help="@所有人")
    parser.add_argument("--server", action="store_true", help="启动Webhook服务")
    parser.add_argument("--port", type=int, default=5000, help="Webhook端口")
    parser.add_argument("--config", help="从JSON配置文件加载")

    args = parser.parse_args()

    dispatcher = MessageDispatcher()

    # 注册机器人
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            configs = json.load(f)
        for cfg in configs:
            dispatcher.register(BotConfig(
                platform=Platform(cfg["platform"]),
                webhook_url=cfg["webhook_url"],
                secret=cfg.get("secret", ""),
                at_mobiles=cfg.get("at_mobiles", []),
                at_all=cfg.get("at_all", False),
            ))
    else:
        if args.wecom:
            dispatcher.register(BotConfig(
                platform=Platform.WECOM,
                webhook_url=args.wecom,
                secret=args.wecom_secret or "",
            ))
        if args.dingtalk:
            dispatcher.register(BotConfig(
                platform=Platform.DINGTALK,
                webhook_url=args.dingtalk,
                secret=args.dingtalk_secret or "",
            ))
        if args.feishu:
            dispatcher.register(BotConfig(
                platform=Platform.FEISHU,
                webhook_url=args.feishu,
                secret=args.feishu_secret or "",
            ))

    if args.server:
        create_webhook_server(dispatcher, port=args.port)
    elif args.msg:
        content = args.msg
        if args.template:
            tpl = TEMPLATES[args.template]
            content = tpl.render(
                time=datetime.now().strftime("%H:%M:%S"),
                date=datetime.now().strftime("%Y-%m-%d"),
                message=args.msg,
                level="WARNING",
                scope="全部",
            )

        msg_type = "markdown" if args.markdown else "text"
        msg = Message(
            title=args.title or "消息通知",
            content=content,
            msg_type=msg_type,
            at_mobiles=args.at_mobiles or [],
            at_all=args.at_all,
        )
        dispatcher.broadcast(msg)
        time.sleep(2)  # 等待发送完成
        logger.info("消息已发送")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()