# Paper: Chip-Remanufacturing Hidden-Failure Detection (target: MDPI *Electronics*)

基于 Phase 1–2 全部任务 + SECOM 真实数据外部验证撰写。所有数字均来自本仓库可复现实验。

## 目录
```
paper/
├── main.tex                     # 正文(MDPI Electronics 官方模板格式)
├── refs.bib                     # 参考文献(全部为真实、可核实的文献/数据集)
├── figures/
│   ├── make_figures.py          # 由代码生成全部配图(无 AI 水印)
│   └── fig1..fig6 *.png         # 生成的图(300 dpi)
└── experiments/
    ├── secom_validation.py      # 真实数据 UCI SECOM 外部验证
    ├── data/secom*.data         # SECOM 原始数据(UCI 下载)
    └── outputs/                 # secom_results.json, secom_topk_curve.csv
```

## 如何编译(得到 Electronics 官方排版的 PDF)
本机未装 LaTeX。请用官方 MDPI 模板编译:
1. 获取 MDPI LaTeX 模板:Overleaf 新建项目 → Templates 搜 “MDPI”(期刊选 *Electronics*);或从 https://www.mdpi.com/authors/latex 下载 LaTeX zip。
2. 把本目录的 `main.tex`、`refs.bib`、`figures/*.png` 放进模板文件夹(模板内含 `Definitions/mdpi.cls`、logo、`.bst`)。
3. 编译顺序:`pdflatex → bibtex → pdflatex → pdflatex`。
> `main.tex` 顶部有一段"最小 fallback"说明:若暂时没有 MDPI 类,可临时切到 `article` 类仅预览文字。

## 复现实验数字
```bash
# 在仓库根目录的 venv 中
.venv/bin/python paper/experiments/secom_validation.py   # 真实数据验证
.venv/bin/python paper/figures/make_figures.py           # 重新生成全部配图
# 合成数据/Phase1-2 的数字由 phase1/、phase2/ 的脚本产生
```

## 投稿前仍需你补的
- 作者、单位、邮箱、ORCID、致谢/资助、贡献声明(main.tex 中已留占位)。
- 如单位按 JCR 评:Electronics 为 Q2;如按中科院:为 4 区——投前确认认可口径。
- 建议再核对 refs.bib 中两条领域综述的卷/页码(核心信息已核实真实)。
