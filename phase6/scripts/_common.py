# -*- coding: utf-8 -*-
"""Phase 6 共享: 数据、特征、路径、加载 Phase 5 适配性头与修复库。"""
from pathlib import Path
import json, pickle
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
SCENARIOS = ['high_frequency_computing', 'power_efficient_device',
             'high_reliability_critical', 'consumer_electronics']

SCRIPT_DIR = Path(__file__).resolve().parent
PHASE6_DIR = SCRIPT_DIR.parent
REPO_ROOT = PHASE6_DIR.parent
PHASE5_OUT = REPO_ROOT / 'phase5' / 'outputs'


def out(*parts):
    p = PHASE6_DIR / 'outputs'
    for x in parts:
        p = p / x
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_base():
    df = pd.read_csv(REPO_ROOT / 'synthetic_data' / 'chip_baseline_data.csv').reset_index(drop=True)
    y = (df['failure_mode'] != 'normal').astype(int).values
    return df, y


def load_repair_mapping():
    with open(PHASE5_OUT / 'data' / 'repair_mapping.json', encoding='utf-8') as f:
        return json.load(f)


def load_compat_heads():
    heads = {}
    for s in SCENARIOS:
        with open(PHASE5_OUT / 'models' / f'compat_head_{s}.pkl', 'rb') as f:
            heads[s] = pickle.load(f)
    return heads


def ground_truth_sort(df, y, repair):
    """真值三分类: reuse(非失效) / repair(失效且可修) / reject(失效且不可修)。"""
    labels = []
    for i in range(len(df)):
        if y[i] == 0:
            labels.append('reuse')
        else:
            mode = df.iloc[i]['failure_mode']
            sr = repair.get(mode, {}).get('success_rate', 0)
            labels.append('repair' if sr and sr > 0 else 'reject')
    return np.array(labels)
