# 桌面批量文件管理GUI工具

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vibe Coding](https://img.shields.io/badge/开发方式-Vibe%20Coding-green.svg)]()

> 使用 Trae AI 辅助开发，开发周期缩短 60%

## 功能

- 批量重命名（支持正则替换、序号递增、模板命名）
- 文件分类整理（按扩展名自动归类到子文件夹）
- 重复文件查找（基于MD5哈希）
- 文件统计（按扩展名统计数量和大小）
- 图形化界面，操作直观

## 快速开始

```bash
pip install -r requirements.txt
python file_manager.py
```

## 功能说明

| 功能 | 说明 |
|------|------|
| 批量重命名 | 支持前缀/后缀添加、查找替换、正则表达式 |
| 分类整理 | 按 .pdf/.docx/.jpg 等扩展名自动归类 |
| 重复查找 | 基于MD5查找完全相同的文件 |
| 文件统计 | 统计各类型文件数量和占用空间 |

## 技术栈

- Python 3.9+
- tkinter
- Pillow

## 适用场景

- 照片/文档批量重命名
- 下载目录自动整理
- 项目文件归档
- 重复文件清理释放空间