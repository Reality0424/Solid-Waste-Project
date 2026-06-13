#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
芯片再制造可靠性评估 - 合成数据生成器
生成1000个合成芯片样本，包含隐性故障模式

生成数据集包括：
1. chip_baseline_data.csv - 基础参数（每个芯片1行）
2. chip_aging_curves.csv - 老化曲线（时间序列）
3. chip_failure_labels.csv - 失效标签和根本原因
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

# 设置随机种子以保证可重复性
np.random.seed(42)

def generate_baseline_data(n_chips=1000):
    """
    生成芯片基础参数数据
    
    包含：
    - 物理参数（6项）
    - 电气参数（直流9项 + 交流6项）
    - 功能测试结果（3类）
    """
    
    print("生成基础参数数据...")
    
    data = {
        'chip_id': [f'CHIP_{i:05d}' for i in range(n_chips)],
        'production_date': [f'2024-{np.random.randint(1,13):02d}-{np.random.randint(1,29):02d}' 
                           for _ in range(n_chips)],
        'chip_model': [np.random.choice(['MODEL_A', 'MODEL_B', 'MODEL_C']) 
                      for _ in range(n_chips)],
    }
    
    # ========== 物理参数 ==========
    # 1. 引脚平整度偏差 (0-50 μm, 平均20μm)
    data['pin_flatness_deviation_um'] = np.random.normal(20, 8, n_chips)
    data['pin_flatness_deviation_um'] = np.clip(data['pin_flatness_deviation_um'], 0, 50)
    
    # 2. 焊盘氧化程度 (0-100%, 平均15%)
    data['solder_pad_oxidation_percent'] = np.random.normal(15, 10, n_chips)
    data['solder_pad_oxidation_percent'] = np.clip(data['solder_pad_oxidation_percent'], 0, 100)
    
    # 3. 封装划痕深度 (0-100 μm, 平均10μm)
    data['package_scratch_depth_um'] = np.random.exponential(10, n_chips)
    data['package_scratch_depth_um'] = np.clip(data['package_scratch_depth_um'], 0, 100)
    
    # 4. 翘曲度 (0-200 μm, 平均60μm)
    data['warpage_um'] = np.random.normal(60, 30, n_chips)
    data['warpage_um'] = np.clip(data['warpage_um'], 0, 200)
    
    # 5. 引脚共面度 (80-100%, 平均95%)
    data['pin_coplanarity_percent'] = np.random.normal(95, 3, n_chips)
    data['pin_coplanarity_percent'] = np.clip(data['pin_coplanarity_percent'], 80, 100)
    
    # 6. 封装尺寸偏差 (-5% ~ +5%, 平均0%)
    data['package_size_deviation_percent'] = np.random.normal(0, 2, n_chips)
    data['package_size_deviation_percent'] = np.clip(data['package_size_deviation_percent'], -5, 5)
    
    # ========== 直流(DC)电气参数 ==========
    # 7. 供电电压 VDD (3.0-3.3V, 标称3.3V ±5%)
    data['vdd_voltage'] = np.random.normal(3.3, 0.08, n_chips)
    data['vdd_voltage'] = np.clip(data['vdd_voltage'], 3.135, 3.465)  # ±5% of 3.3V
    
    # 8. 静态功耗 IDD_static (mA, 正常<10mA)
    data['idd_static_ma'] = np.random.exponential(5, n_chips)
    data['idd_static_ma'] = np.clip(data['idd_static_ma'], 0.1, 20)
    
    # 9. 动态功耗 IDD_dynamic (mA, 50-200mA)
    data['idd_dynamic_ma'] = np.random.normal(120, 40, n_chips)
    data['idd_dynamic_ma'] = np.clip(data['idd_dynamic_ma'], 50, 200)
    
    # 10. 输出电压高 VOH (应接近VDD, 正常>3.0V)
    data['voh_voltage'] = data['vdd_voltage'] - np.random.normal(0.2, 0.1, n_chips)
    data['voh_voltage'] = np.clip(data['voh_voltage'], 2.8, 3.3)
    
    # 11. 输出电压低 VOL (应接近0V, 正常<0.5V)
    data['vol_voltage'] = np.random.normal(0.2, 0.1, n_chips)
    data['vol_voltage'] = np.clip(data['vol_voltage'], 0.05, 0.5)
    
    # 12. 输入阈值高 VIH (应>VDD×0.7, 正常>2.3V)
    vih_target = data['vdd_voltage'] * 0.72
    data['vih_voltage'] = vih_target + np.random.normal(0, 0.1, n_chips)
    data['vih_voltage'] = np.clip(data['vih_voltage'], 2.2, 2.5)
    
    # 13. 输入阈值低 VIL (应<VDD×0.3, 正常<1.0V)
    vil_target = data['vdd_voltage'] * 0.28
    data['vil_voltage'] = vil_target + np.random.normal(0, 0.1, n_chips)
    data['vil_voltage'] = np.clip(data['vil_voltage'], 0.5, 1.1)
    
    # 14. 输入漏电流 IIL (μA, 正常<1μA)
    data['iil_leakage_ua'] = np.random.exponential(0.3, n_chips)
    data['iil_leakage_ua'] = np.clip(data['iil_leakage_ua'], 0.01, 5)
    
    # 15. 输出漏电流 IOL (μA, 正常<10μA)
    data['iol_leakage_ua'] = np.random.exponential(2, n_chips)
    data['iol_leakage_ua'] = np.clip(data['iol_leakage_ua'], 0.1, 20)
    
    # ========== 交流(AC)参数 ==========
    # 16. 建立时间 tSU (ns, 正常1-5ns)
    data['setup_time_ns'] = np.random.normal(3.5, 1, n_chips)
    data['setup_time_ns'] = np.clip(data['setup_time_ns'], 1, 8)
    
    # 17. 保持时间 tH (ns, 正常1-3ns)
    data['hold_time_ns'] = np.random.normal(2, 0.8, n_chips)
    data['hold_time_ns'] = np.clip(data['hold_time_ns'], 0.5, 5)
    
    # 18. 传输延迟 tPD (ns, 正常2-10ns)
    data['propagation_delay_ns'] = np.random.normal(6, 2, n_chips)
    data['propagation_delay_ns'] = np.clip(data['propagation_delay_ns'], 2, 15)
    
    # 19. 上升时间 tR (ns, 正常0.5-2ns)
    data['rise_time_ns'] = np.random.normal(1.2, 0.4, n_chips)
    data['rise_time_ns'] = np.clip(data['rise_time_ns'], 0.3, 3)
    
    # 20. 下降时间 tF (ns, 正常0.5-2ns)
    data['fall_time_ns'] = np.random.normal(1.1, 0.4, n_chips)
    data['fall_time_ns'] = np.clip(data['fall_time_ns'], 0.3, 3)
    
    # 21. 最高工作频率 Fmax (MHz, 假设200-400MHz)
    data['fmax_mhz'] = np.random.normal(300, 50, n_chips)
    data['fmax_mhz'] = np.clip(data['fmax_mhz'], 200, 400)
    
    # ========== 功能测试结果 ==========
    # 22-24. 功能测试 (1=通过, 0=失败)
    data['jtag_scan_pass'] = np.random.binomial(1, 0.95, n_chips)  # 95%通过率
    data['boundary_scan_pass'] = np.random.binomial(1, 0.97, n_chips)  # 97%通过率
    data['functional_test_pass'] = np.random.binomial(1, 0.96, n_chips)  # 96%通过率
    
    # ========== 老化条件 ==========
    # 25-28. 老化条件定义
    data['aging_temperature_c'] = np.full(n_chips, 85)  # 恒温85°C
    data['aging_voltage_v'] = data['vdd_voltage']  # 按名义值
    data['aging_frequency_mhz'] = data['fmax_mhz'] * 0.9  # 90%工作频率
    data['aging_duration_hours'] = np.random.choice([24, 48, 72, 96, 120, 168], n_chips)
    
    df = pd.DataFrame(data)
    return df


