# Phase 1 评估报告

**生成时间**: 2026-06-16T11:14:57.844532

## 📊 图谱完整性评估

- **节点总数**: 1042 (目标 ≥500, ✅)
- **关系总数**: 8072 (目标 ≥1000, ✅)
- **完整性评分**: 100.00%

### 节点类型分布
- ChipModel: 3
- FailureMode: 5
- TestStage: 5
- Dimension: 4
- Parameter: 25
- Chip: 1000

### 关系类型分布
- UNDERGOES_TEST: 5000
- HAS_ABNORMAL: 1014
- CORRELATES_WITH: 4
- BELONGS_TO: 25
- MEASURED_IN: 25
- PRECEDES: 4
- OF_MODEL: 1000
- EXHIBITS: 1000

## 🧠 模型质量评估

- **模型存在**: ✅ 是
- **嵌入维度**: 100
- **嵌入实体数**: 1042
- **嵌入关系数**: 8
- **初始 Loss**: 1.0141
- **最终 Loss**: 0.5630
- **收敛**: ✅ 是

### 链路预测 (raw, 候选实体数=1042, 评估三元组=807)
- **MRR**: 0.2352
- **Hits@1**: 0.1307
- **Hits@3**: 0.2900
- **Hits@10**: 0.4535
- **Mean Rank**: 277.2

## ✅ 架构验证

- **架构有效**: ✅ 是
- **已找到标签**: ChipModel, FailureMode, TestStage, Dimension, Parameter, Chip

## 🎯 成功标准检查

- ✅ 知识图谱实体数 ≥ 500
- ✅ 关系数 ≥ 1000
- ✅ 完整性验证率 ≥ 90%
- ✅ TransE 模型收敛
- ✅ 架构标签完整

**总体状态**: 5/5 标准通过
