#!/usr/bin/env python3
"""
将运行日志 .txt 渲染为终端风格的 PNG 截图 (最终修复版)
====================================================
"""
import sys
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.patches import FancyBboxPatch


def find_chinese_font():
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return None


CHINESE_FONT_PATH = find_chinese_font()

# 清缓存
cache_dir = Path.home() / ".cache" / "matplotlib"
if cache_dir.exists():
    for f in cache_dir.iterdir():
        if f.name.startswith("fontlist"):
            try:
                f.unlink()
            except OSError:
                pass

if CHINESE_FONT_PATH:
    try:
        fontManager.addfont(CHINESE_FONT_PATH)
    except Exception:
        pass


ANSI_COLORS = {
    "30": "#000000", "31": "#e74c3c", "32": "#2ecc71", "33": "#f1c40f",
    "34": "#3498db", "35": "#9b59b6", "36": "#1abc9c", "37": "#ecf0f1",
    "90": "#7f8c8d", "91": "#ff6b6b", "92": "#5cdb6e", "93": "#ffd93d",
    "94": "#74b9ff", "95": "#d6a2e8", "96": "#5fd4d4", "97": "#ffffff",
}
ANSI_BG = {
    "40": "#000000", "41": "#c0392b", "42": "#27ae60", "43": "#d4ac0d",
    "44": "#2980b9", "45": "#8e44ad", "46": "#16a085", "47": "#bdc3c7",
}
ANSI_RE = re.compile(r"\x1b\[([\d;]*)m")


def parse_ansi(line):
    segments = []
    current_fg = "#ecf0f1"
    current_bg = None
    pos = 0
    for m in ANSI_RE.finditer(line):
        s, e = m.span()
        if s > pos:
            text = line[pos:s]
            if text:
                segments.append((text, current_fg, current_bg))
        codes = m.group(1).split(";") if m.group(1) else ["0"]
        for c in codes:
            if c in ("0", ""):
                current_fg = "#ecf0f1"
                current_bg = None
            elif c == "1":
                current_fg = "#ffffff"
            elif c in ANSI_COLORS:
                current_fg = ANSI_COLORS[c]
            elif c in ANSI_BG:
                current_bg = ANSI_BG[c]
        pos = e
    if pos < len(line):
        text = line[pos:]
        if text:
            segments.append((text, current_fg, current_bg))
    if segments and segments[-1][0].endswith("\n"):
        t, fg, bg = segments[-1]
        segments[-1] = (t.rstrip("\n"), fg, bg)
    return segments


def visual_width(s):
    """计算视觉宽度 (中文字符算2)"""
    return sum(2 if ord(c) > 127 else 1 for c in s)


def render_terminal_screenshot(txt_path, png_path, title=None):
    if CHINESE_FONT_PATH:
        font_prop = FontProperties(fname=CHINESE_FONT_PATH)
    else:
        font_prop = FontProperties(family="monospace")

    txt_file = Path(txt_path)
    png_file = Path(png_path)
    png_file.parent.mkdir(parents=True, exist_ok=True)

    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()

    # 限制最大行数
    max_lines = 40
    if len(lines) > max_lines:
        lines = lines[:max_lines - 1] + ["... (后续内容省略) ..."]

    # 限制每行最大视觉宽度
    max_visual_width = 180
    truncated_lines = []
    for line in lines:
        vw = visual_width(line)
        if vw > max_visual_width:
            cur_len = 0
            new_line = ""
            for c in line:
                cur_len += 2 if ord(c) > 127 else 1
                if cur_len > max_visual_width - 6:
                    new_line += " ..."
                    break
                new_line += c
            truncated_lines.append(new_line)
        else:
            truncated_lines.append(line)
    lines = truncated_lines

    # 找最大视觉宽度
    max_visual = max((visual_width(l) for l in lines), default=80)
    max_visual = max(max_visual, 60)  # 最小宽度

    # === 用真实数据坐标 ===
    # 字符宽度单位 (figure单位)
    char_unit = 0.18
    line_unit = 0.4
    padding = 1.0
    title_unit = 1.5 if title else 0.8

    content_w = max_visual * char_unit + 2 * padding
    content_h = len(lines) * line_unit + 2 * padding
    total_w = content_w
    total_h = content_h + title_unit

    # matplotlib figure 尺寸 (英寸) 1 inch = 72pt
    # 1个figure单位 ≈ 1 inch
    fig_w = max(12, total_w * 0.7)
    fig_h = max(6, total_h * 0.7)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=130)
    ax.set_xlim(0, total_w)
    ax.set_ylim(0, total_h)
    ax.set_aspect("equal")
    ax.axis("off")

    # 终端深色背景
    bg = FancyBboxPatch((0, 0), total_w, total_h, boxstyle="round,pad=0.0",
                          facecolor="#1e1e1e", edgecolor="#444", linewidth=1.5)
    ax.add_patch(bg)

    # 标题栏
    if title:
        title_bg = FancyBboxPatch((0, total_h - title_unit), total_w, title_unit,
                                    boxstyle="round,pad=0.0",
                                    facecolor="#2d2d2d", edgecolor="none")
        ax.add_patch(title_bg)

        # 三色按钮
        for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
            circle = plt.Circle((0.8 + i * 0.6, total_h - title_unit / 2), 0.2,
                                  facecolor=color, edgecolor="none")
            ax.add_patch(circle)

        # 标题文字
        ax.text(total_w / 2, total_h - title_unit / 2, title,
                fontsize=11, color="#cccccc", ha="center", va="center",
                fontproperties=font_prop)

    # 渲染每一行
    text_y = total_h - title_unit - padding
    x_start = padding
    for line in lines:
        segments = parse_ansi(line)
        if not segments:
            text_y -= line_unit
            continue
        x = x_start
        for txt, fg, bg_color in segments:
            vw = visual_width(txt)
            w = vw * char_unit
            if bg_color:
                bbox = FancyBboxPatch((x - 0.1, text_y - line_unit * 0.4),
                                       w + 0.2, line_unit * 0.9,
                                       boxstyle="round,pad=0.0",
                                       facecolor=bg_color, edgecolor="none")
                ax.add_patch(bbox)
            if txt:
                ax.text(x, text_y, txt, fontsize=10, color=fg,
                        va="top", ha="left", fontproperties=font_prop)
            x += w
        text_y -= line_unit

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(png_file, dpi=130, facecolor="#1e1e1e", edgecolor="none",
                 bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print(f"✅ 生成截图: {png_file} ({len(lines)} 行, {fig_w:.1f}x{fig_h:.1f}in)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python txt_to_png.py <input.txt> <output.png> [title]")
        sys.exit(1)
    render_terminal_screenshot(sys.argv[1], sys.argv[2],
                                sys.argv[3] if len(sys.argv) > 3 else None)