def add_failure_patterns_to_baseline(df):
    """
    为基础数据添加故障模式
    
    故障模式：
    1. 物理损伤型故障 (20%)
    2. 噪声边裕不足型 (30%)
    3. 热积累型 (25%)
    4. 多参数叠加型 (25%)
    """
    
    print("添加故障模式...")
    
    # 初始化故障标签 (0=故障品, 1=正常品)
    n_chips = len(df)
    n_failures = int(n_chips * 0.1)  # 10%故障率
    
    df['failure_status'] = np.ones(n_chips, dtype=int)  # 默认全部正常
    failure_indices = np.random.choice(n_chips, n_failures, replace=False)
    df.loc[failure_indices, 'failure_status'] = 0
    
    # 为故障品分配失效模式
    failure_modes = ['physical_damage', 'noise_margin_insufficient', 
                     'thermal_accumulation', 'multi_param_combined']
    df['failure_mode'] = 'normal'
    
    for idx in failure_indices:
        mode = np.random.choice(failure_modes, p=[0.2, 0.3, 0.25, 0.25])
        df.loc[idx, 'failure_mode'] = mode
        
        # 根据失效模式调整参数
        if mode == 'physical_damage':
            # 引脚平整度、翘曲度增加
            df.loc[idx, 'pin_flatness_deviation_um'] += np.random.uniform(15, 30)
            df.loc[idx, 'warpage_um'] += np.random.uniform(50, 100)
            df.loc[idx, 'package_scratch_depth_um'] += np.random.uniform(30, 60)
        
        elif mode == 'noise_margin_insufficient':
            # VOH、VOL接近 VIH、VIL
            df.loc[idx, 'voh_voltage'] -= np.random.uniform(0.15, 0.3)
            df.loc[idx, 'vol_voltage'] += np.random.uniform(0.15, 0.3)
            df.loc[idx, 'vih_voltage'] += np.random.uniform(0.1, 0.2)
            df.loc[idx, 'vil_voltage'] -= np.random.uniform(0.1, 0.2)
        
        elif mode == 'thermal_accumulation':
            # 高功耗 + 高翘曲度 + 长老化时间
            df.loc[idx, 'idd_dynamic_ma'] += np.random.uniform(50, 100)
            df.loc[idx, 'warpage_um'] += np.random.uniform(40, 80)
            df.loc[idx, 'aging_duration_hours'] = 168
            df.loc[idx, 'package_scratch_depth_um'] += np.random.uniform(20, 40)
        
        elif mode == 'multi_param_combined':
            # 多个参数同时接近限值
            df.loc[idx, 'setup_time_ns'] += np.random.uniform(2, 4)
            df.loc[idx, 'hold_time_ns'] += np.random.uniform(2, 3)
            df.loc[idx, 'propagation_delay_ns'] += np.random.uniform(3, 6)
            df.loc[idx, 'voh_voltage'] -= np.random.uniform(0.1, 0.2)
            df.loc[idx, 'vol_voltage'] += np.random.uniform(0.1, 0.2)
            df.loc[idx, 'idd_dynamic_ma'] += np.random.uniform(30, 60)
    
    return df


