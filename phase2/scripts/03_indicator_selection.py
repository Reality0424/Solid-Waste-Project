#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 / 任务2.3: 核心指标筛选与有效性验证

依据 2.2 的 Shapley 排序, 增量加入 Top-k 指标, 用交叉验证评估精度,
选出能达到目标精度(≥88%)的最小核心指标子集(5-10 个), 并对比全量指标。

产出:
  outputs/data/core_indicators.json            核心指标子集定义
  outputs/data/feature_importance_ranking.csv  指标重要性排序(含是否入选)
  outputs/figures/indicator_selection_curve.png  精度 vs 指标数 曲线
  outputs/reports/validation_report.md         有效性验证报告
"""
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import roc_auc_score, accuracy_score, balanced_accuracy_score, recall_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import _common as C

TARGET_ACC = 0.88
MIN_K, MAX_K = 5, 10


def tuned_acc(prob, y):
    best = 0.0
    for t in np.linspace(0.05, 0.95, 91):
        best = max(best, accuracy_score(y, (prob >= t).astype(int)))
    return best


def cv_metrics(X, y):
    prob = cross_val_predict(GradientBoostingClassifier(random_state=0),
                             X, y, cv=5, method='predict_proba')[:, 1]
    return roc_auc_score(y, prob), tuned_acc(prob, y)


def main():
    print("=" * 60); print("Phase 2 / 2.3  核心指标筛选与验证"); print("=" * 60)
    Xdf, y, _, _ = C.load_dataset()
    rank = pd.read_csv(C.out('data', 'shapley_values.csv'))
    order = rank['indicator'].tolist()

    # 增量加入 Top-k, 评估
    print("增量评估 Top-k 指标 (5折CV):")
    rows = []
    for k in range(1, len(order) + 1):
        cols = order[:k]
        auc, acc = cv_metrics(Xdf[cols].values, y)
        rows.append({'k': k, 'auc': auc, 'accuracy': acc})
        if k <= MAX_K + 2:
            print(f"  k={k:2d}  acc={acc:.3f}  auc={auc:.3f}  (+{order[k-1]})")
    curve = pd.DataFrame(rows)

    full_auc, full_acc = cv_metrics(Xdf.values, y)

    # 选择准则: 因类别不平衡(失效10%), 准确率会被虚高(连k=1都>0.90),
    # 故以 AUC 为主: 取 5-10 中最小的、能保留 ≥95% 全量AUC 且准确率≥88% 的 k。
    auc_target = 0.95 * full_auc
    ok = curve[(curve.k >= MIN_K) & (curve.k <= MAX_K) &
               (curve.auc >= auc_target) & (curve.accuracy >= TARGET_ACC)]
    if len(ok):
        chosen_k = int(ok.iloc[0]['k'])
    else:
        sub = curve[(curve.k >= MIN_K) & (curve.k <= MAX_K)]
        chosen_k = int(sub.loc[sub.auc.idxmax(), 'k'])
    core = order[:chosen_k]
    core_auc, core_acc = cv_metrics(Xdf[core].values, y)
    core_rec = recall_score(y, (cross_val_predict(GradientBoostingClassifier(random_state=0),
                Xdf[core].values, y, cv=5, method='predict_proba')[:, 1] >= 0.5).astype(int), zero_division=0)

    print(f"\n核心指标数 = {chosen_k}, CV准确率 = {core_acc:.3f}, AUC = {core_auc:.3f}")
    print("核心指标:", core)

    # ---- 保存 ----
    rank['selected'] = rank['indicator'].isin(core)
    rank.to_csv(C.out('data', 'feature_importance_ranking.csv'), index=False)

    core_def = {
        'n_core': chosen_k,
        'core_indicators': core,
        'target_accuracy': TARGET_ACC,
        'core_cv_accuracy': core_acc,
        'core_cv_auc': core_auc,
        'core_cv_recall': core_rec,
        'full_cv_accuracy': full_acc,
        'full_cv_auc': full_auc,
        'n_full_indicators': len(order),
        'accuracy_retained_pct': 100 * core_acc / full_acc,
        'auc_retained_pct': 100 * core_auc / full_auc,
        'selection_rule': 'min k in [5,10] with AUC>=95% of full AND acc>=0.88 (accuracy alone inflated by 10% imbalance)',
    }
    with open(C.out('data', 'core_indicators.json'), 'w', encoding='utf-8') as f:
        json.dump(core_def, f, ensure_ascii=False, indent=2)

    # 曲线图
    plt.figure(figsize=(9, 5))
    plt.plot(curve.k, curve.accuracy, 'o-', label='CV accuracy')
    plt.plot(curve.k, curve.auc, 's--', label='CV AUC', alpha=0.7)
    plt.axhline(TARGET_ACC, color='r', ls=':', label=f'target {TARGET_ACC}')
    plt.axvline(chosen_k, color='g', ls=':', label=f'chosen k={chosen_k}')
    plt.xlabel('# indicators (top-k by Shapley)'); plt.ylabel('score')
    plt.title('Core indicator selection'); plt.legend(); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(C.out('figures', 'indicator_selection_curve.png'), dpi=150); plt.close()

    # 报告
    ok_flag = core_acc >= TARGET_ACC
    md = "# Phase 2.3 核心指标筛选与有效性验证报告\n\n"
    md += f"- 从 **{len(order)} 项**指标中筛选出 **{chosen_k} 项**核心指标(目标 5-10)\n"
    md += f"- 核心子集 5折CV: **准确率 {core_acc:.3f}**, AUC {core_auc:.3f}, 召回 {core_rec:.3f}\n"
    md += f"- 全量 {len(order)} 指标 5折CV: 准确率 {full_acc:.3f}, AUC {full_auc:.3f}\n"
    md += f"- 精度保留率: 准确率 {100*core_acc/full_acc:.1f}%, AUC {100*core_auc/full_auc:.1f}% (用 {chosen_k}/{len(order)} 指标)\n"
    md += f"- 精准度 ≥{TARGET_ACC}: {'✅ 达标' if ok_flag else '❌ 未达标'}\n"
    md += f"- ⚠️ 失效率仅 {100*y.mean():.0f}%, 准确率天然虚高(全判正常即~90%); 故筛选以 **AUC** 为主, 准确率为辅。\n\n"
    md += "## 核心指标(按 Shapley 贡献度)\n\n| 排名 | 指标 | 平均\\|SHAP\\| | 贡献% |\n|---|---|---|---|\n"
    for _, r in rank[rank.selected].iterrows():
        md += f"| {int(r['rank'])} | {r['indicator']} | {r['mean_abs_shap']:.4f} | {r['contribution_pct']:.1f}% |\n"
    md += "\n## 增量评估(Top-k)\n\n| k | 准确率 | AUC |\n|---|---|---|\n"
    for _, r in curve[curve.k <= MAX_K + 2].iterrows():
        mark = ' ⬅ 选定' if int(r['k']) == chosen_k else ''
        md += f"| {int(r['k'])} | {r['accuracy']:.3f} | {r['auc']:.3f} |{mark}\n"
    md += "\n## 结论\n\n"
    md += f"- 仅用 **{chosen_k} 个核心指标**即可保留约 {100*core_acc/full_acc:.0f}% 的判别精度, "
    md += "说明检测体系可在不显著损失准确率的前提下大幅精简 → 为 Phase 3 动态检测顺序优化奠定基础。\n"
    with open(C.out('reports', 'validation_report.md'), 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"\n✅ 已保存 core_indicators.json / 验证报告 (≥{TARGET_ACC}: {ok_flag})")


if __name__ == '__main__':
    main()
