# Phase 1-6 数据支持映射表

**生成日期**: 2026年5月26日

---

## 📊 完整映射矩阵

```
┌─────────┬────────────────────────────────────────────────────────────────┐
│ Phase   │ 核心任务                   │ 所需数据文件           │ 就绪状态  │
├─────────┼─────────────────────────────────────────────────────────────┤
│ Phase 1 │ 知识图谱框架构建           │ chip_baseline_data_extended  │ ✅ 完全 │
│ (1-6月) │ ≥500实体, ≥1000关系        │                              │        │
│         │ TransE嵌入                 │ chip_aging_curves            │ ✅ 完全 │
├─────────┼─────────────────────────────────────────────────────────────┤
│ Phase 2 │ GCN+GAT特征优化            │ chip_baseline_data_extended  │ ✅ 完全 │
│ (6月)   │ Shapley值分析              │ (39列特征, 1000样本)         │        │
│         │ 核心指标筛选 (5-10个)      │ chip_failure_labels_extended │ ✅ 完全 │
│         │ 精准度 ≥88%                │ (1000个失败样本)             │        │
├─────────┼─────────────────────────────────────────────────────────────┤
│ Phase 3 │ MDP + PPO强化学习          │ chip_test_sequence           │ ✅ 完全 │
│ (6-7月) │ 动态检测顺序优化           │ (4个测试阶段, 成本/时间)     │        │
│         │ 时间↓ 30%, 精准度≥91%      │ chip_baseline_data_extended  │ ✅ 完全 │
├─────────┼─────────────────────────────────────────────────────────────┤
│ Phase 4 │ CSS增量学习机制             │ chip_incremental_evolution   │ ✅ 完全 │
│ (7-8月) │ 特征权重自适应             │ (5个更新步骤, 精度升级)      │        │
│         │ 模型迁移测试               │ chip_baseline_data_extended  │ ✅ 完全 │
│         │ 精准度 ≥88%                │                              │        │
├─────────┼─────────────────────────────────────────────────────────────┤
│ Phase 5 │ 适配性预测头               │ chip_compatibility_matrix    │ ✅ 完全 │
│ (8-9月) │ 修复策略映射库             │ (4个应用场景, 1000芯片)      │        │
│         │ 预装配验证流程             │ chip_failure_labels_extended │ ✅ 完全 │
│         │ 精准度 ≥95%                │ (1000个故障模式)             │        │
│         │ 时间 ≤500ms                │ repair_strategy_library      │ ✅ 完全 │
│         │                             │ (4种修复方案, 成功率+成本)   │        │
├─────────┼─────────────────────────────────────────────────────────────┤
│ Phase 6 │ 全流程系统集成             │ 全部6个数据文件集成          │ ✅ 完全 │
│ (9-12月)│ 现场试点应用               │ + 系统集成脚本               │        │
│         │ 知识产权申报               │                              │        │
│         │ KPI: 拆解≥99%, 无损≥95%   │                              │        │
└─────────┴────────────────────────────────────────────────────────────────┘
```

---

## 🔗 数据文件使用详表

### 1. chip_baseline_data_extended.csv (1000行 × 39列)

**使用频率**: ★★★★★ (最高)  
**支持Phase**: 1, 2, 3, 4, 5, 6

| 需求 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 |
|------|---------|---------|---------|---------|---------|---------|
| 参数提取 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 特征工程 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 模型训练 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 验证评估 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**关键列**:
- Phase 1: chip_id, 所有39列
- Phase 2: *_quality_score (11列) + 功能参数 (3列)
- Phase 3: test_pass字段 + 参数相关性
- Phase 4: 电压/电流/频率/延迟 4个关键列
- Phase 5: 所有评分 + risk_level
- Phase 6: 综合评分 + 通过/失败标记

---

### 2. chip_test_sequence.csv (4000行 × 7列)

**使用频率**: ★★★★☆  
**支持Phase**: 3, 6

