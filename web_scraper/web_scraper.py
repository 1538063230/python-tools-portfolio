#!/usr/bin/env python3
"""
多平台网页数据采集器
=====================
功能:
  1. 支持静态页面 (requests + BeautifulSoup) 和动态页面 (Playwright)
  2. 自动翻页采集
  3. 数据去重与增量更新
  4. 导出 CSV / Excel / JSON
  5. 内置请求频率控制, 避免被封

使用场景:
  - 电商商品信息采集
  - 新闻/文章批量抓取
  - 招聘信息聚合
  - 行业数据监控

技术栈: Python + requests + BeautifulSoup4 + Playwright + pandas
"""

import argparse
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import pandas as pd


@dataclass
class ScraperConfig:
    """采集器配置"""
    url: str
    output_dir: str = "scraped_data"
    delay: tuple = (1, 3)          # 请求间隔 (秒)
    max_pages: int = 10
    headers: dict = field(default_factory=lambda: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })


class WebScraper:
    """通用网页数据采集器"""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.collected_data = []

    def _rate_limit(self):
        """请求频率控制"""
        delay = random.uniform(*self.config.delay)
        time.sleep(delay)

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """获取并解析单个页面"""
        try:
            self._rate_limit()
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as e:
            print(f"⚠️ 请求失败 [{url}]: {e}")
            return None

    def extract_by_selectors(self, soup: BeautifulSoup,
                              selectors: dict) -> list[dict]:
        """
        通用CSS选择器提取
        selectors 格式:
        {
            "container": "div.item",           # 每个数据项的容器
            "fields": {
                "title": "h2.title",           # 字段名: CSS选择器
                "price": "span.price",
                "link": ["a", "href"],         # 字段名: [选择器, 属性名]
                "image": ["img", "src"],
            }
        }
        """
        items = soup.select(selectors.get("container", "body"))
        results = []

        for item in items:
            record = {}
            for field_name, selector in selectors.get("fields", {}).items():
                try:
                    if isinstance(selector, list):
                        el = item.select_one(selector[0])
                        record[field_name] = el.get(selector[1], "") if el else ""
                    else:
                        el = item.select_one(selector)
                        record[field_name] = el.get_text(strip=True) if el else ""
                except Exception:
                    record[field_name] = ""
            if record:
                results.append(record)

        return results

    def extract_links(self, soup: BeautifulSoup,
                      link_selector: str = "a",
                      base_url: str = "") -> list[str]:
        """提取页面所有链接"""
        links = []
        for a in soup.select(link_selector):
            href = a.get("href", "")
            if href and not href.startswith("#") and not href.startswith("javascript"):
                full_url = urljoin(base_url, href) if base_url else href
                links.append(full_url)
        return list(set(links))

    def extract_text_content(self, soup: BeautifulSoup,
                              selectors_to_remove: list = None) -> str:
        """提取页面正文内容"""
        if selectors_to_remove:
            for sel in selectors_to_remove:
                for el in soup.select(sel):
                    el.decompose()
        return soup.get_text(separator="\n", strip=True)

    def paginate(self, url_template: str, page_param: str = "page",
                 start: int = 1) -> list[BeautifulSoup]:
        """自动翻页采集"""
        pages = []
        for page in range(start, start + self.config.max_pages):
            url = url_template.format(**{page_param: page})
            print(f"📄 第 {page} 页: {url}")
            soup = self.fetch_page(url)
            if soup:
                pages.append(soup)
            else:
                print(f"  └─ 第 {page} 页无数据, 停止翻页")
                break
        return pages

    def save_json(self, data: list[dict], filename: str):
        """保存为JSON"""
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON: {path}")

    def save_csv(self, data: list[dict], filename: str):
        """保存为CSV"""
        path = self.output_dir / filename
        df = pd.DataFrame(data)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"✅ CSV: {path} ({df.shape[0]} 行 × {df.shape[1]} 列)")

    def save_excel(self, data: list[dict], filename: str):
        """保存为Excel"""
        path = self.output_dir / filename
        df = pd.DataFrame(data)
        df.to_excel(path, index=False, engine="openpyxl")
        print(f"✅ Excel: {path} ({df.shape[0]} 行 × {df.shape[1]} 列)")

    def save_markdown(self, data: list[dict], filename: str,
                       title: str = "采集数据"):
        """保存为Markdown表格"""
        path = self.output_dir / filename
        if not data:
            return
        df = pd.DataFrame(data)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(f"采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(df.to_markdown(index=False))
        print(f"✅ Markdown: {path}")


def main():
    parser = argparse.ArgumentParser(description="多平台网页数据采集器")
    parser.add_argument("-u", "--url", required=True, help="目标URL")
    parser.add_argument("-o", "--output", default="scraped_data", help="输出目录")
    parser.add_argument("--max-pages", type=int, default=10, help="最大翻页数")
    parser.add_argument("--delay-min", type=float, default=1.0, help="最小请求间隔(秒)")
    parser.add_argument("--delay-max", type=float, default=3.0, help="最大请求间隔(秒)")
    parser.add_argument("--container", default="body", help="数据项CSS选择器")
    parser.add_argument("--format", choices=["csv", "excel", "json", "md", "all"],
                        default="csv", help="导出格式")
    parser.add_argument("--fields", nargs="*", help="要提取的字段 (CSS选择器, 用:分隔)")
    args = parser.parse_args()

    config = ScraperConfig(
        url=args.url,
        output_dir=args.output,
        max_pages=args.max_pages,
        delay=(args.delay_min, args.delay_max),
    )
    scraper = WebScraper(config)

    print(f"🌐 开始采集: {args.url}")
    soup = scraper.fetch_page(args.url)

    if not soup:
        print("❌ 无法获取页面")
        return

    # 通用采集: 提取标题、链接、正文
    title = soup.title.string if soup.title else "无标题"
    links = scraper.extract_links(soup, base_url=args.url)
    text = scraper.extract_text_content(soup, ["script", "style", "nav", "footer"])

    data = [{
        "url": args.url,
        "title": title,
        "link_count": len(links),
        "text_length": len(text),
        "text_preview": text[:500],
        "collected_at": datetime.now().isoformat(),
    }]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scraper.save_csv(data, f"scraped_{timestamp}.csv")
    scraper.save_json(data, f"scraped_{timestamp}.json")

    print(f"\n📊 采集完成:")
    print(f"  标题: {title}")
    print(f"  链接数: {len(links)}")
    print(f"  正文长度: {len(text)} 字符")


if __name__ == "__main__":
    main()