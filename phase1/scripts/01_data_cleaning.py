#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: 数据清洗脚本
功能: 读取合成数据、清洗、质量评估

设计原则:
- 标准化到 chip_baseline_data.csv（含 failure_status / failure_mode / chip_model 标签），
  以便下游构建有意义的知识图谱（失效模式、关联挖掘）。
- 保留全部样本与标签：失效样本本身就是统计上的"离群点"，因此用 winsorize（分位裁剪）
  抑制极端值，而不是按 IQR 删除整行，避免把失效芯片清洗掉。
- 保留原始量纲（不做 0-1 归一化），由图构建阶段按需做规范判定与相关性分析。
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 二值 / 标签列：不参与 winsorize，原样保留
BINARY_COLUMNS = {
    'failure_status', 'jtag_scan_pass', 'boundary_scan_pass', 'functional_test_pass'
}
LABEL_COLUMNS = {'chip_id', 'production_date', 'chip_model', 'failure_mode'}


class DataCleaner:
    def __init__(self):
        self.raw_data = None
        self.cleaned_data = None
        self.quality_report = {}

    def load_data(self, input_path):
        """加载CSV数据"""
        try:
            self.raw_data = pd.read_csv(input_path)
            logger.info(f"✅ 数据加载成功: {input_path}")
            logger.info(f"   - 行数: {len(self.raw_data)}")
            logger.info(f"   - 列数: {len(self.raw_data.columns)}")
            return True
        except Exception as e:
            logger.error(f"❌ 数据加载失败: {e}")
            return False

    def _feature_columns(self):
        """连续特征列（参与 winsorize），排除二值列与标签列"""
        numeric_cols = self.raw_data.select_dtypes(include=[np.number]).columns
        return [c for c in numeric_cols if c not in BINARY_COLUMNS]

    def handle_missing_values(self):
        """处理缺失值"""
        logger.info("处理缺失值...")
        missing_before = int(self.raw_data.isnull().sum().sum())

        # 删除完全空行
        self.raw_data = self.raw_data.dropna(how='all')

        # 数值列填充中位数
        numeric_cols = self.raw_data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            self.raw_data[col] = self.raw_data[col].fillna(self.raw_data[col].median())

        # 非数值列填充 'Unknown'
        non_numeric_cols = self.raw_data.select_dtypes(exclude=[np.number]).columns
        for col in non_numeric_cols:
            self.raw_data[col] = self.raw_data[col].fillna('Unknown')

        missing_after = int(self.raw_data.isnull().sum().sum())
        logger.info(f"   缺失值: {missing_before} → {missing_after}")
        self.quality_report['missing_values'] = {'before': missing_before, 'after': missing_after}

    def handle_duplicates(self):
        """处理完全重复行"""
        logger.info("处理重复值...")
        before = len(self.raw_data)
        self.raw_data = self.raw_data.drop_duplicates()
        removed = before - len(self.raw_data)
        logger.info(f"   重复行移除: {removed}")
        self.quality_report['duplicates'] = {'removed': int(removed)}

    def winsorize_outliers(self, lower_q=0.01, upper_q=0.99):
        """对连续特征列做分位裁剪（保留全部样本，不删除失效数据）"""
        logger.info(f"分位裁剪极端值 (q=[{lower_q}, {upper_q}])...")
        feature_cols = self._feature_columns()
        total_clipped = 0
        for col in feature_cols:
            lo = self.raw_data[col].quantile(lower_q)
            hi = self.raw_data[col].quantile(upper_q)
            if hi > lo:
                clipped = int(((self.raw_data[col] < lo) | (self.raw_data[col] > hi)).sum())
                self.raw_data[col] = self.raw_data[col].clip(lower=lo, upper=hi)
                total_clipped += clipped
        logger.info(f"   裁剪数值点: {total_clipped} (列数: {len(feature_cols)}, 行数不变)")
        self.quality_report['outliers_clipped'] = int(total_clipped)
        self.quality_report['rows_preserved'] = int(len(self.raw_data))

    def validate_data(self):
        """数据验证"""
        logger.info("数据验证...")
        self.cleaned_data = self.raw_data.copy()
        issues = []

        # 电压/电流列不应为负
        for col in self.cleaned_data.select_dtypes(include=[np.number]).columns:
            lc = col.lower()
            if ('voltage' in lc or 'current' in lc) and (self.cleaned_data[col] < 0).any():
                issues.append(f"列 {col} 包含负值")

        if len(self.cleaned_data) == 0:
            issues.append("清洗后数据为空")

        # 标签完整性检查（failure_status: 1=正常/通过, 0=失效；以 failure_mode!=normal 计失效）
        if 'failure_mode' in self.cleaned_data.columns:
            n_fail = int((self.cleaned_data['failure_mode'] != 'normal').sum())
            n_normal = int(len(self.cleaned_data) - n_fail)
            logger.info(f"   正常样本: {n_normal}, 失效样本: {n_fail}")
            self.quality_report['n_failure_samples'] = n_fail
            self.quality_report['n_normal_samples'] = n_normal

        self.quality_report['validation_issues'] = issues
        self.quality_report['validation_passed'] = len(issues) == 0
        logger.info("✅ 数据验证通过" if not issues else f"⚠️ 验证发现问题: {issues}")

    def save_cleaned_data(self, output_path):
        """保存清洗后的数据"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.cleaned_data.to_csv(output_path, index=False)
        logger.info(f"✅ 清洗数据已保存: {output_path}")
        logger.info(f"   - 最终行数: {len(self.cleaned_data)}, 列数: {len(self.cleaned_data.columns)}")

    def generate_quality_report(self, output_path):
        """生成 Markdown 质量报告"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        s = self.quality_report
        md = "# Phase 1 数据质量报告\n\n"
        md += f"**生成时间**: {datetime.now().isoformat()}\n\n"
        md += "## 📊 数据概览\n\n"
        md += f"- **原始行数**: {self.raw_data.shape[0]}\n"
        md += f"- **清洗后行数**: {self.cleaned_data.shape[0]}（保留全部样本）\n"
        md += f"- **列数**: {self.cleaned_data.shape[1]}\n\n"

        md += "## 🔧 处理过程\n\n"
        if 'missing_values' in s:
            md += f"### 缺失值\n- 处理前: {s['missing_values']['before']}\n- 处理后: {s['missing_values']['after']}\n\n"
        if 'duplicates' in s:
            md += f"### 重复值\n- 移除行数: {s['duplicates']['removed']}\n\n"
        if 'outliers_clipped' in s:
            md += f"### 极端值（分位裁剪，不删行）\n- 裁剪数值点: {s['outliers_clipped']}\n\n"
        if 'n_failure_samples' in s:
            md += f"### 标签\n- 正常样本: {s.get('n_normal_samples', '?')}\n- 失效样本: {s['n_failure_samples']}\n\n"

        md += "## ✅ 验证结果\n\n"
        md += f"- **验证状态**: {'通过' if s.get('validation_passed') else '未通过'}\n"
        for issue in s.get('validation_issues', []):
            md += f"  - {issue}\n"

        md += "\n## 📈 列清单\n\n| 列名 | 数据类型 |\n|------|--------|\n"
        for col, dtype in self.cleaned_data.dtypes.items():
            md += f"| {col} | {dtype} |\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md)
        logger.info(f"✅ 质量报告已生成: {output_path}")

    def clean(self, input_path, output_path, report_path):
        """执行完整清洗流程"""
        logger.info("=" * 60)
        logger.info("Phase 1: 数据清洗")
        logger.info("=" * 60)
        if not self.load_data(input_path):
            return False
        self.handle_missing_values()
        self.handle_duplicates()
        self.winsorize_outliers()
        self.validate_data()
        self.save_cleaned_data(output_path)
        self.generate_quality_report(report_path)
        logger.info("=" * 60)
        logger.info("✅ 数据清洗完成！")
        logger.info("=" * 60)
        return True


def _resolve(p, base, up=False):
    p = Path(p)
    if p.is_absolute():
        return p
    return (base / '..' / p) if up else (base / p)


def main():
    parser = argparse.ArgumentParser(description='Phase 1 数据清洗脚本')
    parser.add_argument('--input_path', type=str,
                        default='../../synthetic_data/chip_baseline_data.csv',
                        help='输入数据路径（默认带 failure 标签的 baseline）')
    parser.add_argument('--output_path', type=str,
                        default='outputs/data/cleaned_data.csv',
                        help='输出数据路径')
    parser.add_argument('--report_path', type=str,
                        default='outputs/reports/data_quality_report.md',
                        help='报告输出路径')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    input_path = _resolve(args.input_path, script_dir)
    output_path = _resolve(args.output_path, script_dir, up=True)
    report_path = _resolve(args.report_path, script_dir, up=True)

    DataCleaner().clean(str(input_path), str(output_path), str(report_path))


if __name__ == '__main__':
    main()
