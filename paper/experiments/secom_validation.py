#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实数据外部验证: 在 UCI SECOM 半导体制造数据集上复现本文方法学
(多参数测量 -> 失效识别 + Shapley 核心指标精简), 以消除"仅合成数据/自证"的质疑。

SECOM (McCann & Johnston, 2008, UCI ML Repository):
  1567 个样本 × 590 个传感/测量特征, 标签 -1=合格 / 1=失效 (104 失效, ~14:1 不平衡),
  含缺失值与常量列。与本项目"多参数检测数据 -> pass/fail + 高维特征精简"高度同构。

流程(与 Phase 2 一致):
  1) 预处理: 去常量/近常量列, 中位数填补缺失, 标准化
  2) 5 折交叉验证 OOF: 线性(Logistic) vs 梯度提升(GBM), 报告 AUC/准确率/召回/F1
  3) TreeSHAP 指标贡献度排序
  4) 增量 Top-k 核心特征选择: 用极少数特征保留大部分判别力

输出: paper/experiments/outputs/secom_results.json, secom_topk_curve.csv
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import shap
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import roc_auc_score, accuracy_score, recall_score, f1_score, balanced_accuracy_score

HERE = Path(__file__).resolve().parent
DATA = HERE / 'data'
OUT = HERE / 'outputs'; OUT.mkdir(parents=True, exist_ok=True)
SEED = 42


def load_secom():
    X = pd.read_csv(DATA / 'secom.data', sep=r'\s+', header=None, na_values='NaN')
    lab = pd.read_csv(DATA / 'secom_labels.data', sep=r'\s+', header=None, usecols=[0])
    y = (lab[0].values == 1).astype(int)   # 1 = 失效
    return X, y


def tuned_acc(prob, y):
    return max(accuracy_score(y, (prob >= t).astype(int)) for t in np.linspace(0.02, 0.98, 97))


def best_thr_bal(prob, y):
    best, bt = -1, 0.5
    for t in np.linspace(0.02, 0.98, 97):
        b = balanced_accuracy_score(y, (prob >= t).astype(int))
        if b > best:
            best, bt = b, t
    return bt


def cv_oof(model_fn, X, y, cv=5):
    return cross_val_predict(model_fn(), X, y, cv=StratifiedKFold(cv, shuffle=True, random_state=SEED),
                             method='predict_proba')[:, 1]


def main():
    print("=" * 60); print("SECOM 真实数据外部验证"); print("=" * 60)
    Xraw, y = load_secom()
    print(f"原始: {Xraw.shape[0]} 样本 × {Xraw.shape[1]} 特征 | 失效 {int(y.sum())} ({100*y.mean():.1f}%)")

    # 预处理
    imp = SimpleImputer(strategy='median')
    Xi = imp.fit_transform(Xraw)
    vt = VarianceThreshold(threshold=1e-8)        # 去常量列
    Xv = vt.fit_transform(Xi)
    print(f"去常量列后: {Xv.shape[1]} 特征")
    Xs = StandardScaler().fit_transform(Xv)

    # 5 折 OOF: 线性 vs GBM
    lin = cv_oof(lambda: LogisticRegression(max_iter=5000, class_weight='balanced'), Xs, y)
    gbm = cv_oof(lambda: GradientBoostingClassifier(random_state=SEED), Xv, y)
    res = {}
    for name, p, Xref in [('linear', lin, Xs), ('gbm', gbm, Xv)]:
        thr = best_thr_bal(p, y)
        res[name] = {'auc': roc_auc_score(y, p), 'accuracy': tuned_acc(p, y),
                     'recall_at_bal_thr': recall_score(y, (p >= thr).astype(int), zero_division=0),
                     'f1_at_bal_thr': f1_score(y, (p >= thr).astype(int), zero_division=0)}
    print(f"\n线性(全特征): AUC {res['linear']['auc']:.3f}  acc {res['linear']['accuracy']:.3f}")
    print(f"GBM (全特征): AUC {res['gbm']['auc']:.3f}  acc {res['gbm']['accuracy']:.3f}  "
          f"recall {res['gbm']['recall_at_bal_thr']:.3f}")

    # TreeSHAP 贡献度排序
    print("\n计算 TreeSHAP ...")
    gbm_full = GradientBoostingClassifier(random_state=SEED).fit(Xv, y)
    sv = np.asarray(shap.TreeExplainer(gbm_full).shap_values(Xv))
    if sv.ndim == 3:
        sv = sv[:, :, 1]
    mean_abs = np.abs(sv).mean(0)
    order = np.argsort(mean_abs)[::-1]

    # 增量 Top-k 核心特征选择
    print("增量 Top-k (5折CV GBM AUC):")
    rows = []
    for k in [3, 5, 8, 10, 12, 15, 20, 25, 30, 40, 50, 80]:
        cols = order[:k]
        auc = roc_auc_score(y, cv_oof(lambda: GradientBoostingClassifier(random_state=SEED), Xv[:, cols], y))
        rows.append({'k': k, 'auc': auc})
        print(f"  k={k:3d}  AUC={auc:.3f}")
    curve = pd.DataFrame(rows)
    curve.to_csv(OUT / 'secom_topk_curve.csv', index=False)

    full_auc = res['gbm']['auc']
    best_row = curve.loc[curve.auc.idxmax()]
    best_k, best_auc = int(best_row['k']), float(best_row['auc'])
    # 最小 k 使其 ≥95% 全特征AUC
    ok = curve[curve.auc >= 0.95 * full_auc]
    min_k = int(ok.iloc[0]['k']) if len(ok) else best_k

    summary = {
        'dataset': 'UCI SECOM (McCann & Johnston, 2008)',
        'n_samples': int(Xraw.shape[0]), 'n_features_raw': int(Xraw.shape[1]),
        'n_features_after_constfilter': int(Xv.shape[1]),
        'n_fail': int(y.sum()), 'imbalance_ratio': float((1 - y.mean()) / y.mean()),
        'full_feature': res,
        'core_selection': {
            'full_gbm_auc': full_auc,
            'min_k_for_95pct': min_k,
            'best_k': best_k, 'best_k_auc': best_auc,
            'auc_improvement_vs_full': best_auc - full_auc,
        },
        'eval': '5-fold stratified OOF',
    }
    print(f"\n  最小保留95% AUC 的特征数: Top-{min_k}")
    print(f"  最佳: Top-{best_k} -> AUC {best_auc:.3f} (全特征 {full_auc:.3f}, 提升 {best_auc-full_auc:+.3f})")
    with open(OUT / 'secom_results.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"✅ 结果已保存 -> {OUT/'secom_results.json'}")


if __name__ == '__main__':
    main()
