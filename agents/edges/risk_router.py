"""위험도 기반 조건부 라우팅"""
from __future__ import annotations

import logging

from agents.state import AgentState

logger = logging.getLogger(__name__)


def route_by_risk(state: AgentState) -> str:
    """
    위험도 레벨에 따른 라우팅 결정.

    - high/critical → "recommendation_node" (즉시 의료 상담 권고 포함)
    - low/moderate → "recommendation_node" (일반 권고)

    현재는 동일 노드로 라우팅하되, risk_node 결과에 따라
    recommendation_node 내부에서 경고 문구가 달라짐.
    향후 critical 시 별도 emergency_node 분기 가능.
    """
    risk = state.get("risk_assessment")
    if risk and risk.level in ("high", "critical"):
        logger.info("위험도 라우팅: high/critical → 긴급 권고 모드")
        return "recommendation_node"

    logger.info("위험도 라우팅: low/moderate → 일반 권고 모드")
    return "recommendation_node"
