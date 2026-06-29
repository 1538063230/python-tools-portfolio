#!/usr/bin/env python3
"""多平台消息推送机器人 - Web版"""
import sys
import json
import time
import hashlib
import hmac
import base64
import urllib.parse
import threading
import queue
from pathlib import Path
from datetime import datetime

import requests
from flask import Flask, render_template, request, jsonify, send_file

sys.path.insert(0, str(Path(__file__).parent))
from multi_bot import (
    BotConfig, Message, Platform, MessageDispatcher,
    SignUtils, MessageTemplate, TEMPLATES
)

app = Flask(__name__, static_folder=".", static_url_path="/static")

# 全局状态
SENT_HISTORY = []
BOT_CONFIGS = {  # 默认配置 (webhook URL 留空)
    "wecom": {"name": "企业微信", "webhook": "", "secret": "", "enabled": True},
    "dingtalk": {"name": "钉钉", "webhook": "", "secret": "", "enabled": True},
    "feishu": {"name": "飞书", "webhook": "", "secret": "", "enabled": True},
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/templates")
def get_templates():
    """返回所有消息模板"""
    templates = {}
    for key, tpl in TEMPLATES.items():
        templates[key] = {
            "name": tpl.name if hasattr(tpl, "name") else key,
            "description": tpl.description if hasattr(tpl, "description") else "",
            "fields": tpl.fields if hasattr(tpl, "fields") else [],
        }
    return jsonify({"templates": templates})


@app.route("/api/render_template", methods=["POST"])
def render_template_api():
    """渲染消息模板"""
    data = request.json or {}
    tpl_key = data.get("template")
    params = data.get("params", {})
    if tpl_key not in TEMPLATES:
        return jsonify({"error": "模板不存在"}), 404
    try:
        tpl = TEMPLATES[tpl_key]
        content = tpl.render(**params) if hasattr(tpl, "render") else str(tpl)
        return jsonify({"success": True, "content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sign_demo")
def sign_demo():
    """演示签名算法"""
    timestamp = str(int(time.time()))
    secret = "SEC1234567890abcdef"
    return jsonify({
        "timestamp": timestamp,
        "secret": secret,
        "wecom_sign": SignUtils.wecom_sign(timestamp, secret),
        "dingtalk_sign": SignUtils.dingtalk_sign(timestamp, secret),
        "feishu_sign": SignUtils.feishu_sign(timestamp, secret),
    })


@app.route("/api/configs", methods=["GET", "POST"])
def configs():
    """获取/更新机器人配置"""
    if request.method == "GET":
        return jsonify({"configs": BOT_CONFIGS})
    data = request.json or {}
    for platform, cfg in data.items():
        if platform in BOT_CONFIGS:
            BOT_CONFIGS[platform].update(cfg)
    return jsonify({"success": True, "configs": BOT_CONFIGS})


@app.route("/api/send", methods=["POST"])
def send_message():
    """发送消息 (演示模式: 不真实发送, 只记录)"""
    data = request.json or {}
    title = data.get("title", "")
    content = data.get("content", "")
    msg_type = data.get("msg_type", "markdown")
    at_mobiles = data.get("at_mobiles", [])
    targets = data.get("targets", ["wecom", "dingtalk", "feishu"])

    if not content:
        return jsonify({"error": "消息内容不能为空"}), 400

    results = []
    for target in targets:
        if target not in BOT_CONFIGS:
            continue
        cfg = BOT_CONFIGS[target]
        webhook = cfg.get("webhook", "").strip()
        timestamp = str(int(time.time()))

        result = {
            "platform": target,
            "platform_name": cfg["name"],
            "timestamp": timestamp,
            "status": "pending",
        }

        if not webhook:
            # 演示模式
            sign = ""
            if cfg.get("secret"):
                if target == "wecom":
                    sign = SignUtils.wecom_sign(timestamp, cfg["secret"])
                elif target == "dingtalk":
                    sign = SignUtils.dingtalk_sign(timestamp, cfg["secret"])
                elif target == "feishu":
                    sign = SignUtils.feishu_sign(timestamp, cfg["secret"])
            result["status"] = "demo"
            result["message"] = "演示模式: 未配置webhook, 消息已记录"
            result["sign"] = sign[:16] + "..." if sign else ""
            result["payload_preview"] = build_payload_preview(target, title, content, msg_type, at_mobiles)
        else:
            # 真实发送 (此处只模拟)
            result["status"] = "simulated"
            result["message"] = "已模拟发送 (实际环境会调用真实API)"

        results.append(result)

    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": title,
        "content": content[:200],
        "msg_type": msg_type,
        "targets": targets,
        "results": results,
    }
    SENT_HISTORY.insert(0, record)
    if len(SENT_HISTORY) > 50:
        SENT_HISTORY.pop()

    return jsonify({
        "success": True,
        "results": results,
        "record": record,
    })


@app.route("/api/history")
def history():
    return jsonify({"history": SENT_HISTORY})


def build_payload_preview(platform, title, content, msg_type, at_mobiles):
    """构造消息预览"""
    if platform == "wecom":
        return {
            "msgtype": msg_type,
            "markdown": {"content": content[:100] + "..."},
        }
    elif platform == "dingtalk":
        return {
            "msgtype": msg_type,
            "markdown": {"title": title, "text": content[:100] + "..."},
            "at": {"atMobiles": at_mobiles, "isAtAll": False},
        }
    elif platform == "feishu":
        return {
            "msg_type": "interactive",
            "card": {"elements": [{"text": content[:100] + "..."}]},
        }
    return {}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)