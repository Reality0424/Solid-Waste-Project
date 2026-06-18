# -*- coding: utf-8 -*-
"""Phase 4 共享: 数据 + 模拟"固件版本"分布漂移(用于增量学习/迁移测试)。"""
from pathlib import Path
import numpy as np
import pandas as pd

FEATURES = [
    'pin_flatness_deviation_um', 'solder_pad_oxidation_percent', 'package_scratch_depth_um',
    'warpage_um', 'pin_coplanarity_percent', 'package_size_deviation_percent',
    'vdd_voltage', 'idd_static_ma', 'idd_dynamic_ma', 'voh_voltage', 'vol_voltage',
    'vih_voltage', 'vil_voltage', 'iil_leakage_ua', 'iol_leakage_ua',
    'setup_time_ns', 'hold_time_ns', 'propagation_delay_ns', 'rise_time_ns',
    'fall_time_ns', 'fmax_mhz', 'jtag_scan_pass', 'boundary_scan_pass',
    'functional_test_pass', 'aging_temperature_c', 'aging_voltage_v',
    'aging_frequency_mhz', 'aging_duration_hours',
]
VERSIONS = ['v1', 'v2', 'v3']   # 三个"固件/批次"版本

SCRIPT_DIR = Path(__file__).resolve().parent
PHASE4_DIR = SCRIPT_DIR.parent
REPO_ROOT = PHASE4_DIR.parent


def out(*parts):
    p = PHASE4_DIR / 'outputs'
    for x in parts:
        p = p / x
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_versions(seed=42):
    """把 1000 颗芯片分成 3 个版本批次, 对每个版本施加各自的分布漂移
    (模拟固件/工艺变更), 失效标签机制保持不变。返回 {version: (X, y)} 与标准化统计。"""
    df = pd.read_csv(REPO_ROOT / 'synthetic_data' / 'chip_baseline_data.csv').reset_index(drop=True)
    y = (df['failure_mode'] != 'normal').astype(int).values
    X = df[FEATURES].astype(float).values
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(df))
    splits = np.array_split(idx, 3)

    # 版本特定漂移: 对部分指标做轻微缩放/平移(相对各列 std)
    col_std = X.std(0); col_std[col_std == 0] = 1
    drift_specs = [
        {},  # v1: 原始
        {'fmax_mhz': 0.6, 'setup_time_ns': 0.5, 'vdd_voltage': 0.4},          # v2 漂移
        {'idd_dynamic_ma': 0.7, 'warpage_um': 0.6, 'propagation_delay_ns': 0.5},  # v3 漂移
    ]
    data = {}
    for v, sub, spec in zip(VERSIONS, splits, drift_specs):
        Xv = X[sub].copy()
        for col, k in spec.items():
            j = FEATURES.index(col)
            Xv[:, j] = Xv[:, j] + k * col_std[j]   # 平移 k 个标准差
        data[v] = (Xv.astype(np.float32), y[sub])
    return data, FEATURES
