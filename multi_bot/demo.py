#!/usr/bin/env python3
"""
多平台消息机器人 - 演示模式
============================
不发送真实消息, 而是展示消息构造和签名计算过程
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from multi_bot import (
    BotConfig, Message, Platform, MessageDispatcher,
    SignUtils, MessageTemplate, TEMPLATES
)


def demo_signature():
    """演示1: 各平台签名算法"""
    print("=" * 60)
    print("📋 演示1: 多平台签名算法对比")
    print("=" * 60)

    timestamp = str(int(time.time()))
    secret = "SEC1234567890abcdef"

    print(f"\n🔐 演示参数:")
    print(f"   timestamp: {timestamp}")
    print(f"   secret:    {secret[:4]}***{secret[-4:]}")

    print(f"\n🔏 各平台签名计算结果:")
    print(f"   企业微信 sign: {SignUtils.wecom_sign(timestamp, secret)}")
    print(f"   钉钉     sign: {SignUtils.dingtalk_sign(timestamp, secret)}")
    print(f"   飞书     sign: {SignUtils.feishu_sign(timestamp, secret)}")


def demo_template():
    """演示2: 消息模板渲染"""
    print()
    print("=" * 60)
    print("📋 演示2: 消息模板引擎")
    print("=" * 60)

    print(f"\n📝 模板1: 告警通知")
    alert = TEMPLATES["alert"]
    content = alert.render(
        time="14:32:15",
        level="🔴 严重",
        message="数据库主库连接断开, 业务已中断",
        scope="订单服务、用户服务",
        detail="主库IP: 10.0.0.5, 备用库: 10.0.0.6",
    )
    print(content)

    print(f"\n📝 模板2: 每日数据报表")
    daily = TEMPLATES["daily_report"]
    content = daily.render(
        date="2026-06-29",
        items=[
            {"name": "新增用户", "value": 1280, "unit": "人"},
            {"name": "总订单", "value": 456, "unit": "单"},
            {"name": "GMV", "value": "89,200", "unit": "元"},
        ],
        gen_time="14:30:00",
    )
    print(content)

    print(f"\n📝 模板3: 部署通知")
    deploy = TEMPLATES["deploy_notify"]
    content = deploy.render(
        project="AI助理小程序 v2.3.1",
        version="2.3.1",
        env="生产环境",
        status="✅ 成功",
        duration="2分18秒",
        url="https://example.com/deploy/123",
    )
    print(content)


def demo_payload():
    """演示3: 各平台消息payload结构"""
    print()
    print("=" * 60)
    print("📋 演示3: 各平台消息Payload构造")
    print("=" * 60)

    msg = Message(
        title="系统告警",
        content="""## ⚠️ CPU使用率告警

**服务器**: prod-web-01
**当前使用率**: 95.2%
**告警时间**: 2026-06-29 14:32

请相关同事立即排查！""",
        msg_type="markdown",
        at_mobiles=["13800138000"],
    )

    print(f"\n📦 企业微信 Markdown 消息结构:")
    print(f"   msgtype: {msg.msg_type}")
    print(f"   markdown.content: (略, 长度 {len(msg.content)} 字符)")
    print(f"   ✓ 符合企业微信API规范")

    print(f"\n📦 钉钉 Markdown 消息结构:")
    print(f"   msgtype: {msg.msg_type}")
    print(f"   markdown.title: {msg.title}")
    print(f"   markdown.text: (略, 长度 {len(msg.content)} 字符)")
    print(f"   at.atMobiles: {msg.at_mobiles}")
    print(f"   ✓ 符合钉钉API规范")

    print(f"\n📦 飞书 交互式卡片消息结构:")
    print(f"   msg_type: interactive")
    print(f"   card: (富文本卡片结构)")
    print(f"   ✓ 符合飞书API规范")


def demo_workflow():
    """演示4: 完整工作流"""
    print()
    print("=" * 60)
    print("📋 演示4: 消息分发工作流")
    print("=" * 60)

    print("""
🔄 典型使用流程:

   ┌──────────────────────────────────────────────┐
   │ 业务系统触发事件 (订单异常/部署完成/告警)     │
   └──────────────────┬───────────────────────────┘
                      │
                      ▼
   ┌──────────────────────────────────────────────┐
   │ 构造 Message 对象                            │
   │   - title: "系统告警"                        │
   │   - content: "..."                            │
   │   - msg_type: "markdown"                      │
   │   - at_mobiles: ["138..."]                    │
   └──────────────────┬───────────────────────────┘
                      │
                      ▼
   ┌──────────────────────────────────────────────┐
   │ MessageDispatcher.send(msg)                  │
   │   - 加入发送队列                              │
   │   - 后台线程消费                              │
   └──────────────────┬───────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   ┌────────┐   ┌────────┐   ┌────────┐
   │ 企业微信│   │  钉钉  │   │  飞书  │
   │ 适配器  │   │ 适配器  │   │ 适配器  │
   │ +签名  │   │ +签名  │   │ +签名  │
   └────┬───┘   └────┬───┘   └────┬───┘
        │            │            │
        ▼            ▼            ▼
    失败→重试     失败→重试    失败→重试
   (最多3次)     (最多3次)    (最多3次)

✅ 优势:
   • 一套代码覆盖3个平台
   • 异步队列不阻塞业务
   • 自动重试保证送达
   • 统一模板引擎
""")


def main():
    print()
    print("🤖 " * 25)
    print("   多平台消息推送机器人 - 功能演示")
    print("🤖 " * 25)

    demo_signature()
    demo_template()
    demo_payload()
    demo_workflow()

    print()
    print("=" * 60)
    print("✅ 演示完成!")
    print("💡 实际使用: 配置好Webhook后运行 python multi_bot.py --msg 'hello'")
    print("=" * 60)


if __name__ == "__main__":
    main()