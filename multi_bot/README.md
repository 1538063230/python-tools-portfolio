# 多平台消息推送机器人

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vibe Coding](https://img.shields.io/badge/开发方式-Vibe%20Coding-green.svg)]()

> 使用 Trae AI 辅助开发，开发周期缩短 60%

## 功能

- 统一接口，一套代码同时推送至企业微信/钉钉/飞书
- 支持文本、Markdown、图片、文件、卡片消息
- 消息模板引擎（Jinja2）
- 发送队列 + 失败重试机制
- Webhook触发器（HTTP → 消息推送）
- 内置告警/日报/部署通知模板

## 快速开始

```bash
pip install -r requirements.txt

# 发送文本消息
python multi_bot.py --wecom https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY \
    --msg "服务器CPU超过90%"

# 发送Markdown消息到钉钉
python multi_bot.py --dingtalk https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN \
    --secret YOUR_SECRET --markdown --title "日报" --msg "## 今日数据"

# 使用预设模板
python multi_bot.py --wecom YOUR_URL --template alert --msg "数据库连接异常"

# 从配置文件批量注册
python multi_bot.py --config bots.json --msg "测试消息"

# 启动Webhook服务
python multi_bot.py --server --port 5000 --wecom YOUR_URL --dingtalk YOUR_URL
```

## 配置文件

```json
[
    {
        "platform": "wecom",
        "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY",
        "secret": "",
        "at_mobiles": [],
        "at_all": false
    },
    {
        "platform": "dingtalk",
        "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN",
        "secret": "YOUR_SECRET"
    }
]
```

## 技术栈

- Python 3.9+
- requests
- Flask
- jinja2

## 适用场景

- 系统告警通知
- 业务数据日报推送
- CI/CD构建结果通知
- 客户服务提醒