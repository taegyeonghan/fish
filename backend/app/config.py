"""
UngdrooFish 설정 관리
프로젝트 루트의 .env 파일에서 설정 로드
"""

import os
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    load_dotenv(override=True)


class Config:
    """Flask 설정 클래스"""

    # Flask 설정
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ungdroo-fish-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    # JSON 설정 - 한국어 직접 표시
    JSON_AS_ASCII = False

    # LLM 설정 (OpenAI 호환 형식)
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')

    # 로컬 그래프 엔진 설정 (ZEP 대체)
    SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), '../data/graph.db')

    # 임베딩 모델 (한국어 포함 다국어. 384차원으로 기존과 동일해 차원 충돌 없음)
    EMBEDDING_MODEL = os.environ.get(
        'EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
    )
    EMBEDDING_DIM = int(os.environ.get('EMBEDDING_DIM', '384'))

    # 엔티티 해소(병합) 임계값 — 임베딩 코사인 유사도가 이 값 이상이면 동일 노드로 병합
    ENTITY_RESOLUTION_THRESHOLD = float(os.environ.get('ENTITY_RESOLUTION_THRESHOLD', '0.90'))

    # 그래프 빌드 시 청크 추출 병렬 워커 수
    GRAPH_BUILD_MAX_WORKERS = int(os.environ.get('GRAPH_BUILD_MAX_WORKERS', '6'))

    # gemstone MCP로 종목/기업 엔티티 grounding 여부
    GROUND_ENTITIES_WITH_MCP = os.environ.get('GROUND_ENTITIES_WITH_MCP', 'True').lower() == 'true'

    # 문서 미업로드 시 이전 프로젝트 추출텍스트 자동수집 여부 (오염 방지 위해 기본 off)
    AUTO_COLLECT_PREVIOUS_PROJECTS = os.environ.get('AUTO_COLLECT_PREVIOUS_PROJECTS', 'False').lower() == 'true'

    # 빌드 시 차단할 메타/추상 엔티티 타입·이름 패턴 (캐시된 온톨로지에도 강제 적용).
    # 분석 과업/모델/리포트/방법론 등 "현실의 대상이 아닌" 노드를 걸러낸다.
    BLOCKED_ENTITY_PATTERN = os.environ.get(
        'BLOCKED_ENTITY_PATTERN',
        r'(?i)(model|report|prediction|forecast|strateg|method|analysis|scenario|'
        r'pipeline|question|document|source|task|simulation|예측|리포트|모델|시뮬레이션|분석\s*과업)'
    )

    # Gemstone MCP API 설정
    GEMSTONE_BASE_URL = os.environ.get('GEMSTONE_BASE_URL', 'https://gemstone.ngrok.app')

    # 파일 업로드 설정
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}

    # 텍스트 처리 설정
    # 청크가 너무 작으면 청크 수가 늘어 추출 호출이 많아지고 노드가 과도하게 양산됨.
    DEFAULT_CHUNK_SIZE = 1200
    DEFAULT_CHUNK_OVERLAP = 100

    # 그래프 노드 상한 (이상치 방지 — 이 수를 넘으면 추가 추출을 멈춤)
    MAX_GRAPH_NODES = int(os.environ.get('MAX_GRAPH_NODES', '120'))
    # 청크당 추출 엔티티 상한 (가장 핵심적인 대상만)
    MAX_ENTITIES_PER_CHUNK = int(os.environ.get('MAX_ENTITIES_PER_CHUNK', '8'))

    # OASIS 시뮬레이션 설정
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')

    # OASIS 플랫폼 액션 설정
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # 보고서 에이전트 설정
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))

    @classmethod
    def validate(cls):
        """필수 설정 검증"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY 미설정")
        return errors