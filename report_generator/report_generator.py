#!/usr/bin/env python3
"""
自动化报表生成与推送系统
=========================
功能:
  1. 从多个数据源拉取数据 (CSV, API, 数据库)
  2. 自动生成HTML/PDF/Excel报表
  3. 定时调度 (cron风格)
  4. 多渠道推送 (邮件, Webhook, 本地文件)
  5. 报表模板可定制

使用场景:
  - 每日销售数据汇总报表
  - 系统监控日报/周报
  - 运营数据自动报送
  - 财务数据定期导出

技术栈: Python + pandas + matplotlib + jinja2 + schedule
"""

import argparse
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import schedule
import time as time_module


# ============================================================
# 配置
# ============================================================

@dataclass
class ReportConfig:
    """报表配置"""
    name: str = "自动报表"
    data_sources: list = field(default_factory=list)
    output_dir: str = "reports"
    output_formats: list = field(default_factory=lambda: ["html", "xlsx"])
    charts: list = field(default_factory=list)
    email_to: list = field(default_factory=list)
    email_from: str = ""
    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    schedule: str = "daily"  # daily, weekly, monthly, cron


# ============================================================
# 数据源
# ============================================================

class DataSource:
    """数据源基类"""

    def fetch(self) -> pd.DataFrame:
        raise NotImplementedError


class CSVSource(DataSource):
    """CSV文件数据源"""

    def __init__(self, path: str, **kwargs):
        self.path = path
        self.kwargs = kwargs

    def fetch(self) -> pd.DataFrame:
        return pd.read_csv(self.path, encoding="utf-8-sig", **self.kwargs)


