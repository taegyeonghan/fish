"""
로컬 검색 도구 - ZEP Tools 대체
InsightForge, PanoramaSearch, QuickSearch를 로컬 그래프에서 수행
"""

import json
from typing import Dict, List, Optional

from .local_graph import LocalGraphStore, SearchResult
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger('ungdroofish.local_search')


class LocalSearchTools:
    """로컬 그래프 검색 도구 (report_agent에서 사용)"""

    def __init__(self, graph_id: str, graph_store: Optional[LocalGraphStore] = None,
                 llm_client: Optional[LLMClient] = None):
        self.graph_id = graph_id
        self.graph_store = graph_store or LocalGraphStore()
        self.llm_client = llm_client or LLMClient()

    def insight_forge(self, query: str, limit: int = 10) -> Dict:
        """InsightForge 딥 검색 - 쿼리를 서브 질문으로 분해 후 다차원 검색"""
        # 서브 질문 생성
        sub_queries = self._generate_sub_queries(query)

        all_facts = []
        all_nodes = []
        all_edges = []
        seen_uuids = set()

        for sub_q in sub_queries:
            results = self.graph_store.search(self.graph_id, sub_q, limit=5)
            for r in results:
                if r.result_type == "node" and r.node and r.node.uuid not in seen_uuids:
                    seen_uuids.add(r.node.uuid)
                    all_nodes.append({
                        "name": r.node.name,
                        "labels": r.node.labels,
                        "summary": r.node.summary,
                        "score": r.score
                    })
                    # 관련 엣지도 수집
                    edges = self.graph_store.get_node_edges(self.graph_id, r.node.uuid)
                    for edge in edges:
                        if edge.uuid not in seen_uuids:
                            seen_uuids.add(edge.uuid)
                            all_edges.append({
                                "name": edge.name,
                                "fact": edge.fact,
                                "source": edge.source_node_uuid,
                                "target": edge.target_node_uuid
                            })
                            if edge.fact:
                                all_facts.append(edge.fact)

                elif r.result_type == "edge" and r.edge and r.edge.uuid not in seen_uuids:
                    seen_uuids.add(r.edge.uuid)
                    all_edges.append({
                        "name": r.edge.name,
                        "fact": r.edge.fact,
                        "source": r.edge.source_node_uuid,
                        "target": r.edge.target_node_uuid
                    })
                    if r.edge.fact:
                        all_facts.append(r.edge.fact)

        return {
            "query": query,
            "sub_queries": sub_queries,
            "facts": all_facts[:limit],
            "nodes": all_nodes[:limit],
            "edges": all_edges[:limit],
            "total_facts": len(all_facts),
            "total_nodes": len(all_nodes),
            "total_edges": len(all_edges)
        }

    def panorama_search(self, query: str, limit: int = 20) -> Dict:
        """PanoramaSearch 광역 검색 - 노드와 엣지 모두 검색"""
        results = self.graph_store.search(self.graph_id, query, limit=limit)

        facts = []
        nodes = []
        edges = []

        for r in results:
            if r.result_type == "node" and r.node:
                nodes.append({
                    "name": r.node.name,
                    "labels": r.node.labels,
                    "summary": r.node.summary,
                    "score": r.score
                })
            elif r.result_type == "edge" and r.edge:
                edges.append({
                    "name": r.edge.name,
                    "fact": r.edge.fact,
                    "score": r.score
                })
                if r.edge.fact:
                    facts.append(r.edge.fact)

        return {
            "query": query,
            "facts": facts,
            "nodes": nodes,
            "edges": edges
        }

    def quick_search(self, query: str, limit: int = 5) -> Dict:
        """QuickSearch 빠른 검색"""
        results = self.graph_store.search(self.graph_id, query, limit=limit)

        items = []
        for r in results:
            if r.result_type == "node" and r.node:
                items.append({
                    "type": "node",
                    "name": r.node.name,
                    "summary": r.node.summary,
                    "score": r.score
                })
            elif r.result_type == "edge" and r.edge:
                items.append({
                    "type": "edge",
                    "name": r.edge.name,
                    "fact": r.edge.fact,
                    "score": r.score
                })

        return {"query": query, "results": items}

    def graph_statistics(self) -> Dict:
        """그래프 통계"""
        return self.graph_store.get_graph_stats(self.graph_id)

    def _generate_sub_queries(self, query: str) -> List[str]:
        """쿼리를 서브 질문으로 분해"""
        try:
            result = self.llm_client.chat_json(
                messages=[{
                    "role": "system",
                    "content": "주어진 질문을 3-5개의 구체적인 서브 질문으로 분해하세요. JSON 형식: {\"sub_queries\": [\"질문1\", \"질문2\", ...]}"
                }, {
                    "role": "user",
                    "content": query
                }],
                temperature=0.3,
                max_tokens=1024
            )
            return result.get("sub_queries", [query])
        except Exception as e:
            logger.warning(f"서브 질문 생성 실패, 원본 쿼리 사용: {e}")
            return [query]