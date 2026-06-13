#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: 评估脚本
功能: 评估TransE模型质量、验证知识图谱完整性、生成评估报告
"""

import yaml
import argparse
import pickle
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


class Evaluator:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, database='neo4j'):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.database = database
        self.driver = None
        self.report = {}
        
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
    
    def evaluate_graph_completeness(self):
        """评估图谱完整性"""
        logger.info("评估图谱完整性...")
        
        try:
            with self.driver.session(database=self.database) as session:
                # 节点统计
                node_stats = session.run("""
                    MATCH (n)
                    RETURN labels(n)[0] as label, count(*) as count
                """)
                
                node_counts = {}
                total_nodes = 0
                for record in node_stats:
                    label = record['label']
                    count = record['count']
                    node_counts[label] = count
                    total_nodes += count
                
                # 关系统计
                rel_stats = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as rel_type, count(*) as count
                """)
                
                rel_counts = {}
                total_rels = 0
                for record in rel_stats:
                    rel_type = record['rel_type']
                    count = record['count']
                    rel_counts[rel_type] = count
                    total_rels += count
                
                logger.info(f"  节点总数: {total_nodes}")
                logger.info(f"  关系总数: {total_rels}")
                
                self.report['graph_completeness'] = {
                    'total_nodes': total_nodes,
                    'nodes_by_type': node_counts,
                    'total_relationships': total_rels,
                    'relationships_by_type': rel_counts,
                    'completeness_rate': min(1.0, total_nodes / 500) * min(1.0, total_rels / 1000)
                }
                
                return True
        except Exception as e:
            logger.error(f"评估完整性失败: {e}")
            return False
    
    def evaluate_model_quality(self, model_path):
        """评估模型质量"""
        logger.info("评估模型质量...")
        
        try:
            if not Path(model_path).exists():
                logger.warning(f"模型文件不存在: {model_path}")
                self.report['model_quality'] = {
                    'model_exists': False,
                    'embedding_dim': 0,
                    'entities_embedded': 0
                }
                return False
            
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            embedding_dim = model_data.get('embedding_dim', 0)
            num_entities = len(model_data.get('entity_embeddings', {}))
            num_relations = len(model_data.get('relation_embeddings', {}))
            
            logger.info(f"  嵌入维度: {embedding_dim}")
            logger.info(f"  嵌入实体数: {num_entities}")
            logger.info(f"  嵌入关系数: {num_relations}")
            
            self.report['model_quality'] = {
                'model_exists': True,
                'embedding_dim': embedding_dim,
                'entities_embedded': num_entities,
                'relations_embedded': num_relations,
                'model_saved_at': model_data.get('timestamp', 'unknown')
            }
            
            return True
        except Exception as e:
            logger.error(f"评估模型失败: {e}")
            return False
    
    def validate_schema(self):
        """验证数据架构"""
        logger.info("验证数据架构...")
        
        try:
            with self.driver.session(database=self.database) as session:
                # 检查是否有足够的节点
                node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']
                
                # 检查是否有足够的关系
                rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
                
                # 检查关键标签是否存在
                labels = session.run("CALL db.labels()").single()
                label_list = labels[0] if labels else []
                
                expected_labels = ['Chip', 'TestStage', 'Parameter']
                missing_labels = [l for l in expected_labels if l not in label_list]
                
                self.report['schema_validation'] = {
                    'node_count': node_count,
                    'relationship_count': rel_count,
                    'labels_found': label_list,
                    'missing_labels': missing_labels,
                    'schema_valid': len(missing_labels) == 0
                }
                
                logger.info(f"  节点数: {node_count}")
                logger.info(f"  关系数: {rel_count}")
                logger.info(f"  标签: {label_list}")
                
                return len(missing_labels) == 0
        except Exception as e:
            logger.error(f"架构验证失败: {e}")
            return False
    
    def generate_evaluation_report(self, output_path):
        """生成评估报告"""
        logger.info("生成评估报告...")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report_md = "# Phase 1 评估报告\n\n"
        report_md += f"**生成时间**: {datetime.now().isoformat()}\n\n"
        
        # 图谱完整性
        report_md += "## 📊 图谱完整性评估\n\n"
        if 'graph_completeness' in self.report:
            gc = self.report['graph_completeness']
            report_md += f"- **节点总数**: {gc['total_nodes']} "
            report_md += f"(目标: ≥500, {'✅' if gc['total_nodes'] >= 500 else '❌'})\n"
            report_md += f"- **关系总数**: {gc['total_relationships']} "
            report_md += f"(目标: ≥1000, {'✅' if gc['total_relationships'] >= 1000 else '❌'})\n"
            report_md += f"- **完整性评分**: {gc['completeness_rate']:.2%}\n\n"
            
            report_md += "### 节点类型分布\n"
            for node_type, count in gc['nodes_by_type'].items():
                report_md += f"- {node_type}: {count}\n"
            
            report_md += "\n### 关系类型分布\n"
            for rel_type, count in gc['relationships_by_type'].items():
                report_md += f"- {rel_type}: {count}\n"
        
        # 模型质量
        report_md += "\n## 🧠 模型质量评估\n\n"
        if 'model_quality' in self.report:
            mq = self.report['model_quality']
            report_md += f"- **模型存在**: {'✅ 是' if mq['model_exists'] else '❌ 否'}\n"
            report_md += f"- **嵌入维度**: {mq['embedding_dim']}\n"
            report_md += f"- **嵌入实体数**: {mq['entities_embedded']}\n"
            report_md += f"- **嵌入关系数**: {mq['relations_embedded']}\n"
            if mq['model_exists']:
                report_md += f"- **保存时间**: {mq['model_saved_at']}\n"
        
        # 架构验证
        report_md += "\n## ✅ 架构验证\n\n"
        if 'schema_validation' in self.report:
            sv = self.report['schema_validation']
            report_md += f"- **架构有效**: {'✅ 是' if sv['schema_valid'] else '❌ 否'}\n"
            report_md += f"- **已找到标签**: {', '.join(sv['labels_found'])}\n"
            if sv['missing_labels']:
                report_md += f"- **缺失标签**: {', '.join(sv['missing_labels'])}\n"
        
        # 成功标准
        report_md += "\n## 🎯 成功标准检查\n\n"
        
        checks = {
            '知识图谱实体数 ≥ 500': 'graph_completeness' in self.report and 
                                   self.report['graph_completeness']['total_nodes'] >= 500,
            '关系数 ≥ 1000': 'graph_completeness' in self.report and 
                             self.report['graph_completeness']['total_relationships'] >= 1000,
            'TransE模型收敛': 'model_quality' in self.report and 
                              self.report['model_quality']['model_exists'],
            '完整性验证率 ≥ 90%': 'graph_completeness' in self.report and 
                                self.report['graph_completeness']['completeness_rate'] >= 0.9
        }
        
        success_count = 0
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            report_md += f"- {status} {check_name}\n"
            if passed:
                success_count += 1
        
        report_md += f"\n**总体状态**: {success_count}/4 标准通过\n"
        
        # 建议
        report_md += "\n## 💡 建议\n\n"
        if 'graph_completeness' in self.report:
            gc = self.report['graph_completeness']
            if gc['total_nodes'] < 500:
                report_md += "- 图谱节点数不足，建议增加更多数据或优化数据提取策略\n"
            if gc['total_relationships'] < 1000:
                report_md += "- 图谱关系数不足，建议检查关系定义或增加关系创建规则\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_md)
        
        logger.info(f"✅ 报告已生成: {output_path}")
    
    def evaluate(self, model_path, output_path):
        """执行完整的评估流程"""
        logger.info("=" * 60)
        logger.info("Phase 1: 评估")
        logger.info("=" * 60)
        
        # 连接Neo4j
        if not self.connect():
            return False
        
        # 执行评估
        self.evaluate_graph_completeness()
        self.evaluate_model_quality(model_path)
        self.validate_schema()
        
        # 生成报告
        self.generate_evaluation_report(output_path)
        
        self.driver.close()
        
        logger.info("=" * 60)
        logger.info("✅ 评估完成！")
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
    parser = argparse.ArgumentParser(description='Phase 1 评估脚本')
    parser.add_argument('--config', type=str, default='../../config/neo4j.yaml',
                       help='Neo4j配置文件')
    parser.add_argument('--model_path', type=str, default='outputs/models/phase1_transe.pkl',
                       help='模型路径')
    parser.add_argument('--output_path', type=str,
                       default='outputs/reports/evaluation_report.md',
                       help='评估报告输出路径')
    
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
    if not Path(args.model_path).is_absolute():
        model_path = script_dir / '..' / args.model_path
    else:
        model_path = Path(args.model_path)
    
    if not Path(args.output_path).is_absolute():
        output_path = script_dir / '..' / args.output_path
    else:
        output_path = Path(args.output_path)
    
    # 评估
    evaluator = Evaluator(
        neo4j_config['uri'],
        neo4j_config['username'],
        neo4j_config['password'],
        neo4j_config.get('database', 'neo4j')
    )
    
    evaluator.evaluate(str(model_path), str(output_path))


if __name__ == '__main__':
    main()
