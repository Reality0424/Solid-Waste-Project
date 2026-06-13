# 新人入职清单 - 退役数据中心芯片二次利用项目

**创建日期**: 2026年5月26日  
**适用人群**: 项目新成员  
**预计时间**: 2-4小时（完整入职）

---

## 📋 入职流程

### ✅ Day 1: 环境准备 (30分钟)

- [ ] **收取项目信息**
  - 项目GitHub/GitLab地址
  - 开发环境访问权限
  - 团队沟通工具（钉钉/企业微信）

- [ ] **克隆项目代码**
  ```bash
  git clone [项目地址]
  cd solid_waste_projects_260526
  ```

- [ ] **安装Python环境** (3.8+ 推荐3.10)
  ```bash
  python --version  # 检查版本
  pip install --upgrade pip
  ```

- [ ] **安装项目依赖**
  ```bash
  pip install -r requirements.txt
  # 或使用conda
  conda create -n chip_remanufacturing python=3.10
  conda activate chip_remanufacturing
  pip install -r requirements.txt
  ```

- [ ] **验证环境**
  ```bash
  python -c "import pandas; print(pandas.__version__)"
  python -c "import tensorflow; print(tensorflow.__version__)"
  make diagnose
  ```

### ✅ Day 1-2: 项目理解 (1-2小时)

- [ ] **阅读项目文档**
  1. `docs/README.md` (10分钟) - 快速开始
  2. `ORGANIZATION_SUMMARY.md` (15分钟) - 组织概览
  3. `PROJECT_STRUCTURE.md` (20分钟) - 详细结构
  4. `docs/00_完整工作总结.md` (20分钟) - 项目总览

- [ ] **理解业务背景**
  - `docs/01_芯片再制造评估的客观需求分析.md` (30分钟)
  - 了解：芯片测试的28个参数是什么
  - 理解：为什么需要知识图谱、强化学习等技术

- [ ] **熟悉数据集**
  - `data/synthetic/README.md` - 合成数据说明
  - 使用Python加载并探索数据：
  ```python
  import pandas as pd
  df = pd.read_csv('data/synthetic/chip_baseline_data.csv')
  print(df.shape)  # 1000行 × 28列
  print(df.describe())
  ```

### ✅ Day 2-3: 团队融入 (30分钟-1小时)

- [ ] **参加项目启动会**
  - 了解项目6个阶段的目标
  - 了解各自的分工和职责
  - 确认mentor和问题反馈渠道

- [ ] **设置工作环境**
  - IDE: VS Code 或 PyCharm
  - 安装必要插件（Python、Jupyter、Git等）
  - 配置Git：
    ```bash
    git config user.name "Your Name"
    git config user.email "your.email@company.com"
    ```

- [ ] **了解团队工作流**
  - 如何提交代码 (branch naming, pull request流程)
  - 日报/周报提交方式
  - 代码审查标准
  - 问题反馈渠道

### ✅ Day 3-4: 技术深入 (1-2小时，按角色)

**如果你是数据工程师**:
- [ ] 阅读 `docs/02_合成数据集使用指南.md`
- [ ] 理解数据结构和处理流程
- [ ] 查看 `src/data_processing/` 的现有代码
- [ ] 运行示例：
  ```bash
  cd phase1
  python scripts/01_data_cleaning.py
  ```

**如果你是机器学习工程师**:
- [ ] 阅读 `phase1/README.md` (你负责的阶段)
- [ ] 理解该阶段的目标和技术方案
- [ ] 查看 `src/models/[你的阶段]/` 的代码框架
- [ ] 查看 Jupyter notebook了解期望的工作流

**如果你是系统工程师**:
- [ ] 阅读 `docs/04_项目启动清单.md`
- [ ] 理解系统集成的目标
- [ ] 查看 `src/utils/` 和 `config/` 的配置管理方式
- [ ] 熟悉 `Makefile` 的快捷命令

**如果你是项目经理/QA**:
- [ ] 阅读 `docs/05_项目六阶段实施方案.md` (完整版)
- [ ] 理解6个月的时间计划和里程碑
- [ ] 查看 `docs/ACCEPTANCE_CHECKLIST.md` 验收标准
- [ ] 设置项目管理工具（钉钉日历/企业微信提醒等）

---

## 🗂️ 快速导航

### 我是新来的，应该做什么？

**第一天(30分钟)**:
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 验证环境
make diagnose

