# 项目结构说明书

## 📂 完整文件树

```
solid_waste_projects_260526/
│
├─ docs/                                    📚 项目文档目录
│  ├─ README.md                            快速入门指南
│  ├─ 00_完整工作总结.md                    项目总体评价
│  ├─ 01_芯片再制造评估的客观需求分析.md    理论基础与需求分析
│  ├─ 02_合成数据集使用指南.md              数据字典与使用说明
│  ├─ 03_企业数据vs合成数据对比方案.md      问题诊断与方案论证
│  ├─ 04_项目启动清单.md                    项目管理与执行计划
│  ├─ 05_项目六阶段实施方案.md              详细的阶段执行规划
│  └─ ACCEPTANCE_CHECKLIST.md               验收清单与质量标准
│
├─ data/                                    🗂️ 数据目录
│  ├─ raw/                                 原始数据（待企业提供）
│  │  ├─ README.md                        数据说明
│  │  └─ (server_data_*.csv)              企业服务器原始数据
│  │
│  ├─ synthetic/                           合成数据集
│  │  ├─ chip_baseline_data.csv           1000个芯片的基础参数
│  │  ├─ chip_aging_curves.csv            90K+行的老化曲线数据
│  │  ├─ chip_failure_labels.csv          100个失效芯片的标注
│  │  └─ README.md                        合成数据说明
│  │
│  └─ processed/                           处理后的数据
│     ├─ phase1_processed/                 阶段1处理后的数据
│     ├─ phase2_processed/                 阶段2处理后的数据
│     └─ ...
│
├─ src/                                    💻 源代码目录
│  │
│  ├─ data_processing/                    数据处理模块
│  │  ├─ __init__.py
│  │  ├─ data_cleaner.py                  数据清洗函数
│  │  ├─ data_validator.py                数据验证函数
│  │  ├─ data_standardizer.py             数据标准化
│  │  └─ utils.py                         辅助工具函数
│  │
│  ├─ models/                             模型目录（按阶段组织）
│  │  │
│  │  ├─ knowledge_graph/                 🔷 阶段1：知识图谱
│  │  │  ├─ __init__.py
│  │  │  ├─ transe_model.py               TransE模型实现
│  │  │  ├─ graph_builder.py              图构建器
│  │  │  ├─ entity_extractor.py           实体提取
│  │  │  ├─ relationship_mapper.py        关系映射
│  │  │  └─ evaluation.py                 评估指标
│  │  │
│  │  ├─ feature_extraction/              🔶 阶段2：特征优化
│  │  │  ├─ __init__.py
│  │  │  ├─ gcn_model.py                  图卷积网络
│  │  │  ├─ gat_model.py                  图注意力网络
│  │  │  ├─ hybrid_network.py             GCN+GAT混合架构
│  │  │  ├─ shapley_calculator.py         Shapley值计算
│  │  │  └─ feature_selector.py           特征选择算法
│  │  │
│  │  ├─ reinforcement_learning/         🟠 阶段3：强化学习
│  │  │  ├─ __init__.py
│  │  │  ├─ mdp_environment.py            MDP环境定义
│  │  │  ├─ ppo_agent.py                  PPO智能体
│  │  │  ├─ detection_policy.py           检测策略
│  │  │  └─ training_pipeline.py          训练管道
│  │  │
│  │  ├─ incremental_learning/           🟠 阶段4：增量学习
│  │  │  ├─ __init__.py
│  │  │  ├─ css_learner.py                增量学习器
│  │  │  ├─ adaptive_weighting.py         自适应权重
│  │  │  ├─ transfer_learning.py          迁移学习
│  │  │  └─ model_updater.py              模型更新器
│  │  │
│  │  ├─ compatibility/                  🔴 阶段5：适配性预测
│  │  │  ├─ __init__.py
│  │  │  ├─ repair_strategy.py            修复策略库
│  │  │  ├─ compatibility_head.py         适配性预测头
│  │  │  ├─ risk_quantifier.py            风险量化
│  │  │  └─ validation_pipeline.py        预装配验证
│  │  │
│  │  └─ integrated_system/              🔴 阶段6：系统集成
│  │     ├─ __init__.py
│  │     ├─ system_orchestrator.py        系统编排器
│  │     ├─ pipeline_manager.py           管道管理
│  │     ├─ api_server.py                 API服务器
│  │     └─ monitoring.py                 监控与日志
│  │
│  └─ utils/                              工具模块
│     ├─ __init__.py
│     ├─ config.py                        配置管理
│     ├─ logger.py                        日志管理
│     ├─ validators.py                    验证工具
│     ├─ metrics.py                       评估指标
│     └─ visualization.py                 可视化工具
│
├─ phase1/                                🔷 阶段1：知识图谱
│  ├─ scripts/                            执行脚本
│  │  ├─ 01_data_cleaning.py              数据清洗脚本
│  │  ├─ 02_graph_construction.py         图构建脚本
│  │  ├─ 03_transe_training.py            TransE训练脚本
│  │  └─ 04_evaluation.py                 评估脚本
│  │
│  ├─ notebooks/                         Jupyter笔记本
│  │  ├─ 01_eda.ipynb                    探索性数据分析
│  │  ├─ 02_graph_visualization.ipynb     图可视化
│  │  └─ 03_results_analysis.ipynb        结果分析
│  │
│  ├─ outputs/                           输出结果
│  │  ├─ knowledge_graph.pkl              序列化的知识图谱
│  │  ├─ entity_relations.csv             实体与关系
│  │  ├─ transe_embeddings.npy            TransE嵌入向量
│  │  └─ evaluation_report.md             评估报告
│  │
│  └─ README.md                          阶段1文档
│
├─ phase2/                               🔶 阶段2：特征优化
│  ├─ scripts/
│  │  ├─ 01_feature_extraction.py
│  │  ├─ 02_shapley_analysis.py
│  │  └─ 03_indicator_selection.py
│  ├─ notebooks/
│  ├─ outputs/
│  └─ README.md
│
├─ phase3/                               🟠 阶段3：强化学习
│  ├─ scripts/
│  │  ├─ 01_mdp_setup.py
│  │  ├─ 02_ppo_training.py
│  │  └─ 03_policy_evaluation.py
│  ├─ notebooks/
│  ├─ outputs/
│  └─ README.md
│
├─ phase4/                               🟠 阶段4：增量学习
│  ├─ scripts/
│  │  ├─ 01_incremental_setup.py
│  │  ├─ 02_model_training.py
│  │  └─ 03_transfer_testing.py
│  ├─ notebooks/
│  ├─ outputs/
│  └─ README.md
│
├─ phase5/                               🔴 阶段5：适配性预测
│  ├─ scripts/
│  │  ├─ 01_strategy_building.py
│  │  ├─ 02_compatibility_training.py
│  │  └─ 03_validation_testing.py
│  ├─ notebooks/
│  ├─ outputs/
│  └─ README.md
│
├─ phase6/                               🔴 阶段6：系统集成
│  ├─ scripts/
│  │  ├─ 01_system_integration.py
│  │  ├─ 02_pipeline_assembly.py
│  │  └─ 03_deployment.py
│  ├─ notebooks/
│  ├─ outputs/
│  └─ README.md
│
├─ notebooks/                             📔 跨阶段Jupyter笔记本
│  ├─ 00_project_overview.ipynb          项目总览
│  ├─ 01_data_exploration.ipynb          数据探索
│  ├─ 02_eda.ipynb                       探索性数据分析
│  ├─ 03_model_comparison.ipynb          模型对比
│  └─ 04_results_summary.ipynb           结果总结
│
├─ experiments/                          🧪 实验记录目录
│  ├─ phase1_experiments/
│  │  ├─ exp_001_baseline.md
│  │  └─ exp_002_optimized.md
│  ├─ phase2_experiments/
│  │  └─ ...
│  └─ EXPERIMENTS_LOG.md                 实验日志总表
│
├─ config/                               ⚙️ 配置文件
│  ├─ config.yaml                        主配置文件
│  ├─ logging.yaml                       日志配置
│  ├─ model_config.yaml                  模型参数配置
│  └─ paths.yaml                         路径配置
│
├─ results/                              📊 结果输出目录
│  ├─ models/                            训练完成的模型
│  │  ├─ phase1_transe.pkl
│  │  ├─ phase2_gcn_gat.h5
│  │  ├─ phase3_ppo_agent.h5
│  │  ├─ phase4_css_learner.pkl
│  │  ├─ phase5_compatibility.h5
│  │  └─ phase6_integrated_system.pkl
│  │
│  ├─ figures/                           生成的图表
│  │  ├─ knowledge_graph_visualization.png
│  │  ├─ feature_importance.png
│  │  ├─ training_curves.png
│  │  └─ comparison_results.png
│  │
│  └─ reports/                           技术报告
│     ├─ phase1_report.md
│     ├─ phase2_report.md
│     ├─ phase3_report.md
│     ├─ phase4_report.md
│     ├─ phase5_report.md
│     ├─ phase6_report.md
│     └─ final_technical_report.pdf
│
├─ tests/                                🧪 单元与集成测试
│  ├─ test_data_processing.py
│  ├─ test_models.py
│  ├─ test_utils.py
│  ├─ conftest.py                        pytest配置
│  └─ fixtures/                          测试数据
│     └─ sample_data.csv
│
├─ requirements.txt                      📦 Python依赖
├─ setup.py                              📦 项目安装脚本
├─ Makefile                              ⚙️ 快捷命令
├─ .gitignore                            🚫 Git忽略文件
└─ .env.example                          🔐 环境变量模板
```

