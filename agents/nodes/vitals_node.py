"""생체신호 평가 노드 — 정상 범위 비교 + LLM 해석"""
from __future__ import annotations

import logging
from pathlib import Path

from agents.state import AgentState
from models.llm_client import LLMClient
from utils.config_loader import get_vitals_reference

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "vitals_evaluation.md"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return "당신은 생체신호 평가 전문가입니다. 환자의 생체신호를 분석해주세요."


def _evaluate_vitals(vitals) -> str:
    """생체신호를 정상 범위와 비교하여 평가 텍스트 생성"""
    ref = get_vitals_reference()
    findings = []

    # 심박수
    hr_ref = ref.get("heart_rate", {}).get("normal", {})
    hr_min, hr_max = hr_ref.get("min", 60), hr_ref.get("max", 100)
    if vitals.heart_rate < hr_min:
        findings.append(f"심박수 {vitals.heart_rate}bpm — 서맥 (정상: {hr_min}-{hr_max})")
    elif vitals.heart_rate > hr_max:
        findings.append(f"심박수 {vitals.heart_rate}bpm — 빈맥 (정상: {hr_min}-{hr_max})")
    else:
        findings.append(f"심박수 {vitals.heart_rate}bpm — 정상 범위")

    # 혈압
    sys_ref = ref.get("blood_pressure", {}).get("systolic", {}).get("normal", {})
    dia_ref = ref.get("blood_pressure", {}).get("diastolic", {}).get("normal", {})
    sys_max = sys_ref.get("max", 120)
    dia_max = dia_ref.get("max", 80)

    bp_str = f"{vitals.blood_pressure_sys}/{vitals.blood_pressure_dia}mmHg"
    if vitals.blood_pressure_sys > 140 or vitals.blood_pressure_dia > 90:
        findings.append(f"혈압 {bp_str} — 고혈압 (정상: ~{sys_max}/{dia_max})")
    elif vitals.blood_pressure_sys < 90:
        findings.append(f"혈압 {bp_str} — 저혈압")
    else:
        findings.append(f"혈압 {bp_str} — 정상 범위")

    # 체온
    temp_ref = ref.get("body_temperature", {}).get("normal", {})
    temp_min, temp_max = temp_ref.get("min", 36.1), temp_ref.get("max", 37.2)
    if vitals.body_temperature > 38.0:
        findings.append(f"체온 {vitals.body_temperature}°C — 발열 (정상: {temp_min}-{temp_max})")
    elif vitals.body_temperature < 35.0:
        findings.append(f"체온 {vitals.body_temperature}°C — 저체온 (정상: {temp_min}-{temp_max})")
    else:
        findings.append(f"체온 {vitals.body_temperature}°C — 정상 범위")

    return "\n".join(findings)


def vitals_node(state: AgentState) -> dict:
    """
    생체신호 평가 노드.

    정상 범위와 비교한 후 LLM으로 의학적 해석 생성.
    """
    vitals = state.get("vitals")
    if vitals is None:
        return {"vitals_evaluation": "생체신호 데이터가 제공되지 않았습니다."}

    logger.info("생체신호 평가 시작: HR=%d, BP=%d/%d, T=%.1f",
                vitals.heart_rate, vitals.blood_pressure_sys,
                vitals.blood_pressure_dia, vitals.body_temperature)

    eval_text = _evaluate_vitals(vitals)

    user_prompt = (
        f"환자 생체신호 평가:\n{eval_text}\n\n"
        f"위 생체신호를 종합적으로 평가하고, 이상 소견이 있다면 가능한 원인과 주의사항을 설명해주세요."
    )

    try:
        llm = LLMClient()
        system_prompt = _load_prompt()
        evaluation = llm.generate(user_prompt, system_prompt=system_prompt)
        logger.info("생체신호 평가 완료: %d자", len(evaluation))
        return {"vitals_evaluation": evaluation}
    except Exception as e:
        error_msg = f"생체신호 평가 중 오류가 발생했습니다: {e}"
        logger.error(error_msg)
        return {"vitals_evaluation": error_msg}
