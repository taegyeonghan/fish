"""
투자 도메인 온톨로지
사전 정의된 엔티티 타입과 관계 타입
"""


INVESTMENT_ONTOLOGY = {
    "entity_types": [
        {
            "name": "Stock",
            "description": "개별 주식 종목",
            "attributes": [
                {"name": "ticker", "type": "text", "description": "종목 코드"},
                {"name": "sector", "type": "text", "description": "산업 섹터"},
                {"name": "market_cap", "type": "text", "description": "시가총액 규모"},
                {"name": "region", "type": "text", "description": "상장 지역"},
            ],
            "examples": ["삼성전자", "NVIDIA", "Tesla"]
        },
        {
            "name": "Investor",
            "description": "투자자 또는 투자 에이전트",
            "attributes": [
                {"name": "investment_style", "type": "text", "description": "투자 스타일"},
                {"name": "risk_tolerance", "type": "text", "description": "위험 허용도"},
                {"name": "portfolio_focus", "type": "text", "description": "포트폴리오 집중 영역"},
            ],
            "examples": ["가치투자자", "모멘텀 트레이더", "헤지펀드 매니저"]
        },
        {
            "name": "Market",
            "description": "주식 시장 또는 지수",
            "attributes": [
                {"name": "region", "type": "text", "description": "지역"},
                {"name": "index_name", "type": "text", "description": "대표 지수명"},
            ],
            "examples": ["KOSPI", "S&P 500", "NASDAQ"]
        },
        {
            "name": "Sector",
            "description": "산업 섹터",
            "attributes": [
                {"name": "name", "type": "text", "description": "섹터명"},
                {"name": "trend", "type": "text", "description": "현재 트렌드"},
            ],
            "examples": ["반도체", "바이오", "에너지", "금융"]
        },
        {
            "name": "EconomicIndicator",
            "description": "거시경제 지표",
            "attributes": [
                {"name": "name", "type": "text", "description": "지표명"},
                {"name": "value", "type": "text", "description": "현재 값"},
                {"name": "trend", "type": "text", "description": "추세"},
            ],
            "examples": ["GDP", "CPI", "기준금리", "실업률"]
        },
        {
            "name": "Event",
            "description": "시장에 영향을 미치는 이벤트",
            "attributes": [
                {"name": "event_type", "type": "text", "description": "이벤트 유형"},
                {"name": "impact", "type": "text", "description": "예상 영향"},
            ],
            "examples": ["실적 발표", "FOMC 회의", "지정학적 리스크"]
        },
        {
            "name": "FinancialMetric",
            "description": "재무 지표 또는 밸류에이션 지표",
            "attributes": [
                {"name": "metric_name", "type": "text", "description": "지표명"},
                {"name": "value", "type": "text", "description": "값"},
            ],
            "examples": ["PER", "ROE", "배당수익률", "영업이익률"]
        },
        {
            "name": "Organization",
            "description": "기업, 정부 기관, 중앙은행 등",
            "attributes": [
                {"name": "org_type", "type": "text", "description": "조직 유형"},
                {"name": "role", "type": "text", "description": "역할"},
            ],
            "examples": ["한국은행", "연준", "삼성전자", "SEC"]
        },
        {
            "name": "Person",
            "description": "기타 관련 인물",
            "attributes": [
                {"name": "role", "type": "text", "description": "역할"},
            ],
            "examples": ["제롬 파월", "이재용", "워런 버핏"]
        },
    ],
    "edge_types": [
        {"name": "HOLDS_POSITION", "description": "투자자가 종목을 보유"},
        {"name": "ANALYZES", "description": "투자자가 종목/섹터를 분석"},
        {"name": "BULLISH_ON", "description": "투자자가 대상에 강세 의견"},
        {"name": "BEARISH_ON", "description": "투자자가 대상에 약세 의견"},
        {"name": "BELONGS_TO", "description": "종목이 섹터에 속함"},
        {"name": "CORRELATES_WITH", "description": "두 대상이 상관관계"},
        {"name": "IMPACTS", "description": "이벤트/지표가 시장/종목에 영향"},
        {"name": "REPORTS", "description": "기업이 재무 지표를 발표"},
        {"name": "LEADS", "description": "인물이 조직을 이끔"},
        {"name": "COMPETES_WITH", "description": "기업 간 경쟁 관계"},
    ]
}


def get_investment_ontology():
    """투자 도메인 온톨로지 반환"""
    return INVESTMENT_ONTOLOGY


def get_entity_type_names():
    """엔티티 타입 이름 목록"""
    return [et["name"] for et in INVESTMENT_ONTOLOGY["entity_types"]]


def get_edge_type_names():
    """엣지 타입 이름 목록"""
    return [et["name"] for et in INVESTMENT_ONTOLOGY["edge_types"]]