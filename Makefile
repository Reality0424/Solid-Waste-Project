.PHONY: help install clean test lint format run-phase1 run-phase2 run-all docs

# 默认目标
help:
	@echo "退役数据中心芯片二次利用项目 - 快捷命令"
	@echo "=========================================="
	@echo ""
	@echo "安装与配置:"
	@echo "  make install          - 安装所有依赖"
	@echo "  make install-dev      - 安装开发依赖"
	@echo "  make setup            - 初始化项目"
	@echo ""
	@echo "开发:"
	@echo "  make clean            - 清理临时文件"
	@echo "  make lint             - 检查代码风格"
	@echo "  make format           - 格式化代码"
	@echo "  make test             - 运行所有测试"
	@echo "  make test-phase1      - 运行阶段1测试"
	@echo ""
	@echo "执行:"
	@echo "  make run-phase1       - 运行阶段1脚本"
	@echo "  make run-phase2       - 运行阶段2脚本"
	@echo "  make run-all          - 运行所有可用阶段"
	@echo "  make notebook         - 启动Jupyter Lab"
	@echo ""
	@echo "文档:"
	@echo "  make docs             - 查看项目文档"
	@echo "  make tree             - 显示项目文件树"
	@echo ""

# 安装依赖
install:
	pip install -r requirements.txt
	@echo "✓ 依赖安装完成"

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 pylint
	@echo "✓ 开发依赖安装完成"

# 项目初始化
setup: install
	@echo "初始化项目结构..."
	mkdir -p logs experiments results/models results/figures results/reports
	@echo "✓ 项目初始化完成"

# 代码清理
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	rm -rf build/ dist/ *.egg-info/
	@echo "✓ 临时文件已清理"

# 代码检查
lint:
	flake8 src/ phase*/scripts/ --max-line-length=100
	pylint src/ --disable=C0111,W0212
	@echo "✓ 代码检查完成"

# 代码格式化
format:
	black src/ phase*/scripts/ --line-length=100
	@echo "✓ 代码格式化完成"

# 测试
test:
	pytest tests/ -v --cov=src/
	@echo "✓ 所有测试完成"

test-phase1:
	pytest tests/test_phase1_*.py -v
	@echo "✓ 阶段1测试完成"

# 运行阶段脚本
run-phase1:
	@echo "运行阶段1: 知识图谱构建..."
	cd phase1 && python scripts/01_data_cleaning.py
	@echo "✓ 阶段1执行完成"

run-phase2:
	@echo "运行阶段2: 特征优化..."
	cd phase2 && python scripts/01_feature_extraction.py
	@echo "✓ 阶段2执行完成"

run-all:
	@echo "运行所有阶段..."
	$(MAKE) run-phase1
	$(MAKE) run-phase2
	@echo "✓ 所有阶段执行完成"

# Jupyter
notebook:
	jupyter lab

# 文档
docs:
	@echo "项目文档位置:"
	@echo "  - 快速开始: docs/README.md"
	@echo "  - 项目结构: PROJECT_STRUCTURE.md"
	@echo "  - 完整方案: docs/05_项目六阶段实施方案.md"
	@echo "  - 数据说明: data/synthetic/README.md"
	@echo ""
	@echo "打开文档:"
	@echo "  cat docs/README.md"

# 显示文件树
tree:
	@echo "项目文件结构:"
	@tree -L 2 -I '__pycache__|*.pyc'
	@echo ""
	@echo "详细文件树请查看: PROJECT_STRUCTURE.md"

# 版本检查
version:
	@python --version
	@pip list | grep -E "pandas|numpy|tensorflow|torch|scikit-learn"

# 快速诊断
diagnose:
	@echo "项目诊断信息"
	@echo "============"
	@echo "Python版本:"
	@python --version
	@echo ""
	@echo "关键依赖:"
	@pip list | grep -E "pandas|numpy|tensorflow|torch"
	@echo ""
	@echo "数据文件:"
	@ls -lh data/synthetic/
	@echo ""
	@echo "项目体积:"
	@du -sh .
	@echo ""
	@echo "✓ 诊断完成"

.DEFAULT_GOAL := help
