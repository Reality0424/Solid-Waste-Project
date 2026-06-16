#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
芯片再制造可靠性评估 - 合成数据生成器 (v2, 真实隐性故障版)

相比 v1 的关键升级（针对数据审计发现的问题）:
1. 物理耦合: 参数不再各自独立随机, 而是按工程关系联动
   - 动态功耗 IDD ∝ 频率 Fmax (P ∝ C·V²·f)
   - 传输延迟/建立/保持时间 与 Fmax 负相关(同受"工艺速度"潜变量驱动)
   - VOH/VIH/VIL 跟随 VDD
2. 真正的"隐性组合故障": 失效不再是给单指标加大偏移(单查即露馅),
   而是由多个"各自仍在规格内"的轻度劣化指标的【乘积式交互】触发。
   => 任一单指标都不极端, 线性/单指标模型抓不住, 必须靠非线性/图模型学交互。
3. aging_temperature_c 不再是常量(85/125 两档), 老化漂移与初始应力耦合。
4. 加入量测噪声; 修正硬编码输出路径(改为相对仓库根目录)。

产出(schema 与 v1 一致, 不影响下游 Phase 1):
1. chip_baseline_data.csv - 基础参数(每芯片1行)
2. chip_aging_curves.csv  - 老化漂移时间序列
3. chip_failure_labels.csv - 失效标注与根因
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42

# 非物理损伤型失效目标占比(隐性), 物理损伤型(显性)单列
TARGET_FAILURE_RATE = 0.10
PHYSICAL_DAMAGE_FRAC = 0.25   # 失效中约 1/4 是显性物理损伤, 其余 3/4 为隐性组合


def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def _z(a):
    a = np.asarray(a, dtype=float)
    s = a.std()
    return (a - a.mean()) / (s if s > 1e-9 else 1.0)


def generate_baseline_data(n_chips, rng):
    """生成带物理耦合的芯片基础参数(此时全部为"健康"分布, 失效在后续按交互规则注入)"""
    print("生成基础参数数据(含物理耦合)...")

    # ---- 潜变量: 工艺速度 (越大 = 越快的硅片: 高 Fmax / 低延迟) ----
    speed = rng.normal(0, 1, n_chips)

    data = {
        'chip_id': [f'CHIP_{i:05d}' for i in range(n_chips)],
        'production_date': [f'2024-{rng.integers(1,13):02d}-{rng.integers(1,29):02d}'
                            for _ in range(n_chips)],
        'chip_model': rng.choice(['MODEL_A', 'MODEL_B', 'MODEL_C'], n_chips),
    }

    # ---- 物理参数(与电气相对独立, 符合实际) ----
    data['pin_flatness_deviation_um'] = np.clip(rng.normal(20, 8, n_chips), 0, 50)
    data['solder_pad_oxidation_percent'] = np.clip(rng.normal(15, 8, n_chips), 0, 100)
    data['package_scratch_depth_um'] = np.clip(rng.exponential(10, n_chips), 0, 100)
    data['warpage_um'] = np.clip(rng.normal(60, 28, n_chips), 0, 200)
    data['pin_coplanarity_percent'] = np.clip(rng.normal(95, 3, n_chips), 80, 100)
    data['package_size_deviation_percent'] = np.clip(rng.normal(0, 2, n_chips), -5, 5)

    # ---- DC: 供电与逻辑电平(VOH/VIH/VIL 跟随 VDD) ----
    vdd = np.clip(rng.normal(3.3, 0.05, n_chips), 3.135, 3.465)
    data['vdd_voltage'] = vdd
    data['voh_voltage'] = np.clip(vdd - rng.uniform(0.15, 0.28, n_chips), 2.7, 3.3)
    data['vol_voltage'] = np.clip(rng.normal(0.18, 0.06, n_chips), 0.05, 0.5)
    data['vih_voltage'] = np.clip(vdd * 0.72 + rng.normal(0, 0.06, n_chips), 2.2, 2.6)
    data['vil_voltage'] = np.clip(vdd * 0.28 + rng.normal(0, 0.06, n_chips), 0.45, 1.1)
    data['iil_leakage_ua'] = np.clip(rng.exponential(0.3, n_chips), 0.01, 5)
    data['iol_leakage_ua'] = np.clip(rng.exponential(2.0, n_chips), 0.1, 20)

    # ---- AC: 速度类参数由 speed 潜变量驱动(彼此相关, 与 Fmax 负相关) ----
    data['fmax_mhz'] = np.clip(300 + 45 * speed + rng.normal(0, 12, n_chips), 200, 400)
    data['setup_time_ns'] = np.clip(3.5 - 0.55 * speed + rng.normal(0, 0.5, n_chips), 1, 8)
    data['hold_time_ns'] = np.clip(2.0 - 0.28 * speed + rng.normal(0, 0.4, n_chips), 0.5, 5)
    data['propagation_delay_ns'] = np.clip(6.0 - 1.3 * speed + rng.normal(0, 1.0, n_chips), 2, 15)
    data['rise_time_ns'] = np.clip(1.2 - 0.18 * speed + rng.normal(0, 0.3, n_chips), 0.3, 3)
    data['fall_time_ns'] = np.clip(1.1 - 0.18 * speed + rng.normal(0, 0.3, n_chips), 0.3, 3)

    # ---- 动态功耗 ∝ 频率(P ∝ C·V²·f) + 电压 ----
    fmax = data['fmax_mhz']
    data['idd_static_ma'] = np.clip(rng.exponential(3.0, n_chips), 0.1, 15)
    data['idd_dynamic_ma'] = np.clip(
        40 + 0.30 * (fmax - 200) + 60 * (vdd - 3.3) + rng.normal(0, 12, n_chips), 50, 260)

    # ---- 功能测试 ----
    data['jtag_scan_pass'] = rng.binomial(1, 0.97, n_chips)
    data['boundary_scan_pass'] = rng.binomial(1, 0.98, n_chips)
    data['functional_test_pass'] = rng.binomial(1, 0.97, n_chips)

    # ---- 老化条件(温度两档 + 与频率耦合) ----
    data['aging_temperature_c'] = rng.choice([85, 125], n_chips, p=[0.7, 0.3])
    data['aging_voltage_v'] = vdd
    data['aging_frequency_mhz'] = fmax * 0.9
    data['aging_duration_hours'] = rng.choice([24, 48, 72, 96, 120, 168], n_chips)

    return pd.DataFrame(data), speed


