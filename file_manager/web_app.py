#!/usr/bin/env python3
"""桌面批量文件管理GUI工具 - Web版"""
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file

sys.path.insert(0, str(Path(__file__).parent))
from file_manager_core import FileManager

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", default_dir=str(Path.home()))


@app.route("/api/list")
def list_files():
    """列出目录文件"""
    directory = request.args.get("dir", str(Path.home()))
    p = Path(directory).expanduser()
    if not p.exists() or not p.is_dir():
        return jsonify({"error": "目录不存在"}), 404

    files = []
    dirs = []
    try:
        for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                stat = item.stat()
                info = {
                    "name": item.name,
                    "path": str(item),
                    "size": stat.st_size,
                    "size_str": format_size(stat.st_size),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "ext": item.suffix.lower() if item.is_file() else "",
                }
                if item.is_dir():
                    info["type"] = "dir"
                    dirs.append(info)
                else:
                    info["type"] = "file"
                    files.append(info)
            except (PermissionError, OSError):
                continue
    except PermissionError:
        return jsonify({"error": "无权限访问"}), 403

    return jsonify({
        "current": str(p),
        "parent": str(p.parent) if p.parent != p else None,
        "dirs": dirs,
        "files": files,
        "total_files": len(files),
        "total_dirs": len(dirs),
    })


@app.route("/api/stats", methods=["POST"])
def stats():
    """目录统计"""
    data = request.json or {}
    directory = data.get("dir", str(Path.home()))
    try:
        result = FileManager.get_file_stats(directory)
        return jsonify({
            "success": True,
            "stats": {
                "file_count": result["file_count"],
                "total_size_mb": result["total_size_mb"],
                "ext_count": result["ext_count"],
                "ext_size": result["ext_size"],
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/organize", methods=["POST"])
def organize():
    """分类整理"""
    data = request.json or {}
    directory = data.get("dir")
    if not directory:
        return jsonify({"error": "请指定目录"}), 400
    try:
        stats = FileManager.organize_by_extension(directory)
        return jsonify({
            "success": True,
            "categories": {ext: len(files) for ext, files in stats.items()},
            "total_moved": sum(len(v) for v in stats.values()),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/duplicates", methods=["POST"])
def duplicates():
    """查找重复文件"""
    data = request.json or {}
    directory = data.get("dir")
    if not directory:
        return jsonify({"error": "请指定目录"}), 400
    try:
        dups = FileManager.find_duplicates(directory)
        groups = []
        for h, paths in dups.items():
            groups.append({
                "hash": h[:8] + "...",
                "files": [Path(p).name for p in paths],
                "full_paths": paths,
                "count": len(paths),
            })
        return jsonify({
            "success": True,
            "groups": groups,
            "total_groups": len(dups),
            "total_waste": sum(len(v) - 1 for v in dups.values()),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rename", methods=["POST"])
def rename():
    """批量重命名"""
    data = request.json or {}
    directory = data.get("dir")
    if not directory:
        return jsonify({"error": "请指定目录"}), 400
    try:
        results = FileManager.rename_files(
            directory,
            pattern=data.get("find", ""),
            replace=data.get("replace", ""),
            use_regex=data.get("use_regex", False),
            prefix=data.get("prefix", ""),
            suffix=data.get("suffix", ""),
        )
        return jsonify({
            "success": True,
            "renamed": len(results),
            "changes": [{"old": Path(o).name, "new": Path(n).name} for o, n in results[:20]],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def format_size(size):
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)