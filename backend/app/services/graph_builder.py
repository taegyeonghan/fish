"""
그래프 구축 서비스
인터페이스2: LocalGraphStore를 사용한 로컬 지식 그래프 구축
LLM 기반 엔티티/관계 추출
"""

import json
import re
import uuid
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from ..config import Config
from ..models.task import TaskManager, TaskStatus
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from .local_graph import LocalGraphStore, NodeData, EdgeData
from .text_processor import TextProcessor
from ..utils.locale import t, get_locale, set_locale

logger = get_logger('ungdroofish.graph_builder')


# LLM 엔티티/관계 추출용 시스템 프롬프트
EXTRACTION_SYSTEM_PROMPT = """You are a knowledge graph extraction assistant.
Given a text chunk and an ontology definition, extract entities and relationships.

Return a JSON object with:
{
  "entities": [
    {
      "name": "entity name",
      "type": "entity type from ontology",
      "summary": "brief description",
      "attributes": {"attr_name": "attr_value", ...}
    }
  ],
  "relations": [
    {
      "source": "source entity name",
      "target": "target entity name",
      "relation_type": "relation type from ontology",
      "fact": "description of this relationship"
    }
  ]
}

Rules:
- Only use entity types and relation types defined in the ontology.
- If no matching type exists, use "Entity" as a fallback entity type.
- Entity names should be normalized (consistent casing, no duplicates).
- Extract concrete, real-world entities that are EXPLICITLY NAMED in the text:
  specific companies, people, securities/tickers, market indices, sectors/industries,
  economic indicators, named events, organizations, products, places, instruments.
- Keep summaries concise but informative.
- The "fact" field should describe the relationship in natural language.

DO NOT extract (these produce meaningless nodes):
- Abstract concepts, methodologies, models, strategies, or the analysis/prediction
  task itself (e.g. "prediction model", "investment strategy", "the analysis",
  "복합 투자 예측 모델", "수익률 예측 모델"). These describe the task, not the world.
- Generic role descriptions with no concrete named referent. If the text mentions a
  concept only generically (no specific name), SKIP it — do not invent a node for it.
- Document scaffolding / metadata. IGNORE lines and headers such as the prediction
  question, "Prediction question", "Selected local sources", "Auto-collected source",
  "Source type", "Path", "Relevance score", section dividers (===), and file names.
- Prefer specific named instances (e.g. "NVIDIA", "CPI", "FOMC") over generic
  categories (e.g. "a tech company", "an indicator", "a meeting").

Be selective — do NOT exhaustively extract every minor mention:
- Return only the MOST IMPORTANT entities central to this chunk, at most 8.
- Skip incidental, trivial, or one-off mentions that are not central to the meaning.
- Only emit a relationship when BOTH endpoints are among the entities you extracted.
"""


@dataclass
class GraphInfo:
    """그래프 정보"""
    graph_id: str
    node_count: int
    edge_count: int
    entity_types: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "entity_types": self.entity_types,
        }


