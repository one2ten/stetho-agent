"""위험도 평가 노드 — 휴리스틱 점수 + LLM CoT 추론 병합"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from agents.state import AgentState
from models.llm_client import LLMClient
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

_RISK_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "risk_reasoning.md"


def _load_risk_prompt() -> str:
    """위험도 추론 프롬프트 로딩"""
    if _RISK_PROMPT_PATH.exists():
        return _RISK_PROMPT_PATH.read_text(encoding="utf-8")
    return "위험도를 low, moderate, high, critical 중 하나로 판단하세요."


def _calculate_heuristic_risk(state: AgentState) -> RiskAssessment:
    """
    휴리스틱 위험도 산정 (빠른 기본 평가).

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
            break

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


def _llm_risk_reasoning(state: AgentState) -> tuple[str, str | None]:
    """
    LLM 기반 CoT 위험도 추론 (보조 평가).

    Returns:
        (추론 텍스트, LLM 제안 레벨 또는 None)
    """
    try:
        vitals = state.get("vitals")
        auscultation = state.get("auscultation")
        symptoms = state.get("symptoms")
        synthesis = state.get("synthesis", "")

        # 컨텍스트 구성
        context_parts = []
        if vitals:
            context_parts.append(
                f"생체신호: HR={vitals.heart_rate}bpm, "
                f"BP={vitals.blood_pressure_sys}/{vitals.blood_pressure_dia}mmHg, "
                f"T={vitals.body_temperature}°C"
            )
        if auscultation:
            context_parts.append(f"청진음: {auscultation.classification} (신뢰도: {auscultation.confidence:.0%})")
        if symptoms:
            context_parts.append(f"증상: {', '.join(symptoms.checklist)}, 강도: {symptoms.severity}")
        if synthesis:
            context_parts.append(f"종합 판단 요약: {synthesis[:300]}")

        user_prompt = "\n".join(context_parts)

        llm = LLMClient()
        system_prompt = _load_risk_prompt()
        response = llm.generate(user_prompt, system_prompt=system_prompt)

        # JSON 파싱 시도
        llm_level = None
        reasoning_text = response
        try:
            # JSON 블록 추출
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(response[json_start:json_end])
                reasoning_text = parsed.get("reasoning", response)
                llm_level = parsed.get("level")
                if llm_level not in ("low", "moderate", "high", "critical"):
                    llm_level = None
        except (json.JSONDecodeError, KeyError):
            pass

        logger.info("LLM 위험도 추론 완료: level=%s", llm_level)
        return reasoning_text, llm_level

    except Exception as e:
        logger.warning("LLM 위험도 추론 실패 (휴리스틱 사용): %s", e)
        return "", None


def risk_node(state: AgentState) -> dict:
    """
    위험도 평가 노드 (휴리스틱 + LLM CoT 병합).

    1단계: 휴리스틱 점수 기반 빠른 평가
    2단계: LLM CoT 추론으로 맥락 기반 보정
    3단계: 두 결과를 병합하여 최종 위험도 결정
    """
    logger.info("위험도 평가 시작 (휴리스틱 + CoT)")

    # 1단계: 휴리스틱 평가
    heuristic_risk = _calculate_heuristic_risk(state)
    reasoning_trace = list(state.get("reasoning_trace") or [])
    reasoning_trace.append(
        f"[사고] 휴리스틱 위험도 평가: {heuristic_risk.level} ({heuristic_risk.score:.0f}점), "
        f"요인: {', '.join(heuristic_risk.factors)}"
    )

    # 2단계: LLM CoT 추론
    llm_reasoning, llm_level = _llm_risk_reasoning(state)
    if llm_reasoning:
        reasoning_trace.append(f"[사고] LLM 위험도 추론: {llm_reasoning[:200]}")

    # 3단계: 병합 — LLM이 더 높은 위험도를 제안하면 상향 조정
    final_risk = heuristic_risk
    level_order = {"low": 0, "moderate": 1, "high": 2, "critical": 3}

    if llm_level and level_order.get(llm_level, 0) > level_order.get(heuristic_risk.level, 0):
        reasoning_trace.append(
            f"[행동] LLM이 더 높은 위험도({llm_level})를 제안하여 상향 조정합니다."
        )
        final_risk = RiskAssessment(
            level=llm_level,
            score=max(heuristic_risk.score, level_order[llm_level] * 25 + 10),
            factors=heuristic_risk.factors,
            immediate_action_needed=llm_level in ("high", "critical"),
        )

    reasoning_trace.append(
        f"[결론] 최종 위험도: {final_risk.level} ({final_risk.score:.0f}점)"
    )

    logger.info("위험도 평가 완료: level=%s, score=%.0f", final_risk.level, final_risk.score)
    return {
        "risk_assessment": final_risk,
        "reasoning_trace": reasoning_trace,
    }