def generate_aging_curves(baseline_df, output_dir):
    """
    为每个芯片生成老化过程中的参数漂移曲线
    
    模拟：老化过程中VDD、IDD、VOH、VOL、延迟等参数的时间变化
    """
    
    print("生成老化曲线...")
    
    aging_data_list = []
    
    for idx, row in baseline_df.iterrows():
        chip_id = row['chip_id']
        aging_duration = int(row['aging_duration_hours'])
        is_failure = row['failure_status'] == 0
        
        # 生成时间点（分钟级采样，每小时一个点）
        time_points = np.arange(0, aging_duration + 1, 1)  # 小时
        
        # 初始值
        vdd_init = row['vdd_voltage']
        idd_dynamic_init = row['idd_dynamic_ma']
        voh_init = row['voh_voltage']
        vol_init = row['vol_voltage']
        propagation_delay_init = row['propagation_delay_ns']
        
        for t in time_points:
            # 正常的参数漂移（线性或指数衰减）
            if not is_failure:
                # 轻微漂移（<5%）
                vdd_drift = vdd_init * (1 + np.random.normal(0, 0.01))
                idd_drift = idd_dynamic_init * (1 + np.random.normal(0, 0.02))
                voh_drift = voh_init * (1 - 0.001 * t / aging_duration)  # 缓慢下降
                vol_drift = vol_init * (1 + 0.001 * t / aging_duration)   # 缓慢上升
                delay_drift = propagation_delay_init * (1 + 0.001 * t / aging_duration)  # 缓慢增加
            
            else:
                # 故障品的参数漂移（较大，可能非线性）
                if row['failure_mode'] == 'thermal_accumulation':
                    # 加速漂移，呈指数增长
                    acceleration = 1 + (t / aging_duration) ** 1.5
                    vdd_drift = vdd_init * (1 + np.random.normal(0, 0.02) * acceleration)
                    idd_drift = idd_dynamic_init * (1 + np.random.normal(0, 0.05) * acceleration)
                    voh_drift = voh_init * (1 - 0.005 * t / aging_duration * acceleration)
                    vol_drift = vol_init * (1 + 0.005 * t / aging_duration * acceleration)
                    delay_drift = propagation_delay_init * (1 + 0.005 * t / aging_duration * acceleration)
                
                elif row['failure_mode'] == 'noise_margin_insufficient':
                    # VOH、VOL恶化明显
                    vdd_drift = vdd_init * (1 + np.random.normal(-0.02, 0.01))
                    idd_drift = idd_dynamic_init * (1 + np.random.normal(0.03, 0.02))
                    voh_drift = voh_init * (1 - 0.01 * t / aging_duration)  # 快速下降
                    vol_drift = vol_init * (1 + 0.01 * t / aging_duration)   # 快速上升
                    delay_drift = propagation_delay_init * (1 + 0.003 * t / aging_duration)
                
                else:
                    # 其他故障模式
                    vdd_drift = vdd_init * (1 + np.random.normal(-0.01, 0.02))
                    idd_drift = idd_dynamic_init * (1 + np.random.normal(0.02, 0.03))
                    voh_drift = voh_init * (1 - 0.003 * t / aging_duration)
                    vol_drift = vol_init * (1 + 0.003 * t / aging_duration)
                    delay_drift = propagation_delay_init * (1 + 0.002 * t / aging_duration)
            
            aging_data_list.append({
                'chip_id': chip_id,
                'aging_hour': t,
                'vdd_voltage': vdd_drift,
                'idd_dynamic_ma': idd_drift,
                'voh_voltage': voh_drift,
                'vol_voltage': vol_drift,
                'propagation_delay_ns': delay_drift,
            })
    
    aging_df = pd.DataFrame(aging_data_list)
    return aging_df


