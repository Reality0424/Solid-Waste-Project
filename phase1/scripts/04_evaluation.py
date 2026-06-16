#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: 评估脚本
功能:
  1) 知识图谱完整性 / 架构验证（来自 Neo4j）
  2) TransE 链路预测质量 MRR / Hits@K（来自模型，使用训练时留出的测试三元组）
  3) 收敛性检查
  4) 生成 evaluation_report.md 与 transe_validation_report.md
"""

import yaml
import argparse
import pickle
from pathlib import Path
import logging
from datetime import datetime

import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EXPECTED_LABELS = ['Chip', 'Parameter', 'Dimension', 'TestStage', 'FailureMode', 'ChipModel']
EPS = 1e-8


class Evaluator:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, database='neo4j'):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.database = database
        self.driver = None
        self.report = {}

    def connect(self):
        from neo4j import GraphDatabase
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password), encrypted=False)
            with self.driver.session(database=self.database) as s:
                s.run("RETURN 1").single()
            logger.info("✅ 连接 Neo4j 成功")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j 连接失败: {e}")
            return False

    # ---- 图谱完整性 ----------------------------------------------------------
    def evaluate_graph_completeness(self):
        logger.info("评估图谱完整性...")
        with self.driver.session(database=self.database) as s:
            node_counts, total_nodes = {}, 0
            for rec in s.run("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS c"):
                node_counts[rec['label']] = rec['c']; total_nodes += rec['c']
            rel_counts, total_rels = {}, 0
            for rec in s.run("MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS c"):
                rel_counts[rec['t']] = rec['c']; total_rels += rec['c']

        completeness = min(1.0, total_nodes / 500) * min(1.0, total_rels / 1000)
        logger.info(f"  节点 {total_nodes}, 关系 {total_rels}, 完整性 {completeness:.2%}")
        self.report['graph_completeness'] = {
            'total_nodes': total_nodes, 'nodes_by_type': node_counts,
            'total_relationships': total_rels, 'relationships_by_type': rel_counts,
            'completeness_rate': completeness,
        }

    # ---- 架构验证（修复 db.labels() 误用）-----------------------------------
    def validate_schema(self):
        logger.info("验证数据架构...")
        with self.driver.session(database=self.database) as s:
            node_count = s.run("MATCH (n) RETURN count(n) AS c").single()['c']
            rel_count = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()['c']
            # 正确读取：db.labels() 每行一个标签
            label_list = [rec[0] for rec in s.run("CALL db.labels()")]

        missing = [l for l in EXPECTED_LABELS if l not in label_list]
        self.report['schema_validation'] = {
            'node_count': node_count, 'relationship_count': rel_count,
            'labels_found': label_list, 'missing_labels': missing,
            'schema_valid': len(missing) == 0,
        }
        logger.info(f"  标签: {label_list}")
        logger.info(f"  架构有效: {len(missing) == 0}" + (f", 缺失: {missing}" if missing else ""))

    # ---- 模型质量 + 链路预测 -------------------------------------------------
    def evaluate_model_quality(self, model_path):
        logger.info("评估模型质量与链路预测...")
        model_path = Path(model_path)
        if not model_path.exists():
            logger.warning(f"模型文件不存在: {model_path}")
            self.report['model_quality'] = {'model_exists': False}
            return

        with open(model_path, 'rb') as f:
            m = pickle.load(f)

        E = m['entity_embeddings']
        R = m['relation_embeddings']
        losses = m.get('train_losses', [])
        test = np.asarray(m.get('test_triples', np.empty((0, 3), dtype=np.int64)))

        mq = {
            'model_exists': True,
            'embedding_dim': m.get('embedding_dim', E.shape[1]),
            'entities_embedded': E.shape[0],
            'relations_embedded': R.shape[0],
            'final_loss': float(m.get('final_loss', losses[-1] if losses else float('nan'))),
            'initial_loss': float(losses[0]) if losses else float('nan'),
            'model_saved_at': m.get('timestamp', 'unknown'),
        }

        # 收敛性：损失显著下降
        if losses:
            mq['loss_reduction'] = float(losses[0] - losses[-1])
            mq['converged'] = bool(losses[-1] < losses[0] * 0.7 and losses[-1] < m.get('margin', 1.0))
        else:
            mq['converged'] = False

        # 链路预测 MRR / Hits@K（raw，对头尾分别预测取平均）
        if len(test) > 0:
            metrics = self._link_prediction(E, R, test)
            mq.update(metrics)

        self.report['model_quality'] = mq
        logger.info(f"  final_loss={mq['final_loss']:.4f}, converged={mq['converged']}")
        if 'mrr' in mq:
            logger.info(f"  MRR={mq['mrr']:.4f}, Hits@1={mq['hits@1']:.4f}, "
                        f"Hits@3={mq['hits@3']:.4f}, Hits@10={mq['hits@10']:.4f}")

    @staticmethod
    def _link_prediction(E, R, test, max_eval=2000):
        n_ent = E.shape[0]
        if len(test) > max_eval:
            sel = np.random.default_rng(42).choice(len(test), size=max_eval, replace=False)
            test = test[sel]
        ranks = []
        for h, r, t in test:
            # 尾预测: ||E[h]+R[r] - E[*]||
            d_tail = np.linalg.norm((E[h] + R[r])[None, :] - E, axis=1)
            ranks.append(1 + int(np.sum(d_tail < d_tail[t])))
            # 头预测: ||E[*]+R[r] - E[t]||
            d_head = np.linalg.norm(E + (R[r] - E[t])[None, :], axis=1)
            ranks.append(1 + int(np.sum(d_head < d_head[h])))
        ranks = np.array(ranks, dtype=float)
        return {
            'eval_triples': int(len(test)),
            'mean_rank': float(ranks.mean()),
            'mrr': float(np.mean(1.0 / ranks)),
            'hits@1': float(np.mean(ranks <= 1)),
            'hits@3': float(np.mean(ranks <= 3)),
            'hits@10': float(np.mean(ranks <= 10)),
            'candidate_entities': int(n_ent),
        }

    # ---- 报告 ---------------------------------------------------------------
    def generate_reports(self, eval_path, validation_path):
        gc = self.report.get('graph_completeness', {})
        mq = self.report.get('model_quality', {})
        sv = self.report.get('schema_validation', {})

        # 成功标准
        checks = {
            '知识图谱实体数 ≥ 500': gc.get('total_nodes', 0) >= 500,
            '关系数 ≥ 1000': gc.get('total_relationships', 0) >= 1000,
            '完整性验证率 ≥ 90%': gc.get('completeness_rate', 0) >= 0.9,
            'TransE 模型收敛': mq.get('converged', False),
            '架构标签完整': sv.get('schema_valid', False),
        }
        passed = sum(checks.values())

        # ---- evaluation_report.md ----
        md = "# Phase 1 评估报告\n\n"
        md += f"**生成时间**: {datetime.now().isoformat()}\n\n"
        md += "## 📊 图谱完整性评估\n\n"
        md += f"- **节点总数**: {gc.get('total_nodes', 0)} (目标 ≥500, {'✅' if gc.get('total_nodes',0)>=500 else '❌'})\n"
        md += f"- **关系总数**: {gc.get('total_relationships', 0)} (目标 ≥1000, {'✅' if gc.get('total_relationships',0)>=1000 else '❌'})\n"
        md += f"- **完整性评分**: {gc.get('completeness_rate', 0):.2%}\n\n"
        md += "### 节点类型分布\n"
        for k, v in gc.get('nodes_by_type', {}).items():
            md += f"- {k}: {v}\n"
        md += "\n### 关系类型分布\n"
        for k, v in gc.get('relationships_by_type', {}).items():
            md += f"- {k}: {v}\n"

        md += "\n## 🧠 模型质量评估\n\n"
        md += f"- **模型存在**: {'✅ 是' if mq.get('model_exists') else '❌ 否'}\n"
        if mq.get('model_exists'):
            md += f"- **嵌入维度**: {mq.get('embedding_dim')}\n"
            md += f"- **嵌入实体数**: {mq.get('entities_embedded')}\n"
            md += f"- **嵌入关系数**: {mq.get('relations_embedded')}\n"
            md += f"- **初始 Loss**: {mq.get('initial_loss', float('nan')):.4f}\n"
            md += f"- **最终 Loss**: {mq.get('final_loss', float('nan')):.4f}\n"
            md += f"- **收敛**: {'✅ 是' if mq.get('converged') else '❌ 否'}\n"
            if 'mrr' in mq:
                md += f"\n### 链路预测 (raw, 候选实体数={mq['candidate_entities']}, 评估三元组={mq['eval_triples']})\n"
                md += f"- **MRR**: {mq['mrr']:.4f}\n"
                md += f"- **Hits@1**: {mq['hits@1']:.4f}\n"
                md += f"- **Hits@3**: {mq['hits@3']:.4f}\n"
                md += f"- **Hits@10**: {mq['hits@10']:.4f}\n"
                md += f"- **Mean Rank**: {mq['mean_rank']:.1f}\n"

        md += "\n## ✅ 架构验证\n\n"
        md += f"- **架构有效**: {'✅ 是' if sv.get('schema_valid') else '❌ 否'}\n"
        md += f"- **已找到标签**: {', '.join(sv.get('labels_found', []))}\n"
        if sv.get('missing_labels'):
            md += f"- **缺失标签**: {', '.join(sv['missing_labels'])}\n"

        md += "\n## 🎯 成功标准检查\n\n"
        for name, ok in checks.items():
            md += f"- {'✅' if ok else '❌'} {name}\n"
        md += f"\n**总体状态**: {passed}/{len(checks)} 标准通过\n"

        Path(eval_path).parent.mkdir(parents=True, exist_ok=True)
        with open(eval_path, 'w', encoding='utf-8') as f:
            f.write(md)
        logger.info(f"✅ 评估报告: {eval_path}")

        # ---- transe_validation_report.md ----
        vmd = "# Phase 1 TransE 验证报告\n\n"
        vmd += f"**生成时间**: {datetime.now().isoformat()}\n\n"
        if mq.get('model_exists'):
            vmd += "## 训练\n\n"
            vmd += f"- 嵌入维度: {mq.get('embedding_dim')}\n"
            vmd += f"- 初始 Loss → 最终 Loss: {mq.get('initial_loss', float('nan')):.4f} → {mq.get('final_loss', float('nan')):.4f}\n"
            vmd += f"- Loss 下降: {mq.get('loss_reduction', float('nan')):.4f}\n"
            vmd += f"- 收敛判定: {'通过' if mq.get('converged') else '未通过'}\n\n"
            if 'mrr' in mq:
                vmd += "## 链路预测质量 (raw)\n\n"
                vmd += "| 指标 | 数值 |\n|------|------|\n"
                vmd += f"| MRR | {mq['mrr']:.4f} |\n"
                vmd += f"| Hits@1 | {mq['hits@1']:.4f} |\n"
                vmd += f"| Hits@3 | {mq['hits@3']:.4f} |\n"
                vmd += f"| Hits@10 | {mq['hits@10']:.4f} |\n"
                vmd += f"| Mean Rank | {mq['mean_rank']:.1f} |\n"
                vmd += f"| 候选实体数 | {mq['candidate_entities']} |\n"
                vmd += f"| 评估三元组 | {mq['eval_triples']} |\n"
        else:
            vmd += "模型不存在，无法验证。\n"
        with open(validation_path, 'w', encoding='utf-8') as f:
            f.write(vmd)
        logger.info(f"✅ TransE 验证报告: {validation_path}")

        return passed, len(checks)

    def evaluate(self, model_path, eval_path, validation_path):
        logger.info("=" * 60)
        logger.info("Phase 1: 评估")
        logger.info("=" * 60)
        if not self.connect():
            return False
        self.evaluate_graph_completeness()
        self.validate_schema()
        self.driver.close()
        self.evaluate_model_quality(model_path)
        passed, total = self.generate_reports(eval_path, validation_path)
        logger.info("=" * 60)
        logger.info(f"✅ 评估完成！{passed}/{total} 标准通过")
        logger.info("=" * 60)
        return True


def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _resolve(p, base, up=False):
    p = Path(p)
    if p.is_absolute():
        return p
    return (base / '..' / p) if up else (base / p)


def main():
    parser = argparse.ArgumentParser(description='Phase 1 评估脚本')
    parser.add_argument('--config', type=str, default='../../config/neo4j.yaml')
    parser.add_argument('--model_path', type=str, default='outputs/models/phase1_transe.pkl')
    parser.add_argument('--output_path', type=str, default='outputs/reports/evaluation_report.md')
    parser.add_argument('--validation_path', type=str, default='outputs/reports/transe_validation_report.md')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    config_path = _resolve(args.config, script_dir)  # '../../config/neo4j.yaml' -> Solid-Waste-Project/config
    neo4j_config = load_config(config_path)['neo4j']

    Evaluator(
        neo4j_config['uri'], neo4j_config['username'], neo4j_config['password'],
        neo4j_config.get('database', 'neo4j')
    ).evaluate(
        str(_resolve(args.model_path, script_dir, up=True)),
        str(_resolve(args.output_path, script_dir, up=True)),
        str(_resolve(args.validation_path, script_dir, up=True)),
    )


if __name__ == '__main__':
    main()
