"""
투자 도메인 전용 API 라우트
페르소나 관리, 투자 온톨로지, 토픽 설정 등
"""

import traceback
from flask import request, jsonify

from . import invest_bp
from ..services.investor_personas import (
    get_all_personas, get_persona, get_personas_by_ids,
    get_persona_summary, get_recommended_personas
)
from ..services.investment_ontology import get_investment_ontology
from ..utils.logger import get_logger

logger = get_logger('ungdroofish.api.invest')


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