def generate_failure_annotations(baseline_df):
    """
    生成失效标注：芯片失效时间、现象、根本原因
    """
    
    print("生成失效标注...")
    
    failure_annotations = []
    
    for idx, row in baseline_df.iterrows():
        if row['failure_status'] == 0:  # 只标注失效品
            # 失效时间（在老化过程中的某个点失效）
            failure_time = np.random.randint(10, int(row['aging_duration_hours']))
            
            # 失效现象描述
            mode = row['failure_mode']
            if mode == 'physical_damage':
                phenomenon = 'Physical connection broken, device disconnected'
            elif mode == 'noise_margin_insufficient':
                phenomenon = 'Signal integrity failure, intermittent errors'
            elif mode == 'thermal_accumulation':
                phenomenon = 'Thermal runaway, power consumption surged, shutdown protection triggered'
            elif mode == 'multi_param_combined':
                phenomenon = 'Timing violation, failed functional tests at high frequency'
            else:
                phenomenon = 'Unknown'
            
            failure_annotations.append({
                'chip_id': row['chip_id'],
                'failure_mode': mode,
                'failure_time_hours': failure_time,
                'failure_phenomenon': phenomenon,
                'root_cause': f'Parameter degradation due to {mode}',
                'predicted_mttf_hours': failure_time * 2,  # 估计MTTF为失效时间的2倍
            })
    
    failure_df = pd.DataFrame(failure_annotations)
    return failure_df


