#!/usr/bin/env python3
"""
文件管理器 - 命令行演示模式
============================
GUI 模式的演示版本, 用于快速展示核心功能
"""
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))
from file_manager_core import FileManager


def create_demo_files(base_dir: Path):
    """创建演示用的混乱文件结构"""
    print(f"📁 准备演示文件: {base_dir}")

    files_to_create = [
        "IMG_2025-12-01.jpg", "IMG_2025-12-02.jpg", "IMG_2025-12-03.jpg",
        "IMG_2026-01-15.jpg", "IMG_2026-02-20.jpg", "IMG_2026-03-10.jpg",
        "report.pdf", "report_v2.pdf", "report_final.pdf",
        "data.xlsx", "data_backup.xlsx", "data_old.xlsx",
        "notes.txt", "todo.txt", "readme.md",
        "song.mp3", "video.mp4", "image.png",
        "script.py", "config.json", "archive.zip",
        "IMG_2025-11-01.jpg",  # 重复文件
    ]

    for fname in files_to_create:
        fpath = base_dir / fname
        fpath.write_text(f"Demo content for {fname}\n" * 10)

    return base_dir


def demo_organize():
    """演示1: 文件分类整理"""
    print()
    print("=" * 60)
    print("📋 演示1: 按扩展名自动分类整理")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir) / "messy_files"
        base.mkdir()
        create_demo_files(base)

        print(f"\n📂 整理前: {len(list(base.iterdir()))} 个混乱文件")
        print("   文件列表:")
        for f in sorted(base.iterdir())[:8]:
            print(f"     - {f.name}")
        print("     ...")

        print(f"\n🔄 开始按扩展名分类...")
        stats = FileManager.organize_by_extension(str(base))

        print(f"\n✅ 整理完成! 共创建 {len(stats)} 个分类目录:")
        for ext, files in sorted(stats.items()):
            print(f"   📁 {ext:<10}  →  {len(files)} 个文件")


def demo_stats():
    """演示2: 文件统计"""
    print()
    print("=" * 60)
    print("📋 演示2: 文件统计信息")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir) / "stats_demo"
        base.mkdir()
        create_demo_files(base)

        stats = FileManager.get_file_stats(str(base))

        print(f"\n📊 统计结果:")
        print(f"   文件总数: {stats['file_count']}")
        print(f"   总大小:   {stats['total_size_mb']} MB")
        print(f"\n   按扩展名 (Top 10):")
        print(f"   {'扩展名':<15} {'数量':>6} {'大小(MB)':>10}")
        print(f"   {'-' * 35}")

        sorted_exts = sorted(stats["ext_count"].items(),
                              key=lambda x: x[1], reverse=True)
        for ext, count in sorted_exts[:10]:
            size = stats["ext_size"].get(ext, 0)
            print(f"   {ext:<15} {count:>6} {size:>10.4f}")


def demo_duplicates():
    """演示3: 重复文件查找"""
    print()
    print("=" * 60)
    print("📋 演示3: 重复文件查找 (基于MD5)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir) / "dup_demo"
        base.mkdir()

        # 创建文件 + 故意复制一个完全一样的
        (base / "photo_original.jpg").write_bytes(b"same content here " * 100)
        (base / "photo_copy1.jpg").write_bytes(b"same content here " * 100)
        (base / "photo_copy2.jpg").write_bytes(b"same content here " * 100)
        (base / "document.txt").write_text("unique content 1")
        (base / "report.pdf").write_text("unique content 2")
        (base / "data.xlsx").write_bytes(b"another duplicate " * 50)
        (base / "data_backup.xlsx").write_bytes(b"another duplicate " * 50)

        print(f"\n🔍 扫描目录: {base}")
        duplicates = FileManager.find_duplicates(str(base))

        if duplicates:
            print(f"\n⚠️  发现 {len(duplicates)} 组重复文件:")
            for i, (hash_val, paths) in enumerate(duplicates.items(), 1):
                print(f"\n   组 {i} (MD5: {hash_val[:8]}...):")
                for p in paths:
                    print(f"     - {Path(p).name}")
            total_waste = sum(len(v) - 1 for v in duplicates.values())
            print(f"\n💡 建议: 保留每组 1 个, 可清理 {total_waste} 个重复文件")
        else:
            print("   ✅ 未发现重复文件")


def main():
    print()
    print("🗂️ " * 30)
    print("    批量文件管理器 - 功能演示")
    print("🗂️ " * 30)

    demo_organize()
    demo_stats()
    demo_duplicates()

    print()
    print("=" * 60)
    print("✅ 演示完成!")
    print("💡 启动 GUI 界面: python file_manager.py")
    print("=" * 60)


if __name__ == "__main__":
    main()