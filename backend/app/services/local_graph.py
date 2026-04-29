"""
로컬 그래프 엔진 - ZEP Cloud 대체
NetworkX + SQLite + sentence-transformers 기반
"""

import json
import os
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import networkx as nx
import numpy as np

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('ungdroofish.local_graph')


@dataclass
class NodeData:
    """그래프 노드 데이터"""
    uuid: str
    name: str
    labels: List[str] = field(default_factory=list)
    summary: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class EdgeData:
    """그래프 엣지 데이터"""
    uuid: str
    name: str
    fact: str = ""
    source_node_uuid: str = ""
    target_node_uuid: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class SearchResult:
    """검색 결과"""
    node: Optional[NodeData] = None
    edge: Optional[EdgeData] = None
    score: float = 0.0
    result_type: str = "node"  # "node" or "edge"


class EmbeddingService:
    """sentence-transformers 기반 임베딩 서비스 (싱글톤)"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def _ensure_initialized(self):
        if not self._initialized:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
                self._initialized = True
                logger.info("임베딩 모델 로드 완료: all-MiniLM-L6-v2")
            except Exception as e:
                logger.error(f"임베딩 모델 로드 실패: {e}")
                self._model = None
                self._initialized = True

    def encode(self, texts: List[str]) -> np.ndarray:
        """텍스트 리스트를 임베딩 벡터로 변환"""
        self._ensure_initialized()
        if self._model is None:
            return np.zeros((len(texts), 384))
        return self._model.encode(texts, normalize_embeddings=True)

    def encode_single(self, text: str) -> np.ndarray:
        """단일 텍스트를 임베딩 벡터로 변환"""
        return self.encode([text])[0]


class LocalGraphStore:
    """로컬 그래프 저장소 - ZEP Cloud 대체"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.SQLITE_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._graphs: Dict[str, nx.DiGraph] = {}
        self._ontologies: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._embedding_service = EmbeddingService()
        self._init_db()

    def _init_db(self):
        """SQLite 테이블 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graphs (
                    graph_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT DEFAULT '',
                    ontology_json TEXT DEFAULT '{}',
                    created_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    uuid TEXT PRIMARY KEY,
                    graph_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    labels_json TEXT DEFAULT '[]',
                    summary TEXT DEFAULT '',
                    attributes_json TEXT DEFAULT '{}',
                    embedding BLOB,
                    created_at TEXT,
                    FOREIGN KEY (graph_id) REFERENCES graphs(graph_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    uuid TEXT PRIMARY KEY,
                    graph_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    fact TEXT DEFAULT '',
                    source_node_uuid TEXT,
                    target_node_uuid TEXT,
                    attributes_json TEXT DEFAULT '{}',
                    embedding BLOB,
                    created_at TEXT,
                    FOREIGN KEY (graph_id) REFERENCES graphs(graph_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    uuid TEXT PRIMARY KEY,
                    graph_id TEXT NOT NULL,
                    data_text TEXT,
                    processed INTEGER DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY (graph_id) REFERENCES graphs(graph_id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_graph ON nodes(graph_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_graph ON edges(graph_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_graph ON episodes(graph_id)")
            conn.commit()

    # ==================== 그래프 관리 ====================

    def create_graph(self, name: str, description: str = "") -> str:
        """새 그래프 생성"""
        graph_id = f"graph_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO graphs (graph_id, name, description, created_at) VALUES (?, ?, ?, ?)",
                (graph_id, name, description, now)
            )
            conn.commit()

        with self._lock:
            self._graphs[graph_id] = nx.DiGraph()

        logger.info(f"그래프 생성: {graph_id} ({name})")
        return graph_id

    def delete_graph(self, graph_id: str):
        """그래프 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM edges WHERE graph_id = ?", (graph_id,))
            conn.execute("DELETE FROM nodes WHERE graph_id = ?", (graph_id,))
            conn.execute("DELETE FROM episodes WHERE graph_id = ?", (graph_id,))
            conn.execute("DELETE FROM graphs WHERE graph_id = ?", (graph_id,))
            conn.commit()

        with self._lock:
            self._graphs.pop(graph_id, None)
            self._ontologies.pop(graph_id, None)

        logger.info(f"그래프 삭제: {graph_id}")

    def set_ontology(self, graph_id: str, ontology: Dict):
        """온톨로지 설정"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE graphs SET ontology_json = ? WHERE graph_id = ?",
                (json.dumps(ontology, ensure_ascii=False), graph_id)
            )
            conn.commit()

        with self._lock:
            self._ontologies[graph_id] = ontology

        logger.info(f"온톨로지 설정 완료: {graph_id}")

    def get_ontology(self, graph_id: str) -> Dict:
        """온톨로지 조회"""
        with self._lock:
            if graph_id in self._ontologies:
                return self._ontologies[graph_id]

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT ontology_json FROM graphs WHERE graph_id = ?", (graph_id,)
            ).fetchone()

        if row:
            ontology = json.loads(row[0])
            with self._lock:
                self._ontologies[graph_id] = ontology
            return ontology
        return {}

    # ==================== 노드/엣지 관리 ====================

    def add_node(self, graph_id: str, name: str, labels: List[str] = None,
                 summary: str = "", attributes: Dict = None) -> str:
        """노드 추가"""
        node_uuid = f"node_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        labels = labels or []
        attributes = attributes or {}

        # 임베딩 생성
        embed_text = f"{name}. {summary}" if summary else name
        embedding = self._embedding_service.encode_single(embed_text)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO nodes (uuid, graph_id, name, labels_json, summary,
                   attributes_json, embedding, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (node_uuid, graph_id, name, json.dumps(labels, ensure_ascii=False),
                 summary, json.dumps(attributes, ensure_ascii=False),
                 embedding.tobytes(), now)
            )
            conn.commit()

        # NetworkX 그래프 업데이트
        g = self._get_or_load_graph(graph_id)
        g.add_node(node_uuid, name=name, labels=labels, summary=summary, attributes=attributes)

        return node_uuid

    def add_edge(self, graph_id: str, name: str, source_uuid: str, target_uuid: str,
                 fact: str = "", attributes: Dict = None) -> str:
        """엣지 추가"""
        edge_uuid = f"edge_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        attributes = attributes or {}

        embed_text = f"{name}: {fact}" if fact else name
        embedding = self._embedding_service.encode_single(embed_text)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO edges (uuid, graph_id, name, fact, source_node_uuid,
                   target_node_uuid, attributes_json, embedding, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (edge_uuid, graph_id, name, fact, source_uuid, target_uuid,
                 json.dumps(attributes, ensure_ascii=False), embedding.tobytes(), now)
            )
            conn.commit()

        g = self._get_or_load_graph(graph_id)
        g.add_edge(source_uuid, target_uuid, uuid=edge_uuid, name=name, fact=fact)

        return edge_uuid

    def get_all_nodes(self, graph_id: str, label_filter: str = None) -> List[NodeData]:
        """그래프의 모든 노드 조회"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT uuid, name, labels_json, summary, attributes_json, created_at "
                "FROM nodes WHERE graph_id = ?", (graph_id,)
            ).fetchall()

        nodes = []
        for row in rows:
            labels = json.loads(row[2])
            if label_filter and label_filter not in labels:
                continue
            nodes.append(NodeData(
                uuid=row[0], name=row[1], labels=labels,
                summary=row[3], attributes=json.loads(row[4]), created_at=row[5]
            ))
        return nodes

    def get_all_edges(self, graph_id: str) -> List[EdgeData]:
        """그래프의 모든 엣지 조회"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT uuid, name, fact, source_node_uuid, target_node_uuid, "
                "attributes_json, created_at FROM edges WHERE graph_id = ?", (graph_id,)
            ).fetchall()

        return [EdgeData(
            uuid=r[0], name=r[1], fact=r[2], source_node_uuid=r[3],
            target_node_uuid=r[4], attributes=json.loads(r[5]), created_at=r[6]
        ) for r in rows]

    def get_node(self, graph_id: str, node_uuid: str) -> Optional[NodeData]:
        """단일 노드 조회"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT uuid, name, labels_json, summary, attributes_json, created_at "
                "FROM nodes WHERE graph_id = ? AND uuid = ?", (graph_id, node_uuid)
            ).fetchone()

        if not row:
            return None
        return NodeData(
            uuid=row[0], name=row[1], labels=json.loads(row[2]),
            summary=row[3], attributes=json.loads(row[4]), created_at=row[5]
        )

    def get_node_edges(self, graph_id: str, node_uuid: str) -> List[EdgeData]:
        """특정 노드의 관련 엣지 조회"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT uuid, name, fact, source_node_uuid, target_node_uuid, "
                "attributes_json, created_at FROM edges WHERE graph_id = ? "
                "AND (source_node_uuid = ? OR target_node_uuid = ?)",
                (graph_id, node_uuid, node_uuid)
            ).fetchall()

        return [EdgeData(
            uuid=r[0], name=r[1], fact=r[2], source_node_uuid=r[3],
            target_node_uuid=r[4], attributes=json.loads(r[5]), created_at=r[6]
        ) for r in rows]

    def get_graph_stats(self, graph_id: str) -> Dict:
        """그래프 통계"""
        with sqlite3.connect(self.db_path) as conn:
            node_count = conn.execute(
                "SELECT COUNT(*) FROM nodes WHERE graph_id = ?", (graph_id,)
            ).fetchone()[0]
            edge_count = conn.execute(
                "SELECT COUNT(*) FROM edges WHERE graph_id = ?", (graph_id,)
            ).fetchone()[0]

            # 레이블별 통계
            rows = conn.execute(
                "SELECT labels_json FROM nodes WHERE graph_id = ?", (graph_id,)
            ).fetchall()
            label_counts = {}
            for row in rows:
                for label in json.loads(row[0]):
                    label_counts[label] = label_counts.get(label, 0) + 1

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "entity_types": label_counts
        }

    # ==================== 에피소드 (텍스트 청크) ====================

    def add_episode(self, graph_id: str, text: str) -> str:
        """텍스트 에피소드 추가 (LLM으로 엔티티/관계 추출 예정)"""
        ep_uuid = f"ep_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO episodes (uuid, graph_id, data_text, processed, created_at) "
                "VALUES (?, ?, ?, 0, ?)",
                (ep_uuid, graph_id, text, now)
            )
            conn.commit()

        return ep_uuid

    def mark_episode_processed(self, episode_uuid: str):
        """에피소드 처리 완료 표시"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE episodes SET processed = 1 WHERE uuid = ?", (episode_uuid,)
            )
            conn.commit()

    def get_unprocessed_episodes(self, graph_id: str) -> List[Dict]:
        """미처리 에피소드 조회"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT uuid, data_text FROM episodes WHERE graph_id = ? AND processed = 0",
                (graph_id,)
            ).fetchall()
        return [{"uuid": r[0], "text": r[1]} for r in rows]

    # ==================== 시맨틱 검색 ====================

    def search(self, graph_id: str, query: str, limit: int = 10,
               search_type: str = "all") -> List[SearchResult]:
        """시맨틱 검색 (코사인 유사도)"""
        query_embedding = self._embedding_service.encode_single(query)
        results = []

        with sqlite3.connect(self.db_path) as conn:
            # 노드 검색
            if search_type in ("all", "node"):
                rows = conn.execute(
                    "SELECT uuid, name, labels_json, summary, attributes_json, "
                    "created_at, embedding FROM nodes WHERE graph_id = ?", (graph_id,)
                ).fetchall()

                for row in rows:
                    if row[6]:
                        node_emb = np.frombuffer(row[6], dtype=np.float32)
                        score = float(np.dot(query_embedding, node_emb))
                        results.append(SearchResult(
                            node=NodeData(
                                uuid=row[0], name=row[1], labels=json.loads(row[2]),
                                summary=row[3], attributes=json.loads(row[4]),
                                created_at=row[5]
                            ),
                            score=score, result_type="node"
                        ))

            # 엣지 검색
            if search_type in ("all", "edge"):
                rows = conn.execute(
                    "SELECT uuid, name, fact, source_node_uuid, target_node_uuid, "
                    "attributes_json, created_at, embedding FROM edges WHERE graph_id = ?",
                    (graph_id,)
                ).fetchall()

                for row in rows:
                    if row[7]:
                        edge_emb = np.frombuffer(row[7], dtype=np.float32)
                        score = float(np.dot(query_embedding, edge_emb))
                        results.append(SearchResult(
                            edge=EdgeData(
                                uuid=row[0], name=row[1], fact=row[2],
                                source_node_uuid=row[3], target_node_uuid=row[4],
                                attributes=json.loads(row[5]), created_at=row[6]
                            ),
                            score=score, result_type="edge"
                        ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    # ==================== 내부 헬퍼 ====================

    def _get_or_load_graph(self, graph_id: str) -> nx.DiGraph:
        """NetworkX 그래프 로드 (메모리 캐시)"""
        with self._lock:
            if graph_id in self._graphs:
                return self._graphs[graph_id]

        g = nx.DiGraph()

        # SQLite에서 로드
        nodes = self.get_all_nodes(graph_id)
        edges = self.get_all_edges(graph_id)

        for node in nodes:
            g.add_node(node.uuid, name=node.name, labels=node.labels,
                       summary=node.summary, attributes=node.attributes)

        for edge in edges:
            g.add_edge(edge.source_node_uuid, edge.target_node_uuid,
                       uuid=edge.uuid, name=edge.name, fact=edge.fact)

        with self._lock:
            self._graphs[graph_id] = g

        return g

    def update_node_summary(self, graph_id: str, node_uuid: str, summary: str):
        """노드 요약 업데이트"""
        embed_text = summary
        embedding = self._embedding_service.encode_single(embed_text)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE nodes SET summary = ?, embedding = ? WHERE graph_id = ? AND uuid = ?",
                (summary, embedding.tobytes(), graph_id, node_uuid)
            )
            conn.commit()

    def add_fact_to_edge(self, graph_id: str, source_name: str, target_name: str,
                         relation_name: str, fact: str) -> str:
        """팩트 기반 엣지 추가 (이름으로 노드 매칭)"""
        with sqlite3.connect(self.db_path) as conn:
            src = conn.execute(
                "SELECT uuid FROM nodes WHERE graph_id = ? AND name = ?",
                (graph_id, source_name)
            ).fetchone()
            tgt = conn.execute(
                "SELECT uuid FROM nodes WHERE graph_id = ? AND name = ?",
                (graph_id, target_name)
            ).fetchone()

        source_uuid = src[0] if src else self.add_node(graph_id, source_name, labels=["Entity"])
        target_uuid = tgt[0] if tgt else self.add_node(graph_id, target_name, labels=["Entity"])

        return self.add_edge(graph_id, relation_name, source_uuid, target_uuid, fact=fact)


# ==================== ZepEntityReader 호환 어댑터 ====================

@dataclass
class EntityNode:
    """（ ZepEntityReader  EntityNode）"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    related_edges: List[Dict[str, Any]] = field(default_factory=list)
    related_nodes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes,
            "related_edges": self.related_edges,
            "related_nodes": self.related_nodes,
        }

    def get_entity_type(self) -> Optional[str]:
        for label in self.labels:
            if label not in ("Entity", "Node"):
                return label
        return None