| 需求 | Phase 3 | Phase 6 |
|------|---------|---------|
| 成本优化 | ✅ | ✅ |
| 顺序优化 | ✅ | ✅ |
| 时间分析 | ✅ | ✅ |

**关键用法**:
```python
# Phase 3: PPO奖励函数设计
def reward(action):
    cumulative_cost = test_sequence.loc[...]['cumulative_cost_yuan']
    cumulative_time = test_sequence.loc[...]['cumulative_time_minutes']
    # 优化目标: cost↓30%, time↓30%, accuracy≥91%
    return -cost + -time + accuracy_bonus

# Phase 6: 系统优化验证
before = test_sequence.groupby('test_stage')['cumulative_cost_yuan'].max()
after  = optimized_sequence_cost  # 使用PPO策略后的成本
improvement = (before - after) / before * 100  # ≥30%
```

---

### 3. chip_failure_labels_extended.csv (1000行 × 6列)

**使用频率**: ★★★★★ (最高)  
**支持Phase**: 2, 5, 6

| 需求 | Phase 2 | Phase 5 | Phase 6 |
|------|---------|---------|---------|
| 特征相关性 | ✅ | - | - |
| 故障分类 | - | ✅ | ✅ |
| 模型训练 | - | ✅ | ✅ |
| 修复策略 | - | ✅ | ✅ |

**关键用法**:
```python
# Phase 2: 计算Shapley值
# 问题: 哪些参数最容易导致失败?
failures_by_mode = failures.groupby('failure_mode')
for mode in failures_by_mode:
    # 反推导致该故障模式的参数组合

# Phase 5-6: 故障预测和修复建议
# 输入: 新芯片的39个参数
# 输出: 故障概率 + 推荐修复策略
predictions = {
    'physical_damage': 0.05,      # 5% 概率
    'thermal': 0.12,              # 12% 概率
    'noise_margin': 0.08,         # 8% 概率
    'multi_param': 0.15,          # 15% 概率
}
recommend_strategy(predictions)  # 选择修复策略
```

---

### 4. chip_test_sequence.csv (4000行 × 7列)

**使用频率**: ★★★★☆  
**支持Phase**: 3, 6

**关键字段**:
- stage_order: 1-4 (测试顺序)
- test_cost_yuan: 单阶段成本 (50-250元范围)
- test_time_minutes: 单阶段时间 (10-120分钟范围)
- cumulative_*: 累计成本和时间

**数据分布**:
```
外观测试 (appearance):
  成本: 50-100元
  时间: 10-20分钟
  
DC电气 (dc_electrical):
  成本: 80-150元
  时间: 30-60分钟
  
AC电气 (ac_electrical):
  成本: 150-250元
  时间: 60-120分钟
  
功能 (functional):
  成本: 100-200元
  时间: 45-90分钟
  
总计: 330-590元, 145-270分钟
```

---

### 5. chip_compatibility_matrix.csv (4000行 × 4列)

**使用频率**: ★★★☆☆  
**支持Phase**: 5, 6

| 需求 | Phase 5 | Phase 6 |
|------|---------|---------|
| 应用场景匹配 | ✅ | ✅ |
| 品级划分 | ✅ | ✅ |
| 销售推荐 | ✅ | ✅ |

**应用场景**:
```
高频计算 (high_frequency_computing):
  例: 数据中心CPU/GPU
  关键参数: fmax_mhz (目标>300MHz)
  
低功耗 (power_efficient_device):
  例: 物联网/嵌入式
  关键参数: idd_dynamic_ma (目标<100mA)
  
高可靠性 (high_reliability_critical):
  例: 医疗设备/航空航天
  关键参数: reliability_risk_level (目标=low)
  
消费电子 (consumer_electronics):
  例: 手机/平板电脑
  关键参数: appearance_quality_score (目标>80)
```

