#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: 数据清洗脚本
功能: 读取合成数据、清洗、标准化、质量评估
"""

import pandas as pd
import numpy as np
import argparse
import json
from pathlib import Path
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    
    def handle_missing_values(self):
        """处理缺失值"""
        if self.raw_data is None:
            logger.error("没有加载数据")
            return False
        
        logger.info("处理缺失值...")
        missing_before = self.raw_data.isnull().sum().sum()
        
        # 删除完全空行
        self.raw_data = self.raw_data.dropna(how='all')
        
        # 对数值列填充中位数
        numeric_cols = self.raw_data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            median_val = self.raw_data[col].median()
            self.raw_data[col].fillna(median_val, inplace=True)
        
        # 对非数值列填充'Unknown'
        non_numeric_cols = self.raw_data.select_dtypes(exclude=[np.number]).columns
        for col in non_numeric_cols:
            self.raw_data[col].fillna('Unknown', inplace=True)
        
        missing_after = self.raw_data.isnull().sum().sum()
        logger.info(f"   缺失值: {missing_before} → {missing_after}")
        
        self.quality_report['missing_values'] = {
            'before': int(missing_before),
            'after': int(missing_after)
        }
        return True
    
    def handle_duplicates(self):
        """处理重复行"""
        logger.info("处理重复值...")
        duplicates_before = self.raw_data.duplicated().sum()
        
        # 删除完全重复的行
        self.raw_data = self.raw_data.drop_duplicates()
        
        duplicates_after = self.raw_data.duplicated().sum()
        logger.info(f"   重复行: {duplicates_before} → {duplicates_after}")
        
        self.quality_report['duplicates'] = {
            'before': int(duplicates_before),
            'after': int(duplicates_after)
        }
        return True
    
    def normalize_numeric_columns(self):
        """标准化数值列（0-1范围）"""
        logger.info("标准化数值列...")
        numeric_cols = self.raw_data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            min_val = self.raw_data[col].min()
            max_val = self.raw_data[col].max()
            
            if max_val > min_val:
                self.raw_data[col] = (self.raw_data[col] - min_val) / (max_val - min_val)
            else:
                self.raw_data[col] = 0
        
        logger.info(f"   标准化列数: {len(numeric_cols)}")
        return True
    
    def remove_outliers(self, method='iqr'):
        """移除异常值"""
        logger.info(f"移除异常值 (方法: {method})...")
        rows_before = len(self.raw_data)
        
        numeric_cols = self.raw_data.select_dtypes(include=[np.number]).columns
        
        if method == 'iqr':
            for col in numeric_cols:
                Q1 = self.raw_data[col].quantile(0.25)
                Q3 = self.raw_data[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                self.raw_data = self.raw_data[
                    (self.raw_data[col] >= lower_bound) & 
                    (self.raw_data[col] <= upper_bound)
                ]
        
        rows_after = len(self.raw_data)
        logger.info(f"   异常值移除: {rows_before - rows_after} 行")
        
        self.quality_report['outliers_removed'] = rows_before - rows_after
        return True
    
    def validate_data(self):
        """数据验证"""
        logger.info("数据验证...")
        
        self.cleaned_data = self.raw_data.copy()
        
        issues = []
        
        # 检查是否有负值（对于某些应该非负的列）
        numeric_cols = self.cleaned_data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if 'voltage' in col.lower() or 'current' in col.lower():
                if (self.cleaned_data[col] < 0).any():
                    issues.append(f"列 {col} 包含负值")
        
        # 检查数据范围
        if len(self.cleaned_data) > 0:
            logger.info(f"✅ 数据验证通过")
        else:
            issues.append("清洗后数据为空")
        
        self.quality_report['validation_issues'] = issues
        self.quality_report['validation_passed'] = len(issues) == 0
        
        return len(issues) == 0
    
    def save_cleaned_data(self, output_path):
        """保存清洗后的数据"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.cleaned_data.to_csv(output_path, index=False)
            logger.info(f"✅ 清洗数据已保存: {output_path}")
            logger.info(f"   - 最终行数: {len(self.cleaned_data)}")
            logger.info(f"   - 最终列数: {len(self.cleaned_data.columns)}")
            return True
        except Exception as e:
            logger.error(f"❌ 保存数据失败: {e}")
            return False
    
    def generate_quality_report(self, output_path):
        """生成质量报告"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 添加统计信息
            self.quality_report['summary'] = {
                'original_rows': len(self.raw_data),
                'final_rows': len(self.cleaned_data),
                'columns': len(self.cleaned_data.columns),
                'data_types': self.cleaned_data.dtypes.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
            
            # 生成Markdown报告
            report_md = "# Phase 1 数据质量报告\n\n"
            report_md += f"**生成时间**: {self.quality_report['summary']['timestamp']}\n\n"
            
            report_md += "## 📊 数据概览\n\n"
            report_md += f"- **原始行数**: {self.quality_report['summary']['original_rows']}\n"
            report_md += f"- **清洗后行数**: {self.quality_report['summary']['final_rows']}\n"
            report_md += f"- **列数**: {self.quality_report['summary']['columns']}\n\n"
            
            report_md += "## 🔧 数据处理过程\n\n"
            
            if 'missing_values' in self.quality_report:
                mv = self.quality_report['missing_values']
                report_md += f"### 缺失值处理\n"
                report_md += f"- 处理前: {mv['before']} 个\n"
                report_md += f"- 处理后: {mv['after']} 个\n\n"
            
            if 'duplicates' in self.quality_report:
                dups = self.quality_report['duplicates']
                report_md += f"### 重复值处理\n"
                report_md += f"- 处理前: {dups['before']} 行\n"
                report_md += f"- 处理后: {dups['after']} 行\n\n"
            
            if 'outliers_removed' in self.quality_report:
                report_md += f"### 异常值移除\n"
                report_md += f"- 移除行数: {self.quality_report['outliers_removed']}\n\n"
            
            report_md += "## ✅ 验证结果\n\n"
            report_md += f"- **验证状态**: {'通过' if self.quality_report['validation_passed'] else '未通过'}\n"
            if self.quality_report['validation_issues']:
                report_md += f"- **问题**:\n"
                for issue in self.quality_report['validation_issues']:
                    report_md += f"  - {issue}\n"
            
            report_md += "\n## 📈 列统计\n\n"
            report_md += "| 列名 | 数据类型 |\n"
            report_md += "|------|--------|\n"
            for col, dtype in self.quality_report['summary']['data_types'].items():
                report_md += f"| {col} | {dtype} |\n"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_md)
            
            logger.info(f"✅ 质量报告已生成: {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 生成报告失败: {e}")
            return False
    
    def clean(self, input_path, output_path, report_path):
        """执行完整清洗流程"""
        logger.info("=" * 60)
        logger.info("Phase 1: 数据清洗")
        logger.info("=" * 60)
        
        if not self.load_data(input_path):
            return False
        
        self.handle_missing_values()
        self.handle_duplicates()
        self.normalize_numeric_columns()
        self.remove_outliers()
        self.validate_data()
        self.save_cleaned_data(output_path)
        self.generate_quality_report(report_path)
        
        logger.info("=" * 60)
        logger.info("✅ 数据清洗完成！")
        logger.info("=" * 60)
        return True


def main():
    parser = argparse.ArgumentParser(description='Phase 1 数据清洗脚本')
    parser.add_argument('--input_path', type=str,
                       default='../../data/synthetic/chip_baseline_data_extended.csv',
                       help='输入数据路径')
    parser.add_argument('--output_path', type=str,
                       default='outputs/data/cleaned_data.csv',
                       help='输出数据路径')
    parser.add_argument('--report_path', type=str,
                       default='outputs/reports/data_quality_report.md',
                       help='报告输出路径')
    
    args = parser.parse_args()
    
    # 转换为绝对路径
    script_dir = Path(__file__).parent
    if not Path(args.input_path).is_absolute():
        input_path = script_dir / args.input_path
    else:
        input_path = Path(args.input_path)
    
    if not Path(args.output_path).is_absolute():
        output_path = script_dir / '..' / args.output_path
    else:
        output_path = Path(args.output_path)
    
    if not Path(args.report_path).is_absolute():
        report_path = script_dir / '..' / args.report_path
    else:
        report_path = Path(args.report_path)
    
    cleaner = DataCleaner()
    cleaner.clean(str(input_path), str(output_path), str(report_path))


if __name__ == '__main__':
    main()