def assign_interaction_failures(df, rng):
    """
    按【合取-析取交互】注入失效:
      失效区是多个『不同指标子空间里的角落(两两同时劣化)』的【并集】(非凸),
      且各贡献指标都仅轻度劣化(仍在规格内)。
      => 单查不露馅; 因失效区非凸, 单个线性超平面无法刻画(会被大量"单项偏高但不失效"的
         诱饵芯片误判), 必须靠非线性/图模型学习指标间的交互。
      - 物理损伤(显性): 少量芯片单指标极端 -> 容易识别(模拟真实里"一眼可见"的坏件)。
    """
    print("按合取-析取交互注入失效(非凸隐性组合 + 少量显性物理损伤)...")
    n = len(df)

    def adv(col, sign):
        """某指标的'劣化量': 仅当超过 +0.3σ 才开始计入(relu), sign 控制方向"""
        return np.maximum(sign * _z(df[col]) - 0.3, 0.0)

    # --- 机制1: 噪声边裕 = min(高电平裕量, 低电平裕量); 任一坍塌即失效(析取) ---
    nm_high = adv('vih_voltage', +1) * adv('voh_voltage', -1)   # VIH↑ 且 VOH↓ -> 高侧裕量小
    nm_low = adv('vol_voltage', +1) * adv('vil_voltage', -1)    # VOL↑ 且 VIL↓ -> 低侧裕量小
    trig_noise = np.maximum(nm_high, nm_low)

    # --- 机制2: 时序 = 高频 且 (建立紧 或 延迟高) (合取, 不同子空间) ---
    trig_timing = adv('fmax_mhz', +1) * (adv('setup_time_ns', +1) + 0.8 * adv('propagation_delay_ns', +1))

    # --- 机制3: 热积累 = 高功耗 且 (翘曲 或 漏电), 高温放大 ---
    temp_amp = 1.0 + 0.8 * np.maximum((df['aging_temperature_c'].values - 85) / 40.0, 0.0)
    trig_thermal = adv('idd_dynamic_ma', +1) * (adv('warpage_um', +1) + adv('iol_leakage_ua', +1)) * temp_amp

    mech = [trig_noise, trig_timing, trig_thermal]
    mech = [m + rng.normal(0, 0.02, n) for m in mech]
    mode_names = np.array(['noise_margin_insufficient', 'multi_param_combined', 'thermal_accumulation'])

    # 每个机制各取触发量最高的 top-k, 取并集(析取) -> 失效区 = 三个不同子空间角落的并集(非凸)
    n_hidden = int(round(n * TARGET_FAILURE_RATE * (1 - PHYSICAL_DAMAGE_FRAC)))
    k = int(round(n_hidden / 3))
    is_hidden = np.zeros(n, dtype=bool)
    for trig in mech:
        is_hidden[np.argsort(trig)[::-1][:k]] = True

    # 主导模式 = 相对各自分布最异常的那个机制
    trig_z = np.vstack([_z(mech[0]), _z(mech[1]), _z(mech[2])]).T
    dominant = mode_names[np.argmax(trig_z, axis=1)]
    strongest = np.vstack(mech).T.max(axis=1)

    df['failure_status'] = np.ones(n, dtype=int)   # 1=正常, 0=失效
    df['failure_mode'] = 'normal'
    df.loc[is_hidden, 'failure_status'] = 0
    df.loc[is_hidden, 'failure_mode'] = dominant[is_hidden]

    # ---- 显性物理损伤: 在仍正常的芯片里挑少量, 注入极端物理参数 ----
    n_phys = int(round(n * TARGET_FAILURE_RATE * PHYSICAL_DAMAGE_FRAC))
    normal_idx = np.where(df['failure_status'].values == 1)[0]
    phys_idx = rng.choice(normal_idx, size=min(n_phys, len(normal_idx)), replace=False)
    df.loc[phys_idx, 'warpage_um'] = np.clip(df.loc[phys_idx, 'warpage_um'] + rng.uniform(70, 120, len(phys_idx)), 0, 200)
    df.loc[phys_idx, 'package_scratch_depth_um'] = np.clip(df.loc[phys_idx, 'package_scratch_depth_um'] + rng.uniform(40, 70, len(phys_idx)), 0, 100)
    df.loc[phys_idx, 'pin_flatness_deviation_um'] = np.clip(df.loc[phys_idx, 'pin_flatness_deviation_um'] + rng.uniform(20, 35, len(phys_idx)), 0, 50)
    df.loc[phys_idx, 'failure_status'] = 0
    df.loc[phys_idx, 'failure_mode'] = 'physical_damage'

    # 保存潜在风险分(便于审计/老化耦合, 非检测可见字段不写入 baseline csv)
    df.attrs['risk'] = strongest
    return df


