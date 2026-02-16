"""위험도 평가 노드 — 종합 판단에서 위험도 레벨/점수 산정"""
from __future__ import annotations

import logging
import re

from agents.state import AgentState
from schemas.report import RiskAssessment
from utils.config_loader import get_vitals_reference

logger = logging.getLogger(__name__)

# 위험도 키워드 매핑
HIGH_RISK_KEYWORDS = [
    "즉시", "응급", "긴급", "위험", "심각", "critical", "emergency",
    "폐렴", "심부전", "폐색전", "기흉", "급성",
]
MODERATE_RISK_KEYWORDS = [
    "주의", "관찰", "추적", "검사 필요", "의료 상담", "moderate",
    "만성", "악화", "지속",
]


def _calculate_risk(state: AgentState) -> RiskAssessment:
    """
    종합 분석 결과와 입력값으로 위험도 산정.

    점수 산정 기준:
    - 비정상 생체신호: +15점씩
    - 비정상 청진음: +20점 (Crackle/Wheeze/Both)
    - 증상 강도(심함/매우심함): +15점
    - 종합 판단 텍스트 키워드: +10~20점
    """
    score = 0.0
    factors: list[str] = []

    # 1. 생체신호 이상
    vitals = state.get("vitals")
    if vitals:
        ref = get_vitals_reference()
        hr_ref = ref.get("heart_rate", {}).get("normal", {})

        if vitals.heart_rate > hr_ref.get("max", 100):
            score += 15
            factors.append(f"빈맥 ({vitals.heart_rate}bpm)")
        elif vitals.heart_rate < hr_ref.get("min", 60):
            score += 15
            factors.append(f"서맥 ({vitals.heart_rate}bpm)")

        if vitals.blood_pressure_sys > 140:
            score += 15
            factors.append(f"고혈압 ({vitals.blood_pressure_sys}/{vitals.blood_pressure_dia})")
        elif vitals.blood_pressure_sys < 90:
            score += 15
            factors.append(f"저혈압 ({vitals.blood_pressure_sys}/{vitals.blood_pressure_dia})")

        if vitals.body_temperature > 38.0:
            score += 15
            factors.append(f"발열 ({vitals.body_temperature}°C)")

    # 2. 청진음 이상
    auscultation = state.get("auscultation")
    if auscultation and auscultation.classification != "Normal":
        score += 20
        factors.append(f"비정상 청진음 ({auscultation.classification})")

    # 3. 증상 강도
    symptoms = state.get("symptoms")
    if symptoms:
        if symptoms.severity in ("심함", "매우 심함"):
            score += 15
            factors.append(f"증상 강도: {symptoms.severity}")

    # 4. 종합 판단 텍스트 키워드 분석
    synthesis = state.get("synthesis", "")
    synthesis_lower = synthesis.lower()

    for kw in HIGH_RISK_KEYWORDS:
        if kw in synthesis_lower:
            score += 10
            break  # 중복 방지

    for kw in MODERATE_RISK_KEYWORDS:
        if kw in synthesis_lower:
            score += 5
            break

    # 점수 범위 제한
    score = min(score, 100.0)

    # 레벨 결정
    if score >= 75:
        level = "critical"
    elif score >= 50:
        level = "high"
    elif score >= 25:
        level = "moderate"
    else:
        level = "low"

    immediate_action = level in ("high", "critical")

    if not factors:
        factors = ["특이 소견 없음"]

    return RiskAssessment(
        level=level,
        score=score,
        factors=factors,
        immediate_action_needed=immediate_action,
    )


def risk_node(state: AgentState) -> dict:
    """
    위험도 평가 노드.

    생체신호, 청진음, 증상, 종합 판단을 기반으로 위험도 산정.
    """
    logger.info("위험도 평가 시작")
    risk = _calculate_risk(state)
    logger.info("위험도 평가 완료: level=%s, score=%.0f", risk.level, risk.score)
    return {"risk_assessment": risk}
