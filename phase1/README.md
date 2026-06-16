# 阶段1：知识图谱框架构建

**时间**: 2026年5月26日 - 2026年6月15日  
**主要技术**: Neo4j 图数据库、TransE嵌入、图结构学习  
**关键产出**: ≥500实体，≥1000关系的 Neo4j 知识图谱

## 📍 核心任务

### 任务1.1 - 服务器数据清洗 (Week 1-2)
- 整理服务器二次构件历史检测数据集
- 完成数据清洗与标准化
- 建立数据质量评估机制

**输出**: 
- `outputs/data/cleaned_data.csv`
- `outputs/reports/data_quality_report.md`

### 任务1.2 - 多维关系知识图谱框架设计 (Week 2-3)
- 设计多维关系知识图谱框架
- 明确实体与依赖关系定义
- 定义4个维度的关系类型（物理、电气DC、电气AC、可靠性）
- 建立 Neo4j 数据模型与关系约束

**输出**:
- `outputs/graph/entity_definitions.json`
- `outputs/graph/relationship_types.json`
- `outputs/graph/neo4j_import_script.cypher`（Cypher 导入脚本）
- `config/neo4j_connection.yaml`（Neo4j 连接配置）

### 任务1.3 - TransE语义联结模型 (Week 3-4)
- 连接 Neo4j 数据库并加载知识图谱
- 开发基于TransE算法的语义联结模型
- 实现指标间基础关联挖掘
- 将 TransE 嵌入存储回 Neo4j 中（作为节点属性）
- 完成模型训练与验证

**输出**:
- `outputs/models/phase1_transe.pkl`（模型权重）
- Neo4j 数据库中的 embedding 属性（500×100）
- `outputs/figures/embedding_visualization.png`
- `outputs/reports/transe_validation_report.md`

## 🎯 成功标准

- ✅ 知识图谱实体数 ≥ 500
- ✅ 关系数 ≥ 1000
- ✅ TransE模型收敛
- ✅ 完整性验证率 ≥ 90%

## 📁 目录结构

```
phase1/
├── scripts/
│   ├── 00_neo4j_setup.py            # Neo4j 初始化脚本
│   ├── 01_data_cleaning.py          # 数据清洗脚本
│   ├── 02_graph_construction.py     # 图构建脚本 (Neo4j 导入)
│   ├── 03_transe_training.py        # TransE训练脚本
│   └── 04_evaluation.py             # 评估脚本
├── notebooks/
│   ├── 01_eda.ipynb                # 探索性数据分析
│   ├── 02_graph_visualization.ipynb  # Neo4j 图可视化
│   └── 03_results_analysis.ipynb    # 结果分析
├── requirements-phase1.txt          # 阶段1最小依赖
├── outputs/
│   ├── data/
│   │   ├── cleaned_data.csv         # 清洗后的数据（保留全部1000样本+标签）
│   │   └── transe_embeddings.npy    # TransE 实体嵌入矩阵 (1042×100)
│   ├── graph/
│   │   ├── entity_definitions.json       # 实体定义
│   │   ├── relationship_types.json       # 关系类型定义
│   │   ├── knowledge_graph.pkl          # 序列化图谱 (networkx.DiGraph)
│   │   └── neo4j_import_script.cypher   # Neo4j Cypher 导入脚本（复现用）
│   ├── relations/
│   │   ├── entity_relations.csv     # 全部三元组 (head, relation, tail)
│   │   └── relationship_matrix.csv  # 关系类型×(头类型,尾类型) 计数矩阵
│   ├── models/
│   │   └── phase1_transe.pkl        # TransE模型（嵌入+索引+损失+测试集）
│   ├── figures/
│   │   ├── embedding_visualization.png  # 嵌入空间 PCA 可视化（按类型着色）
│   │   └── training_loss.png            # TransE 训练损失曲线
│   └── reports/
│       ├── data_quality_report.md   # 数据质量评估报告
│       ├── transe_validation_report.md  # TransE验证报告（MRR/Hits@K）
│       └── evaluation_report.md     # 评估报告
└── README.md                        # 本文件
```

## 🚀 运行步骤

> Neo4j 连接信息从 `config/neo4j.yaml` 读取（uri / username / password / database），
> 所有脚本默认路径已对齐，无需额外传参即可一键跑通。

### 0. 环境准备（一次性）
```bash
# 在项目根目录创建虚拟环境并安装阶段1依赖
python3 -m venv .venv
.venv/bin/pip install -r phase1/requirements-phase1.txt

# 启动 Neo4j（任意方式：Docker / Neo4j Desktop / 本地 tarball），
# 并确保密码与 config/neo4j.yaml 一致。例如 Docker：
#   docker run -p7474:7474 -p7687:7687 -e NEO4J_AUTH=neo4j/<password> neo4j:5.26
```

### 1. 数据清洗（合成 baseline → 清洗数据 + 质量报告）
```bash
cd phase1
../.venv/bin/python scripts/01_data_cleaning.py
```

### 2. 构建知识图谱并导入 Neo4j（导出 pkl / csv / cypher 等产物）
```bash
../.venv/bin/python scripts/02_graph_construction.py
# 仅导出产物、不写 Neo4j：加 --no-neo4j
```

### 3. 训练 TransE（真实梯度下降）并写回 Neo4j embedding
```bash
../.venv/bin/python scripts/03_transe_training.py
# 可调：--epochs 300 --lr 0.02 --dim 100 --margin 1.0
```

