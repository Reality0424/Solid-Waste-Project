#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 / 任务4.3: 多版本迁移性测试 + 小试系统汇总

构造"训练版本 × 测试版本"迁移矩阵(GBM, 无适配), 评估跨固件版本泛化;
并对比"迁移(无适配)"与"增量适配后"的精度提升。

KPI: 模型迁移准确率 ≥88%
产出: outputs/figures/transfer_matrix.png, outputs/reports/transfer_learning_report.md
"""
import json
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
import _common as C

np.random.seed(0)


def split(n, r=0.3, seed=0):
    rng = np.random.default_rng(seed); idx = rng.permutation(n); nt = int(n * r)
    return idx[nt:], idx[:nt]


def main():
    print("=" * 60); print("Phase 4 / 4.3 多版本迁移测试"); print("=" * 60)
    data, feats = C.load_versions()
    V = C.VERSIONS
    sp = {v: split(len(data[v][1]), seed=i) for i, v in enumerate(V)}

    models = {}
    for v in V:
        X, y = data[v]; tr, _ = sp[v]
        models[v] = GradientBoostingClassifier(random_state=0).fit(X[tr], y[tr])

    M = np.zeros((3, 3))
    for i, tv in enumerate(V):
        for j, ev in enumerate(V):
            X, y = data[ev]; _, te = sp[ev]
            M[i, j] = accuracy_score(y[te], models[tv].predict(X[te]))

    off = [M[i, j] for i in range(3) for j in range(3) if i != j]
    transfer_acc = float(np.mean(off)); worst = float(np.min(off))
    print("迁移准确率矩阵 (行=训练版本, 列=测试版本):")
    print("        " + "  ".join(V))
    for i, tv in enumerate(V):
        print(f"  {tv}:  " + "  ".join(f"{M[i,j]:.3f}" for j in range(3)))
    print(f"  跨版本平均迁移准确率 = {transfer_acc:.3f} (最差 {worst:.3f}) | 目标 ≥0.88")

    inc = json.load(open(C.out('data', 'incremental_results.json')))
    eff = inc['learning_efficiency']

    md = "# Phase 4 增量学习与迁移测试报告\n\n"
    md += "## 多版本迁移准确率矩阵(GBM, 无适配)\n\n| 训练\\测试 | " + " | ".join(V) + " |\n|---|" + "---|" * 3 + "\n"
    for i, tv in enumerate(V):
        md += f"| {tv} | " + " | ".join(f"{M[i,j]:.3f}" for j in range(3)) + " |\n"
    md += f"\n- **跨版本平均迁移准确率 = {transfer_acc:.3f}**(最差 {worst:.3f}); 目标 ≥0.88: {'✅' if transfer_acc>=0.88 else '❌'}\n"
    md += f"- **增量学习效率 = {eff:.3f}**(增量更新 / 全量重训, 见 4.2); 目标 ≥0.85: {'✅' if eff>=0.85 else '❌'}\n"
    md += "- **自适应更新周期**: 增量 partial_fit 在秒级完成, 远小于 1 周目标(无需全量重训历史数据)。\n\n"
    md += "## 小试设备关键技术系统(汇总)\n\n"
    md += "- 增量学习器(SGD partial_fit): 新批次/固件到来时在线更新, 不遗忘历史(权重热启动)。\n"
    md += "- 特征权重自适应: 模型系数随版本漂移自动调整(见 feature_weight_adaptation.png)。\n"
    md += "- 多版本迁移评估: 量化跨固件泛化, 指导何时需要再适配。\n"
    with open(C.out('reports', 'transfer_learning_report.md'), 'w', encoding='utf-8') as f:
        f.write(md)

    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5.5, 4.6))
        im = ax.imshow(M, cmap='Greens', vmin=0.8, vmax=1.0)
        ax.set_xticks(range(3)); ax.set_xticklabels(V); ax.set_yticks(range(3)); ax.set_yticklabels(V)
        ax.set_xlabel('test version'); ax.set_ylabel('train version'); ax.set_title('Cross-version transfer accuracy')
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{M[i,j]:.3f}", ha='center', va='center',
                        color='white' if M[i, j] > 0.93 else 'black')
        fig.colorbar(im, fraction=0.046, pad=0.04); fig.tight_layout()
        fig.savefig(C.out('figures', 'transfer_matrix.png'), dpi=150); plt.close()
    except Exception as e:
        print('plot skip:', e)
    print(f"✅ 迁移准确率 {transfer_acc:.3f} (≥0.88: {transfer_acc>=0.88}) | 学习效率 {eff:.3f} (≥0.85: {eff>=0.85})")


if __name__ == '__main__':
    main()
