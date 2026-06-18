# 阶段3：动态检测策略优化

**时间**: 2026年6月23日 - 2026年7月20日
**主要技术**: MDP、PPO 强化学习（序贯检测 / 主动特征获取）
**关键产出**: 动态检测顺序策略（检测时间降低 ≥30%）

## 📍 核心任务
- **3.1 MDP 建模**：状态 = 已测指标值 + 掩码；动作 = {测第 j 项} ∪ {停止并判定}；奖励 = −时间成本 /（判对+ 判错−，失效类加权抵消不平衡）。
- **3.2 PPO 智能体**：PyTorch 从零实现 actor-critic + GAE + clip + 动作屏蔽（不依赖 gym/SB3）；并行 64 环境 × 32 步 × 400 次更新（约 80 万步）。
- **3.3 序贯检测验证**：测试集上贪心执行策略，与"全检 28 项"基线对比时间/准确率/召回。

## 🎯 成功标准（实测，测试集）

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 检测时间降低 | ≥30% | **92.9%**（成本 100 → 7.1，平均测 4.2 项） | ✅ |
| 准确率 | ≥91% | **0.917** | ✅ |
| 召回（额外） | — | **0.543**（全检仅 0.457） | ✅ 更优 |
| 平衡准确率（额外） | — | **0.754**（全检 0.719） | ✅ 更优 |

> 动态策略不仅省时 93%，**召回与平衡准确率还高于全检**——因为它优先测对失效最有判别力的指标。
> 学到的高频检测项（vol_voltage、warpage、vih、vil、idd_dynamic…）与阶段2 的核心指标（噪声边裕/热）一致,跨阶段自洽。

## 📁 结构
```
phase3/
├── scripts/
│   ├── _common.py                 # 数据 / 28指标 / 时间成本模型 / 掩码分类器
│   ├── 01_mdp_setup.py            # MDP 定义 + 掩码分类器训练
│   ├── 02_ppo_training.py         # 序贯检测环境 + 从零 PPO 训练
│   └── 03_policy_evaluation.py    # 动态 vs 全检 评估
└── outputs/
    ├── models/  masked_classifier.pt, ppo_agent.pt
    ├── data/    mdp_definition.json, detection_policy.csv
    ├── figures/ ppo_training.png, strategy_comparison.png
    └── reports/ optimization_results.md
```

## 🚀 运行
```bash
cd phase3
../.venv/bin/python scripts/01_mdp_setup.py        # 掩码分类器(全测 acc 0.92)
../.venv/bin/python scripts/02_ppo_training.py     # PPO(默认 lam=0.02, class_w=6)
../.venv/bin/python scripts/03_policy_evaluation.py
```
> 依赖:torch + numpy/pandas/sklearn/matplotlib(沿用根目录 .venv)。

## ⚠️ 说明
- 时间降低 92.9% 远超 30% 目标:合成数据的失效由少数指标决定,故少量检测即可判别;在真实数据上降幅会更温和,但方法学不变。
- 成本模型按测试阶段设定(物理 1 / DC 2 / AC 3 / 功能 4 / 老化 11.5,总 100),老化为主要工时——动态策略基本跳过老化。

---
**阶段状态**: ✅ 已完成（2/2 KPI 通过）
**更新日期**: 2026年6月18日
**依赖**: 阶段2（核心指标体系）
**下一步**: 阶段4（增量学习与模型自适应）