# 3. 查看快速开始
cat docs/README.md
```

**第一周(4小时)**:
1. 读完 `ORGANIZATION_SUMMARY.md` 理解项目结构
2. 读完 `PROJECT_STRUCTURE.md` 了解文件位置
3. 读完 `docs/01_芯片再制造...md` 理解业务
4. 读完你负责阶段的 `phaseN/README.md`
5. 参加项目启动会

**开始工作(第二周)**:
1. 创建你的工作分支: `git checkout -b feature/your-feature`
2. 在对应目录编写代码或笔记本
3. 每天填写日报
4. 每周参加周报会

### 常见问题

**Q: 我找不到某个文件？**
A: 查看 `PROJECT_STRUCTURE.md` 中的文件树，或使用命令：
```bash
find . -name "*filename*" -type f
```

**Q: 我想运行某个脚本？**
A: 查看对应的 `phaseN/README.md`，按步骤执行

**Q: 我想写新脚本/笔记本？**
A: 放在 `phaseN/scripts/` 或 `phaseN/notebooks/` 中，遵循命名规范

**Q: 我忘记了依赖怎么办？**
A: 运行 `pip install -r requirements.txt` 再次安装

**Q: 代码有问题怎么办？**
A: 
1. 查看错误信息
2. 查看相关代码注释和文档
3. 在团队沟通工具中提问
4. 指定mentor协助排查

---

## 📚 阅读清单（按优先级）

| 优先级 | 文件 | 用途 | 时间 |
|------|------|------|------|
| 🔴 必读 | `docs/README.md` | 快速开始 | 10分钟 |
| 🔴 必读 | `ORGANIZATION_SUMMARY.md` | 项目组织 | 15分钟 |
| 🔴 必读 | `PROJECT_STRUCTURE.md` | 项目结构 | 20分钟 |
| 🔴 必读 | `docs/00_完整工作总结.md` | 项目总览 | 20分钟 |
| 🟠 强烈推荐 | `docs/01_芯片再制造...md` | 业务理解 | 30分钟 |
| 🟠 强烈推荐 | `phaseN/README.md` (你的阶段) | 阶段计划 | 20分钟 |
| 🟡 推荐 | `docs/02_合成数据集使用指南.md` | 数据使用 | 20分钟 |
| 🟡 推荐 | `docs/05_项目六阶段...md` | 完整方案 | 40分钟 |
| 🔵 可选 | `docs/03_企业数据vs合成数据.md` | 问题诊断 | 30分钟 |
| 🔵 可选 | `docs/04_项目启动清单.md` | 项目管理 | 30分钟 |

**总计阅读时间**: 4-5小时（完整阅读）或 1小时（快速浏览）

---

## 🛠️ 开发工具配置

### VS Code 推荐插件

```
Python                 - ms-python.python
Jupyter                - ms-toolsai.jupyter
Git Graph              - mhutchie.git-graph
GitLens                - eamodio.gitlens
Markdown All in One    - yzhang.markdown-all-in-one
YAML                   - redhat.vscode-yaml
Prettier               - esbenp.prettier-vscode
```

安装方式：
```bash
# 或者在VS Code中直接搜索安装
code --install-extension ms-python.python
code --install-extension ms-toolsai.jupyter
```

### PyCharm 配置

1. 打开项目文件夹
2. 设置Python解释器：File → Settings → Project → Python Interpreter
3. 选择 `requirements.txt` 自动安装依赖

### Anaconda 环境（推荐）

```bash
# 创建环境
conda create -n chip_remanufacturing python=3.10

# 激活环境
conda activate chip_remanufacturing

# 安装依赖
pip install -r requirements.txt

# 启动Jupyter
jupyter lab
```

---

## 👥 角色与职责

### 数据工程师
- **主要目录**: `src/data_processing/`, `data/`, `phase1/`
- **主要任务**: 数据清洗、验证、标准化
- **关键文件**: `docs/02_合成数据集使用指南.md`
- **第一个任务**: 阅读 `phase1/README.md`

### 机器学习工程师
- **主要目录**: `src/models/`, `phaseN/`, `notebooks/`
- **主要任务**: 模型开发、训练、评估
- **关键文件**: `docs/01_芯片再制造...md`
- **第一个任务**: 阅读 `phaseN/README.md`（你负责的阶段）

### 系统工程师
- **主要目录**: `src/utils/`, `config/`, `src/integrated_system/`
- **主要任务**: 系统集成、性能优化、部署
- **关键文件**: `docs/04_项目启动清单.md`
- **第一个任务**: 理解 `config/config.yaml` 的配置体系

### 项目经理/QA
- **主要目录**: `docs/`, `experiments/`, `results/reports/`
- **主要任务**: 进度管理、质量保证、验收
- **关键文件**: `docs/05_项目六阶段...md`, `ACCEPTANCE_CHECKLIST.md`
- **第一个任务**: 理解6个月的时间计划和KPI

---

## ⚡ 快速命令参考

```bash
# 查看所有快捷命令
make help