class GraphBuilderService:
    """
    그래프 구축 서비스
    LocalGraphStore와 LLM을 사용하여 지식 그래프를 구축
    """

    def __init__(self):
        self.graph_store = LocalGraphStore()
        self.llm_client = LLMClient()
        self.task_manager = TaskManager()

    def build_graph_async(
        self,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str = "UngdrooFish Graph",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 3
    ) -> str:
        """
        비동기 그래프 구축

        Args:
            text: 입력 텍스트
            ontology: 온톨로지 정의 (인터페이스1의 출력)
            graph_name: 그래프 이름
            chunk_size: 텍스트 청크 크기
            chunk_overlap: 청크 오버랩 크기
            batch_size: 배치당 청크 수

        Returns:
            태스크 ID
        """
        # 태스크 생성
        task_id = self.task_manager.create_task(
            task_type="graph_build",
            metadata={
                "graph_name": graph_name,
                "chunk_size": chunk_size,
                "text_length": len(text),
            }
        )

        # 백그라운드 스레드 실행 전 로캘 캡처
        current_locale = get_locale()

        # 백그라운드 스레드에서 구축 실행
        thread = threading.Thread(
            target=self._build_graph_worker,
            args=(task_id, text, ontology, graph_name, chunk_size, chunk_overlap, batch_size, current_locale)
        )
        thread.daemon = True
        thread.start()

        return task_id

    def _build_graph_worker(
        self,
        task_id: str,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        batch_size: int,
        locale: str = 'ko'
    ):
        """그래프 구축 워커 스레드"""
        set_locale(locale)
        try:
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                progress=5,
                message=t('progress.startBuildingGraph')
            )

            # 1. 그래프 생성
            graph_id = self.create_graph(graph_name)
            self.task_manager.update_task(
                task_id,
                progress=10,
                message=t('progress.graphCreated', graphId=graph_id)
            )

            # 2. 온톨로지 설정
            self.set_ontology(graph_id, ontology)
            self.task_manager.update_task(
                task_id,
                progress=15,
                message=t('progress.ontologySet')
            )

            # 3. 텍스트 분할
            chunks = TextProcessor.split_text(text, chunk_size, chunk_overlap)
            total_chunks = len(chunks)
            self.task_manager.update_task(
                task_id,
                progress=20,
                message=t('progress.textSplit', count=total_chunks)
            )

            # 4. 청크별 LLM 엔티티/관계 추출 및 그래프에 추가
            self._extract_and_add_entities(
                graph_id, chunks, ontology, batch_size,
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=20 + int(prog * 0.7),  # 20-90%
                    message=msg
                )
            )

            # 5. 그래프 정보 조회
            self.task_manager.update_task(
                task_id,
                progress=90,
                message=t('progress.fetchingGraphInfo')
            )

            graph_info = self._get_graph_info(graph_id)

            # 완료
            self.task_manager.complete_task(task_id, {
                "graph_id": graph_id,
                "graph_info": graph_info.to_dict(),
                "chunks_processed": total_chunks,
            })

        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.task_manager.fail_task(task_id, error_msg)

    def create_graph(self, name: str) -> str:
        """새 그래프 생성 (공개 메서드)"""
        graph_id = self.graph_store.create_graph(
            name=name,
            description="UngdrooFish Investment Simulation Graph"
        )
        return graph_id

    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """그래프 온톨로지 설정 (공개 메서드)"""
        self.graph_store.set_ontology(graph_id, ontology)

    def _build_ontology_description(self, ontology: Dict[str, Any]) -> str:
        """온톨로지를 LLM 프롬프트에 사용할 텍스트로 변환"""
        lines = []

        # 엔티티 타입 설명
        lines.append("Entity Types:")
        for entity_def in ontology.get("entity_types", []):
            name = entity_def["name"]
            desc = entity_def.get("description", "")
            attrs = [a["name"] for a in entity_def.get("attributes", [])]
            attrs_str = f" (attributes: {', '.join(attrs)})" if attrs else ""
            lines.append(f"  - {name}: {desc}{attrs_str}")

        # 관계 타입 설명
        lines.append("\nRelation Types:")
        for edge_def in ontology.get("edge_types", []):
            name = edge_def["name"]
            desc = edge_def.get("description", "")
            source_targets = edge_def.get("source_targets", [])
            st_str = ", ".join(
                f"{st.get('source', '?')} -> {st.get('target', '?')}"
                for st in source_targets
            )
            if st_str:
                lines.append(f"  - {name}: {desc} [{st_str}]")
            else:
                lines.append(f"  - {name}: {desc}")

        return "\n".join(lines)

    def _extract_entities_from_chunk(
        self,
        chunk_text: str,
        ontology_desc: str
    ) -> Dict[str, Any]:
        """LLM을 호출하여 텍스트 청크에서 엔티티와 관계를 추출"""
        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Ontology:\n{ontology_desc}\n\n"
                f"Text chunk:\n{chunk_text}\n\n"
                "Extract entities and relationships as JSON."
            )}
        ]

        raw = ""
        try:
            raw = self.llm_client.chat(
                messages=messages,
                temperature=0.1,
                max_tokens=8192
            )
            import re
            cleaned = raw.strip()
            cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\n?```\s*$', '', cleaned)
            cleaned = cleaned.strip()
            result = LLMClient._parse_json_robust(cleaned)
            return result
        except Exception as e:
            logger.error(f"LLM entity extraction failed. Error: {type(e).__name__}: {str(e)[:150]}")
            logger.error(f"Raw LLM length={len(raw)}, last 400 chars: ...{raw[-400:]}")
            # Salvage: try to extract partial entities from truncated response
            salvaged = self._salvage_partial_json(raw)
            if salvaged:
                logger.info(f"Salvaged {len(salvaged.get('entities', []))} entities from partial response")
                return salvaged
            return {"entities": [], "relations": []}

    def _salvage_partial_json(self, text: str) -> Dict[str, Any]:
        """Extract valid entity/relation objects from a truncated JSON response."""
        import re
        result = {"entities": [], "relations": []}
        # Find all complete {...} objects inside "entities": [ ... ]
        for section_name in ("entities", "relations"):
            section_match = re.search(rf'"{section_name}"\s*:\s*\[', text)
            if not section_match:
                continue
            start = section_match.end()
            depth = 0
            obj_start = None
            in_string = False
            escape = False
            i = start
            while i < len(text):
                c = text[i]
                if escape:
                    escape = False
                    i += 1
                    continue
                if c == '\\':
                    escape = True
                    i += 1
                    continue
                if c == '"':
                    in_string = not in_string
                    i += 1
                    continue
                if not in_string:
                    if c == '{':
                        if depth == 0:
                            obj_start = i
                        depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0 and obj_start is not None:
                            try:
                                obj = json.loads(text[obj_start:i+1])
                                result[section_name].append(obj)
                            except json.JSONDecodeError:
                                pass
                            obj_start = None
                    elif c == ']' and depth == 0:
                        break
                i += 1
        return result if (result["entities"] or result["relations"]) else None

    def _extract_and_add_entities(
        self,
        graph_id: str,
        chunks: List[str],
        ontology: Dict[str, Any],
        batch_size: int = 3,
        progress_callback: Optional[Callable] = None
    ):
        """
        청크별로 LLM을 호출하여 엔티티/관계를 추출하고 그래프에 추가

        Args:
            graph_id: 그래프 ID
            chunks: 텍스트 청크 목록
            ontology: 온톨로지 정의
            batch_size: 배치 크기 (진행률 업데이트 단위)
            progress_callback: 진행률 콜백 함수
        """
        total_chunks = len(chunks)
        if total_chunks == 0:
            return
        ontology_desc = self._build_ontology_description(ontology)

        # 온톨로지 사후 검증용 허용 집합
        allowed_entity_types = {
            e["name"] for e in ontology.get("entity_types", []) if e.get("name")
        }
        allowed_edge_types = {
            e["name"] for e in ontology.get("edge_types", []) if e.get("name")
        }
        GROUNDABLE_LABELS = {"Stock", "Organization"}

        # 메타/추상 엔티티 차단 패턴 (캐시된 온톨로지에도 강제 적용)
        try:
            blocked_re = re.compile(Config.BLOCKED_ENTITY_PATTERN)
        except re.error:
            blocked_re = None
        blocked_count = 0

        logger.info(
            f"[graph_build] chunks={total_chunks}, workers={max(1, min(Config.GRAPH_BUILD_MAX_WORKERS, total_chunks))}, "
            f"max_nodes={Config.MAX_GRAPH_NODES}, meta_block={'on' if blocked_re else 'off'}, "
            f"grounding={Config.GROUND_ENTITIES_WITH_MCP}"
        )

        # ===== Phase 1: 청크별 LLM 추출을 병렬 실행 (가장 느린 부분) =====
        extractions: List[Optional[Dict[str, Any]]] = [None] * total_chunks
        max_workers = max(1, min(Config.GRAPH_BUILD_MAX_WORKERS, total_chunks))
        completed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(self._extract_entities_from_chunk, chunk, ontology_desc): idx
                for idx, chunk in enumerate(chunks)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    extractions[idx] = future.result()
                except Exception as e:
                    logger.error(f"청크 {idx} 추출 실패: {type(e).__name__}: {str(e)[:150]}")
                    extractions[idx] = {"entities": [], "relations": []}
                completed += 1
                if progress_callback:
                    # 추출이 전체의 85%를 차지, 나머지는 그래프 적재
                    progress_callback(
                        t('progress.sendingBatch', current=completed, total=total_chunks, chunks=1),
                        (completed / total_chunks) * 0.85
                    )

        # ===== Phase 2: 순차 적재 (dedup·해소·상한·검증·grounding) =====
        # SQLite 쓰기는 단일 스레드로 유지해 락/순서 충돌 방지
        node_name_map: Dict[str, str] = {}  # 정규화된 이름 -> uuid

        grounder = None
        if Config.GROUND_ENTITIES_WITH_MCP:
            try:
                from .mcp_client import GemstoneClient
                grounder = GemstoneClient()
            except Exception as e:
                logger.warning(f"MCP grounding 비활성(클라이언트 생성 실패): {e}")

        def _norm(name: str) -> str:
            return name.strip().casefold()

        try:
            for i, extraction in enumerate(extractions):
                if not extraction:
                    continue

                ep_uuid = self.graph_store.add_episode(graph_id, chunks[i])

                entities_added_this_chunk = 0
                for entity in extraction.get("entities", []):
                    if len(node_name_map) >= Config.MAX_GRAPH_NODES:
                        break
                    if entities_added_this_chunk >= Config.MAX_ENTITIES_PER_CHUNK:
                        break

                    entity_name = entity.get("name", "").strip()
                    if not entity_name:
                        continue
                    key = _norm(entity_name)
                    if key in node_name_map:
                        continue

                    entity_type = entity.get("type", "Entity")

                    # 메타/추상 노드(모델·리포트·예측 과업 등)는 타입·이름 어느 쪽이든
                    # 패턴에 걸리면 통째로 버린다. → 캐시된 온톨로지에도 적용됨
                    if blocked_re is not None and (
                        blocked_re.search(entity_type) or blocked_re.search(entity_name)
                    ):
                        blocked_count += 1
                        continue

                    # 온톨로지에 없는 타입은 Entity로 강등
                    if allowed_entity_types and entity_type not in allowed_entity_types:
                        entity_type = "Entity"
                    summary = entity.get("summary", "")
                    attributes = entity.get("attributes", {}) or {}

                    # 엔티티 해소: 기존 노드와 임베딩 유사도가 높으면 병합
                    resolve_text = f"{entity_name}. {summary}" if summary else entity_name
                    existing_uuid = self.graph_store.find_similar_node_uuid(
                        graph_id,
                        resolve_text,
                        threshold=Config.ENTITY_RESOLUTION_THRESHOLD,
                        allowed_labels=[entity_type] if entity_type != "Entity" else None,
                    )
                    if existing_uuid:
                        node_name_map[key] = existing_uuid
                        continue

                    # gemstone MCP grounding (종목/기업)
                    if grounder is not None and entity_type in GROUNDABLE_LABELS:
                        try:
                            ground = self._ground_entity(grounder, entity_name)
                            if ground:
                                attributes.update(ground)
                        except Exception as e:
                            logger.debug(f"grounding 실패({entity_name}): {e}")

                    entities_added_this_chunk += 1
                    node_uuid = self.graph_store.add_node(
                        graph_id=graph_id,
                        name=entity_name,
                        labels=[entity_type],
                        summary=summary,
                        attributes=attributes
                    )
                    node_name_map[key] = node_uuid

                # 관계 추가
                for relation in extraction.get("relations", []):
                    source_name = relation.get("source", "").strip()
                    target_name = relation.get("target", "").strip()
                    relation_type = relation.get("relation_type", "RELATED_TO")
                    fact = relation.get("fact", "")

                    if not source_name or not target_name:
                        continue

                    s_key, t_key = _norm(source_name), _norm(target_name)
                    # 끝점이 실제로 추출된 엔티티가 아니면 관계를 버린다.
                    # (예전엔 빈 "Entity" 노드를 자동 생성해 잡노드를 양산했음)
                    if s_key not in node_name_map or t_key not in node_name_map:
                        continue

                    # 온톨로지에 없는 관계 타입은 RELATED_TO로 매핑
                    if allowed_edge_types and relation_type not in allowed_edge_types:
                        relation_type = "RELATED_TO"

                    self.graph_store.add_edge(
                        graph_id=graph_id,
                        name=relation_type,
                        source_uuid=node_name_map[s_key],
                        target_uuid=node_name_map[t_key],
                        fact=fact
                    )

                self.graph_store.mark_episode_processed(ep_uuid)
        finally:
            if grounder is not None:
                try:
                    grounder.close()
                except Exception:
                    pass

        logger.info(
            f"[graph_build] 적재 완료: nodes={len(node_name_map)}, blocked_meta={blocked_count}"
        )

        if progress_callback:
            progress_callback(
                t('progress.processingComplete', completed=total_chunks, total=total_chunks),
                1.0
            )

    def _ground_entity(self, grounder, name: str) -> Optional[Dict[str, str]]:
        """
        gemstone MCP code-search로 종목/기업명을 실제 식별자에 매칭.
        성공 시 {ticker, region, matched_name} 일부를 attributes로 반환.
        응답 스키마가 유동적이므로 방어적으로 파싱한다.
        """
        res = grounder.code_search(name, search_type="ticker")

        items = None
        if isinstance(res, dict):
            if res.get("error"):
                return None
            items = res.get("data") or res.get("results") or res.get("items")
            if items is None and ("ticker" in res or "code" in res):
                items = [res]
        elif isinstance(res, list):
            items = res

        if not items or not isinstance(items, list):
            return None
        first = items[0]
        if not isinstance(first, dict):
            return None

        out: Dict[str, str] = {}
        for src_key, dst_key in (
            ("ticker", "ticker"), ("code", "ticker"),
            ("region", "region"), ("country", "region"),
            ("name", "matched_name"), ("name_kr", "matched_name"),
        ):
            val = first.get(src_key)
            if val and dst_key not in out:
                out[dst_key] = str(val)
        return out or None

    def _get_graph_info(self, graph_id: str) -> GraphInfo:
        """그래프 정보 조회"""
        nodes = self.graph_store.get_all_nodes(graph_id)
        edges = self.graph_store.get_all_edges(graph_id)

        # 엔티티 타입 수집
        entity_types = set()
        for node in nodes:
            for label in node.labels:
                if label not in ("Entity", "Node"):
                    entity_types.add(label)

        return GraphInfo(
            graph_id=graph_id,
            node_count=len(nodes),
            edge_count=len(edges),
            entity_types=list(entity_types)
        )

    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """
        전체 그래프 데이터 조회 (상세 정보 포함)

        Args:
            graph_id: 그래프 ID

        Returns:
            노드와 엣지를 포함한 딕셔너리 (시간 정보, 속성 등 상세 데이터)
        """
        nodes = self.graph_store.get_all_nodes(graph_id)
        edges = self.graph_store.get_all_edges(graph_id)

        # 노드 매핑 생성 (uuid -> name)
        node_map = {}
        for node in nodes:
            node_map[node.uuid] = node.name or ""

        nodes_data = []
        for node in nodes:
            nodes_data.append({
                "uuid": node.uuid,
                "name": node.name,
                "labels": node.labels or [],
                "summary": node.summary or "",
                "attributes": node.attributes or {},
                "created_at": node.created_at,
            })

        edges_data = []
        for edge in edges:
            edges_data.append({
                "uuid": edge.uuid,
                "name": edge.name or "",
                "fact": edge.fact or "",
                "fact_type": edge.name or "",
                "source_node_uuid": edge.source_node_uuid,
                "target_node_uuid": edge.target_node_uuid,
                "source_node_name": node_map.get(edge.source_node_uuid, ""),
                "target_node_name": node_map.get(edge.target_node_uuid, ""),
                "attributes": edge.attributes or {},
                "created_at": edge.created_at,
                "valid_at": None,
                "invalid_at": None,
                "expired_at": None,
                "episodes": [],
            })

        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }

    def delete_graph(self, graph_id: str):
        """그래프 삭제"""
        self.graph_store.delete_graph(graph_id)