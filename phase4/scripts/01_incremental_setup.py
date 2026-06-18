#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 / 任务4.1: 增量学习机制搭建

定义 3 个"固件/批次版本"(带分布漂移), 在初始版本 v1 上训练基础模型并保存,
为后续增量更新(02)与迁移测试(03)提供起点。

产出: outputs/models/base_scaler.npz, outputs/models/base_sgd.pkl, outputs/data/version_stats.json
"""
import json, pickle
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


def split(Xy, r=0.3, seed=0):
    X, y = Xy; rng = np.random.default_rng(seed); idx = rng.permutation(len(y))
    nt = int(len(y) * r); return idx[nt:], idx[:nt]


def main():
    print("=" * 60); print("Phase 4 / 4.1 增量学习机制 (版本与基础模型)"); print("=" * 60)
    data, feats = C.load_versions()
    stats = {}
    for v, (X, y) in data.items():
        stats[v] = {'n': int(len(y)), 'failure_rate': round(float(y.mean()), 3)}
        print(f"  {v}: n={len(y)}  失效率={y.mean():.2f}")

    Xv1, yv1 = data['v1']
    tr, te = split((Xv1, yv1))
    scaler = StandardScaler().fit(Xv1[tr])
    base = SGDClassifier(loss='log_loss', class_weight=balanced_cw(yv1[tr]), random_state=0)
    base.partial_fit(scaler.transform(Xv1[tr]), yv1[tr], classes=np.array([0, 1]))
    for _ in range(30):  # 多轮以充分拟合初始版本
        base.partial_fit(scaler.transform(Xv1[tr]), yv1[tr])
    p = base.predict_proba(scaler.transform(Xv1[te]))[:, 1]
    acc = accuracy_score(yv1[te], (p >= 0.5).astype(int)); auc = roc_auc_score(yv1[te], p)
    print(f"  基础模型(v1): acc={acc:.3f} auc={auc:.3f}")

    np.savez(C.out('models', 'base_scaler.npz'), mean=scaler.mean_, scale=scaler.scale_)
    with open(C.out('models', 'base_sgd.pkl'), 'wb') as f:
        pickle.dump(base, f)
    stats['base_v1'] = {'accuracy': acc, 'auc': auc}
    with open(C.out('data', 'version_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print("✅ 已保存基础模型与版本统计")


if __name__ == '__main__':
    main()
