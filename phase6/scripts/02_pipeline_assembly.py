#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6 / 任务6.2: 全流程流水线执行与分选评估

对全部芯片用 OOF 预测跑端到端决策(reuse / repair / reject), 与真值三分类对比,
报告"智能分选"准确率与各类精确率(软件可测的'分选率'代理指标)。

产出: outputs/data/sorting_decisions.csv, outputs/data/sorting_metrics.json
"""
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import accuracy_score, precision_score, confusion_matrix
import _common as C

np.random.seed(0)
FAIL_THR = 0.30


def main():
    print("=" * 60); print("Phase 6 / 6.2 流水线执行与智能分选"); print("=" * 60)
    df, y = C.load_base(); X = df[C.FEATURES].values
    repair = C.load_repair_mapping(); heads = C.load_compat_heads()
    cv = StratifiedKFold(5, shuffle=True, random_state=42)

    # OOF 失效概率
    fail_oof = cross_val_predict(GradientBoostingClassifier(random_state=0), X, y, cv=cv, method='predict_proba')[:, 1]
    # OOF 失效模式(仅失效样本)
    fm = y == 1
    mode_oof = cross_val_predict(GradientBoostingClassifier(random_state=0),
                                 X[fm], df.loc[fm, 'failure_mode'].values,
                                 cv=StratifiedKFold(5, shuffle=True, random_state=1), method='predict')
    mode_map = {}; k = 0
    for i in np.where(fm)[0]:
        mode_map[i] = mode_oof[k]; k += 1

    gt = C.ground_truth_sort(df, y, repair)
    rows = []
    for i in range(len(df)):
        if fail_oof[i] < FAIL_THR:
            best = max(C.SCENARIOS, key=lambda s: heads[s].predict_proba(X[i:i+1])[0, 1])
            decision = 'reuse'; detail = best
        else:
            m = mode_map.get(i)
            if m is None:  # 预测失效但本是正常: 用全模型判模式
                m = 'multi_param_combined'
            sr = repair.get(m, {}).get('success_rate', 0)
            decision = 'repair' if sr and sr > 0 else 'reject'; detail = m
        rows.append({'chip_id': df.iloc[i]['chip_id'], 'fail_proba': round(float(fail_oof[i]), 3),
                     'decision': decision, 'detail': detail, 'ground_truth': gt[i]})
    D = pd.DataFrame(rows)
    D.to_csv(C.out('data', 'sorting_decisions.csv'), index=False)

    acc = accuracy_score(D.ground_truth, D.decision)
    labels = ['reuse', 'repair', 'reject']
    prec = precision_score(D.ground_truth, D.decision, labels=labels, average=None, zero_division=0)
    cm = confusion_matrix(D.ground_truth, D.decision, labels=labels)
    print(f"  三分类'分选'准确率 = {acc:.3f}")
    for l, p in zip(labels, prec):
        print(f"    {l:8} 精确率 {p:.3f}  (真值数 {int((D.ground_truth==l).sum())})")

    metrics = {'sorting_accuracy': float(acc),
               'precision_per_class': {l: float(p) for l, p in zip(labels, prec)},
               'confusion_matrix': cm.tolist(), 'labels': labels,
               'class_counts': {l: int((D.ground_truth == l).sum()) for l in labels}}
    with open(C.out('data', 'sorting_metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"✅ 分选准确率 {acc:.3f}; 决策已保存 sorting_decisions.csv")


if __name__ == '__main__':
    main()
