"""
MCP 도구 레지스트리
페르소나별 사용 가능한 금융 도구 매핑 및 실행
"""

import json
from typing import Any, Dict, List, Optional

from .mcp_client import GemstoneClient
from ..utils.logger import get_logger

logger = get_logger('ungdroofish.mcp_registry')


# 페르소나 타입별 사용 가능한 도구 매핑
PERSONA_TOOL_MAP: Dict[str, List[str]] = {
    "value_investor": [
        "stock_financial_data", "stock_analysis_fair_value",
        "guru_investors", "screening_value"
    ],
    "growth_investor": [
        "stock_analysis_growth", "stocks_price_trend",
        "screening_growth", "etf_tech_themes"
    ],
    "momentum_trader": [
        "stock_price_history", "market_sorted_return_stocks",
        "market_diagnostic_technical", "stock_analysis_technical"
    ],
    "hedge_fund_manager": [
        "stock_financial_data", "market_diagnostic_vix",
        "screening_factor", "backtesting"
    ],
    "retail_investor": [
        "stock_analysis_overview", "stock_price_history",
        "market_sorted_return_stocks", "code_search"
    ],
    "quant_analyst": [
        "backtesting", "screening_factor",
        "stock_financial_data", "market_diagnostic_factor"
    ],
    "macro_strategist": [
        "economic_indicators", "market_diagnostic_macro",
        "market_region_index_returns", "market_index_similar_period"
    ],
    "esg_investor": [
        "stock_analysis_overview", "stock_financial_data",
        "etf_theme_stocks", "screening_esg"
    ],
    "dividend_investor": [
        "stock_financial_data", "stock_analysis_dividend",
        "screening_dividend", "guru_investors"
    ],
    "etf_strategist": [
        "etf_portfolio_optimization", "etf_taa_strategies",
        "etf_performance_best_worst", "etf_tech_themes"
    ],
}


