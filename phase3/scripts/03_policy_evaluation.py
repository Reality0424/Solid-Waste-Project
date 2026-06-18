#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 / 任务3.3: 序贯检测策略评估(动态 PPO vs 传统全检)

在测试集上贪心执行 PPO 策略, 统计每颗芯片: 测了哪些指标/顺序、总时间、判定、对错。
与"全检 28 项(固定顺序)"基线对比 检测时间 与 准确率/召回。

产出:
  outputs/data/detection_policy.csv     每芯片的动态检测决策
  outputs/reports/optimization_results.md
  outputs/figures/strategy_comparison.png
"""
import json
import numpy as np
import pandas as pd
import torch
from collections import Counter
from sklearn.metrics import accuracy_score, recall_score, balanced_accuracy_score
import _common as C
from importlib import import_module
import sys
sys.path.insert(0, str(C.SCRIPT_DIR))
ACmod = import_module('02_ppo_training')  # reuse ActorCritic

torch.manual_seed(0); np.random.seed(0)


def run_policy(net, clf, x, m, max_steps=28):
    """对单颗芯片贪心执行策略, 返回 (acquired_order, total_cost, pred)。"""
    mask = np.zeros(m, np.float32); order = []
    for _ in range(max_steps + 1):
        s = torch.tensor(np.concatenate([x * mask, mask])[None, :])
        am = np.concatenate([1 - mask, [1.0]]).astype(np.float32)
        with torch.no_grad():
            logits, _ = net(s)
        logits = logits[0].numpy() + (am - 1) * 1e9
        a = int(np.argmax(logits))
        if a == m or mask.sum() == m:   # stop (or everything acquired)
            break
        mask[a] = 1.0; order.append(a)
    with torch.no_grad():
        pred = int(clf(torch.tensor(x[None, :]), torch.tensor(mask[None, :])).argmax(1).item())
    cost = float((mask * C.COST).sum())
    return order, cost, pred, mask


def baseline_full(clf, X, y, idx):
    """全检基线: 测全部 28 项, 用同一分类器判定。"""
    Xt = torch.tensor(X[idx]); mk = torch.ones_like(Xt)
    with torch.no_grad():
        pred = clf(Xt, mk).argmax(1).numpy()
    return pred


def main():
    print("=" * 60); print("Phase 3 / 3.3  动态检测策略评估"); print("=" * 60)
    Xs, y, train_idx, test_idx = C.load()
    m = Xs.shape[1]
    clf = C.MaskedClassifier(m); clf.load_state_dict(torch.load(C.out('models', 'masked_classifier.pt'))); clf.eval()
    net = ACmod.ActorCritic(m); net.load_state_dict(torch.load(C.out('models', 'ppo_agent.pt'))); net.eval()

    rows = []; preds = []; costs = []; acq_counter = Counter(); norder = []
    for i in test_idx:
        order, cost, pred, mask = run_policy(net, clf, Xs[i], m)
        preds.append(pred); costs.append(cost); norder.append(len(order))
        for j in order:
            acq_counter[C.FEATURES[j]] += 1
        rows.append({'chip_index': int(i), 'true': int(y[i]), 'pred': pred,
                     'n_tests': len(order), 'time_cost': cost,
                     'acquired_order': '>'.join(C.FEATURES[j] for j in order)})
    preds = np.array(preds); yt = y[test_idx]
    dyn_acc = accuracy_score(yt, preds); dyn_rec = recall_score(yt, preds, zero_division=0)
    dyn_bacc = balanced_accuracy_score(yt, preds); dyn_cost = float(np.mean(costs))

    bpred = baseline_full(clf, Xs, y, test_idx)
    full_acc = accuracy_score(yt, bpred); full_rec = recall_score(yt, bpred, zero_division=0)
    full_bacc = balanced_accuracy_score(yt, bpred)
    saved = 100 * (1 - dyn_cost / C.FULL_COST)

    pd.DataFrame(rows).to_csv(C.out('data', 'detection_policy.csv'), index=False)

    print(f"\n全检(28项, cost {C.FULL_COST:.0f}) : acc {full_acc:.3f}  recall {full_rec:.3f}  bal-acc {full_bacc:.3f}")
    print(f"动态PPO(均 {np.mean(norder):.1f} 项, cost {dyn_cost:.1f}): acc {dyn_acc:.3f}  recall {dyn_rec:.3f}  bal-acc {dyn_bacc:.3f}")
    print(f"检测时间降低: {saved:.1f}%  (目标 ≥30%)")
    print(f"准确率: {dyn_acc:.3f}  (目标 ≥0.91)")
    print("\n最常被选用的指标(动态策略学到的核心检测项):")
    for f, c in acq_counter.most_common(8):
        print(f"   {f:26} {100*c/len(test_idx):4.0f}% 的芯片")

    ok_time = saved >= 30; ok_acc = dyn_acc >= 0.91
    # 报告
    md = "# Phase 3 序贯检测优化结果\n\n"
    md += f"- 测试芯片: {len(test_idx)} | 全检总时间成本: {C.FULL_COST:.0f}\n\n"
    md += "## 动态策略 vs 传统全检 (测试集)\n\n"
    md += "| 策略 | 平均检测项 | 平均时间 | 时间降低 | 准确率 | 召回 | 平衡准确率 |\n|---|---|---|---|---|---|---|\n"
    md += f"| 传统全检(28项固定) | 28 | {C.FULL_COST:.0f} | - | {full_acc:.3f} | {full_rec:.3f} | {full_bacc:.3f} |\n"
    md += f"| **动态 PPO** | **{np.mean(norder):.1f}** | **{dyn_cost:.1f}** | **{saved:.1f}%** | **{dyn_acc:.3f}** | {dyn_rec:.3f} | {dyn_bacc:.3f} |\n\n"
    md += "## KPI 检查\n\n"
    md += f"- 检测时间降低 ≥30%: {'✅' if ok_time else '❌'} ({saved:.1f}%)\n"
    md += f"- 准确率 ≥91%: {'✅' if ok_acc else '❌'} ({dyn_acc:.3f})\n\n"
    md += "## 动态策略最常选用的核心检测项\n\n| 指标 | 被选用比例 |\n|---|---|\n"
    for f, c in acq_counter.most_common(10):
        md += f"| {f} | {100*c/len(test_idx):.0f}% |\n"
    with open(C.out('reports', 'optimization_results.md'), 'w', encoding='utf-8') as f:
        f.write(md)

    # 对比图
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
        ax[0].bar(['Full test\n(28 items)', 'Dynamic PPO'], [C.FULL_COST, dyn_cost], color=['#888', '#4caf50'])
        ax[0].set_ylabel('test-time cost'); ax[0].set_title(f'Test time  (-{saved:.0f}%)')
        for i, v in enumerate([C.FULL_COST, dyn_cost]):
            ax[0].text(i, v + 1, f'{v:.0f}', ha='center')
        x = np.arange(3); w = 0.35
        ax[1].bar(x - w/2, [full_acc, full_rec, full_bacc], w, label='Full test', color='#888')
        ax[1].bar(x + w/2, [dyn_acc, dyn_rec, dyn_bacc], w, label='Dynamic PPO', color='#4caf50')
        ax[1].set_xticks(x); ax[1].set_xticklabels(['accuracy', 'recall', 'bal-acc'])
        ax[1].axhline(0.91, color='r', ls='--', lw=1, label='acc target')
        ax[1].set_ylim(0, 1.05); ax[1].set_title('Detection quality'); ax[1].legend(fontsize=8)
        fig.tight_layout(); fig.savefig(C.out('figures', 'strategy_comparison.png'), dpi=150); plt.close()
    except Exception as e:
        print('plot skip:', e)

    print(f"\n✅ 已保存 detection_policy.csv / optimization_results.md / strategy_comparison.png")
    print(f"   KPI: 时间↓{saved:.0f}% (≥30%: {ok_time}) | 准确率 {dyn_acc:.3f} (≥0.91: {ok_acc})")


if __name__ == '__main__':
    main()
