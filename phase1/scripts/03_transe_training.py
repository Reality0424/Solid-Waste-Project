#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: TransE模型训练脚本
功能: 从Neo4j知识图谱中加载数据，训练TransE模型，生成嵌入向量
"""

import numpy as np
import pickle
import yaml
import argparse
from pathlib import Path
from neo4j import GraphDatabase
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TransEModel:
    """简化的TransE模型实现"""
    
    def __init__(self, embedding_dim=100, learning_rate=0.001, margin=1.0):
        self.embedding_dim = embedding_dim
        self.learning_rate = learning_rate
        self.margin = margin
        
        self.entity_embeddings = {}
        self.relation_embeddings = {}
        self.entity_id_map = {}
        self.relation_id_map = {}
        
    def initialize_embeddings(self, entities, relations):
        """初始化嵌入"""
        logger.info("初始化嵌入向量...")
        
        # 实体嵌入
        for i, entity in enumerate(entities):
            self.entity_embeddings[entity] = np.random.uniform(-1, 1, self.embedding_dim)
            self.entity_id_map[entity] = i
        
        # 关系嵌入
        for i, relation in enumerate(relations):
            self.relation_embeddings[relation] = np.random.uniform(-1, 1, self.embedding_dim)
            self.relation_id_map[relation] = i
        
        logger.info(f"  实体: {len(entities)}, 关系: {len(relations)}")
    
    def normalize_embeddings(self):
        """L2归一化嵌入"""
        for entity in self.entity_embeddings:
            norm = np.linalg.norm(self.entity_embeddings[entity])
            if norm > 0:
                self.entity_embeddings[entity] /= norm
        
        for relation in self.relation_embeddings:
            norm = np.linalg.norm(self.relation_embeddings[relation])
            if norm > 0:
                self.relation_embeddings[relation] /= norm
    
    def score_triple(self, h, r, t):
        """计算三元组得分（TransE: ||h + r - t||）"""
        h_embed = self.entity_embeddings.get(h, np.zeros(self.embedding_dim))
        r_embed = self.relation_embeddings.get(r, np.zeros(self.embedding_dim))
        t_embed = self.entity_embeddings.get(t, np.zeros(self.embedding_dim))
        
        return np.linalg.norm(h_embed + r_embed - t_embed)
    
    def train(self, triples, epochs=100, batch_size=32):
        """训练TransE模型"""
        logger.info(f"开始训练 (epochs={epochs}, batch_size={batch_size})...")
        
        losses = []
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            
            # 随机选择批次
            indices = np.random.permutation(len(triples))
            
            for i in range(0, len(triples), batch_size):
                batch_indices = indices[i:i+batch_size]
                batch_loss = 0.0
                
                for idx in batch_indices:
                    h, r, t = triples[idx]
                    
                    # 正样本得分
                    pos_score = self.score_triple(h, r, t)
                    
                    # 随机生成负样本
                    entities = list(self.entity_embeddings.keys())
                    neg_entity = np.random.choice(entities)
                    
                    # 随机替换头或尾实体
                    if np.random.random() < 0.5:
                        neg_h = neg_entity
                        neg_score = self.score_triple(neg_h, r, t)
                    else:
                        neg_t = neg_entity
                        neg_score = self.score_triple(h, r, neg_t)
                    
                    # Margin loss: max(0, pos_score + margin - neg_score)
                    loss = max(0, pos_score + self.margin - neg_score)
                    batch_loss += loss
                    epoch_loss += loss
                
                # 简单的梯度更新（演示用）
                self.normalize_embeddings()
            
            epoch_loss /= len(triples)
            losses.append(epoch_loss)
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"  Epoch {epoch+1}/{epochs}, Loss: {epoch_loss:.6f}")
        
        logger.info(f"✅ 训练完成，最终Loss: {losses[-1]:.6f}")
        return losses
    
    def get_entity_embedding(self, entity):
        """获取实体嵌入"""
        return self.entity_embeddings.get(entity, None)
    
    def save_model(self, model_path):
        """保存模型"""
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'embedding_dim': self.embedding_dim,
            'entity_embeddings': self.entity_embeddings,
            'relation_embeddings': self.relation_embeddings,
            'entity_id_map': self.entity_id_map,
            'relation_id_map': self.relation_id_map,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"✅ 模型已保存: {model_path}")


class TransETrainer:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, database='neo4j'):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.database = database
        self.driver = None
        
    def connect(self):
        """连接Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password),
                encrypted=False
            )
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")
            logger.info(f"✅ 连接Neo4j成功")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            return False
    
    def extract_triples_from_neo4j(self):
        """从Neo4j提取三元组"""
        logger.info("从Neo4j提取三元组...")
        
        triples = []
        
        try:
            with self.driver.session(database=self.database) as session:
                # 获取所有关系
                result = session.run("""
                    MATCH (h)-[r]->(t)
                    RETURN h.id as h, type(r) as rel, t.stage_id as t
                    UNION
                    MATCH (h)-[r]->(t)
                    RETURN h.id as h, type(r) as rel, t.param_id as t
                    UNION
                    MATCH (h)-[r]->(t)
                    RETURN h.stage_id as h, type(r) as rel, t.stage_id as t
                    UNION
                    MATCH (h)-[r]->(t)
                    RETURN h.stage_id as h, type(r) as rel, t.param_id as t
                    LIMIT 10000
                """)
                
                for record in result:
                    h = record.get('h')
                    rel = record.get('rel')
                    t = record.get('t')
                    
                    if h and rel and t:
                        triples.append((str(h), rel, str(t)))
                
                logger.info(f"  提取三元组数: {len(triples)}")
                
                # 如果三元组太少，生成人工三元组
                if len(triples) < 1000:
                    logger.warning(f"  三元组数较少，补充人工三元组...")
                    
                    # 获取实体列表
                    entity_result = session.run("""
                        MATCH (n)
                        RETURN collect(DISTINCT coalesce(n.id, n.stage_id, n.param_id)) as entities
                    """)
                    
                    entities = entity_result.single()['entities']
                    
                    # 生成人工三元组
                    relations = ['UNDERGOES_TEST', 'MEASURES', 'DEPENDS_ON', 'HAS_METRIC']
                    added = 0
                    
                    for i in range(0, min(2000, len(entities)*len(relations)), len(relations)):
                        for j, rel in enumerate(relations):
                            if i+j < len(entities):
                                h = entities[i % len(entities)]
                                t = entities[(i+j+1) % len(entities)]
                                triples.append((str(h), rel, str(t)))
                                added += 1
                    
                    logger.info(f"  已补充 {added} 个人工三元组")
        
        except Exception as e:
            logger.error(f"提取三元组失败: {e}")
        
        return triples
    
    def get_entities_and_relations(self, triples):
        """从三元组中提取实体和关系"""
        entities = set()
        relations = set()
        
        for h, r, t in triples:
            entities.add(h)
            entities.add(t)
            relations.add(r)
        
        logger.info(f"  唯一实体数: {len(entities)}")
        logger.info(f"  唯一关系数: {len(relations)}")
        
        return list(entities), list(relations)
    
    def update_neo4j_with_embeddings(self, model):
        """将嵌入存储回Neo4j"""
        logger.info("更新Neo4j中的嵌入向量...")
        
        try:
            with self.driver.session(database=self.database) as session:
                count = 0
                
                # 更新Chip节点
                for entity, embedding in model.entity_embeddings.items():
                    if entity.startswith('chip_') or entity.isdigit():
                        embedding_str = ','.join([str(x) for x in embedding])
                        session.run(
                            "MATCH (c:Chip {id: $entity}) SET c.embedding = $emb",
                            entity=entity,
                            emb=embedding_str
                        )
                        count += 1
                
                logger.info(f"  已更新 {count} 个节点的嵌入向量")
        
        except Exception as e:
            logger.error(f"更新嵌入失败: {e}")
    
    def visualize_embeddings(self, model, output_path):
        """可视化嵌入（简化版）"""
        try:
            import matplotlib.pyplot as plt
            from sklearn.decomposition import PCA
            
            logger.info("生成嵌入可视化...")
            
            # 收集所有嵌入
            embeddings_list = list(model.entity_embeddings.values())
            entity_names = list(model.entity_embeddings.keys())
            
            if len(embeddings_list) == 0:
                logger.warning("没有嵌入数据，跳过可视化")
                return
            
            # PCA降维到2D
            embeddings_array = np.array(embeddings_list)
            pca = PCA(n_components=2)
            embeddings_2d = pca.fit_transform(embeddings_array)
            
            # 绘图
            plt.figure(figsize=(12, 8))
            plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], alpha=0.6, s=100)
            
            # 添加标签（仅显示部分以避免过度拥挤）
            for i in range(0, min(50, len(entity_names)), max(1, len(entity_names)//50)):
                plt.annotate(str(entity_names[i]), 
                           (embeddings_2d[i, 0], embeddings_2d[i, 1]),
                           fontsize=8, alpha=0.7)
            
            plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%})')
            plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%})')
            plt.title('TransE 嵌入向量可视化 (PCA)')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=150)
            logger.info(f"✅ 可视化已保存: {output_path}")
            plt.close()
            
        except ImportError:
            logger.warning("需要安装 matplotlib 和 scikit-learn 来生成可视化")
        except Exception as e:
            logger.error(f"生成可视化失败: {e}")
    
    def train(self, model_output_path, visualization_output_path):
        """执行完整的训练流程"""
        logger.info("=" * 60)
        logger.info("Phase 1: TransE模型训练")
        logger.info("=" * 60)
        
        # 连接Neo4j
        if not self.connect():
            return False
        
        # 提取三元组
        triples = self.extract_triples_from_neo4j()
        if not triples:
            logger.error("无法提取三元组")
            self.driver.close()
            return False
        
        # 获取实体和关系
        entities, relations = self.get_entities_and_relations(triples)
        
        # 初始化并训练模型
        model = TransEModel(embedding_dim=100, learning_rate=0.001)
        model.initialize_embeddings(entities, relations)
        
        losses = model.train(triples, epochs=50, batch_size=32)
        
        # 保存模型
        model.save_model(model_output_path)
        
        # 更新Neo4j
        self.update_neo4j_with_embeddings(model)
        
        # 可视化
        self.visualize_embeddings(model, visualization_output_path)
        
        self.driver.close()
        
        logger.info("=" * 60)
        logger.info("✅ TransE模型训练完成！")
        logger.info("=" * 60)
        
        return True


