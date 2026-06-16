# Phase 1 评估报告

**生成时间**: 2026-06-16T18:25:28.039856

## 📊 图谱完整性评估

- **节点总数**: 1042 (目标 ≥500, ✅)
- **关系总数**: 8179 (目标 ≥1000, ✅)
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
- HAS_ABNORMAL: 1107
- CORRELATES_WITH: 18
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
- **初始 Loss**: 1.0129
- **最终 Loss**: 0.5676
- **收敛**: ✅ 是

### 链路预测 (raw, 候选实体数=1042, 评估三元组=817)
- **MRR**: 0.2386
- **Hits@1**: 0.1346
- **Hits@3**: 0.2913
- **Hits@10**: 0.4559
- **Mean Rank**: 268.4

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
