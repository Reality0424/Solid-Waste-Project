#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1: 知识图谱构建脚本
功能: 从清洗数据构建多维关系知识图谱，导入 Neo4j，并导出图谱产物。

实体类型:
  Chip(芯片) / Parameter(指标) / Dimension(维度) / TestStage(测试阶段)
  / FailureMode(失效模式) / ChipModel(型号)

关系类型（多维）:
  OF_MODEL        Chip       -> ChipModel       芯片型号
  UNDERGOES_TEST  Chip       -> TestStage       芯片经历测试阶段
  EXHIBITS        Chip       -> FailureMode     芯片呈现的（失效/正常）状态
  HAS_ABNORMAL    Chip       -> Parameter       芯片在某指标上异常 (|z|>2)
  BELONGS_TO      Parameter  -> Dimension       指标归属维度
  MEASURED_IN     Parameter  -> TestStage       指标在某阶段被测量
  PRECEDES        TestStage  -> TestStage       测试阶段先后顺序
  CORRELATES_WITH Parameter  -> Parameter       指标间相关性 (|pearson|>=阈值, 基础关联挖掘)

产物:
  outputs/graph/entity_definitions.json     实体定义
  outputs/graph/relationship_types.json     关系类型定义
  outputs/graph/knowledge_graph.pkl         序列化图谱 (networkx.DiGraph)
  outputs/graph/neo4j_import_script.cypher  Cypher 导入脚本（备份/复现用）
  outputs/relations/entity_relations.csv    全部三元组 (head, relation, tail)
  outputs/relations/relationship_matrix.csv 关系类型 × (头类型,尾类型) 计数矩阵
