# -*- coding: utf-8 -*-
"""Phase 2 共享工具: 数据加载、指标清单、路径解析"""
from pathlib import Path
import numpy as np
import pandas as pd

# 28 项检测指标(物理6 + DC9 + AC6 + 功能3 + 老化4), 与需求文档一致
FEATURES = [
    # 物理 (6)
    'pin_flatness_deviation_um', 'solder_pad_oxidation_percent', 'package_scratch_depth_um',
    'warpage_um', 'pin_coplanarity_percent', 'package_size_deviation_percent',
    # 电气 DC (9)
    'vdd_voltage', 'idd_static_ma', 'idd_dynamic_ma', 'voh_voltage', 'vol_voltage',
    'vih_voltage', 'vil_voltage', 'iil_leakage_ua', 'iol_leakage_ua',
    # 电气 AC (6)
    'setup_time_ns', 'hold_time_ns', 'propagation_delay_ns', 'rise_time_ns',
    'fall_time_ns', 'fmax_mhz',
    # 功能 (3)
    'jtag_scan_pass', 'boundary_scan_pass', 'functional_test_pass',
    # 老化条件 (4)
    'aging_temperature_c', 'aging_voltage_v', 'aging_frequency_mhz', 'aging_duration_hours',
]

SCRIPT_DIR = Path(__file__).resolve().parent
PHASE2_DIR = SCRIPT_DIR.parent
REPO_ROOT = PHASE2_DIR.parent


def baseline_path():
    return REPO_ROOT / 'synthetic_data' / 'chip_baseline_data.csv'


def out(*parts):
    p = PHASE2_DIR / 'outputs'
    for x in parts:
        p = p / x
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_dataset():
    """返回 (X[df, 28列], y[0/1 失效], chip_ids, failure_mode)"""
    df = pd.read_csv(baseline_path())
    X = df[FEATURES].astype(float).copy()
    y = (df['failure_mode'] != 'normal').astype(int).values
    return X, y, df['chip_id'].values, df['failure_mode'].values


def stratified_masks(y, seed=42, val=0.15, test=0.2):
    """分层划分 train/val/test, 返回布尔掩码"""
    rng = np.random.default_rng(seed)
    n = len(y)
    train = np.zeros(n, bool); valm = np.zeros(n, bool); testm = np.zeros(n, bool)
    for cls in np.unique(y):
        idx = np.where(y == cls)[0]
        rng.shuffle(idx)
        nt = int(len(idx) * test); nv = int(len(idx) * val)
        testm[idx[:nt]] = True
        valm[idx[nt:nt + nv]] = True
        train[idx[nt + nv:]] = True
    return train, valm, testm
