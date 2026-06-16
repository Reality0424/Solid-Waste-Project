#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: TransE 模型训练脚本
功能: 从 Neo4j 知识图谱抽取三元组，训练 TransE 模型（真正的梯度下降），
      生成实体/关系嵌入，写回 Neo4j，并导出嵌入与训练曲线。

TransE: 对三元组 (h, r, t) 学习使 ||h + r - t|| 尽量小，
        负样本 (h', r, t) / (h, r, t') 的距离尽量大。
        margin ranking loss: max(0, margin + d(h,r,t) - d(h',r,t'))
"""

import numpy as np
import pickle
import yaml
import argparse
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EPS = 1e-8


class TransE:
    """numpy 实现的 TransE（向量化小批量梯度下降）"""

    def __init__(self, n_entities, n_relations, dim=100, margin=1.0, lr=0.01, seed=42):
        self.dim = dim
        self.margin = margin
        self.lr = lr
        rng = np.random.default_rng(seed)
        bound = 6.0 / np.sqrt(dim)
        self.E = rng.uniform(-bound, bound, size=(n_entities, dim))
        self.R = rng.uniform(-bound, bound, size=(n_relations, dim))
        # 关系向量归一化一次（TransE 惯例：仅实体每轮归一化）
        self.R /= (np.linalg.norm(self.R, axis=1, keepdims=True) + EPS)
        self.rng = rng

    def _normalize_entities(self):
        self.E /= (np.linalg.norm(self.E, axis=1, keepdims=True) + EPS)

    def train(self, triples, epochs=200, batch_size=512):
        """triples: int ndarray [N, 3] = (h, r, t)"""
        logger.info(f"开始训练 (epochs={epochs}, batch={batch_size}, lr={self.lr}, margin={self.margin})...")
        n = len(triples)
        n_ent = self.E.shape[0]
        losses = []
        self._normalize_entities()

        for epoch in range(epochs):
            perm = self.rng.permutation(n)
            epoch_loss = 0.0
            for i in range(0, n, batch_size):
                idx = perm[i:i + batch_size]
                h, r, t = triples[idx, 0], triples[idx, 1], triples[idx, 2]
                bs = len(idx)

                # 负采样：随机替换头或尾
                corrupt_head = self.rng.random(bs) < 0.5
                neg_ent = self.rng.integers(0, n_ent, size=bs)
                hn = np.where(corrupt_head, neg_ent, h)
                tn = np.where(corrupt_head, t, neg_ent)

                pos = self.E[h] + self.R[r] - self.E[t]
                neg = self.E[hn] + self.R[r] - self.E[tn]
                d_pos = np.linalg.norm(pos, axis=1)
                d_neg = np.linalg.norm(neg, axis=1)

                loss_vec = self.margin + d_pos - d_neg
                mask = loss_vec > 0
                epoch_loss += float(np.sum(loss_vec[mask]))
                if not np.any(mask):
                    continue

                g_pos = pos[mask] / (d_pos[mask][:, None] + EPS)
                g_neg = neg[mask] / (d_neg[mask][:, None] + EPS)
                hm, rm, tm = h[mask], r[mask], t[mask]
                hnm, tnm = hn[mask], tn[mask]

                gE = np.zeros_like(self.E)
                gR = np.zeros_like(self.R)
                # 正样本：减小 d_pos
                np.add.at(gE, hm, g_pos)
                np.add.at(gE, tm, -g_pos)
                np.add.at(gR, rm, g_pos)
                # 负样本：增大 d_neg
                np.add.at(gE, hnm, -g_neg)
                np.add.at(gE, tnm, g_neg)
                np.add.at(gR, rm, -g_neg)

                self.E -= self.lr * gE / bs
                self.R -= self.lr * gR / bs

            self._normalize_entities()
            epoch_loss /= n
            losses.append(epoch_loss)
            if (epoch + 1) % 10 == 0 or epoch == 0:
                logger.info(f"  Epoch {epoch + 1}/{epochs}, Loss: {epoch_loss:.6f}")

        logger.info(f"✅ 训练完成，最终 Loss: {losses[-1]:.6f}")
        return losses


class TransETrainer:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, database='neo4j'):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.database = database
        self.driver = None

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

    def extract_triples(self):
        """统一抽取三元组：所有节点都有 key 属性"""
        logger.info("从 Neo4j 抽取三元组...")
        triples = []
        with self.driver.session(database=self.database) as s:
            result = s.run("MATCH (h)-[r]->(t) RETURN h.key AS h, type(r) AS rel, t.key AS t")
            for rec in result:
                if rec['h'] and rec['rel'] and rec['t']:
                    triples.append((rec['h'], rec['rel'], rec['t']))
        logger.info(f"  三元组数: {len(triples)}")
        return triples

    def update_neo4j_embeddings(self, entity_list, E):
        """将嵌入写回 Neo4j（按 key 匹配所有节点类型）"""
        logger.info("写回嵌入到 Neo4j...")
        rows = [{'key': k, 'emb': ','.join(f'{x:.6f}' for x in E[i])}
                for i, k in enumerate(entity_list)]
        with self.driver.session(database=self.database) as s:
            updated = 0
            for i in range(0, len(rows), 1000):
                res = s.run(
                    "UNWIND $rows AS row MATCH (n {key: row.key}) "
                    "SET n.embedding = row.emb RETURN count(n) AS c",
                    rows=rows[i:i + 1000]).single()
                updated += res['c']
        logger.info(f"  ✓ 已更新 {updated} 个节点的 embedding")

    def visualize(self, model, entity_list, labels, losses, fig_path, loss_path):
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from sklearn.decomposition import PCA

            # 嵌入 PCA 散点（按实体类型着色）
            emb2d = PCA(n_components=2).fit_transform(model.E)
            plt.figure(figsize=(11, 8))
            uniq = sorted(set(labels))
            cmap = plt.colormaps['tab10'].resampled(len(uniq))
            for ci, lab in enumerate(uniq):
                idx = [i for i, l in enumerate(labels) if l == lab]
                plt.scatter(emb2d[idx, 0], emb2d[idx, 1], s=18, alpha=0.6,
                            color=cmap(ci), label=f"{lab} ({len(idx)})")
            plt.legend(loc='best', fontsize=8)
            plt.title('TransE Entity Embeddings (PCA)')
            plt.xlabel('PC1'); plt.ylabel('PC2'); plt.grid(True, alpha=0.3)
            plt.tight_layout()
            Path(fig_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(fig_path, dpi=150); plt.close()
            logger.info(f"✅ 嵌入可视化: {fig_path}")

            # 训练损失曲线
            plt.figure(figsize=(8, 5))
            plt.plot(range(1, len(losses) + 1), losses, marker='.', ms=3)
            plt.title('TransE Training Loss'); plt.xlabel('Epoch'); plt.ylabel('Margin Loss')
            plt.grid(True, alpha=0.3); plt.tight_layout()
            plt.savefig(loss_path, dpi=150); plt.close()
            logger.info(f"✅ 损失曲线: {loss_path}")
        except Exception as e:
            logger.warning(f"可视化失败（跳过）: {e}")

    def train(self, model_output_path, embeddings_output_path, fig_path, loss_path,
              dim=100, epochs=200, lr=0.01, margin=1.0, test_ratio=0.1, seed=42):
        logger.info("=" * 60)
        logger.info("Phase 1: TransE 模型训练")
        logger.info("=" * 60)
        if not self.connect():
            return False

        triples_raw = self.extract_triples()
        if len(triples_raw) < 100:
            logger.error("三元组过少，无法训练")
            self.driver.close()
            return False

        # 建索引
        entities = sorted({h for h, _, _ in triples_raw} | {t for _, _, t in triples_raw})
        relations = sorted({r for _, r, _ in triples_raw})
        e_idx = {e: i for i, e in enumerate(entities)}
        r_idx = {r: i for i, r in enumerate(relations)}
        logger.info(f"  唯一实体: {len(entities)}, 唯一关系: {len(relations)}")

        triples = np.array([(e_idx[h], r_idx[r], e_idx[t]) for h, r, t in triples_raw], dtype=np.int64)

        # 训练/测试划分（用于链路预测评估）
        rng = np.random.default_rng(seed)
        perm = rng.permutation(len(triples))
        n_test = max(1, int(len(triples) * test_ratio))
        test_idx, train_idx = perm[:n_test], perm[n_test:]
        train_triples, test_triples = triples[train_idx], triples[test_idx]
        logger.info(f"  训练三元组: {len(train_triples)}, 测试三元组: {len(test_triples)}")

        # 训练
        model = TransE(len(entities), len(relations), dim=dim, margin=margin, lr=lr, seed=seed)
        losses = model.train(train_triples, epochs=epochs)

        # 实体类型标签（用于可视化）
        labels = []
        for e in entities:
            if e.startswith('PARAM::'):   labels.append('Parameter')
            elif e.startswith('DIM::'):   labels.append('Dimension')
            elif e.startswith('TS::'):    labels.append('TestStage')
            elif e.startswith('FM::'):    labels.append('FailureMode')
            elif e.startswith('MODEL::'): labels.append('ChipModel')
            else:                          labels.append('Chip')

        # 保存模型
        model_output_path = Path(model_output_path)
        model_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(model_output_path, 'wb') as f:
            pickle.dump({
                'embedding_dim': dim,
                'entity_list': entities,
                'relation_list': relations,
                'entity_embeddings': model.E,
                'relation_embeddings': model.R,
                'entity_id_map': e_idx,
                'relation_id_map': r_idx,
                'entity_labels': labels,
                'train_losses': losses,
                'final_loss': losses[-1],
                'test_triples': test_triples,
                'margin': margin,
                'timestamp': datetime.now().isoformat(),
            }, f)
        logger.info(f"✅ 模型已保存: {model_output_path}")

        # 保存嵌入 npy（实体嵌入矩阵）
        embeddings_output_path = Path(embeddings_output_path)
        embeddings_output_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(embeddings_output_path, model.E)
        logger.info(f"✅ 嵌入向量已保存: {embeddings_output_path} (shape={model.E.shape})")

        # 写回 Neo4j + 可视化
        self.update_neo4j_embeddings(entities, model.E)
        self.visualize(model, entities, labels, losses, fig_path, loss_path)

        self.driver.close()
        logger.info("=" * 60)
        logger.info("✅ TransE 模型训练完成！")
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
    parser = argparse.ArgumentParser(description='Phase 1 TransE 训练脚本')
    parser.add_argument('--config', type=str, default='../../config/neo4j.yaml')
    parser.add_argument('--model_output_path', type=str, default='outputs/models/phase1_transe.pkl')
    parser.add_argument('--embeddings_output', type=str, default='outputs/data/transe_embeddings.npy')
    parser.add_argument('--visualization_output', type=str, default='outputs/figures/embedding_visualization.png')
    parser.add_argument('--loss_output', type=str, default='outputs/figures/training_loss.png')
    parser.add_argument('--dim', type=int, default=100)
    parser.add_argument('--epochs', type=int, default=300)
    parser.add_argument('--lr', type=float, default=0.02)
    parser.add_argument('--margin', type=float, default=1.0)
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    config_path = _resolve(args.config, script_dir)  # '../../config/neo4j.yaml' -> Solid-Waste-Project/config
    neo4j_config = load_config(config_path)['neo4j']

    trainer = TransETrainer(
        neo4j_config['uri'], neo4j_config['username'], neo4j_config['password'],
        neo4j_config.get('database', 'neo4j'))
    trainer.train(
        str(_resolve(args.model_output_path, script_dir, up=True)),
        str(_resolve(args.embeddings_output, script_dir, up=True)),
        str(_resolve(args.visualization_output, script_dir, up=True)),
        str(_resolve(args.loss_output, script_dir, up=True)),
        dim=args.dim, epochs=args.epochs, lr=args.lr, margin=args.margin)


if __name__ == '__main__':
    main()