class MCPToolRegistry:
    """MCP 도구 레지스트리 및 실행기"""

    def __init__(self, client: Optional[GemstoneClient] = None):
        self.client = client or GemstoneClient()

    def get_tools_for_persona(self, persona_type: str) -> List[Dict]:
        """페르소나 타입에 맞는 도구 목록 (OpenAI function calling 형식)"""
        tool_ids = PERSONA_TOOL_MAP.get(persona_type, ["stock_analysis_overview", "stock_price_history"])
        tools = []
        for tool_id in tool_ids:
            tool_def = TOOL_DEFINITIONS.get(tool_id)
            if tool_def:
                tools.append(tool_def)
        return tools

    def execute_tool(self, tool_name: str, params: Dict) -> str:
        """도구 실행 후 결과를 문자열로 반환"""
        try:
            result = self._dispatch(tool_name, params)
            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"도구 실행 실패 [{tool_name}]: {e}")
            return json.dumps({"error": str(e)})

    def _dispatch(self, tool_name: str, params: Dict) -> Any:
        """도구 이름으로 적절한 클라이언트 메서드 호출"""
        c = self.client

        if tool_name == "code_search":
            return c.code_search(params["query"], params.get("search_type", "ticker"))

        elif tool_name == "stock_analysis_overview":
            return c.stock_analysis(params["ticker"], params["region"], "Overview")

        elif tool_name == "stock_analysis_fair_value":
            return c.stock_analysis(params["ticker"], params["region"], "FairValueEstimation")

        elif tool_name == "stock_analysis_growth":
            return c.stock_analysis(params["ticker"], params["region"], "EarningsReport")

        elif tool_name == "stock_analysis_technical":
            return c.stock_analysis(params["ticker"], params["region"], "TechnicalAnalysis")

        elif tool_name == "stock_analysis_dividend":
            return c.stock_analysis(params["ticker"], params["region"], "DividendAnalysis")

        elif tool_name == "stock_financial_data":
            return c.stock_financial_data(
                params["ticker"], params["region"],
                params.get("fs_type", "IS"), params.get("period_typ", "A"),
                params.get("fsitem_names", ""), params.get("startdate", "")
            )

        elif tool_name == "stock_price_history":
            return c.stock_price_history(
                params["ticker"], params["region"], params["startdate"],
                params.get("enddate", "")
            )

        elif tool_name == "stocks_price_trend":
            return c.stocks_price_trend(
                params["tickers"], params["regions"],
                params["startdate"], params.get("enddate", "")
            )

        elif tool_name == "market_diagnostic_technical":
            return c.market_diagnostic("MarketCondition", params.get("question", "Current market condition"), params.get("region", "US"))

        elif tool_name == "market_diagnostic_vix":
            return c.market_diagnostic("VIXSixFactorDecomposition", params.get("question", "VIX analysis"), params.get("region", "US"))

        elif tool_name == "market_diagnostic_macro":
            return c.market_diagnostic("EconomicCalendar", params.get("question", "Upcoming economic events"), params.get("region", "US"))

        elif tool_name == "market_diagnostic_factor":
            return c.market_diagnostic("FactorPerformance", params.get("question", "Factor performance analysis"), params.get("region", "US"))

        elif tool_name == "market_region_index_returns":
            return c.market_region_index_returns(params["region"])

        elif tool_name == "market_sorted_return_stocks":
            return c.market_sorted_return_stocks(
                params["region"], params["startdate"],
                params.get("enddate", ""), params.get("top_n", 20)
            )

        elif tool_name == "market_index_similar_period":
            return c.market_index_similar_period(params["indexname"])

        elif tool_name == "screening_value":
            return c.screening_stocks(params.get("region", "US"), "[PER]_[PBR]_[ROE]", "ranking", params.get("top_n", 20))

        elif tool_name == "screening_growth":
            return c.screening_stocks(params.get("region", "US"), "[Revenue]_[Net_Income]", "ranking", params.get("top_n", 20))

        elif tool_name == "screening_factor":
            return c.screening_stocks(
                params.get("region", "US"),
                params.get("fsitem_names", "[PER]_[ROE]"),
                params.get("mode", "ranking"),
                params.get("top_n", 20)
            )

        elif tool_name == "screening_dividend":
            return c.screening_stocks(params.get("region", "US"), "[Dividend_Yield]_[Payout_Ratio]", "ranking", params.get("top_n", 20))

        elif tool_name == "screening_esg":
            return c.screening_stocks(params.get("region", "US"), "[ROE]_[Revenue]", "ranking", params.get("top_n", 20))

        elif tool_name == "backtesting":
            return c.backtesting(
                params.get("region", "US"), params.get("mode", "ranking"),
                params.get("rebalance_period", "Q"),
                params.get("fsitem_names", "[PER]_[ROE]")
            )

        elif tool_name == "guru_investors":
            return c.guru_investors(params.get("type", "positions"), params.get("guru_name", ""))

        elif tool_name == "economic_indicators":
            return c.economic_indicators(
                params["indicators"], params["start_date"],
                params.get("end_date", "")
            )

        elif tool_name == "etf_portfolio_optimization":
            return c.etf_portfolio_optimization(
                params["target_return"], params["investment_period"]
            )

        elif tool_name == "etf_taa_strategies":
            return c.etf_taa_strategies(params.get("strategy_name", "all"))

        elif tool_name == "etf_performance_best_worst":
            return c.etf_performance_best_worst(
                params["region"], params["startdate"], params.get("ntop", 5)
            )

        elif tool_name == "etf_tech_themes":
            return c.etf_tech_themes_matching(
                params["ticker"], params["region"], params.get("top_n", 5)
            )

        elif tool_name == "etf_theme_stocks":
            return c.etf_theme_stocks(
                params.get("theme_korean", ""), params.get("theme_english", ""),
                params.get("top_n", 20)
            )

        else:
            return {"error": f"알 수 없는 도구: {tool_name}"}


# ==================== 도구 정의 (OpenAI function calling 형식) ====================