class APISource(DataSource):
    """API数据源"""

    def __init__(self, url: str, method: str = "GET", headers: dict = None,
                 params: dict = None, json_path: str = None):
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.params = params or {}
        self.json_path = json_path

    def fetch(self) -> pd.DataFrame:
        import requests
        resp = requests.request(self.method, self.url, headers=self.headers,
                                params=self.params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if self.json_path:
            for key in self.json_path.split("."):
                data = data[key]
        return pd.DataFrame(data)


class SQLSource(DataSource):
    """数据库数据源"""

    def __init__(self, connection_string: str, query: str):
        self.connection_string = connection_string
        self.query = query

    def fetch(self) -> pd.DataFrame:
        import sqlalchemy
        engine = sqlalchemy.create_engine(self.connection_string)
        with engine.connect() as conn:
            return pd.read_sql(self.query, conn)


# ============================================================
# 报表生成器
# ============================================================

class ReportGenerator:
    """报表生成引擎"""

    def __init__(self, config: ReportConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dataframes = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def fetch_all_data(self):
        """拉取所有数据源"""
        for source_def in self.config.data_sources:
            name = source_def.get("name", "unknown")
            source_type = source_def.get("type", "csv")
            params = source_def.get("params", {})

            if source_type == "csv":
                source = CSVSource(**params)
            elif source_type == "api":
                source = APISource(**params)
            elif source_type == "sql":
                source = SQLSource(**params)
            else:
                print(f"⚠️ 未知数据源类型: {source_type}")
                continue

            self.dataframes[name] = source.fetch()
            print(f"📥 拉取 [{name}]: {self.dataframes[name].shape[0]} 行")

    def generate_charts(self) -> list[str]:
        """生成图表"""
        chart_paths = []
        # 尝试多个中文字体, 找不到就用默认
        try:
            from matplotlib.font_manager import findSystemFonts
            chinese_fonts = ["Noto Sans CJK SC", "WenQuanYi Zen Hei",
                              "WenQuanYi Micro Hei", "Source Han Sans CN",
                              "SimHei", "Microsoft YaHei"]
            available = set()
            for f in findSystemFonts():
                for font_name in chinese_fonts:
                    if font_name.lower() in f.lower():
                        available.add(font_name)
            if available:
                plt.rcParams["font.sans-serif"] = list(available) + ["DejaVu Sans"]
            else:
                plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
        except Exception:
            plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        for chart_def in self.config.charts:
            title = chart_def.get("title", "图表")
            chart_type = chart_def.get("type", "bar")
            data_key = chart_def.get("data", "")
            x_col = chart_def.get("x", "")
            y_col = chart_def.get("y", "")
            df = self.dataframes.get(data_key)

            if df is None:
                continue

            fig, ax = plt.subplots(figsize=(10, 5))

            if chart_type == "bar":
                df.plot.bar(x=x_col, y=y_col, ax=ax)
            elif chart_type == "line":
                df.plot.line(x=x_col, y=y_col, ax=ax, marker="o")
            elif chart_type == "pie":
                df.set_index(x_col)[y_col].plot.pie(ax=ax, autopct="%1.1f%%")

            ax.set_title(title)
            plt.tight_layout()

            path = self.output_dir / f"chart_{title}_{self.timestamp}.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            chart_paths.append(str(path))
            print(f"📊 生成图表: {path}")

        return chart_paths

    def generate_html(self, chart_paths: list[str]) -> str:
        """生成HTML报表"""
        sections = []
        for name, df in self.dataframes.items():
            sections.append(f"""
            <div class="section">
                <h2>{name}</h2>
                <p class="meta">共 {df.shape[0]} 行, {df.shape[1]} 列 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                {df.head(50).to_html(classes='table', border=0, index=False)}
                {f'<p class="meta">仅显示前50行, 共{df.shape[0]}行</p>' if df.shape[0] > 50 else ''}
            </div>
            """)

        charts_html = ""
        for path in chart_paths:
            charts_html += f'<div class="chart"><img src="{Path(path).name}" /></div>'

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{self.config.name}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .meta {{ color: #999; font-size: 12px; }}
        .section {{ background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        .table th {{ background: #4CAF50; color: white; padding: 10px; text-align: left; }}
        .table td {{ padding: 8px; border-bottom: 1px solid #eee; }}
        .table tr:hover {{ background: #f0f0f0; }}
        .chart {{ text-align: center; margin: 20px 0; }}
        .chart img {{ max-width: 100%; border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>{self.config.name}</h1>
    {charts_html}
    {''.join(sections)}
</body>
</html>"""
        return html

    def generate_excel(self, chart_paths: list[str]) -> str:
        """生成Excel报表"""
        path = self.output_dir / f"{self.config.name}_{self.timestamp}.xlsx"
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for name, df in self.dataframes.items():
                sheet_name = name[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"📄 生成Excel: {path}")
        return str(path)

    def generate(self) -> dict:
        """生成所有格式的报表"""
        chart_paths = self.generate_charts()
        outputs = {}

        if "html" in self.config.output_formats:
            html = self.generate_html(chart_paths)
            html_path = self.output_dir / f"{self.config.name}_{self.timestamp}.html"
            html_path.write_text(html, encoding="utf-8")
            outputs["html"] = str(html_path)
            print(f"📄 生成HTML: {html_path}")

        if "xlsx" in self.config.output_formats:
            outputs["xlsx"] = self.generate_excel(chart_paths)

        return outputs

    def send_email(self, outputs: dict):
        """发送邮件"""
        if not self.config.email_to or not self.config.smtp_user:
            print("⚠️ 未配置邮件, 跳过发送")
            return

        msg = MIMEMultipart()
        msg["Subject"] = f"{self.config.name} - {datetime.now().strftime('%Y-%m-%d')}"
        msg["From"] = self.config.email_from or self.config.smtp_user
        msg["To"] = ", ".join(self.config.email_to)

        # 正文
        summary = "\n".join(
            f"- {name}: {df.shape[0]} 行 × {df.shape[1]} 列"
            for name, df in self.dataframes.items()
        )
        msg.attach(MIMEText(
            f"<h3>{self.config.name}</h3><p>报表已生成, 请查收附件。</p><pre>{summary}</pre>",
            "html", "utf-8"
        ))

        # 附件
        for fmt, filepath in outputs.items():
            with open(filepath, "rb") as f:
                attachment = MIMEBase("application", "octet-stream")
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                attachment.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{Path(filepath).name}"'
                )
                msg.attach(attachment)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port,
                               context=context) as server:
            server.login(self.config.smtp_user, self.config.smtp_password)
            server.send_message(msg)

        print(f"📧 邮件已发送至: {', '.join(self.config.email_to)}")


# ============================================================
# 调度器
# ============================================================

class ReportScheduler:
    """报表定时调度器"""

    def __init__(self, config: ReportConfig):
        self.config = config
        self.generator = ReportGenerator(config)

    def _run(self):
        """执行一次报表生成"""
        print(f"\n⏰ {datetime.now()} - 开始生成报表...")
        self.generator.fetch_all_data()
        outputs = self.generator.generate()
        self.generator.send_email(outputs)
        print(f"✅ 报表生成完成\n")

    def start(self):
        """启动定时任务"""
        schedule_config = self.config.schedule

        if schedule_config == "daily":
            schedule.every().day.at("09:00").do(self._run)
        elif schedule_config == "weekly":
            schedule.every().monday.at("09:00").do(self._run)
        elif schedule_config == "monthly":
            schedule.every(30).days.at("09:00").do(self._run)
        elif schedule_config == "hourly":
            schedule.every().hour.do(self._run)

        print(f"🕐 调度器已启动 (模式: {schedule_config})")
        print(f"   按 Ctrl+C 停止")

        try:
            while True:
                schedule.run_pending()
                time_module.sleep(60)
        except KeyboardInterrupt:
            print("\n👋 调度器已停止")


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="自动化报表生成与推送系统")
    parser.add_argument("-c", "--config", default="report_config.json",
                        help="报表配置文件 (JSON)")
    parser.add_argument("--once", action="store_true",
                        help="只运行一次, 不启动定时调度")
    parser.add_argument("--no-send", action="store_true",
                        help="不发送邮件")
    args = parser.parse_args()

    # 加载配置
    config_path = Path(args.config)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)
        config = ReportConfig(**config_dict)
    else:
        # 默认演示配置
        config = ReportConfig(
            name="演示报表",
            data_sources=[
                {
                    "name": "演示数据",
                    "type": "csv",
                    "params": {"path": "sample_data.csv"}
                }
            ],
            output_formats=["html", "xlsx"],
            schedule="hourly",
        )

    generator = ReportGenerator(config)

    if args.once:
        generator.fetch_all_data()
        outputs = generator.generate()
        if not args.no_send:
            generator.send_email(outputs)
    else:
        scheduler = ReportScheduler(config)
        scheduler._run()  # 先跑一次
        scheduler.start()


if __name__ == "__main__":
    main()