"""

import pandas as pd
import numpy as np
import json
import yaml
import argparse
import pickle
from pathlib import Path
import logging

import networkx as nx

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---- 领域知识：维度 / 阶段 / 指标映射 -----------------------------------------
DIMENSIONS = {
    'Physical':      {'stage': 'Appearance',
                      'params': ['pin_flatness_deviation_um', 'solder_pad_oxidation_percent',
                                 'package_scratch_depth_um', 'warpage_um',
                                 'pin_coplanarity_percent', 'package_size_deviation_percent']},
    'Electrical_DC': {'stage': 'DC_Electrical',
                      'params': ['vdd_voltage', 'idd_static_ma', 'idd_dynamic_ma', 'voh_voltage',
                                 'vol_voltage', 'vih_voltage', 'vil_voltage',
                                 'iil_leakage_ua', 'iol_leakage_ua']},
    'Electrical_AC': {'stage': 'AC_Electrical',
                      'params': ['setup_time_ns', 'hold_time_ns', 'propagation_delay_ns',
                                 'rise_time_ns', 'fall_time_ns', 'fmax_mhz']},
    'Reliability':   {'stage': 'Aging',
                      'params': ['aging_temperature_c', 'aging_voltage_v',
                                 'aging_frequency_mhz', 'aging_duration_hours']},
}
TEST_SEQUENCE = ['Appearance', 'DC_Electrical', 'AC_Electrical', 'Functional', 'Aging']
STAGE_DESC = {
    'Appearance': '外观/物理检测', 'DC_Electrical': 'DC电气测试', 'AC_Electrical': 'AC电气/时序测试',
    'Functional': '功能测试', 'Aging': '老化/可靠性测试',
}

# 节点 key 约定（全图唯一，便于 TransE 统一抽取三元组）
def k_chip(cid):  return str(cid)
def k_param(p):   return f"PARAM::{p}"
def k_dim(d):     return f"DIM::{d}"
def k_stage(s):   return f"TS::{s}"
def k_fail(m):    return f"FM::{m}"
def k_model(m):   return f"MODEL::{m}"


class GraphBuilder:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, database='neo4j',
                 corr_threshold=0.5, abnormal_z=2.0):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.database = database
        self.corr_threshold = corr_threshold
        self.abnormal_z = abnormal_z
        self.driver = None

        # nodes: key -> {'label':..., 'props':{...}}
        self.nodes = {}
        # edges: list of (head_key, rel_type, tail_key, props)
        self.edges = []
        self.entity_defs = {}
        self.rel_defs = {}

    # ---- Neo4j ---------------------------------------------------------------
    def connect(self):
        from neo4j import GraphDatabase
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password), encrypted=False)
            with self.driver.session(database=self.database) as s:
                s.run("RETURN 1").single()
            logger.info(f"✅ 连接 Neo4j 成功: {self.neo4j_uri}")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j 连接失败: {e}")
            return False

    # ---- 实体 ---------------------------------------------------------------
    def _add_node(self, key, label, **props):
        self.nodes[key] = {'label': label, 'props': {'key': key, **props}}

    def define_entities(self, df):
        logger.info("定义实体...")
        avail_params = []

        # ChipModel
        models = sorted(df['chip_model'].dropna().unique()) if 'chip_model' in df else []
        for m in models:
            self._add_node(k_model(m), 'ChipModel', name=str(m))

        # FailureMode
        modes = sorted(df['failure_mode'].dropna().unique()) if 'failure_mode' in df else ['normal']
        for m in modes:
            self._add_node(k_fail(m), 'FailureMode', name=str(m))

        # Dimension + TestStage + Parameter
        for stage in TEST_SEQUENCE:
            self._add_node(k_stage(stage), 'TestStage', name=stage, description=STAGE_DESC.get(stage, ''))
        for dim, spec in DIMENSIONS.items():
            self._add_node(k_dim(dim), 'Dimension', name=dim, test_stage=spec['stage'])
            for p in spec['params']:
                if p in df.columns:
                    self._add_node(k_param(p), 'Parameter', name=p, dimension=dim,
                                   test_stage=spec['stage'], data_type='numeric')
                    avail_params.append(p)

        # Chip
        for _, row in df.iterrows():
            props = {'model': str(row.get('chip_model', 'Unknown')),
                     'failure_mode': str(row.get('failure_mode', 'normal')),
                     'failure_status': int(row.get('failure_status', 0))}
            self._add_node(k_chip(row['chip_id']), 'Chip', **props)

        # 统计 entity_definitions
        from collections import Counter
        label_counts = Counter(n['label'] for n in self.nodes.values())
        attr_map = {
            'Chip': ['key', 'model', 'failure_mode', 'failure_status', 'embedding'],
            'Parameter': ['key', 'name', 'dimension', 'test_stage', 'data_type'],
            'Dimension': ['key', 'name', 'test_stage'],
            'TestStage': ['key', 'name', 'description'],
            'FailureMode': ['key', 'name'],
            'ChipModel': ['key', 'name'],
        }
        for label, cnt in label_counts.items():
            self.entity_defs[label] = {'count': int(cnt), 'attributes': attr_map.get(label, [])}

        logger.info(f"   实体总数: {len(self.nodes)}")
        for label, cnt in label_counts.items():
            logger.info(f"   - {label}: {cnt}")
        return avail_params

    # ---- 关系 ---------------------------------------------------------------
    def define_relationships(self, df, avail_params):
        logger.info("构建关系...")

        # 结构关系: Parameter -> Dimension / TestStage
        for dim, spec in DIMENSIONS.items():
            for p in spec['params']:
                if p in avail_params:
                    self.edges.append((k_param(p), 'BELONGS_TO', k_dim(dim), {}))
                    self.edges.append((k_param(p), 'MEASURED_IN', k_stage(spec['stage']), {}))

        # TestStage -> TestStage 顺序
        for i in range(len(TEST_SEQUENCE) - 1):
            self.edges.append((k_stage(TEST_SEQUENCE[i]), 'PRECEDES',
                               k_stage(TEST_SEQUENCE[i + 1]), {'sequence': i + 1}))

        # Chip -> ChipModel / FailureMode / TestStage
        for _, row in df.iterrows():
            cid = k_chip(row['chip_id'])
            if 'chip_model' in df:
                self.edges.append((cid, 'OF_MODEL', k_model(row['chip_model']), {}))
            mode = str(row.get('failure_mode', 'normal'))
            self.edges.append((cid, 'EXHIBITS', k_fail(mode), {}))
            for stage in TEST_SEQUENCE:
                self.edges.append((cid, 'UNDERGOES_TEST', k_stage(stage), {}))

        # Chip -> Parameter (HAS_ABNORMAL): |z| > 阈值
        abnormal_count = 0
        for p in avail_params:
            vals = df[p].astype(float)
            mu, sigma = vals.mean(), vals.std()
            if sigma > 0:
                z = (vals - mu) / sigma
                mask = z.abs() > self.abnormal_z
                for cid, zv in zip(df.loc[mask, 'chip_id'], z[mask]):
                    self.edges.append((k_chip(cid), 'HAS_ABNORMAL', k_param(p),
                                       {'z_score': round(float(zv), 3)}))
                    abnormal_count += 1
        logger.info(f"   HAS_ABNORMAL 边: {abnormal_count}")

        # Parameter <-> Parameter (CORRELATES_WITH): 基础关联挖掘
        corr_count = 0
        if len(avail_params) >= 2:
            corr = df[avail_params].astype(float).corr(method='pearson')
            for i in range(len(avail_params)):
                for j in range(i + 1, len(avail_params)):
                    r = corr.iloc[i, j]
                    if pd.notna(r) and abs(r) >= self.corr_threshold:
                        self.edges.append((k_param(avail_params[i]), 'CORRELATES_WITH',
                                           k_param(avail_params[j]), {'weight': round(float(r), 4)}))
                        corr_count += 1
        logger.info(f"   CORRELATES_WITH 边: {corr_count}")

        # rel_defs
        self.rel_defs = {
            'OF_MODEL':        {'from': 'Chip', 'to': 'ChipModel', 'description': '芯片型号'},
            'UNDERGOES_TEST':  {'from': 'Chip', 'to': 'TestStage', 'description': '芯片经历测试阶段'},
            'EXHIBITS':        {'from': 'Chip', 'to': 'FailureMode', 'description': '芯片呈现的状态/失效模式'},
            'HAS_ABNORMAL':    {'from': 'Chip', 'to': 'Parameter', 'description': '芯片在指标上异常', 'properties': ['z_score']},
            'BELONGS_TO':      {'from': 'Parameter', 'to': 'Dimension', 'description': '指标归属维度'},
            'MEASURED_IN':     {'from': 'Parameter', 'to': 'TestStage', 'description': '指标测量阶段'},
            'PRECEDES':        {'from': 'TestStage', 'to': 'TestStage', 'description': '测试阶段顺序', 'properties': ['sequence']},
            'CORRELATES_WITH': {'from': 'Parameter', 'to': 'Parameter', 'description': '指标间相关性', 'properties': ['weight']},
        }
        from collections import Counter
        rel_counts = Counter(e[1] for e in self.edges)
        logger.info(f"   关系总数: {len(self.edges)}")
        for rt, c in rel_counts.items():
            logger.info(f"   - {rt}: {c}")

    # ---- 写入 Neo4j ----------------------------------------------------------
    def write_to_neo4j(self, clear=True):
        logger.info("写入 Neo4j...")
        with self.driver.session(database=self.database) as s:
            if clear:
                s.run("MATCH (n) DETACH DELETE n")
            # 每个 label 一个 key 唯一约束
            for label in self.entity_defs:
                s.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.key IS UNIQUE")

            # 批量建点
            by_label = {}
            for key, node in self.nodes.items():
                by_label.setdefault(node['label'], []).append(node['props'])
            for label, rows in by_label.items():
                for i in range(0, len(rows), 1000):
                    s.run(f"UNWIND $rows AS r CREATE (n:{label}) SET n = r",
                          rows=rows[i:i + 1000])
            logger.info(f"   ✓ 节点已写入: {len(self.nodes)}")

            # 批量建边（按关系类型分组）
            by_rel = {}
            for h, rt, t, props in self.edges:
                by_rel.setdefault(rt, []).append({'h': h, 't': t, 'props': props})
            for rt, rows in by_rel.items():
                for i in range(0, len(rows), 2000):
                    s.run(
                        "UNWIND $rows AS row "
                        "MATCH (h {key: row.h}) MATCH (t {key: row.t}) "
                        f"CREATE (h)-[rel:{rt}]->(t) SET rel = row.props",
                        rows=rows[i:i + 2000])
            logger.info(f"   ✓ 关系已写入: {len(self.edges)}")

    def get_graph_statistics(self):
        with self.driver.session(database=self.database) as s:
            n = s.run("MATCH (n) RETURN count(n) AS c").single()['c']
            r = s.run("MATCH ()-[x]->() RETURN count(x) AS c").single()['c']
        logger.info(f"📊 Neo4j 图谱统计: 节点 {n}, 关系 {r}")
        return {'nodes': n, 'relationships': r}

    # ---- 产物导出 ------------------------------------------------------------
    def export_artifacts(self, graph_dir, relations_dir):
        graph_dir = Path(graph_dir); graph_dir.mkdir(parents=True, exist_ok=True)
        relations_dir = Path(relations_dir); relations_dir.mkdir(parents=True, exist_ok=True)

        # entity_definitions.json / relationship_types.json
        with open(graph_dir / 'entity_definitions.json', 'w', encoding='utf-8') as f:
            json.dump(self.entity_defs, f, ensure_ascii=False, indent=2)
        with open(graph_dir / 'relationship_types.json', 'w', encoding='utf-8') as f:
            json.dump(self.rel_defs, f, ensure_ascii=False, indent=2)

        # entity_relations.csv (所有三元组)
        triples = pd.DataFrame([(h, rt, t) for h, rt, t, _ in self.edges],
                               columns=['head', 'relation', 'tail'])
        triples.to_csv(relations_dir / 'entity_relations.csv', index=False)

        # relationship_matrix.csv: 关系类型 × (头类型, 尾类型) 计数
        label_of = {key: n['label'] for key, n in self.nodes.items()}
        rows = []
        for h, rt, t, _ in self.edges:
            rows.append((rt, label_of.get(h, '?'), label_of.get(t, '?')))
        mat = pd.DataFrame(rows, columns=['relation', 'from_type', 'to_type'])
        mat = mat.value_counts().reset_index(name='count')
        mat.to_csv(relations_dir / 'relationship_matrix.csv', index=False)

        # knowledge_graph.pkl (networkx)
        G = nx.DiGraph()
        for key, node in self.nodes.items():
            G.add_node(key, **node['props'], label=node['label'])
        for h, rt, t, props in self.edges:
            G.add_edge(h, t, relation=rt, **props)
        with open(graph_dir / 'knowledge_graph.pkl', 'wb') as f:
            pickle.dump(G, f)

        # neo4j_import_script.cypher (复现用，紧凑版)
        self._write_cypher(graph_dir / 'neo4j_import_script.cypher')

        logger.info(f"✅ 产物已导出:")
        logger.info(f"   - {graph_dir / 'entity_definitions.json'}")
        logger.info(f"   - {graph_dir / 'relationship_types.json'}")
        logger.info(f"   - {graph_dir / 'knowledge_graph.pkl'}")
        logger.info(f"   - {graph_dir / 'neo4j_import_script.cypher'}")
        logger.info(f"   - {relations_dir / 'entity_relations.csv'}")
        logger.info(f"   - {relations_dir / 'relationship_matrix.csv'}")

    def _write_cypher(self, path):
        lines = ["// Phase 1 知识图谱 Cypher 导入脚本（自动生成）",
                 "MATCH (n) DETACH DELETE n;"]
        for label in self.entity_defs:
            lines.append(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.key IS UNIQUE;")
        # 节点（仅写 key + name 以保持脚本紧凑；完整属性以 pkl/CSV 为准）
        for key, node in self.nodes.items():
            name = str(node['props'].get('name', node['props'].get('key', ''))).replace("'", "\\'")
            lines.append(f"CREATE (:{node['label']} {{key:'{key}', name:'{name}'}});")
        for h, rt, t, _ in self.edges:
            lines.append(f"MATCH (h {{key:'{h}'}}),(t {{key:'{t}'}}) CREATE (h)-[:{rt}]->(t);")
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    # ---- 主流程 --------------------------------------------------------------
    def build(self, cleaned_data_path, graph_dir, relations_dir, use_neo4j=True):
        logger.info("=" * 60)
        logger.info("Phase 1: 知识图谱构建")
        logger.info("=" * 60)
        try:
            df = pd.read_csv(cleaned_data_path)
            logger.info(f"✅ 数据加载: {len(df)} 行, {len(df.columns)} 列")
        except Exception as e:
            logger.error(f"❌ 数据加载失败: {e}")
            return False

        avail_params = self.define_entities(df)
        self.define_relationships(df, avail_params)

        if use_neo4j:
            if not self.connect():
                return False
            self.write_to_neo4j(clear=True)
            self.get_graph_statistics()
            self.driver.close()
        else:
            logger.warning("⚠️ 跳过 Neo4j 写入 (--no-neo4j)")

        self.export_artifacts(graph_dir, relations_dir)

        logger.info("=" * 60)
        logger.info(f"✅ 知识图谱构建完成！实体 {len(self.nodes)}, 关系 {len(self.edges)}")
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
    parser = argparse.ArgumentParser(description='Phase 1 知识图谱构建脚本')
    parser.add_argument('--config', type=str, default='../../config/neo4j.yaml')
    parser.add_argument('--input_path', type=str, default='outputs/data/cleaned_data.csv')
    parser.add_argument('--output_path', type=str, default='outputs/graph/')
    parser.add_argument('--relations_output', type=str, default='outputs/relations/')
    parser.add_argument('--corr_threshold', type=float, default=0.5)
    parser.add_argument('--abnormal_z', type=float, default=2.0)
    parser.add_argument('--no-neo4j', dest='use_neo4j', action='store_false',
                        help='只导出产物，不写 Neo4j')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    config_path = _resolve(args.config, script_dir)  # '../../config/neo4j.yaml' -> Solid-Waste-Project/config
    neo4j_config = load_config(config_path)['neo4j']

    input_path = _resolve(args.input_path, script_dir, up=True)
    graph_dir = _resolve(args.output_path, script_dir, up=True)
    relations_dir = _resolve(args.relations_output, script_dir, up=True)

    builder = GraphBuilder(
        neo4j_config['uri'], neo4j_config['username'], neo4j_config['password'],
        neo4j_config.get('database', 'neo4j'),
        corr_threshold=args.corr_threshold, abnormal_z=args.abnormal_z)
    builder.build(str(input_path), str(graph_dir), str(relations_dir), use_neo4j=args.use_neo4j)


if __name__ == '__main__':
    main()
