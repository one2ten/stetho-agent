"""입력 검증 노드 — 사용자 입력을 검증하고 디폴트 적용"""
from __future__ import annotations

import logging

from agents.state import AgentState
from schemas.symptoms import SymptomInput
from schemas.vitals import VitalSigns

logger = logging.getLogger(__name__)


def input_validator(state: AgentState) -> dict:
    """
    입력 데이터를 검증하고 디폴트 값을 적용.

    - VitalSigns / SymptomInput 없으면 디폴트 생성
    - user_mode 없으면 "general"
    - 중간 분석 필드 초기화
    """
    logger.info("입력 검증 시작")

    vitals = state.get("vitals") or VitalSigns()
    symptoms = state.get("symptoms") or SymptomInput()
    user_mode = state.get("user_mode", "general")
    auscultation = state.get("auscultation")

    logger.info(
        "입력 검증 완료: vitals=HR%d, symptoms=%d개, mode=%s, audio=%s",
        vitals.heart_rate,
        len(symptoms.checklist),
        user_mode,
        "있음" if auscultation else "없음",
    )

    return {
        "vitals": vitals,
        "symptoms": symptoms,
        "user_mode": user_mode,
        "auscultation": auscultation,
    }
