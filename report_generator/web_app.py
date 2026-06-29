#!/usr/bin/env python3
"""自动化报表生成与推送系统 - Web版"""
import os
import io
import sys
import json
import base64
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from report_generator import ReportConfig, ReportGenerator

app = Flask(__name__, static_folder="reports", static_url_path="/reports")

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/sample_data")
def sample_data():
    """返回示例销售数据"""
    csv_path = Path(__file__).parent / "sample_sales.csv"
    if not csv_path.exists():
        return jsonify({"error": "示例数据不存在"}), 404
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    return jsonify({
        "columns": list(df.columns),
        "rows": df.values.tolist(),
        "total": int(df.shape[0]),
    })


@app.route("/api/generate", methods=["POST"])
def generate():
    """生成报表"""
    data = request.json or {}
    chart_configs = data.get("charts", [])
    output_formats = data.get("formats", ["html", "xlsx"])

    try:
        csv_path = Path(__file__).parent / "sample_sales.csv"
        df = pd.read_csv(csv_path, encoding="utf-8-sig")

        # 设置中文字体
        set_chinese_font()

        # 生成图表
        chart_files = []
        for cfg in chart_configs:
            chart_type = cfg.get("type", "line")
            x_col = cfg.get("x", df.columns[0])
            y_col = cfg.get("y", df.columns[1] if len(df.columns) > 1 else df.columns[0])
            title = cfg.get("title", f"{y_col}趋势图")

            fig, ax = plt.subplots(figsize=(10, 5))
            if chart_type == "line":
                df.plot.line(x=x_col, y=y_col, ax=ax, marker="o", color="#4CAF50", linewidth=2)
            elif chart_type == "bar":
                df.plot.bar(x=x_col, y=y_col, ax=ax, color="#2196F3")
            elif chart_type == "pie":
                df.set_index(x_col)[y_col].plot.pie(ax=ax, autopct="%1.1f%%", figsize=(8, 8))

            ax.set_title(title, fontsize=14, fontweight="bold")
            ax.grid(True, alpha=0.3)
            plt.tight_layout()

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            chart_name = f"chart_{title}_{ts}.png"
            chart_path = REPORTS_DIR / chart_name
            fig.savefig(chart_path, dpi=120, bbox_inches="tight")
            plt.close(fig)

            # 转 base64 用于页面预览
            with open(chart_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()

            chart_files.append({
                "name": chart_name,
                "title": title,
                "path": f"/reports/{chart_name}",
                "base64": f"data:image/png;base64,{b64}",
            })

        # 生成 HTML 报表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = data.get("name", "数据报表")
        html_content = generate_html_report(report_name, df, chart_files)
        html_path = REPORTS_DIR / f"report_{timestamp}.html"
        html_path.write_text(html_content, encoding="utf-8")

        # 生成 Excel
        xlsx_path = REPORTS_DIR / f"report_{timestamp}.xlsx"
        df.to_excel(xlsx_path, index=False, engine="openpyxl")

        return jsonify({
            "success": True,
            "report_name": report_name,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "charts": [{"title": c["title"], "base64": c["base64"]} for c in chart_files],
            "data_preview": {
                "columns": list(df.columns),
                "rows": df.head(10).values.tolist(),
                "total_rows": int(df.shape[0]),
            },
            "downloads": {
                "html": f"/reports/report_{timestamp}.html",
                "xlsx": f"/reports/report_{timestamp}.xlsx",
            },
        })
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


def set_chinese_font():
    """设置中文字体"""
    try:
        from matplotlib.font_manager import findSystemFonts
        chinese_fonts = ["Noto Sans CJK SC", "WenQuanYi Zen Hei",
                          "WenQuanYi Micro Hei", "Source Han Sans CN",
                          "SimHei", "Microsoft YaHei"]
        available = []
        for f in findSystemFonts():
            for font_name in chinese_fonts:
                if font_name.lower() in f.lower():
                    available.append(font_name)
        if available:
            plt.rcParams["font.sans-serif"] = available + ["DejaVu Sans"]
        else:
            plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    except Exception:
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def generate_html_report(name, df, charts):
    """生成HTML报表"""
    chart_html = "".join(
        f'<div class="chart"><img src="{c["path"]}" alt="{c["title"]}"></div>'
        for c in charts
    )
    table_html = df.head(50).to_html(classes="table", border=0, index=False)

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>{name}</title>
<style>
body {{ font-family: "Microsoft YaHei", sans-serif; margin: 20px; background: #f5f5f5; }}
h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
.meta {{ color: #999; font-size: 12px; margin-bottom: 16px; }}
.chart {{ text-align: center; margin: 20px 0; }}
.chart img {{ max-width: 100%; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.table {{ width: 100%; border-collapse: collapse; font-size: 13px; background: white; }}
.table th {{ background: #4CAF50; color: white; padding: 10px; text-align: left; }}
.table td {{ padding: 8px; border-bottom: 1px solid #eee; }}
.table tr:hover {{ background: #f0f0f0; }}
</style></head><body>
<h1>{name}</h1>
<p class="meta">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 共 {df.shape[0]} 行 × {df.shape[1]} 列</p>
{chart_html}
<h2>数据明细</h2>
{table_html}
</body></html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)