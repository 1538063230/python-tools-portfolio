# Python 工具集 - AI 辅助开发作品集

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vibe Coding](https://img.shields.io/badge/开发方式-Vibe%20Coding-green.svg)](https://www.proginn.com/b/vibecoding)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 使用 Trae AI 辅助开发，Vibe Coding 工作流，开发效率提升 60%+

## 项目列表

| # | 项目 | 说明 | 一键运行 | 截图 |
|---|------|------|----------|------|
| 1 | [data_cleaner](./data_cleaner/) | CSV智能数据清洗与合并 | `python data_cleaner.py -i sample_data` | [运行日志](./data_cleaner/screenshots/run_log.txt) |
| 2 | [web_scraper](./web_scraper/) | 多平台网页数据采集器 | `python demo.py` | [运行日志](./web_scraper/screenshots/run_log.txt) |
| 3 | [file_manager](./file_manager/) | GUI批量文件管理工具 | `python demo.py` / `python file_manager.py` | [GUI截图](./file_manager/screenshots/gui_mockup.png) |
| 4 | [report_generator](./report_generator/) | 自动化报表生成与推送 | `python report_generator.py -c report_config.json --once --no-send` | [运行日志](./report_generator/screenshots/run_log.txt) |
| 5 | [multi_bot](./multi_bot/) | 多平台消息推送机器人 | `python demo.py` | [运行日志](./multi_bot/screenshots/run_log.txt) |

## 开发方式

所有项目均采用 **Vibe Coding** 工作流开发：

1. **需求拆解** → 将需求分解为明确的功能模块
2. **AI 生成** → 使用 Trae AI 生成代码框架和主要逻辑
3. **人工审查** → 审核代码质量、逻辑正确性、安全性
4. **测试交付** → 运行验证、编写文档、打包交付

## 快速开始

每个项目独立运行，进入对应目录即可：

```bash
cd data_cleaner
pip install -r requirements.txt
python data_cleaner.py -i ./data
```

## 关于我

- 在职开发者，擅长 Python 自动化、数据处理、小工具开发
- 熟练使用 Trae AI 辅助开发，交付效率高
- 可工作时间：工作日晚上 19:00-22:00，周末全天

## License

MIT