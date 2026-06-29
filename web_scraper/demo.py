#!/usr/bin/env python3
"""
本地演示模式 - 不需要联网也能看到效果
================================
通过读取一个内置的"假HTML"来模拟爬取过程, 输出和真实爬取一样的效果
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from web_scraper import WebScraper, ScraperConfig

# 内置的演示 HTML (模拟一个新闻列表页面)
DEMO_HTML = """
<html><body>
<div class="news-item">
    <h2 class="title">AI编程工具Trae 2.0发布, 性能提升300%</h2>
    <span class="source">科技日报</span>
    <span class="time">2026-06-29 10:30</span>
    <a class="link" href="/article/1001">查看详情</a>
</div>
<div class="news-item">
    <h2 class="title">Python 3.13正式发布, 引入JIT编译器</h2>
    <span class="source">Python官网</span>
    <span class="time">2026-06-28 15:20</span>
    <a class="link" href="/article/1002">查看详情</a>
</div>
<div class="news-item">
    <h2 class="title">2026年最受欢迎的5种AI开发工作流</h2>
    <span class="source">开发者周刊</span>
    <span class="time">2026-06-28 09:15</span>
    <a class="link" href="/article/1003">查看详情</a>
</div>
<div class="news-item">
    <h2 class="title">Rust 1.85新增异步trait支持</h2>
    <span class="source">Rust官方博客</span>
    <span class="time">2026-06-27 18:45</span>
    <a class="link" href="/article/1004">查看详情</a>
</div>
<div class="news-item">
    <h2 class="title">调查显示: 90%开发者使用AI辅助编码</h2>
    <span class="source">Stack Overflow</span>
    <span class="time">2026-06-27 11:00</span>
    <a class="link" href="/article/1005">查看详情</a>
</div>
</body></html>
"""

def main():
    print("=" * 60)
    print("🌐 网页数据采集器 - 本地演示模式")
    print("=" * 60)
    print("📄 目标URL: https://demo.example.com/news (模拟)")
    print()

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(DEMO_HTML, "html.parser")

    config = ScraperConfig(
        url="https://demo.example.com/news",
        output_dir="output",
    )
    scraper = WebScraper(config)

    selectors = {
        "container": "div.news-item",
        "fields": {
            "title": "h2.title",
            "source": "span.source",
            "time": "span.time",
        },
    }

    print(f"🔍 解析页面...")
    data = scraper.extract_by_selectors(soup, selectors)
    print(f"   提取到 {len(data)} 条数据\n")

    print(f"📊 采集结果预览:")
    for i, item in enumerate(data, 1):
        print(f"   {i}. [{item['source']}] {item['title']}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scraper.save_csv(data, f"news_demo_{timestamp}.csv")
    scraper.save_excel(data, f"news_demo_{timestamp}.xlsx")
    scraper.save_json(data, f"news_demo_{timestamp}.json")
    scraper.save_markdown(data, f"news_demo_{timestamp}.md", title="新闻采集结果")

    print()
    print("=" * 60)
    print("✅ 采集完成! 输出文件已保存到 output/ 目录")
    print("=" * 60)

if __name__ == "__main__":
    main()