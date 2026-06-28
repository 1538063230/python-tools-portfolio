# CSV智能数据清洗与合并工具

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vibe Coding](https://img.shields.io/badge/开发方式-Vibe%20Coding-green.svg)]()

> 使用 Trae AI 辅助开发，开发周期缩短 60%

## 功能

- 多CSV文件智能合并（支持不同列结构自动对齐）
- 数据清洗流水线（去重、空值填充、异常值检测、列名标准化）
- 多格式导出（CSV、Excel、JSON）
- 数据质量报告自动生成

## 快速开始

```bash
pip install -r requirements.txt
python data_cleaner.py -i ./data -o ./output
```

## 使用示例

```bash
# 基本使用：合并并清洗
python data_cleaner.py -i ./data

# 按指定列合并（而非纵向拼接）
python data_cleaner.py -i ./data --merge-on id

# 检测异常值 + 删除空值行
python data_cleaner.py -i ./data --detect-outliers --fill drop

# 只处理 xlsx 文件
python data_cleaner.py -i ./data --pattern "*.xlsx"
```

## 技术栈

- Python 3.9+
- pandas
- openpyxl

## 适用场景

- 合并多个来源的销售/用户数据
- 清洗脏数据，输出标准化报表
- 数据迁移前的预处理
- ETL 数据管道中间环节