def generate_aging_curves(baseline_df, rng):
    """老化漂移时间序列: 失效品漂移更大/更非线性, 且与初始风险耦合"""
    print("生成老化曲线...")
    rows = []
    risk = baseline_df.attrs.get('risk', np.zeros(len(baseline_df)))
    risk_n = (risk - risk.min()) / (np.ptp(risk) + 1e-9)

    for i, (_, row) in enumerate(baseline_df.iterrows()):
        dur = int(row['aging_duration_hours'])
        is_fail = row['failure_status'] == 0
        rk = risk_n[i]
        temp_acc = 1.0 + 0.5 * (row['aging_temperature_c'] - 85) / 40.0  # 125°C 漂移更快
        for t in np.arange(0, dur + 1, 1):
            frac = t / max(dur, 1)
            if not is_fail:
                k = 0.001 + 0.002 * rk
                vdd_d = row['vdd_voltage'] * (1 + rng.normal(0, 0.008))
                idd_d = row['idd_dynamic_ma'] * (1 + rng.normal(0, 0.015))
                voh_d = row['voh_voltage'] * (1 - k * frac * temp_acc)
                vol_d = row['vol_voltage'] * (1 + k * frac * temp_acc)
                delay_d = row['propagation_delay_ns'] * (1 + k * frac * temp_acc)
            else:
                accel = (1 + frac ** 1.5) * temp_acc
                if row['failure_mode'] == 'thermal_accumulation':
                    idd_d = row['idd_dynamic_ma'] * (1 + rng.normal(0.04, 0.02) * accel)
                    voh_d = row['voh_voltage'] * (1 - 0.006 * frac * accel)
                    vol_d = row['vol_voltage'] * (1 + 0.006 * frac * accel)
                    delay_d = row['propagation_delay_ns'] * (1 + 0.005 * frac * accel)
                    vdd_d = row['vdd_voltage'] * (1 + rng.normal(0, 0.02) * accel)
                elif row['failure_mode'] == 'noise_margin_insufficient':
                    voh_d = row['voh_voltage'] * (1 - 0.011 * frac * accel)
                    vol_d = row['vol_voltage'] * (1 + 0.011 * frac * accel)
                    idd_d = row['idd_dynamic_ma'] * (1 + rng.normal(0.02, 0.02))
                    delay_d = row['propagation_delay_ns'] * (1 + 0.003 * frac * accel)
                    vdd_d = row['vdd_voltage'] * (1 + rng.normal(-0.01, 0.01))
                else:
                    voh_d = row['voh_voltage'] * (1 - 0.004 * frac * accel)
                    vol_d = row['vol_voltage'] * (1 + 0.004 * frac * accel)
                    idd_d = row['idd_dynamic_ma'] * (1 + rng.normal(0.02, 0.03))
                    delay_d = row['propagation_delay_ns'] * (1 + 0.004 * frac * accel)
                    vdd_d = row['vdd_voltage'] * (1 + rng.normal(-0.01, 0.02))
            rows.append({'chip_id': row['chip_id'], 'aging_hour': int(t),
                         'vdd_voltage': vdd_d, 'idd_dynamic_ma': idd_d,
                         'voh_voltage': voh_d, 'vol_voltage': vol_d,
                         'propagation_delay_ns': delay_d})
    return pd.DataFrame(rows)