### 4. 评估（图谱完整性 + 架构验证 + 链路预测 MRR/Hits@K）
```bash
../.venv/bin/python scripts/04_evaluation.py
```

> 也可使用 `00_neo4j_setup.py` 做索引初始化/清库（可选）。

## 📊 预期输出

| 文件/数据库 | 说明 | 路径 |
|-----------|------|------|
| Neo4j 数据库 | 500+实体与1000+关系图 | bolt://localhost:7687 |
| 清洗数据 | 标准化数据 | `outputs/data/cleaned_data.csv` |
| 实体定义 | 500+实体的详细定义 | `outputs/graph/entity_definitions.json` |
| 关系类型 | 关系类型定义 | `outputs/graph/relationship_types.json` |
| Neo4j导入脚本 | Cypher导入脚本 | `outputs/graph/neo4j_import_script.cypher` |
| 关系数据 | 验证用关系数据 | `outputs/relations/entity_relations.csv` |
| TransE模型 | 模型权重 | `outputs/models/phase1_transe.pkl` |
| 嵌入向量可视化 | 2D/3D嵌入空间图 | `outputs/figures/embedding_visualization.png` |
| 数据质量报告 | 数据清洗评估 | `outputs/reports/data_quality_report.md` |
| TransE验证报告 | 嵌入质量评估 | `outputs/reports/transe_validation_report.md` |
| 评估报告 | 完整评估结果 | `outputs/reports/evaluation_report.md` |

## 📈 关键指标（实测）

> 复现命令：见下方"运行步骤"，全流程可在本地 Neo4j 上一键跑通。

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 实体数 | ≥500 | **1042** | ✅ |
| 关系数 | ≥1000 | **8072** | ✅ |
| 图谱完整性 | ≥90% | **100%** | ✅ |
| TransE 收敛 | Loss 显著下降 | **1.01 → 0.56**（单调收敛） | ✅ |
| 架构标签完整 | 6 类实体齐全 | **6/6** | ✅ |

**链路预测质量**（raw，候选实体 1042，测试三元组 807；随机基线 Hits@10≈0.96%）：

| MRR | Hits@1 | Hits@3 | Hits@10 | Mean Rank |
|-----|--------|--------|---------|-----------|
| 0.235 | 0.131 | 0.290 | 0.454 | 277 |

**实体分布**：Chip 1000 / Parameter 25 / TestStage 5 / FailureMode 5 / Dimension 4 / ChipModel 3
**关系分布**：UNDERGOES_TEST 5000 / HAS_ABNORMAL 1014 / OF_MODEL 1000 / EXHIBITS 1000 / BELONGS_TO 25 / MEASURED_IN 25 / CORRELATES_WITH 4 / PRECEDES 4

**总体验收**：✅ **5/5 标准通过**

## 🔗 依赖关系

**输入依赖**:
- 合成数据集 (`data/synthetic/`)

**输出供给**:
- 知识图谱 → 阶段2 (特征提取)

## 💡 常见问题

**Q: 如何安装和启动 Neo4j?**
```bash
# 使用 Docker 快速启动
docker run --name neo4j -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4JLABS_PLUGINS='["apoc"]' \
  neo4j:latest

# 或使用本地安装，参考：https://neo4j.com/download/
```

**Q: 如何可视化知识图谱?**
访问 Neo4j Browser: http://localhost:7474
```cypher
# 查看所有节点
MATCH (n) RETURN n LIMIT 100

# 查看特定关系
MATCH (a)-[r:DEPENDS_ON]->(b) RETURN a, r, b LIMIT 50
```

**Q: Neo4j 连接失败?**
- 检查 Neo4j 服务是否运行：`neo4j status`
- 验证连接参数（URI、用户名、密码）
- 检查防火墙设置，确保 7687 端口开放
- 查看 Neo4j 日志：`docker logs neo4j`

**Q: TransE 模型不收敛?**
- 检查学习率设置 (建议0.001)
- 增加训练轮数 (建议≥100)
- 检查数据质量
- 确保 Neo4j 中的关系数据完整（≥1000）

**Q: 如何调整实体数量?**
编辑 `scripts/02_graph_construction.py` 中的 `min_support` 参数

**Q: 如何导出 Neo4j 数据进行备份?**
```bash
# 导出为 CSV
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
# 自定义导出逻辑
"

# 或使用 Neo4j 官方工具
neo4j-admin dump --to=/path/to/backup.dump
```

## 📝 笔记与经验

- **Neo4j 性能**：创建索引提升查询速度，特别是频繁查询的属性
  ```cypher
  CREATE INDEX ON :Chip(id);
  CREATE INDEX ON :Parameter(name);
  ```
- **TransE 对异常值敏感**，确保数据清洗充分
- **嵌入维度 100** 较好平衡精度和效率
- **建议使用 GPU** 加速 TransE 训练（可将速度提升 10-50 倍）
- **定期备份 Neo4j 数据库**，避免数据丢失
- **APOC 扩展**提供强大的图算法，可进一步优化关系挖掘

## 👥 负责人

- **知识图谱工程师**: 数据清洗 + 图构建
- **ML工程师**: TransE模型开发
- **测试工程师**: 结果验证

---

**阶段状态**: ✅ 已完成（全流程在本地 Neo4j 上跑通，5/5 验收标准通过）
**更新日期**: 2026年6月16日
**下一步**: 进入阶段2（GCN+GAT 特征优化 + Shapley 核心指标筛选）