**评分转换**:
```python
# 实现品级划分
for chip in chips:
    scores = [
        compat[chip, 'high_frequency'],
        compat[chip, 'power_efficient'],
        compat[chip, 'high_reliability'],
        compat[chip, 'consumer']
    ]
    if all(s > 85 for s in scores):
        grade = 'A'  # 通用型, 高价值
    elif max(scores) > 70:
        grade = 'B'  # 专用型, 中等价值
    elif max(scores) > 50:
        grade = 'C'  # 限定型, 低价值
    else:
        grade = 'D'  # 报废
```

---

### 6. chip_incremental_evolution.csv (5000行 × 8列)

**使用频率**: ★★★☆☆  
**支持Phase**: 4

| 需求 | Phase 4 |
|------|---------|
| 增量学习模拟 | ✅ |
| 模型升级验证 | ✅ |

**数据含义**:
```
每个芯片有5个版本的参数记录:

v1.1 (初始, 基于合成数据):
  精度: 78%
  参数: 噪声较大
  
v1.2-v1.5 (进化过程):
  每次更新精度↑3%
  参数逐步拟合真实数据
  
v1.5 (最终):
  精度: 90%
  参数: 接近真实值
```

**CSS机制实现**:
```python
# Continuous/Streaming Stateless Learning
class CSS_Learner:
    def __init__(self):
        self.model_v = 1.1
        self.accuracy = 0.78
    
    def update(self, new_batch):
        # 1. 学习新数据
        gradients = compute_gradients(new_batch)
        # 2. 更新模型 (避免灾难遗忘)
        apply_elastic_weight_consolidation(gradients)
        # 3. 验证性能
        old_acc = test_old_data()  # 确保不下降
        new_acc = test_new_data()
        # 4. 升级版本
        if new_acc > self.accuracy:
            self.accuracy = new_acc
            self.model_v += 0.1
        return self.model_v
```

---

### 7. repair_strategy_library.json

**使用频率**: ★★★☆☆  
**支持Phase**: 5, 6

**4种修复策略**:
```json
{
  "physical_damage": {
    "success_rate": 0.0,
    "cost": 0,
    "action": "REJECT"
  },
  "thermal_accumulation": {
    "success_rate": 0.85,
    "cost": 150,
    "action": "REPAIR_THERMAL_MGMT"
  },
  "noise_margin_insufficient": {
    "success_rate": 0.75,
    "cost": 80,
    "action": "DERATE_FREQUENCY"
  },
  "multi_param_combined": {
    "success_rate": 0.6,
    "cost": 120,
    "action": "LIMIT_APPLICATION_SCOPE"
  }
}
```

**决策逻辑**:
```python
def repair_decision(chip_params):
    failure_probs = predict_failure_modes(chip_params)
    
    total_cost = 0
    success_prob = 1.0
    
    for mode, prob in failure_probs.items():
        if prob > threshold:
            strategy = repair_strategies[mode]
            total_cost += strategy['cost'] * prob
            success_prob *= strategy['success_rate']
    
    if success_prob * value > total_cost:
        return "REPAIR"
    elif failure_probs['physical_damage'] > 0.5:
        return "REJECT"
    else:
        return "LIMIT_USE"
```

---

## 🎯 数据就绪状况总结

### ✅ 完全就绪 (Phase 1-6) - 最坏打算版本

| 数据文件 | 准备完成 | 质量 | 规模 | 覆盖 |
|---------|---------|------|------|------|
| chip_baseline_data_extended.csv | ✅ | 高 | 1000 | Phase 1-6 |
| chip_test_sequence.csv | ✅ | 高 | 4000 | Phase 3, 6 |
| chip_failure_labels_extended.csv | ✅ | 中 | 1000 | Phase 2, 5, 6 |
| chip_aging_curves.csv | ✅ | 中 | 90K | Phase 1, 4 |
| **chip_incremental_evolution_robust.csv** | ✅ | 中 | **20000** | **Phase 4 (强化)** |
| **chip_compatibility_matrix_robust.csv** | ✅ | 中 | **12000** | **Phase 5 (12个场景)** |
| **chip_field_trial_simulation.csv** | ✅ | 中 | **13000+** | **Phase 6 (现场模拟)** |
| **chip_failure_scenarios.csv** | ✅ | 中 | **25+** | **Phase 5-6 (故障库)** |
| **chip_lifecycle_data.csv** | ✅ | 中 | **1000** | **Phase 6 (生命周期)** |

