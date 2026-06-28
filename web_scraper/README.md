# 多平台网页数据采集器

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vibe Coding](https://img.shields.io/badge/开发方式-Vibe%20Coding-green.svg)]()

> 使用 Trae AI 辅助开发，开发周期缩短 60%

## 功能

- 静态页面采集（requests + BeautifulSoup）
- 通用CSS选择器数据提取
- 自动翻页采集
- 内置请求频率控制，避免被封
- 多格式导出（CSV、Excel、JSON、Markdown）

## 快速开始

```bash
pip install -r requirements.txt
python web_scraper.py -u https://example.com
```

## 使用示例

```bash
# 基本采集
python web_scraper.py -u https://example.com

# 指定输出目录和格式
python web_scraper.py -u https://example.com -o ./output --format excel

# 设置请求间隔（避免被封）
python web_scraper.py -u https://example.com --delay-min 2 --delay-max 5
```

## 技术栈

- Python 3.9+
- requests
- BeautifulSoup4
- pandas
- lxml

## 适用场景

- 电商商品信息采集
- 新闻/文章批量抓取
- 招聘信息聚合
- 行业数据监控