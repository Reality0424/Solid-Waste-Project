#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: 知识图谱构建脚本
功能: 从清洗数据构建知识图谱，导入Neo4j
"""

import pandas as pd
import json
import yaml
import argparse
from pathlib import Path
from neo4j import GraphDatabase
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GraphBuilder:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, database='neo4j'):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.database = database
        self.driver = None
        self.entities = {}
        self.relationships = {}
        
    def connect(self):
        """连接到Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password),
                encrypted=False
            )
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1 as ping")
            logger.info(f"✅ 连接到Neo4j成功: {self.neo4j_uri}")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            return False
    
    def define_entities(self, cleaned_data):
        """从数据定义实体"""
        logger.info("定义实体...")
        
        # 芯片实体
        chip_ids = cleaned_data['chip_id'].unique()
        self.entities['Chip'] = {
            'ids': list(chip_ids),
            'count': len(chip_ids),
            'attributes': ['id', 'model', 'batch_id', 'manufacturing_date']
        }
        
        # 测试阶段实体
        test_stages = [
            {'name': 'Appearance', 'stage_id': 'TS_001', 'description': '外观检测'},
            {'name': 'DC_Electrical', 'stage_id': 'TS_002', 'description': 'DC电气测试'},
            {'name': 'AC_Electrical', 'stage_id': 'TS_003', 'description': 'AC电气测试'},
            {'name': 'Functional', 'stage_id': 'TS_004', 'description': '功能测试'},
            {'name': 'Aging', 'stage_id': 'TS_005', 'description': '老化测试'}
        ]
        self.entities['TestStage'] = {
            'data': test_stages,
            'count': len(test_stages),
            'attributes': ['stage_id', 'stage_name', 'description']
        }
        
        # 参数实体
        numeric_cols = cleaned_data.select_dtypes(include=['number']).columns
        parameters = []
        for i, col in enumerate(numeric_cols):
            parameters.append({
                'param_id': f'PM_{i:03d}',
                'param_name': col,
                'data_type': 'numeric'
            })
        self.entities['Parameter'] = {
            'data': parameters,
            'count': len(parameters),
            'attributes': ['param_id', 'param_name', 'data_type']
        }
        
        logger.info(f"   定义实体:")
        for entity_type, entity_info in self.entities.items():
            count = entity_info.get('count', 0)
            logger.info(f"   - {entity_type}: {count}")
        
        return True
    
    def define_relationships(self):
        """定义关系类型"""
        logger.info("定义关系类型...")
        
        self.relationships = {
            'UNDERGOES_TEST': {
                'from': 'Chip',
                'to': 'TestStage',
                'description': '芯片进行测试',
                'properties': ['test_date', 'result']
            },
            'MEASURES': {
                'from': 'TestStage',
                'to': 'Parameter',
                'description': '测试阶段测量参数',
                'properties': ['measured_value', 'unit', 'tolerance']
            },
            'DEPENDS_ON': {
                'from': 'TestStage',
                'to': 'TestStage',
                'description': '测试阶段依赖关系',
                'properties': ['sequence', 'condition']
            },
            'HAS_METRIC': {
                'from': 'Chip',
                'to': 'Parameter',
                'description': '芯片具有参数',
                'properties': ['value', 'timestamp']
            }
        }
        
        logger.info(f"   定义关系类型: {len(self.relationships)}")
        for rel_type in self.relationships.keys():
            logger.info(f"   - {rel_type}")
        
        return True
    
    def save_entity_definitions(self, output_path):
        """保存实体定义"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        entity_defs = {}
        for entity_type, entity_info in self.entities.items():
            entity_defs[entity_type] = {
                'count': entity_info.get('count', 0),
                'attributes': entity_info.get('attributes', [])
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(entity_defs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 实体定义已保存: {output_path}")
    
    def save_relationship_types(self, output_path):
        """保存关系类型定义"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        rel_defs = {}
        for rel_type, rel_info in self.relationships.items():
            rel_defs[rel_type] = {
                'from': rel_info['from'],
                'to': rel_info['to'],
                'description': rel_info['description'],
                'properties': rel_info['properties']
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rel_defs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 关系类型已保存: {output_path}")
    
    def create_nodes_in_neo4j(self, cleaned_data):
        """在Neo4j中创建节点"""
        logger.info("创建Neo4j节点...")
        
        try:
            with self.driver.session(database=self.database) as session:
                # 创建芯片节点
                logger.info("  创建Chip节点...")
                chip_count = 0
                for chip_id in self.entities['Chip']['ids']:
                    session.run(
                        "CREATE (c:Chip {id: $chip_id}) RETURN c",
                        chip_id=str(chip_id)
                    )
                    chip_count += 1
                logger.info(f"    ✓ {chip_count} 个Chip节点已创建")
                
                # 创建测试阶段节点
                logger.info("  创建TestStage节点...")
                for ts in self.entities['TestStage']['data']:
                    session.run(
                        "CREATE (t:TestStage {stage_id: $stage_id, stage_name: $stage_name, "
                        "description: $desc}) RETURN t",
                        stage_id=ts['stage_id'],
                        stage_name=ts['name'],
                        desc=ts['description']
                    )
                logger.info(f"    ✓ {len(self.entities['TestStage']['data'])} 个TestStage节点已创建")
                
                # 创建参数节点
                logger.info("  创建Parameter节点...")
                param_count = 0
                for param in self.entities['Parameter']['data']:
                    session.run(
                        "CREATE (p:Parameter {param_id: $param_id, name: $name, "
                        "data_type: $dtype}) RETURN p",
                        param_id=param['param_id'],
                        name=param['param_name'],
                        dtype=param['data_type']
                    )
                    param_count += 1
                logger.info(f"    ✓ {param_count} 个Parameter节点已创建")
            
            return True
        except Exception as e:
            logger.error(f"❌ 创建节点时出错: {e}")
            return False
    
    def create_relationships_in_neo4j(self):
        """在Neo4j中创建关系"""
        logger.info("创建Neo4j关系...")
        
        try:
            with self.driver.session(database=self.database) as session:
                # UNDERGOES_TEST: Chip -> TestStage
                logger.info("  创建 UNDERGOES_TEST 关系...")
                session.run("""
                    MATCH (c:Chip), (t:TestStage)
                    WITH c, t
                    CREATE (c)-[r:UNDERGOES_TEST]->(t)
                    RETURN count(r) as count
                """)
                
                # MEASURES: TestStage -> Parameter
                logger.info("  创建 MEASURES 关系...")
                session.run("""
                    MATCH (t:TestStage), (p:Parameter)
                    WITH t, p
                    CREATE (t)-[r:MEASURES]->(p)
                    RETURN count(r) as count
                """)
                
                # DEPENDS_ON: TestStage -> TestStage（测试阶段顺序依赖）
                logger.info("  创建 DEPENDS_ON 关系...")
                session.run("""
                    MATCH (t1:TestStage), (t2:TestStage)
                    WHERE t1.stage_id < t2.stage_id
                    WITH t1, t2
                    CREATE (t1)-[r:DEPENDS_ON]->(t2)
                    RETURN count(r) as count
                """)
                
                logger.info("    ✓ 关系创建完成")
            
            return True
        except Exception as e:
            logger.error(f"❌ 创建关系时出错: {e}")
            return False
    
    def get_graph_statistics(self):
        """获取知识图谱统计"""
        logger.info("获取图谱统计...")
        
        try:
            with self.driver.session(database=self.database) as session:
                node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']
                rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
                
                logger.info(f"📊 图谱统计:")
                logger.info(f"   - 节点数: {node_count}")
                logger.info(f"   - 关系数: {rel_count}")
                
                return {'nodes': node_count, 'relationships': rel_count}
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return None
    
    def build(self, cleaned_data_path, output_path, relations_output_path):
        """执行完整的图谱构建流程"""
        logger.info("=" * 60)
        logger.info("Phase 1: 知识图谱构建")
        logger.info("=" * 60)
        
        # 加载数据
        try:
            cleaned_data = pd.read_csv(cleaned_data_path)
            logger.info(f"✅ 数据加载成功: {len(cleaned_data)} 行")
        except Exception as e:
            logger.error(f"❌ 数据加载失败: {e}")
            return False
        
        # 连接Neo4j
        if not self.connect():
            return False
        
        # 定义实体和关系
        self.define_entities(cleaned_data)
        self.define_relationships()
        
        # 保存定义
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        self.save_entity_definitions(output_path / 'entity_definitions.json')
        self.save_relationship_types(output_path / 'relationship_types.json')
        
        # 创建节点和关系
        self.create_nodes_in_neo4j(cleaned_data)
        self.create_relationships_in_neo4j()
        
        # 获取统计
        stats = self.get_graph_statistics()
        
        self.driver.close()
        
        logger.info("=" * 60)
        logger.info("✅ 知识图谱构建完成！")
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
    parser = argparse.ArgumentParser(description='Phase 1 知识图谱构建脚本')
    parser.add_argument('--config', type=str, default='../../config/neo4j.yaml',
                       help='Neo4j配置文件')
    parser.add_argument('--input_path', type=str, default='outputs/data/cleaned_data.csv',
                       help='清洗数据路径')
    parser.add_argument('--output_path', type=str, default='outputs/graph/',
                       help='输出路径（图定义）')
    parser.add_argument('--relations_output', type=str, default='outputs/relations/',
                       help='输出路径（关系数据）')
    
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
    if not Path(args.input_path).is_absolute():
        input_path = script_dir / '..' / args.input_path
    else:
        input_path = Path(args.input_path)
    
    if not Path(args.output_path).is_absolute():
        output_path = script_dir / '..' / args.output_path
    else:
        output_path = Path(args.output_path)
    
    # 构建图谱
    builder = GraphBuilder(
        neo4j_config['uri'],
        neo4j_config['username'],
        neo4j_config['password'],
        neo4j_config.get('database', 'neo4j')
    )
    
    builder.build(str(input_path), str(output_path), args.relations_output)


if __name__ == '__main__':
    main()
