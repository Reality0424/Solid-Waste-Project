"""
增强型合成数据生成脚本
支持 Phase 1-6 的完整数据需求
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

class EnhancedSyntheticDataGenerator:
    """为 Phase 1-6 生成增强型合成数据"""
    
    def __init__(self, seed=42, n_samples=1000):
        """
        初始化数据生成器
        Args:
            seed: 随机种子
            n_samples: 样本数量（推荐1000）
        """
        np.random.seed(seed)
        self.n_samples = n_samples
        self.chip_ids = [f"CHIP_{i:05d}" for i in range(n_samples)]
        
    def generate_appearance_params(self):
        """生成外观测试参数"""
        data = {}
        # 外观测试参数
        data['pin_flatness_deviation_um'] = np.random.normal(20, 15, self.n_samples)
        data['solder_pad_oxidation_percent'] = np.random.uniform(0, 30, self.n_samples)
        data['package_scratch_depth_um'] = np.random.exponential(10, self.n_samples)
        data['warpage_um'] = np.random.normal(50, 30, self.n_samples)
        data['pin_coplanarity_percent'] = np.random.normal(97, 3, self.n_samples)
        data['package_size_deviation_percent'] = np.random.normal(-0.5, 1.5, self.n_samples)
        
        # 外观测试通过/失败（基于参数阈值）
        appearance_scores = self._calculate_appearance_score(data)
        data['appearance_test_pass'] = (appearance_scores > 70).astype(int)
        data['appearance_quality_score'] = appearance_scores
        
        return pd.DataFrame(data)
    
    def generate_dc_electrical_params(self, appearance_scores):
        """生成DC电气测试参数（依赖外观测试）"""
        data = {}
        # DC电气测试参数
        data['vdd_voltage'] = np.random.normal(3.3, 0.1, self.n_samples)
        data['idd_static_ma'] = np.random.exponential(5, self.n_samples)
        data['idd_dynamic_ma'] = np.random.normal(150, 50, self.n_samples)
        data['voh_voltage'] = np.random.normal(3.0, 0.15, self.n_samples)
        data['vol_voltage'] = np.random.exponential(0.1, self.n_samples)
        data['vih_voltage'] = np.random.normal(2.4, 0.1, self.n_samples)
        data['vil_voltage'] = np.random.normal(0.9, 0.1, self.n_samples)
        data['iil_leakage_ua'] = np.random.exponential(0.2, self.n_samples)
        data['iol_leakage_ua'] = np.random.exponential(2, self.n_samples)
        
        # DC测试通过/失败（外观差的芯片更容易失败）
        dc_scores = self._calculate_dc_score(data, appearance_scores)
        data['dc_test_pass'] = (dc_scores > 70).astype(int)
        data['dc_electrical_quality_score'] = dc_scores
        
        return pd.DataFrame(data)
    
    def generate_ac_electrical_params(self, dc_scores):
        """生成AC电气测试参数（依赖DC电气）"""
        data = {}
        # AC电气测试参数
        data['setup_time_ns'] = np.random.normal(3.5, 1.5, self.n_samples)
        data['hold_time_ns'] = np.random.normal(2.2, 0.8, self.n_samples)
        data['propagation_delay_ns'] = np.random.normal(5.5, 2, self.n_samples)
        data['rise_time_ns'] = np.random.normal(1.5, 0.6, self.n_samples)
        data['fall_time_ns'] = np.random.normal(1.2, 0.5, self.n_samples)
        data['fmax_mhz'] = np.random.normal(300, 80, self.n_samples)
        
        # AC测试通过/失败（DC差的芯片更容易失败）
        ac_scores = self._calculate_ac_score(data, dc_scores)
        data['ac_test_pass'] = (ac_scores > 70).astype(int)
        data['ac_electrical_quality_score'] = ac_scores
        
        return pd.DataFrame(data)
    
    def generate_functional_params(self, ac_scores):
        """生成功能测试参数（依赖AC电气）"""
        data = {}
        # 功能测试（扫描、边界扫描、功能测试）
        fail_rate = 1.0 - (ac_scores / 100.0)  # AC得分越低，功能测试失败率越高
        data['jtag_scan_pass'] = (np.random.random(self.n_samples) > fail_rate * 0.3).astype(int)
        data['boundary_scan_pass'] = (np.random.random(self.n_samples) > fail_rate * 0.2).astype(int)
        data['functional_test_pass'] = (np.random.random(self.n_samples) > fail_rate * 0.15).astype(int)
        
        # 功能测试综合评分
        functional_scores = (data['jtag_scan_pass'] * 33.3 + 
                            data['boundary_scan_pass'] * 33.3 + 
                            data['functional_test_pass'] * 33.4)
        data['functional_quality_score'] = functional_scores
        
        return pd.DataFrame(data)
    
    def generate_aging_conditions_and_results(self, all_scores):
        """生成老化测试条件和结果"""
        data = {}
        # 老化条件（固定或略微变化）
        data['aging_temperature_c'] = np.full(self.n_samples, 85)
        data['aging_voltage_v'] = np.random.normal(3.3, 0.05, self.n_samples)
        data['aging_frequency_mhz'] = np.random.normal(250, 50, self.n_samples)
        data['aging_duration_hours'] = np.random.choice([24, 48, 72, 96, 120, 168], self.n_samples)
        
        # 计算老化可靠性风险等级
        overall_quality = np.mean(all_scores, axis=0)  # 改为axis=0，计算每个样本的平均质量
        aging_risk = 1.0 - (overall_quality / 100.0)  # 质量越差，老化风险越高
        
        # 将风险等级转换为标签
        risk_labels = []
        for risk_val in aging_risk:
            if risk_val < 0.2:
                risk_labels.append('low')
            elif risk_val < 0.5:
                risk_labels.append('medium')
            else:
                risk_labels.append('high')
        data['reliability_risk_level'] = risk_labels
        
        return pd.DataFrame(data)
    
    def generate_test_sequence_data(self):
        """生成测试序列和成本数据（Phase 3需要）"""
        test_data = []
        test_sequence = ['appearance', 'dc_electrical', 'ac_electrical', 'functional']
        
        # 每个芯片的测试成本和时间
        for chip_id in self.chip_ids:
            for i, test_stage in enumerate(test_sequence):
                # 成本（单位：元）
                if test_stage == 'appearance':
                    cost = np.random.uniform(50, 100)
                    time_min = np.random.uniform(10, 20)
                elif test_stage == 'dc_electrical':
                    cost = np.random.uniform(80, 150)
                    time_min = np.random.uniform(30, 60)
                elif test_stage == 'ac_electrical':
                    cost = np.random.uniform(150, 250)
                    time_min = np.random.uniform(60, 120)
                else:  # functional
                    cost = np.random.uniform(100, 200)
                    time_min = np.random.uniform(45, 90)
                
                test_data.append({
                    'chip_id': chip_id,
                    'test_stage': test_stage,
                    'stage_order': i + 1,
                    'test_cost_yuan': cost,
                    'test_time_minutes': time_min,
                    'cumulative_cost_yuan': cost * (i + 1),
                    'cumulative_time_minutes': time_min * (i + 1),
                })
        
        return pd.DataFrame(test_data)
    
    def generate_failure_labels_extended(self, n_failures=1000):
        """扩展故障标签（从100个扩展到1000个）"""
        # 故障模式分布
        failure_modes = ['physical_damage', 'thermal_accumulation', 
                        'noise_margin_insufficient', 'multi_param_combined']
        
        # 选择失败芯片（约10%的芯片失败）
        fail_indices = np.random.choice(self.n_samples, n_failures, replace=False)
        fail_chip_ids = [self.chip_ids[i] for i in fail_indices]
        
        failures = []
        for chip_id in fail_chip_ids:
            failure_mode = np.random.choice(failure_modes)
            
            # 根据故障模式生成失败时间和现象
            if failure_mode == 'physical_damage':
                failure_time = np.random.exponential(20)
                phenomenon = "Physical connection broken, device disconnected"
            elif failure_mode == 'thermal_accumulation':
                failure_time = np.random.normal(80, 30)
                phenomenon = "Thermal runaway, power consumption surged"
            elif failure_mode == 'noise_margin_insufficient':
                failure_time = np.random.normal(100, 40)
                phenomenon = "Signal integrity failure, intermittent errors"
            else:  # multi_param_combined
                failure_time = np.random.normal(60, 25)
                phenomenon = "Timing violation, failed functional tests"
            
            failures.append({
                'chip_id': chip_id,
                'failure_mode': failure_mode,
                'failure_time_hours': max(1, failure_time),
                'failure_phenomenon': phenomenon,
                'root_cause': f"Parameter degradation due to {failure_mode}",
                'predicted_mttf_hours': max(1, failure_time * 2),
            })
        
        return pd.DataFrame(failures)
    
    def generate_compatibility_matrix(self):
        """生成适配性矩阵（Phase 5需要）"""
        # 定义应用场景
        application_scenarios = [
            'high_frequency_computing', 'power_efficient_device',
            'high_reliability_critical', 'consumer_electronics'
        ]
        
        compatibility_data = []
        for chip_id in self.chip_ids:
            for app in application_scenarios:
                # 适配性评分 0-100（基于某些特性）
                if app == 'high_frequency_computing':
                    score = np.random.normal(75, 20)
                elif app == 'power_efficient_device':
                    score = np.random.normal(70, 25)
                elif app == 'high_reliability_critical':
                    score = np.random.normal(65, 30)
                else:
                    score = np.random.normal(80, 15)
                
                compatibility_data.append({
                    'chip_id': chip_id,
                    'application_scenario': app,
                    'compatibility_score': np.clip(score, 0, 100),
                    'compatibility_level': 'compatible' if score > 70 else 'marginal' if score > 50 else 'incompatible',
                })
        
        return pd.DataFrame(compatibility_data)
    
    def generate_incremental_evolution_data(self):
        """生成增量演化数据（Phase 4 增量学习需要）"""
        # 模拟芯片参数随着更新步骤的演化
        evolution_data = []
        
        for chip_id in self.chip_ids:
            # 每个芯片有多个时间点的参数记录
            for update_step in range(1, 6):  # 5个更新步骤
                evolution_data.append({
                    'chip_id': chip_id,
                    'update_step': update_step,
                    'vdd_voltage': np.random.normal(3.3, 0.1),
                    'idd_dynamic_ma': np.random.normal(150, 50),
                    'propagation_delay_ns': np.random.normal(5.5, 2),
                    'fmax_mhz': np.random.normal(300, 80),
                    'model_accuracy': 0.75 + update_step * 0.03,  # 精度随步骤提升
                    'model_version': f"v1.{update_step}",
                })
        
        return pd.DataFrame(evolution_data)
    
    def generate_repair_strategy_library(self):
        """生成修复策略库（Phase 5需要）"""
        failure_modes = ['physical_damage', 'thermal_accumulation', 
                        'noise_margin_insufficient', 'multi_param_combined']
        
        strategies = {}
        for mode in failure_modes:
            if mode == 'physical_damage':
                strategies[mode] = {
                    'description': 'Physical damage detected',
                    'repair_method': 'Component replacement or rejection',
                    'success_rate': 0.0,  # 无法修复
                    'cost_yuan': 0,
                }
            elif mode == 'thermal_accumulation':
                strategies[mode] = {
                    'description': 'Thermal degradation detected',
                    'repair_method': 'Thermal management enhancement, derate operation',
                    'success_rate': 0.85,
                    'cost_yuan': 150,
                }
            elif mode == 'noise_margin_insufficient':
                strategies[mode] = {
                    'description': 'Signal integrity issue detected',
                    'repair_method': 'Frequency derate, voltage adjustment',
                    'success_rate': 0.75,
                    'cost_yuan': 80,
                }
            else:
                strategies[mode] = {
                    'description': 'Multiple parameter degradation detected',
                    'repair_method': 'Limited application scope, frequency cap',
                    'success_rate': 0.6,
                    'cost_yuan': 120,
                }
        
        return strategies
    
    def _calculate_appearance_score(self, data):
        """计算外观质量评分"""
        scores = np.zeros(self.n_samples)
        scores += 100 - np.clip(data['pin_flatness_deviation_um'] / 2, 0, 50)
        scores += 100 - np.clip(data['solder_pad_oxidation_percent'], 0, 30)
        scores += 100 - np.clip(data['package_scratch_depth_um'] / 5, 0, 50)
        scores += 100 - np.clip(np.abs(data['warpage_um']) / 2, 0, 50)
        scores += data['pin_coplanarity_percent']
        scores += 100 - np.clip(np.abs(data['package_size_deviation_percent']) * 50, 0, 30)
        return scores / 6
    
    def _calculate_dc_score(self, data, appearance_scores):
        """计算DC电气质量评分（依赖外观）"""
        scores = np.zeros(self.n_samples)
        scores += 100 * (1 - np.abs(data['vdd_voltage'] - 3.3) / 0.5)
        scores += 100 - np.clip(data['idd_static_ma'], 0, 20)
        scores += 100 - np.clip(data['idd_dynamic_ma'] / 3, 0, 50)
        scores += 100 * (np.clip(data['voh_voltage'], 2.5, 3.3) / 3.3)
        scores += 100 - np.clip(data['vol_voltage'] * 100, 0, 20)
        scores = scores / 5
        
        # 外观质量影响DC测试可靠性
        scores = scores * (0.8 + appearance_scores / 500)
        return np.clip(scores, 0, 100)
    
    def _calculate_ac_score(self, data, dc_scores):
        """计算AC电气质量评分（依赖DC）"""
        scores = np.zeros(self.n_samples)
        scores += 100 - np.clip(data['setup_time_ns'], 0, 10)
        scores += 100 - np.clip(data['hold_time_ns'] * 20, 0, 20)
        scores += 100 - np.clip(data['propagation_delay_ns'], 0, 15)
        scores += 100 - np.clip(data['rise_time_ns'] * 30, 0, 30)
        scores += 100 - np.clip(data['fall_time_ns'] * 40, 0, 30)
        scores += np.clip(data['fmax_mhz'] / 4, 0, 100)
        scores = scores / 6
        
        # DC质量影响AC测试可靠性
        scores = scores * (0.8 + dc_scores / 500)
        return np.clip(scores, 0, 100)
    
    def generate_all(self, output_dir='./synthetic_data'):
        """生成所有增强型数据文件"""
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"[INFO] 正在生成 {self.n_samples} 个芯片的增强型合成数据...")
        
        # 生成外观、电气、功能参数
        appearance_df = self.generate_appearance_params()
        appearance_scores = appearance_df['appearance_quality_score'].values
        
        dc_df = self.generate_dc_electrical_params(appearance_scores)
        dc_scores = dc_df['dc_electrical_quality_score'].values
        
        ac_df = self.generate_ac_electrical_params(dc_scores)
        ac_scores = ac_df['ac_electrical_quality_score'].values
        
        functional_df = self.generate_functional_params(ac_scores)
        functional_scores = functional_df['functional_quality_score'].values
        
        aging_df = self.generate_aging_conditions_and_results(
            np.array([appearance_scores, dc_scores, ac_scores, functional_scores])
        )
        
        # 合并基线数据
        baseline_df = pd.DataFrame({'chip_id': self.chip_ids})
        baseline_df = pd.concat([baseline_df, appearance_df], axis=1)
        baseline_df = pd.concat([baseline_df, dc_df], axis=1)
        baseline_df = pd.concat([baseline_df, ac_df], axis=1)
        baseline_df = pd.concat([baseline_df, functional_df], axis=1)
        baseline_df = pd.concat([baseline_df, aging_df], axis=1)
        
        # 添加生产日期和模型信息
        baseline_df['production_date'] = [
            (datetime(2024, 1, 1) + timedelta(days=int(np.random.uniform(0, 365)))).strftime('%Y-%m-%d')
            for _ in range(self.n_samples)
        ]
        baseline_df['chip_model'] = np.random.choice(['MODEL_A', 'MODEL_B', 'MODEL_C'], self.n_samples)
        
        # 保存基线数据
        baseline_path = os.path.join(output_dir, 'chip_baseline_data_extended.csv')
        baseline_df.to_csv(baseline_path, index=False)
        print(f"✅ 已保存：{baseline_path}")
        
        # 生成并保存测试序列数据（Phase 3）
        test_sequence_df = self.generate_test_sequence_data()
        test_sequence_path = os.path.join(output_dir, 'chip_test_sequence.csv')
        test_sequence_df.to_csv(test_sequence_path, index=False)
        print(f"✅ 已保存：{test_sequence_path}")
        
        # 生成并保存扩展故障标签（Phase 5-6）
        failures_df = self.generate_failure_labels_extended(n_failures=1000)
        failures_path = os.path.join(output_dir, 'chip_failure_labels_extended.csv')
        failures_df.to_csv(failures_path, index=False)
        print(f"✅ 已保存：{failures_path}")
        
        # 生成并保存适配性矩阵（Phase 5）
        compat_df = self.generate_compatibility_matrix()
        compat_path = os.path.join(output_dir, 'chip_compatibility_matrix.csv')
        compat_df.to_csv(compat_path, index=False)
        print(f"✅ 已保存：{compat_path}")
        
        # 生成并保存增量演化数据（Phase 4）
        evolution_df = self.generate_incremental_evolution_data()
        evolution_path = os.path.join(output_dir, 'chip_incremental_evolution.csv')
        evolution_df.to_csv(evolution_path, index=False)
        print(f"✅ 已保存：{evolution_path}")
        
        # 生成并保存修复策略库（Phase 5）
        strategy_lib = self.generate_repair_strategy_library()
        strategy_path = os.path.join(output_dir, 'repair_strategy_library.json')
        with open(strategy_path, 'w', encoding='utf-8') as f:
            json.dump(strategy_lib, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存：{strategy_path}")
        
        print("\n" + "="*60)
        print("📊 增强型合成数据生成完成！")
        print("="*60)
        print(f"\n生成的文件：")
        print(f"  1. chip_baseline_data_extended.csv ({self.n_samples} 个芯片，45+ 个字段)")
        print(f"  2. chip_test_sequence.csv (测试序列和成本数据)")
        print(f"  3. chip_failure_labels_extended.csv (1000 个故障样本)")
        print(f"  4. chip_compatibility_matrix.csv (适配性评分)")
        print(f"  5. chip_incremental_evolution.csv (增量学习数据)")
        print(f"  6. repair_strategy_library.json (修复策略库)")
        print("\n支持阶段：Phase 1-6 (完整覆盖)")


if __name__ == '__main__':
    generator = EnhancedSyntheticDataGenerator(n_samples=1000)
    generator.generate_all(output_dir='D:\\laboratory_projects\\solid_waste_projects_260526\\synthetic_data')
