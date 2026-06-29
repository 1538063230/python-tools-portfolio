#!/usr/bin/env python3
"""
生成 GUI 界面的示意图 (用于作品集展示)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.font_manager as fm


def draw_gui_mockup(output_path: str):
    """绘制 GUI 界面示意图"""
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.axis("off")

    # 字体
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
    except Exception:
        pass
    plt.rcParams["axes.unicode_minus"] = False

    # 窗口背景
    bg = FancyBboxPatch((1, 1), 98, 68, boxstyle="round,pad=0.5",
                          facecolor="#f5f5f5", edgecolor="#888", linewidth=1.5)
    ax.add_patch(bg)

    # 标题栏
    title = FancyBboxPatch((1, 64), 98, 5, boxstyle="round,pad=0.2",
                             facecolor="#4CAF50", edgecolor="none")
    ax.add_patch(title)
    ax.text(3, 66.5, "批量文件管理器", fontsize=14, color="white", weight="bold")

    # 顶部工具栏
    toolbar = FancyBboxPatch((1, 58), 98, 5, boxstyle="round,pad=0.1",
                               facecolor="#e0e0e0", edgecolor="none")
    ax.add_patch(toolbar)

    # 按钮
    btn1 = FancyBboxPatch((3, 59.5), 10, 2.5, boxstyle="round,pad=0.1",
                            facecolor="#2196F3", edgecolor="none")
    ax.add_patch(btn1)
    ax.text(8, 60.7, "选择目录", fontsize=10, color="white", ha="center")

    # 路径输入框
    input_bg = FancyBboxPatch((15, 59.5), 60, 2.5, boxstyle="round,pad=0.1",
                                facecolor="white", edgecolor="#bbb")
    ax.add_patch(input_bg)
    ax.text(17, 60.7, "/home/user/Downloads", fontsize=10, color="#333")

    btn2 = FancyBboxPatch((78, 59.5), 10, 2.5, boxstyle="round,pad=0.1",
                            facecolor="#2196F3", edgecolor="none")
    ax.add_patch(btn2)
    ax.text(83, 60.7, "刷新", fontsize=10, color="white", ha="center")

    # 标签页
    tab_x = 5
    tabs = [("批量重命名", "#4CAF50", "white"),
            ("分类整理", "#e0e0e0", "#666"),
            ("重复查找", "#e0e0e0", "#666"),
            ("文件统计", "#e0e0e0", "#666")]

    for i, (name, color, txt_color) in enumerate(tabs):
        tab = FancyBboxPatch((tab_x, 53), 14, 3, boxstyle="round,pad=0.1",
                              facecolor=color, edgecolor="none")
        ax.add_patch(tab)
        ax.text(tab_x + 7, 54.5, name, fontsize=10, color=txt_color, ha="center")
        tab_x += 14

    # 重命名面板内容
    panel = FancyBboxPatch((3, 5), 94, 47, boxstyle="round,pad=0.3",
                             facecolor="white", edgecolor="#ddd", linewidth=1)
    ax.add_patch(panel)

    # 表单字段
    fields = [
        ("前缀:", "", 0),
        ("查找:", "IMG_", 8),
        ("替换为:", "照片_", 16),
        ("后缀:", "", 24),
    ]
    y = 46
    for label, val, dy in fields:
        ax.text(7, y, label, fontsize=11, color="#555", weight="bold")
        if val or dy:
            inp = FancyBboxPatch((18, y - 1), 30, 2.5, boxstyle="round,pad=0.1",
                                  facecolor="white", edgecolor="#ccc")
            ax.add_patch(inp)
            if val:
                ax.text(20, y + 0.2, val, fontsize=10, color="#333")
        y -= 4

    # 复选框
    ax.add_patch(plt.Rectangle((7, 30), 1.5, 1.5, facecolor="#4CAF50", edgecolor="none"))
    ax.text(7.7, 30.7, "✓", fontsize=10, color="white", ha="center", va="center")
    ax.text(11, 30.5, "使用正则表达式", fontsize=10, color="#555")

    # 开始按钮
    start_btn = FancyBboxPatch((7, 23), 18, 4, boxstyle="round,pad=0.2",
                                 facecolor="#4CAF50", edgecolor="none")
    ax.add_patch(start_btn)
    ax.text(16, 25, "开始重命名", fontsize=12, color="white", ha="center", weight="bold")

    # 预览列表
    ax.text(7, 19, "文件列表预览:", fontsize=10, color="#666", weight="bold")
    list_bg = FancyBboxPatch((7, 7), 86, 11, boxstyle="round,pad=0.1",
                               facecolor="#fafafa", edgecolor="#ddd")
    ax.add_patch(list_bg)

    files = [
        "IMG_2025-12-01.jpg",
        "IMG_2025-12-02.jpg",
        "IMG_2025-12-03.jpg",
        "IMG_2026-01-15.jpg",
        "IMG_2026-02-20.jpg",
        "IMG_2026-03-10.jpg",
    ]
    for i, fname in enumerate(files):
        col = i % 2
        row = i // 2
        ax.text(10 + col * 43, 15 - row * 1.5, fname, fontsize=9, color="#444")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"✅ 生成截图: {output_path}")


if __name__ == "__main__":
    import sys
    output = sys.argv[1] if len(sys.argv) > 1 else "screenshots/gui_mockup.png"
    draw_gui_mockup(output)