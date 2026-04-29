"""
MCP 클라이언트 - Gemstone API 래퍼
gemstone.ngrok.app의 25개 금융 데이터 엔드포인트를 호출
"""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('ungdroofish.mcp_client')

# 요청 타임아웃 (초)
DEFAULT_TIMEOUT = 60.0


class GemstoneClient:
    """Gemstone 금융 API 클라이언트"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or Config.GEMSTONE_BASE_URL).rstrip('/')
        self._client = httpx.Client(timeout=DEFAULT_TIMEOUT)

    def _get(self, path: str, params: Dict = None) -> Any:
        """GET 요청"""
        url = f"{self.base_url}{path}"
        try:
            resp = self._client.get(url, params=params or {})
            resp.raise_for_status()
            return resp.json() if 'json' in resp.headers.get('content-type', '') else resp.text
        except httpx.HTTPStatusError as e:
            logger.error(f"API 오류 {path}: {e.response.status_code} - {e.response.text[:200]}")
            return {"error": str(e), "status_code": e.response.status_code}
        except Exception as e:
            logger.error(f"요청 실패 {path}: {e}")
            return {"error": str(e)}

    def _post(self, path: str, data: Dict = None) -> Any:
        """POST 요청"""
        url = f"{self.base_url}{path}"
        try:
            resp = self._client.post(url, json=data or {})
            resp.raise_for_status()
            return resp.json() if 'json' in resp.headers.get('content-type', '') else resp.text
        except httpx.HTTPStatusError as e:
            logger.error(f"API 오류 {path}: {e.response.status_code} - {e.response.text[:200]}")
            return {"error": str(e), "status_code": e.response.status_code}
        except Exception as e:
            logger.error(f"요청 실패 {path}: {e}")
            return {"error": str(e)}

    # ==================== 종목 검색 ====================

    def code_search(self, query: str, search_type: str = "ticker") -> Any:
        """티커, 산업코드, 테마 키워드 검색"""
        return self._get("/code-search/", {"query": query, "search_type": search_type})

    # ==================== 종목 분석 ====================

    def stock_analysis(self, ticker: str, region: str, analysis_type: str,
                       question: str = "", feature_item: str = "") -> Any:
        """종목 상세 분석 보고서"""
        params = {"ticker": ticker, "region": region, "analysis_type": analysis_type}
        if question:
            params["question"] = question
        if feature_item:
            params["feature_item"] = feature_item
        return self._get("/stock/analysis/", params)

    def stock_financial_data(self, ticker: str, region: str, fs_type: str = "IS",
                             period_typ: str = "A", fsitem_names: str = "",
                             startdate: str = "") -> Any:
        """종목 재무데이터 조회"""
        params = {"ticker": ticker, "region": region, "fs_type": fs_type,
                  "period_typ": period_typ}
        if fsitem_names:
            params["fsitem_names"] = fsitem_names
        if startdate:
            params["startdate"] = startdate
        return self._get("/stock/financial-data/", params)

    def stocks_financial_data(self, stocks: List[Dict], period_typ: str = "A",
                              fsitem_names: str = "", startdate: str = "") -> Any:
        """다중 종목 재무데이터"""
        data = {"stocks": stocks, "period_typ": period_typ}
        if fsitem_names:
            data["fsitem_names"] = fsitem_names
        if startdate:
            data["startdate"] = startdate
        return self._post("/stocks/financial-data/", data)

    def stock_price_history(self, ticker: str, region: str, startdate: str,
                            enddate: str = "") -> Any:
        """종목 가격 히스토리"""
        params = {"ticker": ticker, "region": region, "startdate": startdate}
        if enddate:
            params["enddate"] = enddate
        return self._get("/stock/price-history/", params)

    def stocks_price_trend(self, tickers: List[str], regions: List[str],
                           startdate: str, enddate: str = "") -> Any:
        """다중 종목 누적수익률 비교"""
        data = {"tickers": tickers, "regions": regions, "startdate": startdate}
        if enddate:
            data["enddate"] = enddate
        return self._post("/stocks/price-trend/", data)

    # ==================== 시장 분석 ====================

    def market_diagnostic(self, analysis_type: str, question: str,
                          region: str = "") -> Any:
        """시장 진단 분석"""
        params = {"analysis_type": analysis_type, "question": question}
        if region:
            params["region"] = region
        return self._get("/market/diagnostic/", params)

    def market_region_index_returns(self, region: str) -> Any:
        """지역별 지수 수익률"""
        return self._get("/market/region-index-returns/", {"region": region})

    def market_sorted_return_stocks(self, region: str, startdate: str,
                                    enddate: str = "", top_n: int = 20,
                                    sign: int = 1) -> Any:
        """수익률 순 종목 정렬"""
        params = {"region": region, "startdate": startdate, "top_n": top_n, "sign": sign}
        if enddate:
            params["enddate"] = enddate
        return self._get("/market/sorted-return-stocks/", params)

    def market_industry_stocks(self, region: str, hierarchicalid: str) -> Any:
        """산업별 종목 조회"""
        return self._get("/market/industry-stocks/",
                         {"region": region, "hierarchicalid": hierarchicalid})

    def market_index_value_history(self, indexname: str, data_type: str,
                                   startdate: str, enddate: str = "") -> Any:
        """주가지수 시계열"""
        params = {"indexname": indexname, "data_type": data_type, "startdate": startdate}
        if enddate:
            params["enddate"] = enddate
        return self._get("/market/stock-index/value-history/", params)

    def market_index_similar_period(self, indexname: str) -> Any:
        """현재와 유사한 과거 구간 분석"""
        return self._get("/market/index-similar-period-analysis/",
                         {"indexname": indexname})

    def market_styles_recommendations(self, region: str, styles: List[str],
                                      top_n: int = 20) -> Any:
        """스타일 기반 종목 추천"""
        return self._post("/market/styles-recommendations/",
                          {"region": region, "styles": styles, "top_n": top_n})

    # ==================== 스크리닝 & 백테스팅 ====================

    def screening_stocks(self, region: str, fsitem_names: str, mode: str = "ranking",
                         top_n: int = 20, **kwargs) -> Any:
        """종목 스크리닝/랭킹"""
        params = {"region": region, "fsitem_names": fsitem_names, "mode": mode,
                  "top_n": top_n}
        params.update(kwargs)
        return self._get("/screening-stocks/", params)

    def backtesting(self, region: str, mode: str, rebalance_period: str,
                    fsitem_names: str = "", **kwargs) -> Any:
        """팩터 백테스팅"""
        params = {"region": region, "mode": mode, "rebalance_period": rebalance_period}
        if fsitem_names:
            params["fsitem_names"] = fsitem_names
        params.update(kwargs)
        return self._get("/backtesting/", params)

    # ==================== 구루 투자자 ====================

    def guru_investors(self, type: str = "philosophy", guru_name: str = "") -> Any:
        """구루 투자자 철학 및 포지션"""
        params = {"type": type}
        if guru_name:
            params["guru_name"] = guru_name
        return self._get("/guru-investors/", params)

    # ==================== ETF ====================

    def etf_portfolio_optimization(self, target_return: str,
                                   investment_period: str) -> Any:
        """ETF 포트폴리오 최적화"""
        return self._get("/etf/portfolio-optimization/",
                         {"target_return": target_return,
                          "investment_period": investment_period})

    def etf_taa_strategies(self, strategy_name: str = "all",
                           data_type: str = "all") -> Any:
        """ETF TAA 전략"""
        return self._get("/etf/taa-strategies/",
                         {"strategy_name": strategy_name, "data_type": data_type})

    def etf_performance_best_worst(self, region: str, startdate: str,
                                   ntop: int = 5) -> Any:
        """ETF 최고/최저 성과"""
        return self._get("/etf/performance-best-worst/",
                         {"region": region, "startdate": startdate, "ntop": ntop})

    def etf_tech_themes_matching(self, ticker: str, region: str,
                                 top_n: int = 5) -> Any:
        """기업 비즈니스와 매칭되는 ETF 테마"""
        return self._get("/etf/tech-themes-matching/",
                         {"ticker": ticker, "region": region, "top_n": top_n})

    def etf_theme_stocks(self, theme_korean: str = "", theme_english: str = "",
                         top_n: int = 20, region: str = "") -> Any:
        """테마별 관련 종목"""
        params = {"top_n": top_n}
        if theme_korean:
            params["theme_korean"] = theme_korean
        if theme_english:
            params["theme_english"] = theme_english
        if region:
            params["region"] = region
        return self._get("/etf/theme-stocks/", params)

    # ==================== 경제지표 ====================

    def economic_indicators(self, indicators: List[Dict], start_date: str,
                            end_date: str = "") -> Any:
        """경제지표 비교 (최대 2개)"""
        data = {"indicators": indicators, "start_date": start_date}
        if end_date:
            data["end_date"] = end_date
        return self._post("/market/economic-indicators/", data)

    # ==================== 포트폴리오 ====================

    def user_portfolio(self, user_id: str, action: str,
                       portfolio: List[Dict] = None,
                       user_name: str = "") -> Any:
        """포트폴리오 업데이트/분석"""
        data = {"user_id": user_id, "action": action}
        if portfolio:
            data["portfolio"] = portfolio
        if user_name:
            data["user_name"] = user_name
        return self._post("/user/portfolio/", data)

    # ==================== 차트 ====================

    def chart_time_series(self, series: List[Dict], title: str = "",
                          chart_type: str = "line") -> Any:
        """시계열 차트 생성 (base64 PNG 반환)"""
        return self._post("/chart/time-series/",
                          {"series": series, "title": title, "chart_type": chart_type})

    # ==================== 유틸리티 ====================

    def available_fsitem_list(self) -> Any:
        """사용 가능한 재무제표 항목 목록"""
        return self._get("/available-fsitem-list/")

    def close(self):
        """HTTP 클라이언트 종료"""
        self._client.close()