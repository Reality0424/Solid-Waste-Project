#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 6 / 任务6.1: 全流程闭环系统集成

把各阶段能力串成一个决策系统(每颗芯片):
  失效检测(Phase2式) -> 若失效: 失效模式分类 + 修复策略(Phase5库) -> 三分类分选
  若非失效: 适配性头(Phase5)选最佳应用场景 -> reuse
训练失效检测器与失效模式分类器并保存; 定义 decide() 单芯片接口。

产出: outputs/models/fault_detector.pkl, outputs/models/mode_classifier.pkl
"""
import pickle
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
import _common as C

np.random.seed(0)


def main():
    print("=" * 60); print("Phase 6 / 6.1 全流程系统集成"); print("=" * 60)
    df, y = C.load_base()
    X = df[C.FEATURES].values

    fault = GradientBoostingClassifier(random_state=0).fit(X, y)
    # 失效模式分类器(仅在失效样本上训练)
    fail_mask = y == 1
    mode = GradientBoostingClassifier(random_state=0).fit(X[fail_mask], df.loc[fail_mask, 'failure_mode'].values)
    with open(C.out('models', 'fault_detector.pkl'), 'wb') as f:
        pickle.dump(fault, f)
    with open(C.out('models', 'mode_classifier.pkl'), 'wb') as f:
        pickle.dump(mode, f)

    heads = C.load_compat_heads(); repair = C.load_repair_mapping()
    print(f"  失效检测器 + 失效模式分类器 已训练并保存")
    print(f"  已加载 {len(heads)} 个适配性头, 修复库覆盖 {len([k for k in repair if not k.startswith('_')])} 失效模式")

    # 单芯片决策演示
    demo = X[:1]
    fp = fault.predict_proba(demo)[0, 1]
    if fp < 0.3:
        best = max(C.SCENARIOS, key=lambda s: heads[s].predict_proba(demo)[0, 1])
        print(f"  [演示] 芯片0: 失效概率 {fp:.2f} -> REUSE @ {best}")
    else:
        m = mode.predict(demo)[0]
        print(f"  [演示] 芯片0: 失效概率 {fp:.2f}, 模式 {m} -> {'REPAIR' if repair.get(m,{}).get('success_rate',0)>0 else 'REJECT'}")
    print("✅ 系统组件就绪 (fault_detector, mode_classifier, compat heads, repair lib)")


if __name__ == '__main__':
    main()