@dataclass
class FilteredEntities:
    """（ ZepEntityReader  FilteredEntities）"""
    entities: List[EntityNode]
    entity_types: set
    total_count: int
    filtered_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "entity_types": list(self.entity_types),
            "total_count": self.total_count,
            "filtered_count": self.filtered_count,
        }


class LocalEntityReader:
    """
    （ ZepEntityReader）
     LocalGraphStore  ZepEntityReader 
    """

    def __init__(self, graph_store: Optional[LocalGraphStore] = None):
        self.store = graph_store or LocalGraphStore()

    def filter_defined_entities(
        self,
        graph_id: str,
        defined_entity_types: Optional[List[str]] = None,
        enrich_with_edges: bool = True
    ) -> FilteredEntities:
        all_nodes = self.store.get_all_nodes(graph_id)
        total_count = len(all_nodes)

        entities: List[EntityNode] = []
        entity_types: set = set()

        for node in all_nodes:
            custom_labels = [l for l in node.labels if l not in ("Entity", "Node")]
            if not custom_labels:
                continue

            if defined_entity_types:
                match = any(
                    cl.lower() in [dt.lower() for dt in defined_entity_types]
                    for cl in custom_labels
                )
                if not match:
                    continue

            entity = EntityNode(
                uuid=node.uuid,
                name=node.name,
                labels=node.labels,
                summary=node.summary,
                attributes=node.attributes,
            )

            if enrich_with_edges:
                edges = self.store.get_node_edges(graph_id, node.uuid)
                entity.related_edges = [
                    {
                        "edge_name": e.name,
                        "fact": e.fact,
                        "direction": "outgoing" if e.source_node_uuid == node.uuid else "incoming",
                        "source_uuid": e.source_node_uuid,
                        "target_uuid": e.target_node_uuid,
                    }
                    for e in edges
                ]

                related_uuids = set()
                for e in edges:
                    other = e.target_node_uuid if e.source_node_uuid == node.uuid else e.source_node_uuid
                    if other and other != node.uuid:
                        related_uuids.add(other)

                for ruuid in related_uuids:
                    rn = self.store.get_node(graph_id, ruuid)
                    if rn:
                        entity.related_nodes.append({
                            "uuid": rn.uuid,
                            "name": rn.name,
                            "labels": rn.labels,
                            "summary": rn.summary,
                        })

            for cl in custom_labels:
                entity_types.add(cl)
            entities.append(entity)

        return FilteredEntities(
            entities=entities,
            entity_types=entity_types,
            total_count=total_count,
            filtered_count=len(entities),
        )

    def get_entity_with_context(self, graph_id: str, entity_uuid: str) -> Optional[EntityNode]:
        node = self.store.get_node(graph_id, entity_uuid)
        if not node:
            return None

        entity = EntityNode(
            uuid=node.uuid,
            name=node.name,
            labels=node.labels,
            summary=node.summary,
            attributes=node.attributes,
        )

        edges = self.store.get_node_edges(graph_id, entity_uuid)
        entity.related_edges = [
            {
                "edge_name": e.name,
                "fact": e.fact,
                "direction": "outgoing" if e.source_node_uuid == entity_uuid else "incoming",
                "source_uuid": e.source_node_uuid,
                "target_uuid": e.target_node_uuid,
            }
            for e in edges
        ]

        related_uuids = set()
        for e in edges:
            other = e.target_node_uuid if e.source_node_uuid == entity_uuid else e.source_node_uuid
            if other and other != entity_uuid:
                related_uuids.add(other)

        for ruuid in related_uuids:
            rn = self.store.get_node(graph_id, ruuid)
            if rn:
                entity.related_nodes.append({
                    "uuid": rn.uuid,
                    "name": rn.name,
                    "labels": rn.labels,
                    "summary": rn.summary,
                })

        return entity

    def get_entities_by_type(
        self,
        graph_id: str,
        entity_type: str,
        enrich_with_edges: bool = True
    ) -> List[EntityNode]:
        result = self.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=[entity_type],
            enrich_with_edges=enrich_with_edges,
        )
        return result.entities