---

## 📖 目录说明

### 1. **docs/** - 项目文档
存放所有项目文档、计划、需求分析等。

| 文件 | 用途 |
|------|------|
| README.md | 快速入门指南 |
| 00_完整工作总结.md | 项目总体评价与成果 |
| 01_芯片再制造评估的客观需求分析.md | 理论基础与需求定义 |
| 02_合成数据集使用指南.md | 数据字典与使用说明 |
| 03_企业数据vs合成数据对比方案.md | 问题诊断与方案论证 |
| 04_项目启动清单.md | 项目管理与时间计划 |
| 05_项目六阶段实施方案.md | 详细阶段执行规划 |
| ACCEPTANCE_CHECKLIST.md | 验收标准与质量指标 |

**谁应该看**: 所有项目成员（PM、工程师、决策者）

---

### 2. **data/** - 数据目录
按照数据处理流程组织：原始数据 → 合成数据 → 处理后数据

#### **data/raw/** - 原始数据
存放企业提供的服务器数据（待收集）

#### **data/synthetic/** - 合成数据
已生成的合成芯片数据集
- `chip_baseline_data.csv`: 1000个芯片 × 28参数
- `chip_aging_curves.csv`: 90K+行时间序列
- `chip_failure_labels.csv`: 100个失效样本的标注