### 📌 最坏打算版本战略

**假设条件**: 永不接收真实企业数据，完全基于现有合成数据完成项目

**数据策略变更**:
- Phase 4: 从5步演化 → 10步演化 (20000行数据), 包含灾难遗忘场景
- Phase 5: 从4个应用 → 12个应用场景 (12000行数据), 覆盖航天/医疗/汽车等
- Phase 6: 新增虚拟现场试点模拟 (2个试点, 180天运营数据)
- Phase 6: 新增生命周期追踪 (生产→检测→部署→维修→报废)

**实施原则**:
- ✅ 不依赖企业真实数据
- ✅ 充分利用和优化现有合成数据
- ✅ 添加随机性和复杂性，接近真实情况
- ✅ Phase 1-6 全部可独立完成

---

## 📈 项目进度与数据可用性

```
现在 (5月26日)           →  Phase 1-6 全部可立即开始 ✅
                            数据 100% 就绪 (合成数据)
                           
6月15日 (Phase 1完)    →  Phase 2 可以开始
                            依赖: Phase 1的知识图谱输出 ✅
                           
6月30日 (Phase 2完)    →  Phase 3 可以开始
                            依赖: Phase 2的核心指标定义 ✅
                           
7月20日 (Phase 3完)    →  Phase 4 可以开始
                            数据: 完全就绪 (20000行强化数据) ✅
                           
8月31日 (Phase 4完)    →  Phase 5 可以开始
                            数据: 完全就绪 (12个应用场景) ✅
                           
9月30日 (Phase 5完)    →  Phase 6 可以开始
                            数据: 完全就绪 (虚拟现场+生命周期) ✅
                           
12月31日 (Phase 6完)   →  项目交付完成
                            全部基于合成数据，无需真实数据
```

---

## ✅ 检查清单

在启动各阶段前，请确认:

### Phase 1 启动前 ✅
- [ ] chip_baseline_data_extended.csv 可读
- [ ] 39列全部完整, 无缺失值
- [ ] 1000个芯片ID唯一
- [ ] 参数范围检查通过

### Phase 2 启动前 ✅
- [ ] Phase 1完成知识图谱构建
- [ ] chip_failure_labels_extended.csv 加载成功
- [ ] 1000个故障样本覆盖4种模式
- [ ] Shapley计算库 (shap, lime) 安装

### Phase 3 启动前 ✅
- [ ] Phase 2完成核心指标筛选 (≤10个)
- [ ] chip_test_sequence.csv 成本/时间数据有效
- [ ] 4个测试阶段顺序确定
- [ ] OpenAI Gym/RLlib 环境配置

### Phase 4 启动前 ⚠️
- [ ] Phase 3完成PPO智能体训练
- [ ] chip_incremental_evolution.csv 结构理解
- [ ] 增量学习库安装 (river, continual-learning)
- [ ] 9月: 补充真实企业演化数据

### Phase 5 启动前 ⚠️
- [ ] Phase 4完成模型迁移测试 (≥88%精度)
- [ ] chip_compatibility_matrix.csv 应用场景定义
- [ ] repair_strategy_library.json 修复方案确认
- [ ] 9月: 验证修复策略的真实成功率

### Phase 6 启动前 ⚠️
- [ ] Phase 5完成适配性预测 (≥95%精度)
- [ ] 所有模型和策略库集成完成
- [ ] 系统集成脚本编写和测试
- [ ] 9月: 准备现场试点部署

---

**文档版本**: v1.0  
**最后更新**: 2026年5月26日  
**维护负责人**: 项目技术团队
