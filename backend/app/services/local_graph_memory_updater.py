"""
로컬 그래프 메모리 업데이터 - ZEP Graph Memory Updater 대체
시뮬레이션 중 에이전트 활동을 그래프에 반영
"""

import json
import threading
import queue
from dataclasses import dataclass
from typing import Dict, List, Optional

from .local_graph import LocalGraphStore
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger('ungdroofish.memory_updater')


@dataclass
class AgentActivity:
    """에이전트 활동 데이터"""
    agent_name: str
    action_type: str  # post, comment, like, repost, etc.
    content: str
    round_number: int
    platform: str = "twitter"
    target_agent: str = ""
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LocalGraphMemoryUpdater:
    """로컬 그래프 메모리 업데이터"""

    def __init__(self, graph_id: str, graph_store: Optional[LocalGraphStore] = None,
                 llm_client: Optional[LLMClient] = None, batch_size: int = 10):
        self.graph_id = graph_id
        self.graph_store = graph_store or LocalGraphStore()
        self.llm_client = llm_client or LLMClient()
        self.batch_size = batch_size
        self._activity_queue = queue.Queue()
        self._running = False
        self._thread = None

    def start(self):
        """백그라운드 메모리 업데이트 시작"""
        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        logger.info(f"메모리 업데이터 시작: {self.graph_id}")

    def stop(self):
        """메모리 업데이트 중지"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info(f"메모리 업데이터 중지: {self.graph_id}")

    def add_activity(self, activity: AgentActivity):
        """에이전트 활동 추가"""
        self._activity_queue.put(activity)

    def add_activities_batch(self, activities: List[AgentActivity]):
        """에이전트 활동 배치 추가"""
        for activity in activities:
            self._activity_queue.put(activity)

    def flush(self):
        """큐에 남은 활동 모두 처리"""
        activities = []
        while not self._activity_queue.empty():
            try:
                activities.append(self._activity_queue.get_nowait())
            except queue.Empty:
                break

        if activities:
            self._process_batch(activities)

    def _process_loop(self):
        """백그라운드 처리 루프"""
        while self._running:
            batch = []
            try:
                # 첫 아이템은 블로킹 대기
                item = self._activity_queue.get(timeout=2)
                batch.append(item)

                # 나머지는 배치 크기까지 논블로킹으로 수집
                while len(batch) < self.batch_size:
                    try:
                        item = self._activity_queue.get_nowait()
                        batch.append(item)
                    except queue.Empty:
                        break

                self._process_batch(batch)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"메모리 업데이트 루프 에러: {e}")

    def _process_batch(self, activities: List[AgentActivity]):
        """활동 배치를 그래프에 반영"""
        if not activities:
            return

        try:
            # 활동 요약을 텍스트로 변환
            summary_text = self._activities_to_text(activities)

            # 에피소드로 추가
            ep_uuid = self.graph_store.add_episode(self.graph_id, summary_text)

            # LLM으로 엔티티/관계 추출 후 그래프에 추가
            self._extract_and_add(summary_text)

            self.graph_store.mark_episode_processed(ep_uuid)

            logger.debug(f"배치 처리 완료: {len(activities)}개 활동")

        except Exception as e:
            logger.error(f"배치 처리 실패: {e}")

    def _activities_to_text(self, activities: List[AgentActivity]) -> str:
        """활동들을 텍스트로 변환"""
        lines = []
        for act in activities:
            if act.action_type in ("post", "CREATE_POST"):
                lines.append(f"[Round {act.round_number}] {act.agent_name} posted: {act.content}")
            elif act.action_type in ("comment", "CREATE_COMMENT"):
                target = f" (replying to {act.target_agent})" if act.target_agent else ""
                lines.append(f"[Round {act.round_number}] {act.agent_name} commented{target}: {act.content}")
            elif act.action_type in ("like", "LIKE_POST"):
                lines.append(f"[Round {act.round_number}] {act.agent_name} liked a post by {act.target_agent}")
            elif act.action_type in ("repost", "REPOST"):
                lines.append(f"[Round {act.round_number}] {act.agent_name} reposted from {act.target_agent}")
            else:
                lines.append(f"[Round {act.round_number}] {act.agent_name} performed {act.action_type}: {act.content}")

        return "\n".join(lines)

    def _extract_and_add(self, text: str):
        """LLM으로 텍스트에서 엔티티/관계 추출 후 그래프에 추가"""
        try:
            ontology = self.graph_store.get_ontology(self.graph_id)
            entity_types = [et.get("name", "") for et in ontology.get("entity_types", [])]

            result = self.llm_client.chat_json(
                messages=[{
                    "role": "system",
                    "content": f"""텍스트에서 엔티티와 관계를 추출하세요.