# 安装依赖
make install

# 代码检查
make lint

# 代码格式化
make format

# 运行测试
make test

# 启动Jupyter
make notebook

# 项目诊断
make diagnose

# 清理临时文件
make clean
```

---

## 📅 入职时间线示例

### 第1天（2小时）
- [ ] 环境安装与验证 (30分钟)
- [ ] 阅读README和项目组织文档 (30分钟)
- [ ] 了解项目结构和自己的工作目录 (30分钟)
- [ ] 配置IDE和Git (30分钟)

### 第2-3天（4小时）
- [ ] 阅读业务背景文档 (1小时)
- [ ] 探索数据集 (1小时)
- [ ] 阅读阶段指南 (1小时)
- [ ] 设置开发环境和运行hello world (1小时)

### 第4-5天（2小时）
- [ ] 参加项目启动会 (1小时)
- [ ] 与mentor讨论任务分工 (1小时)

### 第2周
- [ ] 开始第一个任务
- [ ] 每天填写日报
- [ ] 周五参加周报会

---

## 💬 沟通联系

### 问题反馈渠道

| 问题类型 | 联系方式 | 响应时间 |
|--------|--------|--------|
| 紧急问题 | 直接电话/钉钉 | 30分钟 |
| 技术问题 | 提问在团队群里 | 1-2小时 |
| 文档问题 | 更新Issue或反馈 | 1天 |
| 想法建议 | 周会讨论 | 1周 |

### Mentor分配

**如果你是数据工程师**:
- Mentor: [数据团队负责人]
- 联系方式: 钉钉 or Email

**如果你是机器学习工程师**:
- Mentor: [ML团队负责人]
- 联系方式: 钉钉 or Email

**如果你是系统工程师**:
- Mentor: [系统团队负责人]
- 联系方式: 钉钉 or Email

**如果你是项目经理**:
- Mentor: [项目经理]
- 联系方式: 钉钉 or Email

---

## ✅ 入职完成检查

### 环境就绪
- [ ] Python 3.8+ 已安装
- [ ] 依赖已安装 (`pip install -r requirements.txt`)
- [ ] IDE已配置 (VS Code 或 PyCharm)
- [ ] Git已配置
- [ ] `make diagnose` 运行成功

### 知识就绪
- [ ] 已读 `docs/README.md`
- [ ] 已读 `PROJECT_STRUCTURE.md`
- [ ] 已读 `docs/00_完整工作总结.md`
- [ ] 已读你负责阶段的README

### 工作就绪
- [ ] 已获取Git访问权限
- [ ] 已创建工作分支
- [ ] 已与mentor沟通过
- [ ] 已获取第一个任务
- [ ] 已能运行示例代码

### 团队融入
- [ ] 已加入团队沟通工具
- [ ] 已参加项目启动会
- [ ] 已了解工作流程
- [ ] 已清楚问题反馈渠道
- [ ] 已获取mentor联系方式

---

## 🎯 第一周目标

```
Week 1 Goals:
├─ ✅ 完成入职培训
├─ ✅ 理解项目背景和目标
├─ ✅ 配置好开发环境
├─ ✅ 理解代码结构
├─ ✅ 能运行第一个demo
├─ ✅ 与mentor确认任务分工
└─ ✅ 准备开始实际工作
```

---

## 💡 Tips

1. **不要跳过阅读文档** - 花30分钟读文档可以节省后续2小时的时间
2. **建立清晰的工作流** - 了解你的工作目录、输入、输出
3. **定期与mentor同步** - 遇到问题不要憋着，及时反馈
4. **记录自己的问题** - 建立FAQ，帮助后续新人
5. **贡献改进建议** - 看到不合理的地方及时提出

---

**欢迎加入团队！** 🎉

如有任何问题，请及时反馈。祝你工作顺利！

**文档版本**: v1.0  
**更新日期**: 2026年5月26日

