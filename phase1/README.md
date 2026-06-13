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
├── outputs/
│   ├── data/
│   │   └── cleaned_data.csv         # 清洗后的数据
│   ├── graph/
│   │   ├── entity_definitions.json       # 实体定义
│   │   ├── relationship_types.json       # 关系类型定义
│   │   └── neo4j_import_script.cypher   # Neo4j Cypher 导入脚本
│   ├── relations/
│   │   └── entity_relations.csv     # 关系数据
│   ├── models/
│   │   └── phase1_transe.pkl        # TransE模型权重
│   ├── figures/
│   │   └── embedding_visualization.png  # 嵌入空间可视化
│   └── reports/
│       ├── data_quality_report.md   # 数据质量评估报告
│       ├── transe_validation_report.md  # TransE验证报告
│       └── evaluation_report.md     # 评估报告
└── README.md                        # 本文件
```

## 🚀 运行步骤

### 0. Neo4j 初始化 (必须)
```bash
cd phase1
# 配置 Neo4j 连接信息（编辑或使用环境变量）
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password

# 初始化 Neo4j 数据库
python scripts/00_neo4j_setup.py --uri $NEO4J_URI --user $NEO4J_USER --password $NEO4J_PASSWORD
```

### 1. 数据准备
```bash
# 确保数据已在 data/synthetic/ 中
ls data/synthetic/
```

### 2. 清洗数据
```bash
cd phase1
python scripts/01_data_cleaning.py \
    --input_path ../../data/synthetic/chip_baseline_data.csv \
    --output_path outputs/data/cleaned_data.csv
```

### 3. 构建知识图谱并导入 Neo4j
```bash
python scripts/02_graph_construction.py \
    --input_path outputs/data/cleaned_data.csv \
    --output_path outputs/graph/ \
    --relations_output outputs/relations/ \
    --neo4j_uri $NEO4J_URI \
    --neo4j_user $NEO4J_USER \
    --neo4j_password $NEO4J_PASSWORD
```

### 4. 训练 TransE 模型并更新 Neo4j
```bash
python scripts/03_transe_training.py \
    --neo4j_uri $NEO4J_URI \
    --neo4j_user $NEO4J_USER \
    --neo4j_password $NEO4J_PASSWORD \
    --model_output_path outputs/models/phase1_transe.pkl \
    --visualization_output outputs/figures/embedding_visualization.png
```

### 5. 评估结果
```bash
python scripts/04_evaluation.py \
    --neo4j_uri $NEO4J_URI \
    --neo4j_user $NEO4J_USER \
    --neo4j_password $NEO4J_PASSWORD \
    --output_path outputs/reports/evaluation_report.md
```

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

## 📈 关键指标

| 指标 | 目标 | 实际 |
|------|------|------|
| 实体数 | ≥500 | - |
| 关系数 | ≥1000 | - |
| 完整性 | ≥90% | - |
| TransE Loss | <0.1 | - |

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

**阶段状态**: 未开始  
**更新日期**: 2026年5月26日  
**下一步**: 启动数据清洗工作