사용 가능한 엔티티 타입: {json.dumps(entity_types, ensure_ascii=False)}
JSON 형식으로 응답:
{{"entities": [{{"name": "이름", "type": "타입", "summary": "설명"}}],
  "edges": [{{"source": "출발엔티티", "target": "도착엔티티", "name": "관계명", "fact": "사실"}}]}}
엔티티나 관계가 없으면 빈 배열을 반환하세요."""
                }, {
                    "role": "user",
                    "content": text
                }],
                temperature=0.2,
                max_tokens=4096
            )

            # 엔티티 추가
            for entity in result.get("entities", []):
                self.graph_store.add_node(
                    self.graph_id,
                    name=entity["name"],
                    labels=[entity.get("type", "Entity")],
                    summary=entity.get("summary", "")
                )

            # 관계 추가
            for edge in result.get("edges", []):
                self.graph_store.add_fact_to_edge(
                    self.graph_id,
                    source_name=edge["source"],
                    target_name=edge["target"],
                    relation_name=edge["name"],
                    fact=edge.get("fact", "")
                )

        except Exception as e:
            logger.warning(f"엔티티 추출 실패 (무시): {e}")

    def add_activity_from_dict(self, data: Dict, platform: str):
        """
        （ ZepGraphMemoryUpdater ）

        Args:
            data:  actions.jsonl 
            platform:  (twitter/reddit)
        """
        if "event_type" in data:
            return

        activity = AgentActivity(
            agent_name=data.get("agent_name", ""),
            action_type=data.get("action_type", ""),
            content=data.get("action_args", {}).get("content", ""),
            round_number=data.get("round", 0),
            platform=platform,
            target_agent=data.get("action_args", {}).get("target_agent", ""),
            metadata=data.get("action_args", {}),
        )
        self.add_activity(activity)


class LocalGraphMemoryManager:
    """
    （ ZepGraphMemoryManager）
    """

    _updaters: Dict[str, LocalGraphMemoryUpdater] = {}
    _lock = threading.Lock()
    _stop_all_done = False

    @classmethod
    def create_updater(cls, simulation_id: str, graph_id: str) -> LocalGraphMemoryUpdater:
        with cls._lock:
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()

            updater = LocalGraphMemoryUpdater(graph_id)
            updater.start()
            cls._updaters[simulation_id] = updater
            logger.info(f": simulation_id={simulation_id}, graph_id={graph_id}")
            return updater

    @classmethod
    def get_updater(cls, simulation_id: str) -> Optional[LocalGraphMemoryUpdater]:
        return cls._updaters.get(simulation_id)

    @classmethod
    def stop_updater(cls, simulation_id: str):
        with cls._lock:
            if simulation_id in cls._updaters:
                cls._updaters[simulation_id].stop()
                del cls._updaters[simulation_id]
                logger.info(f": simulation_id={simulation_id}")

    @classmethod
    def stop_all(cls):
        if cls._stop_all_done:
            return
        cls._stop_all_done = True

        with cls._lock:
            if cls._updaters:
                for simulation_id, updater in list(cls._updaters.items()):
                    try:
                        updater.stop()
                    except Exception as e:
                        logger.error(f": simulation_id={simulation_id}, error={e}")
                cls._updaters.clear()
            logger.info("")