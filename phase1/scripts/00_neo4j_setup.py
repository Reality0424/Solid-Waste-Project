#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: Neo4j 初始化脚本
功能: 连接Neo4j、验证连接、创建索引
"""

import sys
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


class Neo4jManager:
    def __init__(self, uri, username, password, database='neo4j'):
        """初始化Neo4j管理器"""
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
        
    def connect(self):
        """连接到Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                encrypted=False
            )
            # 测试连接
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as ping")
                result.single()
            logger.info(f"✅ 成功连接到 Neo4j: {self.uri}")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j 连接失败: {e}")
            return False
    
    def clear_database(self, confirm=False):
        """清除数据库中的所有数据"""
        if not confirm:
            logger.warning("跳过数据库清空操作")
            return
        
        try:
            with self.driver.session(database=self.database) as session:
                session.run("MATCH (n) DETACH DELETE n")
                session.run("DROP INDEX constraint ON (n) IF EXISTS")
            logger.info("✅ 数据库已清空")
        except Exception as e:
            logger.error(f"清空数据库时出错: {e}")
    
    def create_indexes(self):
        """创建索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (n:Chip) ON (n.id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Parameter) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:TestStage) ON (n.stage_name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Metric) ON (n.metric_id)",
        ]
        
        try:
            with self.driver.session(database=self.database) as session:
                for index_query in indexes:
                    session.run(index_query)
            logger.info("✅ 索引创建完成")
            return True
        except Exception as e:
            logger.error(f"❌ 创建索引失败: {e}")
            return False
    
    def get_database_info(self):
        """获取数据库信息"""
        try:
            with self.driver.session(database=self.database) as session:
                # 获取节点数
                node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
                # 获取关系数
                rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
            
            logger.info(f"📊 数据库信息:")
            logger.info(f"   - 节点数: {node_count}")
            logger.info(f"   - 关系数: {rel_count}")
            return {"nodes": node_count, "relationships": rel_count}
        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            return None
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j 连接已关闭")


def load_config(config_path):
    """加载YAML配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"❌ 加载配置文件失败: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Neo4j 初始化脚本')
    parser.add_argument('--config', type=str, default='../../config/neo4j.yaml',
                       help='配置文件路径')
    parser.add_argument('--clear', action='store_true',
                       help='清空数据库（谨慎使用）')
    parser.add_argument('--uri', type=str, default=None,
                       help='Neo4j URI（覆盖配置文件）')
    parser.add_argument('--user', type=str, default=None,
                       help='用户名（覆盖配置文件）')
    parser.add_argument('--password', type=str, default=None,
                       help='密码（覆盖配置文件）')
    
    args = parser.parse_args()
    
    # 加载配置
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path(__file__).parent.parent / args.config
    
    config = load_config(config_path)
    if not config:
        logger.error("无法加载配置文件，请检查路径")
        sys.exit(1)
    
    # 获取Neo4j配置
    neo4j_config = config.get('neo4j', {})
    uri = args.uri or neo4j_config.get('uri')
    username = args.user or neo4j_config.get('username')
    password = args.password or neo4j_config.get('password')
    database = neo4j_config.get('database', 'neo4j')
    
    logger.info("=" * 60)
    logger.info("Phase 1: Neo4j 初始化")
    logger.info("=" * 60)
    
    # 创建管理器
    manager = Neo4jManager(uri, username, password, database)
    
    # 连接
    if not manager.connect():
        sys.exit(1)
    
    # 清空数据库（如果指定）
    if args.clear:
        confirm = input("⚠️  确实要清空数据库吗？(yes/no): ")
        manager.clear_database(confirm == 'yes')
    
    # 创建索引
    manager.create_indexes()
    
    # 获取数据库信息
    manager.get_database_info()
    
    manager.close()
    logger.info("=" * 60)
    logger.info("✅ Neo4j 初始化完成！")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
