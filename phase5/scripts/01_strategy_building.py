#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5 / 任务5.1: 功能修复策略映射库 + 适配性数据派生

- 加载修复策略库(failure_mode -> 修复方法/成功率/成本), 计算修复覆盖率。
- 派生有意义、可学习的适配性数据(见 _common.derive_compatibility)并落盘, 供 5.2/5.3 与 Phase 6 使用。

产出: outputs/data/repair_mapping.json, outputs/data/compatibility_dataset.csv
"""
import json
import numpy as np
import _common as C

FAILURE_MODES = ['physical_damage', 'noise_margin_insufficient', 'thermal_accumulation', 'multi_param_combined']


def main():
    print("=" * 60); print("Phase 5 / 5.1 修复策略库 + 适配性数据"); print("=" * 60)
    lib = C.load_repair_library()
    covered = [m for m in FAILURE_MODES if m in lib]
    coverage = len(covered) / len(FAILURE_MODES)
    print(f"修复策略覆盖: {len(covered)}/{len(FAILURE_MODES)} 失效模式 = {coverage:.0%}")
    for m in FAILURE_MODES:
        s = lib.get(m, {})
        print(f"  {m:28} 成功率 {s.get('success_rate','-')}, 成本 {s.get('cost_yuan','-')}元, "
              f"方法: {s.get('repair_method','-')}")

    mapping = {m: {'repair_method': lib[m]['repair_method'], 'success_rate': lib[m]['success_rate'],
                   'cost_yuan': lib[m]['cost_yuan'], 'covered': True} for m in covered}
    mapping['_coverage'] = coverage
    with open(C.out('data', 'repair_mapping.json'), 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    comp, base, y = C.derive_compatibility()
    comp.to_csv(C.out('data', 'compatibility_dataset.csv'), index=False)
    print(f"\n适配性数据集: {len(comp)} 行 (1000芯片 × 4场景)")
    print("等级分布:", comp['compatibility_level'].value_counts().to_dict())
    print(f"✅ 修复覆盖率 {coverage:.0%} (≥92%: {coverage>=0.92}) | 已保存 repair_mapping.json, compatibility_dataset.csv")


if __name__ == '__main__':
    main()
