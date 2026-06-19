"""
투자 도메인 전용 API 라우트
페르소나 관리, 투자 온톨로지, 토픽 설정 등
"""

import traceback
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from flask import request, jsonify

from . import invest_bp
from ..services.investor_personas import (
    get_all_personas, get_persona, get_personas_by_ids,
    get_persona_summary, get_recommended_personas
)
from ..services.investment_ontology import get_investment_ontology
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger('ungdroofish.api.invest')

NEWS_QUERIES = [
    'global markets stocks economy latest news',
    'AI semiconductors stocks latest news',
    'Federal Reserve rates inflation markets latest news',
    'oil energy defense geopolitics markets latest news',
]

SAMPLE_CACHE_TTL_SECONDS = 15 * 60
_sample_questions_cache = {
    "expires_at": 0,
    "payload": None,
}

FALLBACK_SAMPLE_QUESTIONS = [
    {
        "label": "에너지 섹터",
        "question": "원유 가격 급등과 지정학적 리스크가 에너지 섹터, 방산주, 인플레이션 기대에 미칠 영향을 분석하고, 각 투자자 페르소나의 관점에서 향후 3개월 전략을 제시해주세요.",
        "topic": "energy_geopolitics"
    },
    {
        "label": "AI 반도체",
        "question": "AI 반도체 수요와 데이터센터 투자 사이클이 엔비디아, TSMC, SK하이닉스 등 주요 기업의 실적과 밸류에이션에 미칠 영향을 토론해주세요.",
        "topic": "ai_semiconductors"
    },
    {
        "label": "금리 인상",
        "question": "연준의 기준금리 경로와 인플레이션 전망 변화가 성장주, 가치주, 금융주에 미치는 차별적 영향을 분석하고 섹터별 포지셔닝 전략을 제시해주세요.",
        "topic": "rates_inflation"
    },
]


def _fetch_google_news_rss(query: str, limit: int = 5) -> list[dict]:
    encoded = urllib.parse.quote(query)
    url = f'https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko'
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (compatible; OntologySimulator/1.0)',
            'Accept': 'application/rss+xml, application/xml, text/xml',
        },
    )

    with urllib.request.urlopen(req, timeout=8) as resp:
        raw = resp.read()

    root = ET.fromstring(raw)
    items = []
    for item in root.findall('.//channel/item')[:limit]:
        title = (item.findtext('title') or '').strip()
        source = (item.findtext('source') or '').strip()
        pub_date = (item.findtext('pubDate') or '').strip()
        link = (item.findtext('link') or '').strip()
        if title:
            items.append({
                "title": title,
                "source": source,
                "published_at": pub_date,
                "url": link,
            })
    return items


def _collect_latest_news() -> list[dict]:
    news = []
    seen = set()
    for query in NEWS_QUERIES:
        try:
            for item in _fetch_google_news_rss(query):
                key = item.get("title", "").lower()
                if key and key not in seen:
                    seen.add(key)
                    news.append(item)
        except Exception as exc:
            logger.warning(f"뉴스 RSS 조회 실패: {query}: {exc}")
    return news[:16]


def _generate_sample_questions(news_items: list[dict]) -> list[dict]:
    if not news_items:
        return FALLBACK_SAMPLE_QUESTIONS

    news_text = "\n".join(
        f"- {item['title']} ({item.get('source') or 'unknown'}, {item.get('published_at') or 'unknown date'})"
        for item in news_items
    )

    try:
        result = LLMClient().chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 투자 예측 시뮬레이터의 샘플 질문 편집자입니다. "
                        "최신 뉴스 헤드라인을 바탕으로 사용자가 바로 실행할 수 있는 한국어 예측 시뮬레이션 질문 3개를 만드세요. "
                        "질문은 특정 종목/섹터/매크로 변수와 예측 기간을 포함하고, 서로 겹치지 않아야 합니다. "
                        "JSON만 반환하세요: {\"samples\":[{\"label\":\"짧은 칩 라벨\", \"question\":\"질문\", \"topic\":\"snake_case\"}]}"
                    ),
                },
                {
                    "role": "user",
                    "content": f"뉴스 헤드라인:\n{news_text}",
                },
            ],
            temperature=0.4,
            max_tokens=1800,
        )
        samples = result.get("samples", [])
        cleaned = []
        for sample in samples:
            label = str(sample.get("label", "")).strip()[:16]
            question = str(sample.get("question", "")).strip()
            topic = str(sample.get("topic", "latest_news")).strip()[:48] or "latest_news"
            if label and question:
                cleaned.append({"label": label, "question": question, "topic": topic})
        return cleaned[:3] or FALLBACK_SAMPLE_QUESTIONS
    except Exception as exc:
        logger.warning(f"최신 뉴스 기반 샘플 질문 생성 실패: {exc}")
        return FALLBACK_SAMPLE_QUESTIONS


# ============== 페르소나 API ==============

@invest_bp.route('/personas', methods=['GET'])
def list_personas():
    """전체 투자자 페르소나 목록 (요약)"""
    return jsonify({
        "success": True,
        "data": get_persona_summary()
    })


@invest_bp.route('/personas/<persona_id>', methods=['GET'])
def get_persona_detail(persona_id: str):
    """개별 페르소나 상세 정보"""
    persona = get_persona(persona_id)
    if not persona:
        return jsonify({
            "success": False,
            "error": f"페르소나를 찾을 수 없습니다: {persona_id}"
        }), 404

    return jsonify({
        "success": True,
        "data": persona.to_dict()
    })


@invest_bp.route('/personas/recommend', methods=['POST'])
def recommend_personas():
    """토론 주제에 맞는 페르소나 추천"""
    data = request.get_json() or {}
    topic = data.get("topic", "")

    recommended_ids = get_recommended_personas(topic)
    personas = get_personas_by_ids(recommended_ids)

    return jsonify({
        "success": True,
        "data": {
            "topic": topic,
            "recommended": [p.to_dict() for p in personas]
        }
    })


# ============== 온톨로지 API ==============

@invest_bp.route('/ontology', methods=['GET'])
def get_ontology():
    """투자 도메인 온톨로지"""
    return jsonify({
        "success": True,
        "data": get_investment_ontology()
    })


@invest_bp.route('/sample-questions', methods=['GET'])
def get_sample_questions():
    """최신 뉴스 기반 예측 시뮬레이션 샘플 질문"""
    now = time.time()
    if _sample_questions_cache["payload"] and _sample_questions_cache["expires_at"] > now:
        return jsonify(_sample_questions_cache["payload"])

    news_items = _collect_latest_news()
    samples = _generate_sample_questions(news_items)

    payload = {
        "success": True,
        "data": {
            "samples": samples,
            "news": news_items[:6],
            "fallback": samples == FALLBACK_SAMPLE_QUESTIONS,
        }
    }
    _sample_questions_cache["payload"] = payload
    _sample_questions_cache["expires_at"] = now + SAMPLE_CACHE_TTL_SECONDS

    return jsonify(payload)
