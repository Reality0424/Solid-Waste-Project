# 合成数据集目录

此目录包含项目生成的合成芯片检测数据集。

## 数据文件说明

### 1. chip_baseline_data.csv
- **说明**: 1000个芯片的基础参数
- **行数**: 1000 (每个芯片一行)
- **列数**: 28 (6物理 + 9电气DC + 6电气AC + 3功能 + 4老化条件)
- **关键列**:
  - `chip_id`: 芯片ID (CHIP_00000 to CHIP_00999)
  - `pin_flatness_deviation_um`: 引脚平整度偏差
  - `solder_pad_oxidation_um`: 焊盘氧化
  - `vdd_voltage`: 电源电压
  - `failure_status`: 0=失效, 1=正常
  - `failure_mode`: 失效模式 (normal/physical_damage/noise_margin/thermal_accumulation/multi_param)

### 2. chip_aging_curves.csv
- **说明**: 芯片老化过程的时间序列数据
- **行数**: 90,424 (1000芯片 × ~90小时/芯片)
- **列数**: 7 (时间 + 参数)
- **关键列**:
  - `chip_id`: 芯片ID
  - `aging_hour`: 老化时间 (0-168小时)
  - `vdd_voltage`: 电源电压随时间变化
  - `idd_dynamic_ma`: 动态电流
  - `voh_voltage`: 高电平输出电压
  - `vol_voltage`: 低电平输出电压
  - `propagation_delay_ns`: 传播延迟

### 3. chip_failure_labels.csv
- **说明**: 失效芯片的标注数据
- **行数**: 100 (所有失效芯片)
- **列数**: 6 (标注信息)
- **关键列**:
  - `chip_id`: 失效芯片ID
  - `failure_mode`: 失效模式
  - `failure_time_hours`: 失效发生时间
  - `failure_phenomenon`: 失效现象描述
  - `root_cause`: 根本原因分析
  - `predicted_mttf`: 预测平均失效时间

## 数据统计

| 指标 | 数值 |
|------|------|
| 总芯片数 | 1000 |
| 正常芯片 | 900 (90%) |
| 失效芯片 | 100 (10%) |
| 时间序列点数 | 90,424 |
| 特征维数 | 28 |
| 失效模式数 | 4 |

## 失效模式分布

- **物理损伤** (13%): 平整度偏差、翘曲度大、划伤
- **噪声余裕不足** (35%): VOH/VOL压缩、VIH/VIL收敛
- **热积累** (30%): 高功耗、温度积累、指数劣化
- **多参数叠加** (22%): 多个参数组合恶化

## 使用示例

### Python加载数据
```python
import pandas as pd
import numpy as np

# 加载基础参数
df_baseline = pd.read_csv('chip_baseline_data.csv')
print(f"加载 {len(df_baseline)} 个芯片样本")

# 加载老化曲线
df_aging = pd.read_csv('chip_aging_curves.csv')
print(f"加载 {len(df_aging)} 个时间序列数据点")

# 加载失效标注
df_failures = pd.read_csv('chip_failure_labels.csv')
print(f"加载 {len(df_failures)} 个失效样本标注")

# 数据探索
print(df_baseline.describe())
```

### 数据访问
```python
# 获取特定芯片的基础数据
chip_data = df_baseline[df_baseline['chip_id'] == 'CHIP_00000']

# 获取该芯片的老化曲线
aging_curve = df_aging[df_aging['chip_id'] == 'CHIP_00000']

# 检查是否失效
if chip_data['failure_status'].values[0] == 0:
    failure_info = df_failures[df_failures['chip_id'] == 'CHIP_00000']
    print(failure_info['failure_mode'].values[0])
```

## 数据质量检查

✅ **通过质量检验**:
- 所有VOH > VOL ✓
- 所有VIH > VIL ✓
- 所有物理参数在有效范围内 ✓
- 没有缺失值 ✓
- 时间序列连续且光滑 ✓

## 后续流程

1. **阶段1**: 用于知识图谱构建
2. **阶段2**: 用于GCN+GAT特征提取
3. **阶段3**: 用于强化学习策略训练
4. **后续**: 与企业真实数据混合训练

---

**数据生成日期**: 2026年5月26日  
**数据版本**: v1.0  
**下一更新**: 与企业数据融合

