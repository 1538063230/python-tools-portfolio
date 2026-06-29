#!/usr/bin/env python3
"""多平台网页数据采集器 - Web版"""
import sys
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file, Response

sys.path.insert(0, str(Path(__file__).parent))
from web_scraper import WebScraper, ScraperConfig

app = Flask(__name__, static_folder="sample_data", static_url_path="/sample_data")

OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scrape", methods=["POST"])
def scrape():
    data = request.json or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "请输入URL"}), 400
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    container = data.get("container", "").strip()
    fields_config = data.get("fields", {})

    try:
        config = ScraperConfig(
            url=url,
            output_dir=str(OUTPUT_DIR),
            max_pages=1,
            delay=(0.5, 1.0),
        )
        scraper = WebScraper(config)
        soup = scraper.fetch_page(url)
        if not soup:
            return jsonify({"error": "无法获取页面，请检查URL或网络"}), 500

        result = {
            "url": url,
            "title": soup.title.string if soup.title else "无标题",
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 提取链接
        links = scraper.extract_links(soup, base_url=url)
        result["link_count"] = len(links)
        result["links_sample"] = links[:20]

        # 提取文本
        text = scraper.extract_text_content(soup, ["script", "style", "nav", "footer", "header"])
        result["text_length"] = len(text)
        result["text_preview"] = text[:1000]

        # 按字段提取
        if container and fields_config:
            selectors = {"container": container, "fields": fields_config}
            items = scraper.extract_by_selectors(soup, selectors)
            result["items"] = items
            result["items_count"] = len(items)

            if items:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                df = pd.DataFrame(items)
                csv_path = OUTPUT_DIR / f"scraped_{ts}.csv"
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                result["download_csv"] = f"/api/download/{csv_path.name}"

        # 自动提取通用信息 (标题、段落、图片)
        result["auto_extract"] = {
            "headings": [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])[:10]],
            "paragraphs": [p.get_text(strip=True)[:100] for p in soup.find_all("p")[:5] if p.get_text(strip=True)],
            "images": [img.get("src", "") for img in soup.find_all("img")[:5] if img.get("src")],
        }

        return jsonify({"success": True, "result": result})

    except requests.RequestException as e:
        return jsonify({"error": f"请求失败: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"处理失败: {str(e)}"}), 500


@app.route("/api/demo")
def demo():
    """演示模式 - 返回内置示例数据"""
    demo_data = [
        {"title": "AI编程工具Trae 2.0发布, 性能提升300%", "source": "科技日报", "time": "2026-06-29 10:30"},
        {"title": "Python 3.13正式发布, 引入JIT编译器", "source": "Python官网", "time": "2026-06-28 15:20"},
        {"title": "2026年最受欢迎的5种AI开发工作流", "source": "开发者周刊", "time": "2026-06-28 09:15"},
        {"title": "Rust 1.85新增异步trait支持", "source": "Rust官方博客", "time": "2026-06-27 18:45"},
        {"title": "调查显示: 90%开发者使用AI辅助编码", "source": "Stack Overflow", "time": "2026-06-27 11:00"},
    ]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame(demo_data)
    csv_path = OUTPUT_DIR / f"demo_{ts}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    return jsonify({
        "success": True,
        "result": {
            "url": "https://demo.example.com/news (模拟)",
            "title": "演示新闻列表页面",
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": demo_data,
            "items_count": 5,
            "link_count": 12,
            "text_length": 1280,
            "auto_extract": {
                "headings": ["最新科技资讯", "热门文章"],
                "paragraphs": ["关注AI、编程语言、开发工具的最新动态"],
                "images": [],
            },
            "download_csv": f"/api/download/{csv_path.name}",
        }
    })


@app.route("/api/download/<filename>")
def download(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return jsonify({"error": "文件不存在"}), 404
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)