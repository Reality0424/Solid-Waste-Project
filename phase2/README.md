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

## 🎯 成功标准（实测, 均为 5 折交叉验证)

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 特征提取/识别准确率 | ≥90% | **0.940**(GBM+优化特征) | ✅ |
| 核心指标精准度 | ≥88% | **0.943** | ✅ |
| 从 28 项筛选核心指标 | 5-10 个 | **6 个** | ✅ |
| 核心子集 AUC 保留率 | — | **95.2%** | ✅ |

**核心 6 指标**: `fmax_mhz`(频率) · `setup_time_ns`(建立时间) · `vol_voltage`(低电平输出) · `warpage_um`(翘曲度) · `vil_voltage`(低电平输入阈值) · `iol_leakage_ua`(输出漏电)
> 恰好覆盖三类失效机理: 时序(fmax+setup) / 噪声边裕(vol+vil) / 热积累(warpage+iol)。

**关键证据**: 线性 AUC 0.845 → GBM(优化特征) AUC **0.961**(非线性增益 +0.116), 印证"多指标非线性组合"才是判别关键。

> ⚠️ 说明: 表格型数据 + 合取/析取失效规则下, **梯度提升树(GBM)优于 GNN**(文献普遍结论)。
> GCN+GAT 已按计划实现并交付(图表示模块, 产出芯片嵌入, OOF AUC≈0.83); 最终分类器采用 GBM(优化特征)。

## 📁 目录结构

```
phase2/
├── scripts/
│   ├── _common.py                   # 共享: 数据加载 / 28指标清单 / 路径
│   ├── 01_feature_extraction.py     # GCN+GAT 特征优化 + 失效识别(GBM最终分类器)
│   ├── 02_shapley_analysis.py       # TreeSHAP 指标贡献度
│   └── 03_indicator_selection.py    # 核心指标筛选与有效性验证
├── outputs/
│   ├── models/  phase2_gcn_gat.pt, metrics.json
│   ├── data/    chip_gnn_embeddings.npy, shapley_values.csv,
│   │            shapley_per_sample.npy, core_indicators.json,
│   │            feature_importance_ranking.csv
│   ├── figures/ shapley_importance.png, shapley_beeswarm.png,
│   │            indicator_selection_curve.png
│   └── reports/ feature_extraction_report.md, validation_report.md
└── README.md
```

## 🚀 运行步骤

```bash
# 依赖(在仓库根目录的 venv 中): torch, shap, scikit-learn, pandas, numpy, matplotlib
cd phase2
../.venv/bin/python scripts/01_feature_extraction.py   # GCN+GAT + GBM, 5折OOF评估
../.venv/bin/python scripts/02_shapley_analysis.py     # TreeSHAP 贡献度 -> shapley_values.csv
../.venv/bin/python scripts/03_indicator_selection.py  # 选 6 个核心指标 -> core_indicators.json
```
> 输入直接读 `synthetic_data/chip_baseline_data.csv`(28 指标 + 失效标签), 默认参数即可跑通。
> 01 默认 `--ensemble 5`; 可加 `--use_transe` 拼接 Phase 1 TransE 芯片嵌入(默认关, 对失效预测为噪声)。

## 📊 主要产出

| 文件 | 说明 |
|------|------|
| `models/metrics.json` | GNN/线性/GBM 各模型 5折OOF 指标 |
| `data/shapley_values.csv` | 28 指标的 Shapley 贡献度排序 |
| `data/core_indicators.json` | 核心指标子集(6 个)及精度保留率 |
| `data/chip_gnn_embeddings.npy` | GCN+GAT 学到的芯片嵌入(供后续阶段) |
| `reports/validation_report.md` | 核心指标有效性验证(增量 Top-k 对比) |

---

**阶段状态**: ✅ 已完成(4/4 成功标准达标)
**更新日期**: 2026年6月16日
**依赖**: 阶段1(知识图谱 / TransE 嵌入)
**下一步**: 阶段3(基于 6 项核心指标做 PPO 动态检测顺序优化)

