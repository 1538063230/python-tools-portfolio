"""
文件操作核心引擎 - 可独立导入, 不依赖 GUI 库
"""
import re
import shutil
import hashlib
from pathlib import Path
from collections import defaultdict


class FileManager:
    """文件操作核心引擎"""

    @staticmethod
    def rename_files(directory, pattern, replace,
                     use_regex=False, prefix="", suffix="",
                     start_num=1, pad=3):
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
            counter = 1
            while new_path.exists():
                new_path = file_path.with_name(f"{new_name}_{counter}{ext}")
                counter += 1

            file_path.rename(new_path)
            results.append((str(file_path), str(new_path)))

        return results

    @staticmethod
    def organize_by_extension(directory):
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
    def find_duplicates(directory):
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
    def get_file_stats(directory):
        total_size = 0
        ext_count = defaultdict(int)
        ext_size = defaultdict(int)
        file_count = 0
        for f in Path(directory).rglob("*"):
            if f.is_file():
                try:
                    size = f.stat().st_size
                    total_size += size
                    ext = f.suffix.lower() or "no_ext"
                    ext_count[ext] += 1
                    ext_size[ext] += size
                    file_count += 1
                except OSError:
                    continue
        return {
            "file_count": file_count,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 4),
            "ext_count": dict(ext_count),
            "ext_size": {k: round(v / (1024 * 1024), 4) for k, v in ext_size.items()},
        }