#!/usr/bin/env python3
"""
CSV智能数据清洗与合并工具 - Web版
"""
import uuid
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file, session

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent))
from data_cleaner import DataCleaner

app = Flask(__name__, static_folder="sample_data", static_url_path="/sample_data")
app.secret_key = "data-cleaner-secret"

UPLOAD_DIR = Path(__file__).parent / "uploads"
OUTPUT_DIR = Path(__file__).parent / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    """上传CSV文件"""
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "未上传文件"}), 400

    session_id = session.get("session_id") or str(uuid.uuid4())[:8]
    session["session_id"] = session_id
    work_dir = UPLOAD_DIR / session_id
    work_dir.mkdir(exist_ok=True)

    saved = []
    for f in files:
        if f and f.filename and f.filename.endswith(".csv"):
            save_path = work_dir / f.filename
            f.save(save_path)
            saved.append(f.filename)

    return jsonify({
        "session_id": session_id,
        "files": saved,
        "count": len(saved),
    })


@app.route("/api/preview", methods=["POST"])
def preview():
    """预览上传的文件内容"""
    data = request.json or {}
    session_id = data.get("session_id") or session.get("session_id")
    if not session_id:
        return jsonify({"error": "无会话"}), 400

    work_dir = UPLOAD_DIR / session_id
    if not work_dir.exists():
        return jsonify({"error": "无文件"}), 404

    previews = []
    for f in sorted(work_dir.glob("*.csv")):
        try:
            df = pd.read_csv(f, encoding="utf-8-sig")
            previews.append({
                "name": f.name,
                "rows": int(df.shape[0]),
                "cols": int(df.shape[1]),
                "columns": list(df.columns),
                "head": df.head(3).fillna("").to_dict(orient="records"),
            })
        except Exception as e:
            previews.append({"name": f.name, "error": str(e)})

    return jsonify({"files": previews})


@app.route("/api/clean", methods=["POST"])
def clean():
    """执行清洗"""
    data = request.json or {}
    session_id = data.get("session_id") or session.get("session_id")
    if not session_id:
        return jsonify({"error": "无会话"}), 400

    work_dir = UPLOAD_DIR / session_id
    files = list(work_dir.glob("*.csv"))
    if not files:
        return jsonify({"error": "无文件"}), 400

    cleaner = DataCleaner(str(work_dir), str(OUTPUT_DIR))
    try:
        merged = cleaner.merge_files(files, on=data.get("merge_on") or None)
        cleaned = cleaner.clean(
            merged,
            drop_duplicates=data.get("dedup", True),
            fill_na_strategy=data.get("fill_na", "auto"),
            detect_outliers=data.get("detect_outliers", False),
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_base = f"cleaned_{session_id}_{timestamp}"

        # 保存多种格式
        csv_path = OUTPUT_DIR / f"{out_base}.csv"
        xlsx_path = OUTPUT_DIR / f"{out_base}.xlsx"
        json_path = OUTPUT_DIR / f"{out_base}.json"

        cleaned.to_csv(csv_path, index=False, encoding="utf-8-sig")
        cleaned.to_excel(xlsx_path, index=False, engine="openpyxl")
        cleaned.to_json(json_path, orient="records", force_ascii=False, indent=2)

        # 返回预览
        preview_data = cleaned.head(20).fillna("").to_dict(orient="records")
        report = cleaner.report(cleaned)

        return jsonify({
            "success": True,
            "rows": int(cleaned.shape[0]),
            "cols": int(cleaned.shape[1]),
            "columns": list(cleaned.columns),
            "preview": preview_data,
            "report": report,
            "files": {
                "csv": f"/api/download/{out_base}.csv",
                "xlsx": f"/api/download/{out_base}.xlsx",
                "json": f"/api/download/{out_base}.json",
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/<filename>")
def download(filename):
    """下载结果文件"""
    path = OUTPUT_DIR / filename
    if not path.exists():
        return jsonify({"error": "文件不存在"}), 404
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)