def generate_failure_annotations(baseline_df, rng):
    """失效标注: 时间/现象/根因"""
    print("生成失效标注...")
    phen = {
        'physical_damage': 'Physical connection broken, device disconnected',
        'noise_margin_insufficient': 'Signal integrity failure, intermittent errors',
        'thermal_accumulation': 'Thermal runaway, power surged, shutdown protection triggered',
        'multi_param_combined': 'Timing violation, functional test fails at high frequency',
    }
    rows = []
    for _, row in baseline_df.iterrows():
        if row['failure_status'] == 0:
            ft = int(rng.integers(10, max(11, int(row['aging_duration_hours']))))
            rows.append({'chip_id': row['chip_id'], 'failure_mode': row['failure_mode'],
                         'failure_time_hours': ft,
                         'failure_phenomenon': phen.get(row['failure_mode'], 'Unknown'),
                         'root_cause': f"Parameter interaction / degradation: {row['failure_mode']}",
                         'predicted_mttf_hours': ft * 2})
    return pd.DataFrame(rows)


def main():
    print("=" * 60)
    print("芯片再制造可靠性评估 - 合成数据生成 (v2 真实隐性故障)")
    print("=" * 60)

    rng = np.random.default_rng(SEED)
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = repo_root / 'synthetic_data'
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline_df, _ = generate_baseline_data(1000, rng)
    print(f"✓ 基础参数: {len(baseline_df)} 芯片")

    baseline_df = assign_interaction_failures(baseline_df, rng)
    nfail = int((baseline_df['failure_status'] == 0).sum())
    print(f"✓ 失效注入: {nfail} 个失效品 ({100*nfail/len(baseline_df):.1f}%)")

    aging_df = generate_aging_curves(baseline_df, rng)
    print(f"✓ 老化曲线: {len(aging_df)} 行")

    failure_df = generate_failure_annotations(baseline_df, rng)
    print(f"✓ 失效标注: {len(failure_df)} 条")

    baseline_df.to_csv(output_dir / 'chip_baseline_data.csv', index=False, encoding='utf-8')
    aging_df.to_csv(output_dir / 'chip_aging_curves.csv', index=False, encoding='utf-8')
    failure_df.to_csv(output_dir / 'chip_failure_labels.csv', index=False, encoding='utf-8')

    print(f"\n✓ 已保存到: {output_dir}")
    print("\n故障模式分布:")
    print(baseline_df[baseline_df.failure_status == 0]['failure_mode'].value_counts().to_string())
    print("\n" + "=" * 60)
    print("数据生成完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
