#!/usr/bin/env python3
"""
CSV智能数据清洗与合并工具
===========================
功能:
  1. 多CSV文件合并 (支持不同列结构, 智能对齐)
  2. 数据清洗 (去重、空值填充、异常值检测、格式标准化)
  3. 多格式导出 (CSV, Excel, JSON)
  4. 数据质量报告

使用场景:
  - 合并多个来源的销售/用户数据
  - 清洗脏数据, 输出标准化报表
  - 数据迁移前的预处理

技术栈: Python + pandas + openpyxl
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd


class DataCleaner:
    """智能数据清洗与合并引擎"""

    def __init__(self, input_dir: str, output_dir: str = "output"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cleaning_log = []

    def load_csvs(self, pattern: str = "*.csv") -> list:
        """加载目录下所有CSV文件"""
        files = list(self.input_dir.glob(pattern))
        if not files:
            raise FileNotFoundError(f"在 {self.input_dir} 中未找到 {pattern} 文件")
        print(f"📂 找到 {len(files)} 个文件: {[f.name for f in files]}")
        return files

    def merge_files(self, files: list, on: Optional[str] = None) -> pd.DataFrame:
        """智能合并多个CSV文件, 自动对齐列"""
        dfs = []
        for f in files:
            df = pd.read_csv(f, encoding="utf-8-sig")
            dfs.append(df)
            print(f"  ├─ {f.name}: {df.shape[0]} 行 × {df.shape[1]} 列")

        if on and on in dfs[0].columns:
            merged = dfs[0]
            for df in dfs[1:]:
                merged = merged.merge(df, on=on, how="outer", suffixes=("", "_dup"))
            print(f"  └─ 按 '{on}' 列合并完成")
        else:
            merged = pd.concat(dfs, ignore_index=True, sort=False)
            print("  └─ 纵向拼接完成")

        self.cleaning_log.append(f"合并后: {merged.shape[0]} 行 × {merged.shape[1]} 列")
        return merged

    def clean(self, df: pd.DataFrame,
              drop_duplicates: bool = True,
              fill_na_strategy: str = "auto",
              detect_outliers: bool = False) -> pd.DataFrame:
        """数据清洗流水线"""
        before = df.shape[0]

        # 1. 去重
        if drop_duplicates:
            df = df.drop_duplicates()
            after = df.shape[0]
            self.cleaning_log.append(f"去重: 移除 {before - after} 行")

        # 2. 空值处理
        na_before = df.isna().sum().sum()
        if na_before > 0:
            if fill_na_strategy == "auto":
                for col in df.columns:
                    if df[col].dtype in ("int64", "float64"):
                        df[col] = df[col].fillna(df[col].median())
                    else:
                        df[col] = df[col].fillna("未知")
            elif fill_na_strategy == "drop":
                df = df.dropna()
            self.cleaning_log.append(f"空值处理: 填充/移除 {na_before} 个空值")

        # 3. 异常值标记 (数值列)
        if detect_outliers:
            for col in df.select_dtypes(include="number").columns:
                q1, q3 = df[col].quantile([0.25, 0.75])
                iqr = q3 - q1
                lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                outliers = df[(df[col] < lower) | (df[col] > upper)].shape[0]
                if outliers > 0:
                    self.cleaning_log.append(f"异常值[{col}]: {outliers} 个 (范围: {lower:.1f}~{upper:.1f})")

        # 4. 列名标准化
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        return df

    def export(self, df: pd.DataFrame, base_name: str):
        """导出为多种格式"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # CSV
        csv_path = self.output_dir / f"{base_name}_{timestamp}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"✅ CSV: {csv_path}")

        # Excel
        xlsx_path = self.output_dir / f"{base_name}_{timestamp}.xlsx"
        df.to_excel(xlsx_path, index=False, engine="openpyxl")
        print(f"✅ Excel: {xlsx_path}")

        # JSON
        json_path = self.output_dir / f"{base_name}_{timestamp}.json"
        df.to_json(json_path, orient="records", force_ascii=False, indent=2)
        print(f"✅ JSON: {json_path}")

    def report(self, df: pd.DataFrame) -> str:
        """生成数据质量报告"""
        report_lines = [
            "=" * 50,
            "📊 数据质量报告",
            "=" * 50,
            f"总行数:     {df.shape[0]}",
            f"总列数:     {df.shape[1]}",
            f"列名:       {list(df.columns)}",
            f"空值总数:   {df.isna().sum().sum()}",
            f"内存占用:   {df.memory_usage(deep=True).sum() / 1024:.1f} KB",
        ]
        report_lines.append("─" * 50)
        report_lines.append("📋 清洗日志:")
        for log in self.cleaning_log:
            report_lines.append(f"  • {log}")
        report_lines.append("=" * 50)
        return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(
        description="CSV智能数据清洗与合并工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python data_cleaner.py -i ./data -o ./output
  python data_cleaner.py -i ./data --merge-on id --no-dedup
  python data_cleaner.py -i ./data --fill drop --detect-outliers
        """
    )
    parser.add_argument("-i", "--input", required=True, help="CSV文件所在目录")
    parser.add_argument("-o", "--output", default="output", help="输出目录 (默认: output)")
    parser.add_argument("--merge-on", help="按指定列合并 (否则纵向拼接)")
    parser.add_argument("--no-dedup", action="store_true", help="不去重")
    parser.add_argument("--fill", choices=["auto", "drop"], default="auto",
                        help="空值处理策略: auto=自动填充, drop=删除行")
    parser.add_argument("--detect-outliers", action="store_true", help="检测异常值")
    parser.add_argument("--pattern", default="*.csv", help="文件匹配模式 (默认: *.csv)")

    args = parser.parse_args()

    cleaner = DataCleaner(args.input, args.output)
    files = cleaner.load_csvs(args.pattern)
    merged = cleaner.merge_files(files, on=args.merge_on)
    cleaned = cleaner.clean(
        merged,
        drop_duplicates=not args.no_dedup,
        fill_na_strategy=args.fill,
        detect_outliers=args.detect_outliers,
    )
    cleaner.export(cleaned, "cleaned_data")
    print(cleaner.report(cleaned))


if __name__ == "__main__":
    main()