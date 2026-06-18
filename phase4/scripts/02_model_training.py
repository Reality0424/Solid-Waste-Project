#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 / 任务4.2: 增量更新 + 特征权重自适应

从 v1 基础模型出发, 依次对 v2、v3 做 partial_fit 增量更新(无需全量重训),
对比"增量模型"与"全量重训模型"在最新版本上的精度 -> 学习效率。
同时记录特征权重(系数)随版本的自适应变化。

KPI: 新数据学习效率 ≥85% (= 增量精度 / 全量重训精度)
产出: outputs/figures/feature_weight_adaptation.png, outputs/figures/incremental_curve.png,
      outputs/data/incremental_results.json
"""
import json, pickle, copy
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.utils.class_weight import compute_class_weight
import _common as C


def balanced_cw(y):
    w = compute_class_weight('balanced', classes=np.array([0, 1]), y=y)
    return {0: float(w[0]), 1: float(w[1])}

np.random.seed(0)


def split(n, r=0.3, seed=0):
    rng = np.random.default_rng(seed); idx = rng.permutation(n); nt = int(n * r)
    return idx[nt:], idx[:nt]


def main():
    print("=" * 60); print("Phase 4 / 4.2 增量更新 + 特征权重自适应"); print("=" * 60)
    data, feats = C.load_versions()
    d = np.load(C.out('models', 'base_scaler.npz'))
    scaler = StandardScaler(); scaler.mean_ = d['mean']; scaler.scale_ = d['scale']; scaler.n_features_in_ = len(d['mean'])
    with open(C.out('models', 'base_sgd.pkl'), 'rb') as f:
        base = pickle.load(f)

    # per-version train/test split
    sp = {v: split(len(data[v][1]), seed=i) for i, v in enumerate(C.VERSIONS)}
    coef_hist = [base.coef_.ravel().copy()]
    incr = copy.deepcopy(base)
    acc_incr = {}

    for v in ['v2', 'v3']:
        X, y = data[v]; tr, te = sp[v]
        Xtr = scaler.transform(X[tr])
        for _ in range(20):
            incr.partial_fit(Xtr, y[tr])   # 增量更新(不重训历史数据)
        coef_hist.append(incr.coef_.ravel().copy())
        p = incr.predict_proba(scaler.transform(X[te]))[:, 1]
        acc_incr[v] = accuracy_score(y[te], (p >= 0.5).astype(int))
        print(f"  增量更新到 {v}: acc(on {v} test)={acc_incr[v]:.3f}")

    # 全量重训(在 v3 上从零训练)作为参照
    Xv3, yv3 = data['v3']; tr3, te3 = sp['v3']
    full = SGDClassifier(loss='log_loss', class_weight=balanced_cw(yv3[tr3]), random_state=0)
    Xtr3 = scaler.transform(Xv3[tr3])
    full.partial_fit(Xtr3, yv3[tr3], classes=np.array([0, 1]))
    for _ in range(50):
        full.partial_fit(Xtr3, yv3[tr3])
    pf = full.predict_proba(scaler.transform(Xv3[te3]))[:, 1]
    acc_full = accuracy_score(yv3[te3], (pf >= 0.5).astype(int))
    eff = acc_incr['v3'] / acc_full if acc_full > 0 else 0
    print(f"  全量重训(v3): acc={acc_full:.3f}")
    print(f"  学习效率 = 增量/全量 = {acc_incr['v3']:.3f}/{acc_full:.3f} = {eff:.3f}  (目标 ≥0.85)")

    res = {'acc_incremental': acc_incr, 'acc_full_retrain_v3': acc_full,
           'learning_efficiency': eff, 'kpi_pass': bool(eff >= 0.85)}
    with open(C.out('data', 'incremental_results.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    # 特征权重自适应图(Top-12 变化最大的指标)
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        H = np.array(coef_hist)  # [3 versions, n_feat]
        drift = np.abs(H[-1] - H[0]); top = np.argsort(drift)[::-1][:12]
        fig, ax = plt.subplots(figsize=(9, 5))
        for j in top:
            ax.plot(['v1', 'v2', 'v3'], H[:, j], marker='o', label=feats[j])
        ax.set_ylabel('SGD weight'); ax.set_title('Feature-weight adaptation across versions')
        ax.legend(fontsize=7, ncol=2); ax.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(C.out('figures', 'feature_weight_adaptation.png'), dpi=150); plt.close()

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(['incremental\n(v3)', 'full retrain\n(v3)'], [acc_incr['v3'], acc_full], color=['#4caf50', '#888'])
        ax.axhline(0.85 * acc_full, color='r', ls='--', label='85% of full'); ax.legend()
        ax.set_ylabel('accuracy on v3'); ax.set_title(f'Learning efficiency = {eff:.2f}')
        fig.tight_layout(); fig.savefig(C.out('figures', 'incremental_curve.png'), dpi=150); plt.close()
    except Exception as e:
        print('plot skip:', e)
    print(f"✅ 学习效率 {eff:.3f} (≥0.85: {eff>=0.85})")


if __name__ == '__main__':
    main()
