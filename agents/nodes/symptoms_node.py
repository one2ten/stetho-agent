"""증상 분석 노드 — 증상 패턴을 LLM으로 분석"""
from __future__ import annotations

import logging
from pathlib import Path

from agents.state import AgentState
from models.llm_client import LLMClient

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "symptom_analysis.md"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return "당신은 증상 분석 전문가입니다. 환자의 증상을 분석해주세요."


def symptoms_node(state: AgentState) -> dict:
    """
    증상 분석 노드.

    자유텍스트 + 체크리스트 + 기간 + 강도를 종합하여 LLM 분석.
    """
    symptoms = state.get("symptoms")
    if symptoms is None:
        return {"symptom_analysis": "증상 데이터가 제공되지 않았습니다."}

    logger.info("증상 분석 시작: checklist=%d개, severity=%s", len(symptoms.checklist), symptoms.severity)

    checklist_str = ", ".join(symptoms.checklist) if symptoms.checklist else "선택 없음"

    user_prompt = (
        f"환자 증상 정보:\n"
        f"- 증상 설명: {symptoms.free_text}\n"
        f"- 선택 증상: {checklist_str}\n"
        f"- 지속 기간: {symptoms.duration}\n"
        f"- 강도: {symptoms.severity}\n\n"
        f"위 증상들을 종합 분석하고, 의심되는 호흡기/심혈관 관련 소견을 설명해주세요."
    )

    try:
        llm = LLMClient()
        system_prompt = _load_prompt()
        analysis = llm.generate(user_prompt, system_prompt=system_prompt)
        logger.info("증상 분석 완료: %d자", len(analysis))
        return {"symptom_analysis": analysis}
    except Exception as e:
        error_msg = f"증상 분석 중 오류가 발생했습니다: {e}"
        logger.error(error_msg)
        return {"symptom_analysis": error_msg}