#### **data/processed/** - 处理后数据
各阶段处理后的数据存放位置

**谁应该看**: 数据科学家、机器学习工程师

---

### 3. **src/** - 源代码目录
存放所有可复用的Python模块和库

#### **src/data_processing/** - 数据处理模块
```python
from src.data_processing import data_cleaner, data_validator
cleaner = data_cleaner.DataCleaner()
cleaner.clean(data)
```

#### **src/models/** - 模型模块（按阶段组织）
每个阶段有对应的模型子目录：
- `knowledge_graph/` - 阶段1
- `feature_extraction/` - 阶段2
- `reinforcement_learning/` - 阶段3
- `incremental_learning/` - 阶段4
- `compatibility/` - 阶段5
- `integrated_system/` - 阶段6

#### **src/utils/** - 工具模块
```python
from src.utils import config, logger, metrics
logger.setup_logging()
```

**谁应该看**: 工程师、后端开发者

---

### 4. **phase1-6/** - 各阶段实验目录
每个阶段有相同的结构，便于独立开发和管理

#### **scripts/** - 执行脚本
包含该阶段的所有执行脚本，按顺序编号
```bash
python phase1/scripts/01_data_cleaning.py
python phase1/scripts/02_graph_construction.py
```

#### **notebooks/** - Jupyter笔记本
用于探索、分析、可视化该阶段的工作
- 快速试验代码
- 数据探索和可视化
- 结果分析

#### **outputs/** - 输出结果
该阶段生成的所有输出文件
- 模型权重和日志
- 中间结果
- 阶段报告

#### **README.md** - 阶段说明
该阶段的详细说明和执行指南

---

