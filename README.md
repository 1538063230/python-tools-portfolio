# Python 工具集 - AI 辅助开发作品集

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vibe Coding](https://img.shields.io/badge/开发方式-Vibe%20Coding-green.svg)](https://www.proginn.com/b/vibecoding)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 使用 Trae AI 辅助开发，Vibe Coding 工作流，开发效率提升 60%+

## 🚀 快速启动 (推荐)

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动所有 Web 应用
python start_all.py

# 3. 或单独启动某个项目
python start_all.py data_cleaner
```

## 📋 项目列表

| # | 项目 | 端口 | 访问地址 | 说明 |
|---|------|------|----------|------|
| 1 | data_cleaner | 5001 | http://localhost:5001 | CSV智能数据清洗与合并 |
| 2 | web_scraper | 5002 | http://localhost:5002 | 多平台网页数据采集器 |
| 3 | file_manager | 5003 | http://localhost:5003 | 桌面批量文件管理工具 |
| 4 | report_generator | 5004 | http://localhost:5004 | 自动化报表生成与推送 |
| 5 | multi_bot | 5005 | http://localhost:5005 | 多平台消息推送机器人 |

## 🎨 各项目 Web 界面功能

### 1. CSV智能数据清洗与合并工具 (端口 5001)
- 📤 拖拽上传多个 CSV 文件
- 👀 文件预览 (前3行)
- ⚙️ 清洗选项 (去重、空值处理、异常值检测)
- 📊 清洗结果统计 + 数据预览
- 📥 下载 CSV / Excel / JSON

### 2. 多平台网页数据采集器 (端口 5002)
- 🌐 输入 URL 进行网页采集
- 📋 自定义 CSS 选择器提取字段
- 📚 演示模式 (无需联网)
- 📊 自动提取标题、段落、链接
- 📥 下载采集结果 CSV

### 3. 桌面批量文件管理工具 (端口 5003)
- 📁 浏览本地文件系统
- ✏️ 批量重命名 (前缀/后缀/查找替换/正则)
- 📂 按扩展名自动分类
- 🔍 重复文件查找 (MD5)
- 📊 文件统计 (按扩展名)

### 4. 自动化报表生成与推送系统 (端口 5004)
- 📊 数据源预览 (示例销售数据)
- 📈 自定义图表配置 (折线/柱状/饼图)
- 📄 一键生成 HTML/Excel 报表
- 🖼️ 图表实时预览
- 📥 下载报表文件

### 5. 多平台消息推送机器人 (端口 5005)
- 📨 多平台选择 (企业微信/钉钉/飞书)
- 📝 Markdown 消息编辑
- 📋 内置消息模板 (告警/日报/部署通知)
- 🔏 签名算法演示
- 📜 发送历史记录

## 📁 目录结构

```
portfolio_projects/
├── start_all.py              # 统一启动脚本
├── requirements.txt          # 全局依赖
├── README.md                 # 本文件
├── PROGUINN_PROJECTS.md      # 程序员客栈作品集填充内容
├── data_cleaner/             # 项目1
│   ├── web_app.py            # Flask Web 应用
│   ├── data_cleaner.py       # 核心清洗引擎
│   ├── templates/index.html  # Web 界面
│   ├── sample_data/          # 示例CSV数据
│   └── requirements.txt
├── web_scraper/              # 项目2
├── file_manager/             # 项目3
├── report_generator/         # 项目4
└── multi_bot/                # 项目5
```

## 🛠️ 技术栈

- **后端**: Python 3.9+ / Flask 3.0
- **数据处理**: pandas, openpyxl
- **爬虫**: requests, beautifulsoup4
- **可视化**: matplotlib
- **前端**: 原生 HTML + CSS + JavaScript (无框架依赖)

## 📸 作品集截图指南

每个项目都有完整可交互的 Web 界面，截图时建议:

1. **首页截图**: 打开 `http://localhost:500X` 截全屏
2. **操作截图**: 执行一次完整操作流程 (上传→清洗→下载)
3. **结果截图**: 显示结果统计或数据表格
4. **多张组合**: 同一项目可截 2-3 张不同功能的图

## 📝 License

MIT