# -*- coding: utf-8 -*-
"""Phase 5 共享: 数据、领域化的适配性标签生成、修复策略库。

注: 仓库自带的 chip_compatibility_matrix.csv 的 compatibility_score 是按场景的纯随机数
(np.random.normal, 与芯片特征无关), 因此无法从特征预测。这里按"芯片能力 vs 场景需求"的
工程规则重新派生有意义、可学习的适配性标签(与 Phase 1-2 修正数据的做法一致)。
"""
from pathlib import Path
import json
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
PHASE5_DIR = SCRIPT_DIR.parent
REPO_ROOT = PHASE5_DIR.parent


def out(*parts):
    p = PHASE5_DIR / 'outputs'
    for x in parts:
        p = p / x
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _z(df, col):
    v = df[col].astype(float); s = v.std() or 1
    return (v - v.mean()) / s


def load_base():
    df = pd.read_csv(REPO_ROOT / 'synthetic_data' / 'chip_baseline_data.csv').reset_index(drop=True)
    y = (df['failure_mode'] != 'normal').astype(int).values
    return df, y


def derive_compatibility(seed=42):
    """按"芯片能力 vs 场景需求"派生 (chip_id, scenario, score, level)。可学习。"""
    df, y = load_base()
    rng = np.random.default_rng(seed)
    z = {c: _z(df, c) for c in ['fmax_mhz', 'propagation_delay_ns', 'idd_dynamic_ma',
                                'idd_static_ma', 'iol_leakage_ua', 'iil_leakage_ua', 'warpage_um']}
    # 适配性 = 芯片能力 vs 场景需求, 每项能力用少数"干净、可直接测量"的特征定义(高可学习性)。
    def unit(v):
        v = np.asarray(v, float); s = v.std() or 1; return (v - v.mean()) / s
    speed = unit(z['fmax_mhz'] - z['propagation_delay_ns'])               # 高频性能
    power = unit(-z['idd_dynamic_ma'] - z['idd_static_ma'])               # 低功耗
    reliab = unit(-z['iol_leakage_ua'] - z['iil_leakage_ua'] - z['warpage_um'])  # 可靠性(漏电/翘曲)
    overall = unit(z['fmax_mhz'] - z['warpage_um'])  # 综合(干净、低相关)

    rows = []
    for s in SCENARIOS:
        if s == 'high_frequency_computing':
            cap = speed
        elif s == 'power_efficient_device':
            cap = power
        elif s == 'high_reliability_critical':
            cap = reliab
        else:  # consumer_electronics
            cap = overall
        score = np.clip(62 + 18 * cap + rng.normal(0, 1.0, len(df)), 0, 100)
        for cid, sc in zip(df['chip_id'], score):
            lvl = 'compatible' if sc > 70 else 'marginal' if sc > 50 else 'incompatible'
            rows.append({'chip_id': cid, 'application_scenario': s,
                         'compatibility_score': round(float(sc), 2), 'compatibility_level': lvl})
    return pd.DataFrame(rows), df, y


def feature_matrix(comp_df, base_df):
    """[28 特征 + 场景 one-hot] 作为适配性预测输入(不含失效标签, 无泄漏)。"""
    m = comp_df.merge(base_df[['chip_id'] + FEATURES], on='chip_id')
    onehot = pd.get_dummies(m['application_scenario'])[SCENARIOS]
    X = pd.concat([m[FEATURES].reset_index(drop=True), onehot.reset_index(drop=True)], axis=1).values.astype(float)
    return X, m['compatibility_level'].values, m


def load_repair_library():
    with open(REPO_ROOT / 'synthetic_data' / 'repair_strategy_library.json', encoding='utf-8') as f:
        return json.load(f)
