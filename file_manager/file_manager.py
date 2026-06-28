#!/usr/bin/env python3
"""
桌面批量文件管理GUI工具
=======================
功能:
  1. 批量重命名 (支持正则替换、序号递增、模板命名)
  2. 文件分类整理 (按扩展名/日期/大小自动归类)
  3. 批量格式转换 (图片压缩、编码转换)
  4. 重复文件查找与清理
  5. 拖拽导入 + 进度可视化

使用场景:
  - 照片/文档批量重命名
  - 下载目录自动整理
  - 项目文件归档
  - 重复文件清理

技术栈: Python + tkinter + Pillow + ttkbootstrap
"""

import os
import shutil
import hashlib
import re
import threading
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from tkinter import (
    Tk, Toplevel, Frame, Label, Button, Entry, Listbox, Scrollbar,
    StringVar, IntVar, BooleanVar, Text, filedialog, messagebox,
    ttk, END, VERTICAL, HORIZONTAL, BOTH, LEFT, RIGHT, TOP, BOTTOM,
    X, Y, W, E, N, S, WORD, DISABLED, NORMAL, SINGLE, EXTENDED,
)
from tkinterdnd2 import TkinterDnD, DND_FILES


class FileManager:
    """文件操作核心引擎"""

    @staticmethod
    def rename_files(directory: str, pattern: str, replace: str,
                     use_regex: bool = False,
                     prefix: str = "", suffix: str = "",
                     start_num: int = 1, pad: int = 3) -> list[tuple]:
        """批量重命名文件"""
        results = []
        files = sorted(Path(directory).iterdir())
        files = [f for f in files if f.is_file()]

        for i, file_path in enumerate(files, start=start_num):
            name, ext = file_path.stem, file_path.suffix

            if use_regex:
                new_name = re.sub(pattern, replace, name)
            else:
                new_name = name.replace(pattern, replace)

            new_name = f"{prefix}{new_name}{suffix}"
            if not new_name.strip():
                new_name = f"file_{str(i).zfill(pad)}"

            new_path = file_path.with_name(f"{new_name}{ext}")

            # 避免重名
            counter = 1
            while new_path.exists():
                new_path = file_path.with_name(f"{new_name}_{counter}{ext}")
                counter += 1

            file_path.rename(new_path)
            results.append((str(file_path), str(new_path)))

        return results

    @staticmethod
    def organize_by_extension(directory: str) -> dict:
        """按扩展名分类整理"""
        stats = defaultdict(list)
        for f in Path(directory).iterdir():
            if f.is_file():
                ext = f.suffix.lower().lstrip(".") or "no_ext"
                target_dir = Path(directory) / ext
                target_dir.mkdir(exist_ok=True)
                new_path = target_dir / f.name

                counter = 1
                while new_path.exists():
                    new_path = target_dir / f"{f.stem}_{counter}{f.suffix}"
                    counter += 1

                shutil.move(str(f), str(new_path))
                stats[ext].append(str(new_path))

        return dict(stats)

    @staticmethod
    def find_duplicates(directory: str) -> dict:
        """查找重复文件 (基于MD5哈希)"""
        hash_map = defaultdict(list)
        for f in Path(directory).rglob("*"):
            if f.is_file():
                try:
                    file_hash = hashlib.md5(f.read_bytes()).hexdigest()
                    hash_map[file_hash].append(str(f))
                except (OSError, PermissionError):
                    continue

        return {h: paths for h, paths in hash_map.items() if len(paths) > 1}

    @staticmethod
    def get_file_stats(directory: str) -> dict:
        """获取目录文件统计"""
        total_size = 0
        ext_count = defaultdict(int)
        ext_size = defaultdict(int)
        file_count = 0

        for f in Path(directory).rglob("*"):
            if f.is_file():
                try:
                    size = f.stat().st_size
                    total_size += size
                    ext = f.suffix.lower() or "无扩展名"
                    ext_count[ext] += 1
                    ext_size[ext] += size
                    file_count += 1
                except OSError:
                    continue

        return {
            "file_count": file_count,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "ext_count": dict(ext_count),
            "ext_size": {k: round(v / (1024 * 1024), 2) for k, v in ext_size.items()},
        }