def main():
    """主函数"""
    
    print("=" * 60)
    print("芯片再制造可靠性评估 - 合成数据生成")
    print("=" * 60)
    
    output_dir = r'D:\laboratory_projects\solid_waste_projects_260526\synthetic_data'
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 生成基础数据
    baseline_df = generate_baseline_data(n_chips=1000)
    print(f"✓ 生成了 {len(baseline_df)} 个芯片的基础参数")
    
    # 2. 添加故障模式
    baseline_df = add_failure_patterns_to_baseline(baseline_df)
    n_failures = (baseline_df['failure_status'] == 0).sum()
    print(f"✓ 添加了故障模式，其中 {n_failures} 个故障品({100*n_failures/len(baseline_df):.1f}%)")
    
    # 3. 生成老化曲线
    aging_df = generate_aging_curves(baseline_df, output_dir)
    print(f"✓ 生成了 {len(aging_df)} 条老化曲线数据")
    
    # 4. 生成失效标注
    failure_df = generate_failure_annotations(baseline_df)
    print(f"✓ 生成了 {len(failure_df)} 条失效标注")
    
    # 保存数据
    baseline_path = os.path.join(output_dir, 'chip_baseline_data.csv')
    aging_path = os.path.join(output_dir, 'chip_aging_curves.csv')
    failure_path = os.path.join(output_dir, 'chip_failure_labels.csv')
    
    baseline_df.to_csv(baseline_path, index=False, encoding='utf-8')
    aging_df.to_csv(aging_path, index=False, encoding='utf-8')
    failure_df.to_csv(failure_path, index=False, encoding='utf-8')
    
    print(f"\n✓ 数据已保存到: {output_dir}")
    print(f"  - {baseline_path}")
    print(f"  - {aging_path}")
    print(f"  - {failure_path}")
    
    # 打印数据统计
    print("\n" + "=" * 60)
    print("数据统计")
    print("=" * 60)
    print(f"\n基础数据集规模:")
    print(f"  - 总芯片数: {len(baseline_df)}")
    print(f"  - 正常品: {(baseline_df['failure_status'] == 1).sum()}")
    print(f"  - 故障品: {(baseline_df['failure_status'] == 0).sum()}")
    print(f"\n故障模式分布:")
    for mode in baseline_df[baseline_df['failure_status'] == 0]['failure_mode'].unique():
        count = ((baseline_df['failure_status'] == 0) & (baseline_df['failure_mode'] == mode)).sum()
        print(f"  - {mode}: {count}")
    
    print(f"\n基础参数样本 (前5行):")
    print(baseline_df.iloc[:5, :10].to_string())
    
    print(f"\n老化曲线样本 (某芯片的10小时数据):")
    sample_chip = baseline_df.iloc[0]['chip_id']
    sample_aging = aging_df[aging_df['chip_id'] == sample_chip].head(10)
    print(sample_aging.to_string())
    
    print(f"\n失效标注样本:")
    if len(failure_df) > 0:
        print(failure_df.head().to_string())
    else:
        print("  (本次生成没有失效品)")
    
    print("\n" + "=" * 60)
    print("数据生成完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
