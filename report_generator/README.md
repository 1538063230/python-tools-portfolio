# 自动化报表生成与推送系统

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vibe Coding](https://img.shields.io/badge/开发方式-Vibe%20Coding-green.svg)]()

> 使用 Trae AI 辅助开发，开发周期缩短 60%

## 功能

- 多数据源支持（CSV、API、数据库）
- 自动生成HTML/Excel报表（含数据可视化图表）
- 定时调度（支持 daily/weekly/monthly/hourly）
- 邮件自动推送（含附件）
- JSON配置文件驱动

## 快速开始

```bash
pip install -r requirements.txt

# 运行一次（使用演示数据）
python report_generator.py --once

# 从配置文件运行
python report_generator.py -c report_config.json --once
```

## 配置文件示例

```json
{
    "name": "每日销售数据报表",
    "data_sources": [
        {
            "name": "销售数据",
            "type": "csv",
            "params": {"path": "sales_data.csv"}
        }
    ],
    "output_formats": ["html", "xlsx"],
    "charts": [
        {
            "title": "每日销售额趋势",
            "type": "line",
            "data": "销售数据",
            "x": "日期",
            "y": "销售额"
        }
    ],
    "schedule": "daily"
}
```

## 技术栈

- Python 3.9+
- pandas
- matplotlib
- openpyxl
- jinja2
- schedule

## 适用场景

- 每日销售数据汇总报表
- 系统监控日报/周报
- 运营数据自动报送
- 财务数据定期导出