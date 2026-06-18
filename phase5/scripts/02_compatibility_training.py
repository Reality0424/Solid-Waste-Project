#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5 / 任务5.2: 适配性预测头 + 风险量化

为每个应用场景训练"适配性预测头"(GBM): 预测芯片是否适配该场景(suitable=compatible)。
报告 per-scenario 与平均准确率(KPI ≥95%)、推理延迟(KPI ≤500ms), 并输出三级等级预测与置信度。

产出: outputs/models/compat_head_<scenario>.pkl, outputs/data/compatibility_predictions.csv,
      outputs/figures/compatibility_accuracy.png, outputs/data/compat_metrics.json
"""
import json, pickle, time
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold, cross_val_predict
from sklearn.metrics import accuracy_score
import _common as C

np.random.seed(0)


def main():
    print("=" * 60); print("Phase 5 / 5.2 适配性预测头"); print("=" * 60)
    comp, base, y = C.derive_compatibility()
    m = comp.merge(base[['chip_id'] + C.FEATURES], on='chip_id')
    m['suitable'] = (m['compatibility_level'] == 'compatible').astype(int)
    cv = StratifiedKFold(5, shuffle=True, random_state=42)

    rows = []; accs = {}
    for s in C.SCENARIOS:
        sub = m[m.application_scenario == s].reset_index(drop=True)
        X = sub[C.FEATURES].values; ys = sub['suitable'].values
        acc = cross_val_score(GradientBoostingClassifier(n_estimators=200, random_state=0),
                              X, ys, cv=cv, scoring='accuracy').mean()
        proba = cross_val_predict(GradientBoostingClassifier(n_estimators=200, random_state=0),
                                  X, ys, cv=cv, method='predict_proba')[:, 1]
        accs[s] = float(acc)
        print(f"  {s:26} suitable-acc = {acc:.3f}")
        head = GradientBoostingClassifier(n_estimators=200, random_state=0).fit(X, ys)
        with open(C.out('models', f'compat_head_{s}.pkl'), 'wb') as f:
            pickle.dump(head, f)
        for cid, p, lvl, sc in zip(sub['chip_id'], proba, sub['compatibility_level'], sub['compatibility_score']):
            rows.append({'chip_id': cid, 'scenario': s, 'suitable_proba': round(float(p), 3),
                         'pred_suitable': int(p >= 0.5), 'true_level': lvl, 'true_score': sc})
    mean_acc = float(np.mean(list(accs.values())))
    print(f"  平均适配性预测准确率 = {mean_acc:.3f}  (目标 ≥0.95)")

    # 推理延迟(单芯片 × 4 场景)
    heads = {s: pickle.load(open(C.out('models', f'compat_head_{s}.pkl'), 'rb')) for s in C.SCENARIOS}
    x1 = m[C.FEATURES].values[:1]
    t0 = time.perf_counter()
    for _ in range(100):
        for s in C.SCENARIOS:
            heads[s].predict_proba(x1)
    latency_ms = (time.perf_counter() - t0) / 100 * 1000
    print(f"  单芯片全场景推理延迟 ≈ {latency_ms:.2f} ms  (目标 ≤500ms)")

    pd.DataFrame(rows).to_csv(C.out('data', 'compatibility_predictions.csv'), index=False)
    metrics = {'per_scenario_suitable_acc': accs, 'mean_suitable_acc': mean_acc,
               'inference_latency_ms': latency_ms,
               'kpi_acc_pass': bool(mean_acc >= 0.95), 'kpi_latency_pass': bool(latency_ms <= 500)}
    with open(C.out('data', 'compat_metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4.5))
        names = [s.replace('_', '\n') for s in C.SCENARIOS]
        bars = ax.bar(names, [accs[s] for s in C.SCENARIOS], color='#3b7dd8')
        ax.axhline(0.95, color='r', ls='--', label='target 0.95')
        ax.axhline(mean_acc, color='g', ls=':', label=f'mean {mean_acc:.3f}')
        for b, s in zip(bars, C.SCENARIOS):
            ax.text(b.get_x() + b.get_width()/2, accs[s] + 0.005, f'{accs[s]:.3f}', ha='center', fontsize=9)
        ax.set_ylim(0.8, 1.0); ax.set_ylabel('suitability prediction accuracy'); ax.legend()
        ax.set_title('Phase 5: per-scenario compatibility head accuracy')
        fig.tight_layout(); fig.savefig(C.out('figures', 'compatibility_accuracy.png'), dpi=150); plt.close()
    except Exception as e:
        print('plot skip:', e)
    print(f"✅ 平均准确率 {mean_acc:.3f} (≥0.95: {mean_acc>=0.95}) | 延迟 {latency_ms:.1f}ms (≤500: {latency_ms<=500})")


if __name__ == '__main__':
    main()