### 5. **notebooks/** - 跨阶段笔记本
存放跨越多个阶段的分析笔记本
- 项目总览
- 数据探索
- 模型对比
- 最终结果总结

---

### 6. **experiments/** - 实验记录
记录所有实验的设置、参数、结果

```markdown
# 实验 001: 基础TransE模型

**目的**: 建立知识图谱的基础baseline

**参数**: 
- embedding_dim: 100
- learning_rate: 0.01

**结果**:
- 精度: 85.2%
```

---

### 7. **config/** - 配置文件
集中管理所有配置，支持不同环境

- `config.yaml` - 主配置
- `logging.yaml` - 日志配置
- `model_config.yaml` - 模型超参数
- `paths.yaml` - 路径映射

使用方式：
```python
from src.utils import config
cfg = config.load_config('config/config.yaml')
```

---

### 8. **results/** - 结果输出
集中存放所有最终结果，便于后续使用和演示

#### **models/** - 训练完成的模型
```
results/models/
├── phase1_transe.pkl
├── phase2_gcn_gat.h5
├── phase3_ppo_agent.h5
├── phase4_css_learner.pkl
├── phase5_compatibility.h5
└── phase6_integrated_system.pkl
```

#### **figures/** - 生成的图表
用于论文、报告和演示的高质量图表

#### **reports/** - 技术报告
每个阶段的技术报告 + 最终综合报告

---

### 9. **tests/** - 测试目录
包含单元测试和集成测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_data_processing.py
```

---

## 🚀 使用流程示例

### 快速开始
```bash
# 1. 进入项目目录
cd solid_waste_projects_260526

# 2. 安装依赖
pip install -r requirements.txt

# 3. 查看快速入门指南
cat docs/README.md

# 4. 运行阶段1脚本
python phase1/scripts/01_data_cleaning.py
```

### 添加新的阶段1脚本
```
phase1/
├── scripts/
│   ├── 01_data_cleaning.py
│   ├── 02_graph_construction.py     <- NEW!
│   └── ...
└── notebooks/
```

### 更新配置
```yaml
# config/config.yaml
phase1:
  data_path: "data/raw/"
  output_path: "phase1/outputs/"
  batch_size: 32
```

---

## 📊 数据流向

```
data/raw/ (企业数据)
    ↓
src/data_processing/ (清洗&标准化)
    ↓
data/processed/ (处理后数据)
    ↓
phase1/scripts/ (运行分析)
    ↓
phase1/outputs/ (中间结果)
    ↓
results/models/ + results/reports/ (最终成果)
```

---

## 👥 角色与目录对应

| 角色 | 主要工作目录 |
|------|-----------|
| **数据工程师** | `data/`, `src/data_processing/` |
| **ML工程师** | `src/models/`, `phase1-6/`, `notebooks/` |
| **系统工程师** | `src/utils/`, `config/`, `tests/` |
| **项目经理** | `docs/`, `experiments/` |
| **研究员** | `notebooks/`, `results/reports/` |

---

## 💾 版本控制建议

```bash
# 在 .gitignore 中已忽略
/data/raw/              # 大型原始数据
/results/models/        # 大型模型文件
*.pkl, *.h5             # 二进制模型权重
__pycache__/            # Python缓存
.env                    # 敏感信息
```

---

## 📝 文件命名约定

| 类型 | 格式 | 示例 |
|------|------|------|
| Python脚本 | `NN_description.py` | `01_data_cleaning.py` |
| Jupyter笔记本 | `NN_description.ipynb` | `01_eda.ipynb` |
| 文档 | `NN_description.md` | `01_requirements.md` |
| 数据文件 | `domain_stage.csv` | `chip_baseline_data.csv` |
| 模型文件 | `phaseN_modelname.ext` | `phase1_transe.pkl` |

---

## ✅ 检查清单

- [ ] 所有源代码在 `src/` 中
- [ ] 每个阶段的脚本在对应的 `phaseN/scripts/`
- [ ] 配置文件在 `config/`
- [ ] 测试在 `tests/`
- [ ] 原始数据在 `data/raw/`
- [ ] 输出结果在 `phase*/outputs/` 或 `results/`
- [ ] 文档完整且最新

---

**文档版本**: v1.0  
**更新日期**: 2026年5月26日

