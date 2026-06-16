#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 / 任务2.2: Shapley 值指标贡献度分析

在 28 项原始检测指标上训练梯度提升模型, 用 TreeSHAP 计算每个指标对
"失效判定"的边际贡献(Shapley 值), 得到可解释的指标重要性排序,
为任务2.3 的核心指标筛选提供依据。

产出:
  outputs/data/shapley_values.csv          每指标 平均|SHAP| 贡献度排序
  outputs/data/shapley_per_sample.npy       每样本每指标 SHAP 值(供后续分析)
  outputs/figures/shapley_importance.png    贡献度条形图
  outputs/figures/shapley_beeswarm.png      SHAP 蜂群图
"""
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import GradientBoostingClassifier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import _common as C


def main():
    print("=" * 60); print("Phase 2 / 2.2  Shapley 指标贡献度分析"); print("=" * 60)
    Xdf, y, _, _ = C.load_dataset()
    print(f"芯片 {len(y)}, 指标 {Xdf.shape[1]}, 失效 {int(y.sum())}")

    # 在 28 原始指标上训练 GBM(可解释、与核心指标筛选一致)
    model = GradientBoostingClassifier(random_state=0)
    model.fit(Xdf.values, y)

    # TreeSHAP
    print("计算 TreeSHAP ...")
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(Xdf.values)
    sv = np.asarray(sv)
    if sv.ndim == 3:           # 某些版本返回 (n, feat, class)
        sv = sv[:, :, 1]
    mean_abs = np.abs(sv).mean(axis=0)

    rank = pd.DataFrame({'indicator': C.FEATURES, 'mean_abs_shap': mean_abs})
    rank = rank.sort_values('mean_abs_shap', ascending=False).reset_index(drop=True)
    rank['rank'] = rank.index + 1
    rank['contribution_pct'] = 100 * rank['mean_abs_shap'] / rank['mean_abs_shap'].sum()
    rank['cumulative_pct'] = rank['contribution_pct'].cumsum()

    rank.to_csv(C.out('data', 'shapley_values.csv'), index=False)
    np.save(C.out('data', 'shapley_per_sample.npy'), sv)
    print("\nTop 12 指标(按平均|SHAP|):")
    print(rank.head(12).to_string(index=False))

    # 条形图
    top = rank.head(15)[::-1]
    plt.figure(figsize=(9, 7))
    plt.barh(top['indicator'], top['mean_abs_shap'], color='#3b7dd8')
    plt.xlabel('mean(|SHAP value|)'); plt.title('Indicator contribution (Shapley)')
    plt.tight_layout(); plt.savefig(C.out('figures', 'shapley_importance.png'), dpi=150); plt.close()

    # 蜂群图
    try:
        shap.summary_plot(sv, Xdf.values, feature_names=C.FEATURES, show=False, max_display=15)
        plt.tight_layout(); plt.savefig(C.out('figures', 'shapley_beeswarm.png'), dpi=150); plt.close()
    except Exception as e:
        print("蜂群图跳过:", e)

    print(f"\n✅ 已保存 shapley_values.csv / 图 到 phase2/outputs/")
    print(f"   前5指标累计贡献: {rank.iloc[4]['cumulative_pct']:.1f}%")


if __name__ == '__main__':
    main()
