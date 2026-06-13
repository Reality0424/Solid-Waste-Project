# 阶段2：指标特征优化与体系建立

**时间**: 2026年6月1日 - 2026年6月30日  
**主要技术**: GCN、GAT、Shapley值分析  
**关键产出**: 核心指标体系（5-10个关键指标）

## 📍 核心任务

### 任务2.1 - GCN+GAT混合架构开发 (Week 1)
- 开发图卷积网络(GCN)与图注意力机制(GAT)混合架构
- 优化指标特征提取能力
- 在1000个合成样本上进行训练

### 任务2.2 - Shapley值贡献度分析 (Week 2)
- 开发基于Shapley值的指标贡献度量化模型
- 计算每个指标的边际贡献
- 识别核心指标子集

### 任务2.3 - 核心指标有效性验证 (Week 3-4)
- 开展对比试验验证
- 验证核心指标子集的有效性
- 建立质量检测指标体系

## 🎯 成功标准

- ✅ 核心指标精准度 ≥ 88%
- ✅ 特征提取准确率 ≥ 90%
- ✅ 从28参数筛选出5-10个核心指标
- ✅ 体系完整性评分 ≥ 85%

## 📁 目录结构

```
phase2/
├── scripts/
│   ├── 01_feature_extraction.py     # 特征提取脚本
│   ├── 02_shapley_analysis.py       # Shapley分析脚本
│   └── 03_indicator_selection.py    # 指标选择脚本
├── notebooks/
│   ├── 01_model_training.ipynb      # 模型训练
│   ├── 02_shapley_visualization.ipynb # Shapley可视化
│   └── 03_validation.ipynb          # 验证分析
├── outputs/
│   ├── gcn_gat_model.h5
│   ├── shapley_values.csv
│   ├── core_indicators.json
│   └── validation_report.md
└── README.md
```

## 🚀 运行步骤

```bash
cd phase2

# 1. 特征提取
python scripts/01_feature_extraction.py \
    --graph_path ../results/models/phase1_transe.pkl \
    --data_path ../data/synthetic/

# 2. Shapley分析
python scripts/02_shapley_analysis.py \
    --model_path outputs/gcn_gat_model.h5 \
    --data_path ../data/synthetic/

# 3. 指标选择
python scripts/03_indicator_selection.py \
    --shapley_path outputs/shapley_values.csv \
    --output_path outputs/core_indicators.json
```

## 📊 预期输出

| 文件 | 说明 |
|------|------|
| `gcn_gat_model.h5` | 训练完成的混合网络模型 |
| `shapley_values.csv` | 28个参数的Shapley值排序 |
| `core_indicators.json` | 核心指标子集(5-10个) |
| `validation_report.md` | 对比试验报告 |

---

**阶段状态**: 未开始  
**依赖**: 阶段1（知识图谱）

