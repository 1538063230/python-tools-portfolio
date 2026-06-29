#!/usr/bin/env python3
"""
统一启动所有 Web 应用 - 作品集演示
================================
用法:
    python start_all.py              # 启动全部
    python start_all.py data_cleaner # 只启动指定项目
    python start_all.py --list       # 列出所有项目
"""
import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from threading import Thread

BASE_DIR = Path(__file__).parent

PROJECTS = {
    "data_cleaner": {
        "name": "CSV智能数据清洗与合并工具",
        "dir": "data_cleaner",
        "port": 5001,
        "color": "\033[92m",  # 绿色
    },
    "web_scraper": {
        "name": "多平台网页数据采集器",
        "dir": "web_scraper",
        "port": 5002,
        "color": "\033[94m",  # 蓝色
    },
    "file_manager": {
        "name": "桌面批量文件管理工具",
        "dir": "file_manager",
        "port": 5003,
        "color": "\033[93m",  # 黄色
    },
    "report_generator": {
        "name": "自动化报表生成与推送系统",
        "dir": "report_generator",
        "port": 5004,
        "color": "\033[95m",  # 紫色
    },
    "multi_bot": {
        "name": "多平台消息推送机器人",
        "dir": "multi_bot",
        "port": 5005,
        "color": "\033[96m",  # 青色
    },
}

processes = []


def start_project(key):
    """启动单个项目"""
    proj = PROJECTS[key]
    proj_dir = BASE_DIR / proj["dir"]
    cmd = [sys.executable, "web_app.py"]
    print(f"{proj['color']}🚀 启动 [{key}] {proj['name']} → http://localhost:{proj['port']}\033[0m")
    p = subprocess.Popen(cmd, cwd=str(proj_dir))
    processes.append((key, p))
    return p


def signal_handler(sig, frame):
    """Ctrl+C 优雅退出"""
    print("\n\033[91m🛑 正在停止所有服务...\033[0m")
    for key, p in processes:
        try:
            p.terminate()
            p.wait(timeout=3)
            print(f"  ✓ 已停止 [{key}]")
        except subprocess.TimeoutExpired:
            p.kill()
            print(f"  ⚡ 强制停止 [{key}]")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    args = sys.argv[1:]
    if "--list" in args:
        print("\n📋 可启动的项目:\n")
        for key, proj in PROJECTS.items():
            print(f"  {proj['color']}●\033[0m {key:<20} {proj['name']:<30} 端口 {proj['port']}")
        print()
        return

    targets = [a for a in args if not a.startswith("-")]
    if not targets:
        targets = list(PROJECTS.keys())

    print("=" * 60)
    print("🌟 Python 工具集作品集 - Web 应用启动器")
    print("=" * 60)
    print()
    for key in targets:
        if key in PROJECTS:
            start_project(key)
            time.sleep(0.5)
        else:
            print(f"⚠️ 未知项目: {key}")

    print()
    print("=" * 60)
    print("✅ 所有服务已启动! 访问地址:")
    for key in targets:
        if key in PROJECTS:
            proj = PROJECTS[key]
            print(f"  {proj['color']}http://localhost:{proj['port']}\033[0m  - {proj['name']}")
    print()
    print("按 Ctrl+C 停止所有服务")
    print("=" * 60)

    # 等待所有进程
    try:
        while True:
            for key, p in processes:
                if p.poll() is not None:
                    print(f"⚠️  [{key}] 进程已退出 (返回码: {p.returncode})")
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()