# -*- coding: utf-8 -*-
"""Phase 3 共享: 数据、28 指标、检测时间成本模型、掩码分类器(可从任意已测子集预测)。"""
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

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

# 各指标的检测"时间成本"(相对单位), 按测试阶段设定: 物理便宜, 老化最贵(burn-in 主导工时)
_STAGE_COST = {'physical': 1.0, 'dc': 2.0, 'ac': 3.0, 'functional': 4.0, 'aging': 11.5}
_FEATURE_STAGE = {
    **{f: 'physical' for f in FEATURES[0:6]},
    **{f: 'dc' for f in FEATURES[6:15]},
    **{f: 'ac' for f in FEATURES[15:21]},
    **{f: 'functional' for f in FEATURES[21:24]},
    **{f: 'aging' for f in FEATURES[24:28]},
}
COST = np.array([_STAGE_COST[_FEATURE_STAGE[f]] for f in FEATURES], dtype=np.float32)
FULL_COST = float(COST.sum())   # 全测一遍的总时间

SCRIPT_DIR = Path(__file__).resolve().parent
PHASE3_DIR = SCRIPT_DIR.parent
REPO_ROOT = PHASE3_DIR.parent


def out(*parts):
    p = PHASE3_DIR / 'outputs'
    for x in parts:
        p = p / x
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load(seed=42, test_ratio=0.3):
    """返回标准化特征 X, 标签 y, 训练/测试索引, scaler 统计。"""
    df = pd.read_csv(REPO_ROOT / 'synthetic_data' / 'chip_baseline_data.csv')
    X = df[FEATURES].astype(float).values
    y = (df['failure_mode'] != 'normal').astype(int).values
    mu, sd = X.mean(0), X.std(0); sd[sd == 0] = 1
    Xs = ((X - mu) / sd).astype(np.float32)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(y))
    nt = int(len(y) * test_ratio)
    test_idx, train_idx = idx[:nt], idx[nt:]
    return Xs, y, train_idx, test_idx


class MaskedClassifier(nn.Module):
    """输入 [x*mask, mask] (2m 维), 可从任意已测子集预测失效概率。"""
    def __init__(self, m, hid=128, dropout=0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2 * m, hid), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hid, hid), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hid, 2))

    def forward(self, x, mask):
        return self.net(torch.cat([x * mask, mask], dim=1))
