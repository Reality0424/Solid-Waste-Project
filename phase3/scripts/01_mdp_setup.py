#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 / 任务3.1: MDP 定义 + 掩码分类器训练

- MDP: 状态=已测指标值+掩码; 动作={测第j项} ∪ {停止判定}; 奖励=−时间成本/判对+判错−。
- 掩码分类器: 用随机掩码训练的 MLP, 可在"任意已测子集"下给出失效判定, 供 MDP 在"停止"时打分。

产出:
  outputs/models/masked_classifier.pt
  outputs/data/mdp_definition.json
"""
import json
import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score, accuracy_score
import _common as C

torch.manual_seed(0); np.random.seed(0)


def train_masked_classifier(Xs, y, train_idx, epochs=400):
    m = Xs.shape[1]
    model = C.MaskedClassifier(m)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    Xt = torch.tensor(Xs[train_idx]); yt = torch.tensor(y[train_idx])
    n = len(train_idx)
    # 类别权重缓解不平衡
    w = torch.tensor([1.0, float(np.sqrt((yt == 0).sum() / max((yt == 1).sum(), 1)))])
    rng = np.random.default_rng(0)
    for ep in range(epochs):
        model.train(); opt.zero_grad()
        # 每个样本一个随机掩码(保留比例 ~U(0.1,1)); 偶尔全掩(冷启动)
        keep_p = rng.uniform(0.1, 1.0, size=(n, 1)).astype(np.float32)
        mask = (rng.random((n, m)) < keep_p).astype(np.float32)
        mask = torch.tensor(mask)
        logits = model(Xt, mask)
        loss = F.cross_entropy(logits, yt, weight=w)
        loss.backward(); opt.step()
    return model


def evaluate(model, Xs, y, idx, mask_frac=1.0):
    model.eval()
    X = torch.tensor(Xs[idx]); mask = torch.ones_like(X) * mask_frac
    with torch.no_grad():
        p = torch.softmax(model(X, (torch.rand_like(X) < mask_frac).float() if mask_frac < 1 else torch.ones_like(X)), 1)[:, 1].numpy()
    return roc_auc_score(y[idx], p), accuracy_score(y[idx], (p >= 0.5).astype(int))


def main():
    print("=" * 60); print("Phase 3 / 3.1  MDP 定义 + 掩码分类器"); print("=" * 60)
    Xs, y, train_idx, test_idx = C.load()
    m = Xs.shape[1]
    print(f"芯片 {len(y)}, 指标 {m}, 失效率 {100*y.mean():.1f}% | 全测总成本 {C.FULL_COST:.1f}")

    model = train_masked_classifier(Xs, y, train_idx)
    auc_full, acc_full = evaluate(model, Xs, y, test_idx, mask_frac=1.0)
    auc_half, acc_half = evaluate(model, Xs, y, test_idx, mask_frac=0.5)
    print(f"掩码分类器 (全测)  : AUC {auc_full:.3f}  acc {acc_full:.3f}")
    print(f"掩码分类器 (半数随机): AUC {auc_half:.3f}  acc {acc_half:.3f}")

    torch.save(model.state_dict(), C.out('models', 'masked_classifier.pt'))

    mdp = {
        'state': 'revealed indicator values (m) concatenated with binary acquired-mask (m); m=%d' % m,
        'actions': '%d acquire-indicator actions + 1 stop-and-decide action = %d' % (m, m + 1),
        'reward': 'per acquire: -lambda * time_cost[j]; on stop: +1 if classifier decision correct else -1',
        'cost_model': {C.FEATURES[i]: float(C.COST[i]) for i in range(m)},
        'full_test_cost': C.FULL_COST,
        'classifier': 'masked MLP trained with random masks (handles any acquired subset)',
        'objective': 'minimize total test time while keeping accuracy >= 0.91 (>=30% time reduction vs full test)',
        'masked_clf_test_auc_full': auc_full, 'masked_clf_test_acc_full': acc_full,
    }
    with open(C.out('data', 'mdp_definition.json'), 'w', encoding='utf-8') as f:
        json.dump(mdp, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已保存 masked_classifier.pt 与 mdp_definition.json")


if __name__ == '__main__':
    main()