TOOL_DEFINITIONS: Dict[str, Dict] = {
    "code_search": {
        "type": "function",
        "function": {
            "name": "code_search",
            "description": "티커 심볼, 산업 코드, 테마 키워드 검색",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색 키워드"},
                    "search_type": {"type": "string", "enum": ["ticker", "industry", "tech_theme_keyword"]}
                },
                "required": ["query"]
            }
        }
    },
    "stock_analysis_overview": {
        "type": "function",
        "function": {
            "name": "stock_analysis_overview",
            "description": "종목 종합 분석 보고서 조회",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "종목 코드"},
                    "region": {"type": "string", "description": "ISO Alpha-2 지역코드 (KR, US 등)"}
                },
                "required": ["ticker", "region"]
            }
        }
    },
    "stock_analysis_fair_value": {
        "type": "function",
        "function": {
            "name": "stock_analysis_fair_value",
            "description": "종목 적정가치 추정",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"}, "region": {"type": "string"}
                },
                "required": ["ticker", "region"]
            }
        }
    },
    "stock_analysis_growth": {
        "type": "function",
        "function": {
            "name": "stock_analysis_growth",
            "description": "종목 실적 보고서 분석",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"}, "region": {"type": "string"}
                },
                "required": ["ticker", "region"]
            }
        }
    },
    "stock_analysis_technical": {
        "type": "function",
        "function": {
            "name": "stock_analysis_technical",
            "description": "종목 기술적 분석",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"}, "region": {"type": "string"}
                },
                "required": ["ticker", "region"]
            }
        }
    },
    "stock_analysis_dividend": {
        "type": "function",
        "function": {
            "name": "stock_analysis_dividend",
            "description": "종목 배당 분석",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"}, "region": {"type": "string"}
                },
                "required": ["ticker", "region"]
            }
        }
    },
    "stock_financial_data": {
        "type": "function",
        "function": {
            "name": "stock_financial_data",
            "description": "종목 재무데이터 조회 (재무제표, 비율 등)",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "region": {"type": "string"},
                    "fs_type": {"type": "string", "enum": ["BS", "IS", "CF", "Ratio"]},
                    "period_typ": {"type": "string", "enum": ["Q", "A"]},
                    "fsitem_names": {"type": "string", "description": "[항목1]_[항목2] 형식"},
                    "startdate": {"type": "string", "description": "YYYYMMDD"}
                },
                "required": ["ticker", "region"]
            }
        }
    },
    "stock_price_history": {
        "type": "function",
        "function": {
            "name": "stock_price_history",
            "description": "종목 과거 가격 데이터 조회",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "region": {"type": "string"},
                    "startdate": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["ticker", "region", "startdate"]
            }
        }
    },
    "stocks_price_trend": {
        "type": "function",
        "function": {
            "name": "stocks_price_trend",
            "description": "여러 종목의 누적수익률 비교",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "array", "items": {"type": "string"}},
                    "regions": {"type": "array", "items": {"type": "string"}},
                    "startdate": {"type": "string"}
                },
                "required": ["tickers", "regions", "startdate"]
            }
        }
    },
    "market_diagnostic_technical": {
        "type": "function",
        "function": {
            "name": "market_diagnostic_technical",
            "description": "시장 현황 진단",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"}, "region": {"type": "string"}
                },
                "required": ["question"]
            }
        }
    },
    "market_diagnostic_vix": {
        "type": "function",
        "function": {
            "name": "market_diagnostic_vix",
            "description": "VIX 6팩터 분해 분석",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"}, "region": {"type": "string"}
                },
                "required": ["question"]
            }
        }
    },
    "market_diagnostic_macro": {
        "type": "function",
        "function": {
            "name": "market_diagnostic_macro",
            "description": "경제 캘린더 및 매크로 이벤트",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"}, "region": {"type": "string"}
                },
                "required": ["question"]
            }
        }
    },
    "market_diagnostic_factor": {
        "type": "function",
        "function": {
            "name": "market_diagnostic_factor",
            "description": "팩터 성과 분석",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"}, "region": {"type": "string"}
                },
                "required": ["question"]
            }
        }
    },
    "market_region_index_returns": {
        "type": "function",
        "function": {
            "name": "market_region_index_returns",
            "description": "지역별 주요 지수 수익률",
            "parameters": {
                "type": "object",
                "properties": {"region": {"type": "string"}},
                "required": ["region"]
            }
        }
    },
    "market_sorted_return_stocks": {
        "type": "function",
        "function": {
            "name": "market_sorted_return_stocks",
            "description": "특정 기간 수익률 상위/하위 종목",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {"type": "string"},
                    "startdate": {"type": "string"},
                    "top_n": {"type": "integer"}
                },
                "required": ["region", "startdate"]
            }
        }
    },
    "market_index_similar_period": {
        "type": "function",
        "function": {
            "name": "market_index_similar_period",
            "description": "현재와 유사한 과거 시장 구간 분석",
            "parameters": {
                "type": "object",
                "properties": {"indexname": {"type": "string"}},
                "required": ["indexname"]
            }
        }
    },
    "screening_value": {
        "type": "function",
        "function": {
            "name": "screening_value",
            "description": "가치주 스크리닝 (PER, PBR, ROE 기반)",
            "parameters": {
                "type": "object",
                "properties": {"region": {"type": "string"}, "top_n": {"type": "integer"}},
                "required": ["region"]
            }
        }
    },
    "screening_growth": {
        "type": "function",
        "function": {
            "name": "screening_growth",
            "description": "성장주 스크리닝 (매출, 순이익 기반)",
            "parameters": {
                "type": "object",
                "properties": {"region": {"type": "string"}, "top_n": {"type": "integer"}},
                "required": ["region"]
            }
        }
    },
    "screening_factor": {
        "type": "function",
        "function": {
            "name": "screening_factor",
            "description": "커스텀 팩터 스크리닝",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {"type": "string"},
                    "fsitem_names": {"type": "string"},
                    "mode": {"type": "string", "enum": ["screening", "ranking"]},
                    "top_n": {"type": "integer"}
                },
                "required": ["region", "fsitem_names"]
            }
        }
    },
    "screening_dividend": {
        "type": "function",
        "function": {
            "name": "screening_dividend",
            "description": "배당주 스크리닝",
            "parameters": {
                "type": "object",
                "properties": {"region": {"type": "string"}, "top_n": {"type": "integer"}},
                "required": ["region"]
            }
        }
    },
    "backtesting": {
        "type": "function",
        "function": {
            "name": "backtesting",
            "description": "팩터 기반 백테스팅",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {"type": "string"},
                    "fsitem_names": {"type": "string"},
                    "mode": {"type": "string"},
                    "rebalance_period": {"type": "string", "enum": ["M", "Q", "S", "A"]}
                },
                "required": ["region", "rebalance_period"]
            }
        }
    },
    "guru_investors": {
        "type": "function",
        "function": {
            "name": "guru_investors",
            "description": "유명 투자자의 투자 철학 및 현재 포지션",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["philosophy", "positions"]},
                    "guru_name": {"type": "string"}
                },
                "required": ["type"]
            }
        }
    },
    "economic_indicators": {
        "type": "function",
        "function": {
            "name": "economic_indicators",
            "description": "경제지표 비교 분석 (최대 2개)",
            "parameters": {
                "type": "object",
                "properties": {
                    "indicators": {"type": "array", "items": {"type": "object"}},
                    "start_date": {"type": "string"}
                },
                "required": ["indicators", "start_date"]
            }
        }
    },
    "etf_portfolio_optimization": {
        "type": "function",
        "function": {
            "name": "etf_portfolio_optimization",
            "description": "ETF 최적 포트폴리오 배분",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_return": {"type": "string"},
                    "investment_period": {"type": "string"}
                },
                "required": ["target_return", "investment_period"]
            }
        }
    },
    "etf_taa_strategies": {
        "type": "function",
        "function": {
            "name": "etf_taa_strategies",
            "description": "ETF 전술적 자산배분 전략",
            "parameters": {
                "type": "object",
                "properties": {"strategy_name": {"type": "string"}},
                "required": []
            }
        }
    },
    "etf_performance_best_worst": {
        "type": "function",
        "function": {
            "name": "etf_performance_best_worst",
            "description": "ETF 최고/최저 성과",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {"type": "string"},
                    "startdate": {"type": "string"}
                },
                "required": ["region", "startdate"]
            }
        }
    },
    "etf_tech_themes": {
        "type": "function",
        "function": {
            "name": "etf_tech_themes",
            "description": "기업과 매칭되는 기술 테마 ETF",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"}, "region": {"type": "string"}
                },
                "required": ["ticker", "region"]
            }
        }
    },
    "etf_theme_stocks": {
        "type": "function",
        "function": {
            "name": "etf_theme_stocks",
            "description": "테마별 관련 종목 조회",
            "parameters": {
                "type": "object",
                "properties": {
                    "theme_korean": {"type": "string"},
                    "theme_english": {"type": "string"},
                    "top_n": {"type": "integer"}
                },
                "required": []
            }
        }
    },
}