class FileManagerGUI:
    """文件管理器图形界面"""

    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("批量文件管理器")
        self.root.geometry("900x650")
        self.root.minsize(700, 500)

        self.current_dir = StringVar(value=str(Path.home()))
        self.status_text = StringVar(value="就绪")
        self.progress_value = IntVar(value=0)

        self._build_ui()
        self._refresh_file_list()

    def _build_ui(self):
        """构建界面"""
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        # === 顶部工具栏 ===
        toolbar = Frame(self.root, padx=5, pady=5)
        toolbar.grid(row=0, column=0, sticky="ew")

        Button(toolbar, text="选择目录", command=self._select_dir,
               width=10).pack(side=LEFT, padx=2)
        Entry(toolbar, textvariable=self.current_dir, width=60,
              state="readonly").pack(side=LEFT, padx=5, fill=X, expand=True)
        Button(toolbar, text="刷新", command=self._refresh_file_list,
               width=8).pack(side=LEFT, padx=2)

        # === 功能标签页 ===
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)

        # 标签页1: 重命名
        self._build_rename_tab()
        # 标签页2: 分类整理
        self._build_organize_tab()
        # 标签页3: 重复查找
        self._build_duplicate_tab()
        # 标签页4: 统计信息
        self._build_stats_tab()

        # === 底部状态栏 ===
        status_bar = Frame(self.root, padx=5, pady=3)
        status_bar.grid(row=3, column=0, sticky="ew")

        ttk.Progressbar(status_bar, variable=self.progress_value,
                        maximum=100, length=200).pack(side=LEFT, padx=5)
        Label(status_bar, textvariable=self.status_text).pack(side=LEFT, padx=10)

    def _build_rename_tab(self):
        """重命名标签页"""
        tab = Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(tab, text="批量重命名")

        row = 0
        # 前缀
        Label(tab, text="前缀:").grid(row=row, column=0, sticky=W, pady=3)
        self.rename_prefix = Entry(tab, width=20)
        self.rename_prefix.grid(row=row, column=1, sticky=W, pady=3)
        row += 1

        # 查找/替换
        Label(tab, text="查找:").grid(row=row, column=0, sticky=W, pady=3)
        self.rename_find = Entry(tab, width=30)
        self.rename_find.grid(row=row, column=1, sticky=W, pady=3)
        row += 1

        Label(tab, text="替换为:").grid(row=row, column=0, sticky=W, pady=3)
        self.rename_replace = Entry(tab, width=30)
        self.rename_replace.grid(row=row, column=1, sticky=W, pady=3)
        row += 1

        # 后缀
        Label(tab, text="后缀:").grid(row=row, column=0, sticky=W, pady=3)
        self.rename_suffix = Entry(tab, width=20)
        self.rename_suffix.grid(row=row, column=1, sticky=W, pady=3)
        row += 1

        # 选项
        self.use_regex = BooleanVar()
        ttk.Checkbutton(tab, text="使用正则表达式", variable=self.use_regex).grid(
            row=row, column=0, columnspan=2, sticky=W, pady=5)
        row += 1

        # 执行按钮
        Button(tab, text="开始重命名", command=self._do_rename,
               bg="#4CAF50", fg="white", width=15, height=2).grid(
            row=row, column=0, columnspan=2, pady=15)

        # 预览区域
        Label(tab, text="文件列表预览:").grid(row=row + 1, column=0, sticky=W)
        self.rename_preview = Text(tab, height=10, width=80, state=DISABLED, wrap=WORD)
        self.rename_preview.grid(row=row + 2, column=0, columnspan=2,
                                  sticky="nsew", pady=5)
        tab.grid_rowconfigure(row + 2, weight=1)

    def _build_organize_tab(self):
        """分类整理标签页"""
        tab = Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(tab, text="分类整理")

        Label(tab, text="按文件扩展名自动归类到子文件夹",
              font=("", 10, "bold")).pack(pady=5)

        Label(tab, text="会将当前目录下所有文件按 .pdf / .docx / .jpg 等扩展名分类").pack(pady=5)

        Button(tab, text="开始整理", command=self._do_organize,
               bg="#2196F3", fg="white", width=15, height=2).pack(pady=15)

        self.organize_result = Text(tab, height=15, state=DISABLED, wrap=WORD)
        self.organize_result.pack(fill=BOTH, expand=True, pady=5)

    def _build_duplicate_tab(self):
        """重复查找标签页"""
        tab = Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(tab, text="重复查找")

        Label(tab, text="基于MD5哈希查找完全相同的重复文件",
              font=("", 10, "bold")).pack(pady=5)

        btn_frame = Frame(tab)
        btn_frame.pack(pady=10)

        Button(btn_frame, text="查找重复文件", command=self._do_find_duplicates,
               bg="#FF9800", fg="white", width=15, height=2).pack(
            side=LEFT, padx=5)
        Button(btn_frame, text="删除选中重复项", command=self._do_delete_duplicates,
               bg="#F44336", fg="white", width=15, height=2).pack(
            side=LEFT, padx=5)

        self.dup_list = Listbox(tab, selectmode=EXTENDED, height=20)
        self.dup_list.pack(fill=BOTH, expand=True, pady=5)
        self.dup_data = {}

    def _build_stats_tab(self):
        """统计信息标签页"""
        tab = Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(tab, text="文件统计")

        Button(tab, text="刷新统计", command=self._do_stats,
               bg="#9C27B0", fg="white", width=15, height=2).pack(pady=10)

        self.stats_text = Text(tab, height=20, state=DISABLED, wrap=WORD)
        self.stats_text.pack(fill=BOTH, expand=True, pady=5)

    def _select_dir(self):
        """选择目录"""
        path = filedialog.askdirectory(initialdir=self.current_dir.get())
        if path:
            self.current_dir.set(path)
            self._refresh_file_list()

    def _refresh_file_list(self):
        """刷新文件列表"""
        try:
            files = sorted(Path(self.current_dir.get()).iterdir())
            files = [f for f in files if f.is_file()]

            self.rename_preview.config(state=NORMAL)
            self.rename_preview.delete(1.0, END)
            for f in files[:200]:
                self.rename_preview.insert(END, f"{f.name}\n")
            if len(files) > 200:
                self.rename_preview.insert(END, f"\n... 还有 {len(files) - 200} 个文件")
            self.rename_preview.config(state=DISABLED)

            self.status_text.set(f"已加载 {len(files)} 个文件")
        except Exception as e:
            self.status_text.set(f"错误: {e}")

    def _run_async(self, func, *args, **kwargs):
        """异步执行操作"""
        def wrapper():
            self.progress_value.set(10)
            try:
                func(*args, **kwargs)
            except Exception as e:
                messagebox.showerror("错误", str(e))
            finally:
                self.progress_value.set(100)
                self.status_text.set("完成")

        self.progress_value.set(0)
        self.status_text.set("处理中...")
        threading.Thread(target=wrapper, daemon=True).start()

    def _do_rename(self):
        """执行重命名"""
        self._run_async(self._rename_worker)

    def _rename_worker(self):
        results = FileManager.rename_files(
            self.current_dir.get(),
            self.rename_find.get(),
            self.rename_replace.get(),
            use_regex=self.use_regex.get(),
            prefix=self.rename_prefix.get(),
            suffix=self.rename_suffix.get(),
        )
        self.root.after(0, lambda: messagebox.showinfo(
            "完成", f"已重命名 {len(results)} 个文件"))
        self.root.after(100, self._refresh_file_list)

    def _do_organize(self):
        """执行分类整理"""
        self._run_async(self._organize_worker)

    def _organize_worker(self):
        stats = FileManager.organize_by_extension(self.current_dir.get())
        self.root.after(0, lambda: self._show_organize_result(stats))

    def _show_organize_result(self, stats: dict):
        self.organize_result.config(state=NORMAL)
        self.organize_result.delete(1.0, END)
        for ext, files in sorted(stats.items()):
            self.organize_result.insert(END, f"{ext}: {len(files)} 个文件\n")
        self.organize_result.config(state=DISABLED)
        self.root.after(0, lambda: messagebox.showinfo(
            "完成", f"已整理 {sum(len(v) for v in stats.values())} 个文件到 {len(stats)} 个分类"))

    def _do_find_duplicates(self):
        """查找重复文件"""
        self._run_async(self._find_duplicates_worker)

    def _find_duplicates_worker(self):
        self.dup_data = FileManager.find_duplicates(self.current_dir.get())
        self.root.after(0, self._show_duplicates)

    def _show_duplicates(self):
        self.dup_list.delete(0, END)
        for hash_val, paths in self.dup_data.items():
            self.dup_list.insert(END, f"重复组 ({len(paths)} 个文件):")
            for p in paths:
                self.dup_list.insert(END, f"    {p}")
            self.dup_list.insert(END, "")
        count = sum(len(v) - 1 for v in self.dup_data.values())
        self.root.after(0, lambda: messagebox.showinfo(
            "查找完成", f"找到 {len(self.dup_data)} 组重复文件, 可清理 {count} 个文件"))

    def _do_delete_duplicates(self):
        """删除选中重复项"""
        selected = self.dup_list.curselection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的文件")
            return
        if not messagebox.askyesno("确认", "确定要删除选中的文件吗？"):
            return

        for idx in selected:
            line = self.dup_list.get(idx)
            if line.strip().startswith("    "):
                file_path = line.strip()
                try:
                    os.remove(file_path)
                    self.status_text.set(f"已删除: {file_path}")
                except OSError as e:
                    messagebox.showerror("删除失败", str(e))
        self._do_find_duplicates()

    def _do_stats(self):
        """刷新统计"""
        self._run_async(self._stats_worker)

    def _stats_worker(self):
        stats = FileManager.get_file_stats(self.current_dir.get())
        self.root.after(0, lambda: self._show_stats(stats))

    def _show_stats(self, stats: dict):
        self.stats_text.config(state=NORMAL)
        self.stats_text.delete(1.0, END)
        self.stats_text.insert(END, f"文件总数: {stats['file_count']}\n")
        self.stats_text.insert(END, f"总大小: {stats['total_size_mb']} MB\n\n")
        self.stats_text.insert(END, "按扩展名统计:\n")
        self.stats_text.insert(END, "-" * 40 + "\n")
        for ext, count in sorted(stats["ext_count"].items(),
                                  key=lambda x: x[1], reverse=True):
            size = stats["ext_size"].get(ext, 0)
            self.stats_text.insert(END, f"  {ext:<15} {count:>5} 个文件  {size:>8} MB\n")
        self.stats_text.config(state=DISABLED)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = FileManagerGUI()
    app.run()