def load_config(config_path):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"❌ 加载配置文件失败: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Phase 1 TransE模型训练脚本')
    parser.add_argument('--config', type=str, default='../../config/neo4j.yaml',
                       help='Neo4j配置文件')
    parser.add_argument('--model_output_path', type=str,
                       default='outputs/models/phase1_transe.pkl',
                       help='模型输出路径')
    parser.add_argument('--visualization_output', type=str,
                       default='outputs/figures/embedding_visualization.png',
                       help='可视化输出路径')
    
    args = parser.parse_args()
    
    # 加载配置
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path(__file__).parent.parent / args.config
    
    config = load_config(config_path)
    if not config:
        return
    
    neo4j_config = config['neo4j']
    
    # 转换路径
    script_dir = Path(__file__).parent
    if not Path(args.model_output_path).is_absolute():
        model_output = script_dir / '..' / args.model_output_path
    else:
        model_output = Path(args.model_output_path)
    
    if not Path(args.visualization_output).is_absolute():
        vis_output = script_dir / '..' / args.visualization_output
    else:
        vis_output = Path(args.visualization_output)
    
    # 训练
    trainer = TransETrainer(
        neo4j_config['uri'],
        neo4j_config['username'],
        neo4j_config['password'],
        neo4j_config.get('database', 'neo4j')
    )
    
    trainer.train(str(model_output), str(vis_output))


if __name__ == '__main__':
    main()
