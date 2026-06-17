#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文配图生成(全部由代码生成, 无 AI 水印, 300 dpi)。
图类型多样化(示意图/图结构/热力图/散点/ROC/蜂群/曲线), 避免清一色柱状图。

输出 paper/figures/*.png:
  fig1_framework.png        方法框架(示意)
  fig2_kg_schema.png        知识图谱 schema(实体/关系元图)
  fig3_correlation.png      指标相关性热力图(物理耦合)
  fig4_hidden_failure.png   隐性故障: 散点(VOH-VIH 噪声边裕) + 全程±2σ占比(双面板)
  fig5_roc.png              合成数据 ROC: 线性 vs GBM(raw/opt)
  fig6_shap_beeswarm.png    SHAP 蜂群图(28 指标)
  fig7_core_selection.png   合成数据核心指标选择曲线
  fig8_secom.png            真实数据 SECOM Top-k 特征 AUC 曲线
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import shap
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import roc_curve, roc_auc_score

plt.rcParams.update({'font.size': 11, 'axes.grid': True, 'grid.alpha': 0.3,
                     'figure.dpi': 300, 'savefig.dpi': 300, 'savefig.bbox': 'tight'})

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
P2 = REPO / 'phase2' / 'outputs'
SECOM = REPO / 'paper' / 'experiments' / 'outputs'
BLUE, ORANGE, GREEN, RED, GRAY, PURPLE = '#3b7dd8', '#e8883a', '#4caf50', '#d9534f', '#888888', '#7e57c2'
CV = StratifiedKFold(5, shuffle=True, random_state=42)

FEATS = ['pin_flatness_deviation_um','solder_pad_oxidation_percent','package_scratch_depth_um','warpage_um',
'pin_coplanarity_percent','package_size_deviation_percent','vdd_voltage','idd_static_ma','idd_dynamic_ma',
'voh_voltage','vol_voltage','vih_voltage','vil_voltage','iil_leakage_ua','iol_leakage_ua','setup_time_ns',
'hold_time_ns','propagation_delay_ns','rise_time_ns','fall_time_ns','fmax_mhz','jtag_scan_pass',
'boundary_scan_pass','functional_test_pass','aging_temperature_c','aging_voltage_v','aging_frequency_mhz',
'aging_duration_hours']


def save(fig, name):
    fig.savefig(HERE / name); plt.close(fig); print('  ->', name)


def load_synth():
    df = pd.read_csv(REPO / 'synthetic_data' / 'chip_baseline_data.csv')
    y = (df.failure_mode != 'normal').astype(int).values
    return df, y


def engineer(df):
    e = {}
    e['vnm_high'] = df['voh_voltage'] - df['vih_voltage']
    e['vnm_low'] = df['vil_voltage'] - df['vol_voltage']
    per = 1000.0 / df['fmax_mhz'].clip(lower=1)
    e['setup_slack'] = per - df['setup_time_ns'] - df['propagation_delay_ns']
    e['dyn_power'] = df['idd_dynamic_ma'] * df['fmax_mhz'] / 1000.0
    e['thermal_index'] = df['idd_dynamic_ma'] * (1 + df['warpage_um'] / 100.0) * (df['aging_temperature_c'] / 85.0)
    e['leak_total'] = df['iil_leakage_ua'] + df['iol_leakage_ua']
    return np.column_stack([e[k].values for k in e])


# ---------- Fig 1: framework ----------
def fig_framework():
    fig, ax = plt.subplots(figsize=(11, 3.4)); ax.axis('off'); ax.grid(False)
    ax.set_xlim(0, 11); ax.set_ylim(0, 3.4)
    blocks = [(0.15, "Chip test data\n(28 indicators)\nphysical/DC/AC/aging", BLUE),
              (2.4, "Phase 1\nKnowledge graph\n+ TransE", GREEN),
              (4.65, "Phase 2.1\nFeature optimization\nGCN+GAT / GBM", ORANGE),
              (6.9, "Phase 2.2\nShapley (SHAP)\ncontribution", ORANGE),
              (9.15, "Phase 2.3\nCore indicators\n(28 -> 6)", RED)]
    for x, txt, c in blocks:
        ax.add_patch(FancyBboxPatch((x, 1.0), 1.9, 1.4, boxstyle="round,pad=0.06",
                     linewidth=1.4, edgecolor=c, facecolor=c + '22'))
        ax.text(x + 0.95, 1.7, txt, ha='center', va='center', fontsize=9)
    for x in [2.10, 4.35, 6.60, 8.85]:
        ax.add_patch(FancyArrowPatch((x, 1.7), (x + 0.30, 1.7), arrowstyle='-|>',
                     mutation_scale=15, linewidth=1.4, color=GRAY))
    ax.text(5.5, 0.35, "Validated on synthetic benchmark (hidden multi-parameter failures) + real UCI SECOM dataset",
            ha='center', fontsize=9, style='italic', color=GRAY)
    save(fig, 'fig1_framework.png')


# ---------- Fig 2: KG schema ----------
def fig_kg_schema():
    import networkx as nx
    G = nx.DiGraph()
    inter = [('Chip', 'ChipModel', 'OF_MODEL'), ('Chip', 'TestStage', 'UNDERGOES_TEST'),
             ('Chip', 'FailureMode', 'EXHIBITS'), ('Chip', 'Parameter', 'HAS_ABNORMAL'),
             ('Parameter', 'Dimension', 'BELONGS_TO'), ('Parameter', 'TestStage', 'MEASURED_IN')]
    for a, b, r in inter:
        G.add_edge(a, b, label=r)
    pos = {'Chip': (0, 0.2), 'ChipModel': (-2.4, 1.5), 'FailureMode': (-2.4, -1.2),
           'TestStage': (2.4, 1.5), 'Parameter': (2.0, -1.4), 'Dimension': (4.0, -2.4)}
    colors = {'Chip': BLUE, 'ChipModel': GREEN, 'FailureMode': RED, 'TestStage': ORANGE,
              'Parameter': PURPLE, 'Dimension': GRAY}
    fig, ax = plt.subplots(figsize=(9.5, 6.2)); ax.axis('off'); ax.grid(False)
    ax.set_xlim(-3.6, 5.4); ax.set_ylim(-3.3, 2.6)
    nx.draw_networkx_nodes(G, pos, node_color=[colors[n] for n in G.nodes],
                           node_size=1500, alpha=0.9, ax=ax)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=GRAY, arrows=True, arrowsize=15,
                           width=1.4, connectionstyle='arc3,rad=0.06', node_size=1500)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, 'label'),
                                 font_size=8, ax=ax, label_pos=0.5, rotate=False,
                                 bbox=dict(boxstyle='round,pad=0.18', fc='white', ec=GRAY, alpha=0.9))
    # 节点名放在节点下方(黑色), 避免裁切
    for n, (x, yv) in pos.items():
        ax.text(x, yv - 0.32, n, ha='center', va='top', fontsize=10, fontweight='bold')
    # 两个自关系以注记表示(self-loops)
    ax.annotate('↺ PRECEDES', xy=pos['TestStage'], xytext=(pos['TestStage'][0], pos['TestStage'][1] + 0.55),
                ha='center', fontsize=8, color=GRAY)
    ax.annotate('↺ CORRELATES_WITH', xy=pos['Parameter'], xytext=(pos['Parameter'][0] - 0.1, pos['Parameter'][1] + 0.5),
                ha='center', fontsize=8, color=GRAY)
    ax.set_title('Knowledge-graph schema: 6 entity types, 8 relation types', fontsize=12)
    save(fig, 'fig2_kg_schema.png')


# ---------- Fig 3: correlation heatmap ----------
def fig_correlation():
    df, _ = load_synth()
    cont = [c for c in FEATS if df[c].nunique() > 3]  # 连续指标
    corr = df[cont].corr().values
    fig, ax = plt.subplots(figsize=(8.5, 7.5))
    im = ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1)
    ax.set_xticks(range(len(cont))); ax.set_xticklabels(cont, rotation=90, fontsize=6.5)
    ax.set_yticks(range(len(cont))); ax.set_yticklabels(cont, fontsize=6.5)
    ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='Pearson r')
    ax.set_title('Indicator correlation (engineering coupling)')
    save(fig, 'fig3_correlation.png')


# ---------- Fig 4: hidden failure scatter + bar ----------
def fig_hidden_failure():
    df, _ = load_synth()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    # (a) derived noise margins: high-side (VOH-VIH) vs low-side (VIL-VOL).
    #     Noise-margin failures hug the low-margin edges -> non-convex (L-shaped) failing region.
    a = axes[0]; a.grid(True, alpha=0.3)
    df = df.copy()
    df['m_high'] = df['voh_voltage'] - df['vih_voltage']
    df['m_low'] = df['vil_voltage'] - df['vol_voltage']
    nrm = df[df.failure_mode == 'normal']
    nm = df[df.failure_mode == 'noise_margin_insufficient']
    a.scatter(nrm['m_high'], nrm['m_low'], s=10, c=GRAY, alpha=0.35, label='normal')
    a.scatter(nm['m_high'], nm['m_low'], s=34, c=RED, edgecolor='k', linewidth=0.3,
              label='noise-margin failure')
    a.set_xlabel('high-side margin  VOH$-$VIH (V)'); a.set_ylabel('low-side margin  VIL$-$VOL (V)')
    a.set_title('(a) Failures hug the low-margin edges\n(non-convex region; each axis alone overlaps normal)')
    a.legend(fontsize=9)
    # (b) within ±2σ bar
    b = axes[1]; b.grid(True, alpha=0.3)
    # 仅用连续测量指标(排除二值通过/失败标志, 其 0/1 会产生极大 z 值)
    feats = [c for c in FEATS if df[c].nunique() > 3]
    mu, sd = nrm[feats].mean(), nrm[feats].std().replace(0, 1)
    Z = (df[feats] - mu) / sd
    within2 = (Z.abs() <= 2).all(axis=1)
    order = ['physical_damage', 'noise_margin_insufficient', 'thermal_accumulation', 'multi_param_combined']
    pct = [100 * within2[df.failure_mode == m].mean() for m in order]
    labels = ['physical\ndamage', 'noise\nmargin', 'thermal', 'multi-\nparam']
    bars = b.bar(labels, pct, color=[GRAY, BLUE, ORANGE, RED])
    for bb, p in zip(bars, pct):
        b.text(bb.get_x() + bb.get_width() / 2, p + 1, f'{p:.0f}%', ha='center', fontsize=9)
    b.set_ylabel('% within $\\pm2\\sigma$ on ALL indicators'); b.set_ylim(0, max(pct) + 12)
    b.set_title('(b) Hidden failures have no single\nabnormal indicator')
    save(fig, 'fig4_hidden_failure.png')


# ---------- Fig 5: ROC ----------
def fig_roc():
    df, y = load_synth()
    rawX = StandardScaler().fit_transform(df[FEATS].values)
    optX = np.hstack([df[FEATS].values, engineer(df)])
    lin = cross_val_predict(LogisticRegression(max_iter=3000, class_weight='balanced'), rawX, y, cv=CV, method='predict_proba')[:, 1]
    gbm_raw = cross_val_predict(GradientBoostingClassifier(random_state=0), df[FEATS].values, y, cv=CV, method='predict_proba')[:, 1]
    gbm_opt = cross_val_predict(GradientBoostingClassifier(random_state=0), optX, y, cv=CV, method='predict_proba')[:, 1]
    fig, ax = plt.subplots(figsize=(6.4, 6))
    for p, c, lab in [(lin, GRAY, 'Linear (raw 28)'), (gbm_raw, BLUE, 'GBM (raw 28)'),
                      (gbm_opt, GREEN, 'GBM (optimized 28+6)')]:
        fpr, tpr, _ = roc_curve(y, p)
        ax.plot(fpr, tpr, color=c, lw=2, label=f'{lab}, AUC={roc_auc_score(y,p):.3f}')
    ax.plot([0, 1], [0, 1], '--', color='k', lw=1, alpha=0.5)
    ax.set_xlabel('False positive rate'); ax.set_ylabel('True positive rate')
    ax.set_title('ROC on synthetic benchmark (5-fold OOF)'); ax.legend(loc='lower right', fontsize=9)
    save(fig, 'fig5_roc.png')


# ---------- Fig 6: SHAP beeswarm ----------
def fig_shap_beeswarm():
    df, y = load_synth()
    model = GradientBoostingClassifier(random_state=0).fit(df[FEATS].values, y)
    sv = np.asarray(shap.TreeExplainer(model).shap_values(df[FEATS].values))
    if sv.ndim == 3:
        sv = sv[:, :, 1]
    shap.summary_plot(sv, df[FEATS].values, feature_names=FEATS, show=False, max_display=15)
    fig = plt.gcf(); fig.set_size_inches(8, 6)
    plt.title('SHAP summary (synthetic)')
    save(fig, 'fig6_shap_beeswarm.png')


# ---------- Fig 7: core selection ----------
def fig_core_selection():
    from sklearn.metrics import roc_auc_score as auc
    df, y = load_synth()
    rank = pd.read_csv(P2 / 'data' / 'shapley_values.csv')['indicator'].tolist()
    ks, aucs = list(range(1, 13)), []
    for k in ks:
        p = cross_val_predict(GradientBoostingClassifier(random_state=0), df[rank[:k]].values, y,
                              cv=CV, method='predict_proba')[:, 1]
        aucs.append(auc(y, p))
    ck = json.load(open(P2 / 'data' / 'core_indicators.json'))['n_core']
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.plot(ks, aucs, 'o-', color=BLUE)
    ax.axvline(ck, color=GREEN, ls='--', label=f'selected k={ck}')
    ax.set_xlabel('# indicators (top-k by Shapley)'); ax.set_ylabel('CV AUC')
    ax.set_title('Synthetic: core-indicator selection'); ax.legend()
    save(fig, 'fig7_core_selection.png')


# ---------- Fig 8: SECOM ----------
def fig_secom():
    curve = pd.read_csv(SECOM / 'secom_topk_curve.csv')
    s = json.load(open(SECOM / 'secom_results.json'))
    full = s['full_feature']['gbm']['auc']; nfull = s['n_features_after_constfilter']; bk = s['core_selection']['best_k']
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.plot(curve.k, curve.auc, 'o-', color=ORANGE, label='SHAP top-k features')
    ax.axhline(full, color=GRAY, ls='--', label=f'all {nfull} features (AUC {full:.3f})')
    ax.axvline(bk, color=GREEN, ls=':', label=f'best k={bk}')
    ax.set_xlabel('# features (top-k by Shapley)'); ax.set_ylabel('GBM CV AUC')
    ax.set_title('Real data (UCI SECOM): feature selection improves AUC'); ax.legend()
    save(fig, 'fig8_secom_validation.png')


if __name__ == '__main__':
    print('Generating figures ->', HERE)
    fig_framework(); fig_kg_schema(); fig_correlation(); fig_hidden_failure()
    fig_roc(); fig_shap_beeswarm(); fig_core_selection(); fig_secom()
    print('Done.')
