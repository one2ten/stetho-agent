"""LangGraph 에이전트 상태 정의"""
from __future__ import annotations

from typing import Literal, Optional

from typing_extensions import TypedDict

from schemas.auscultation import AuscultationResult
from schemas.literature import LiteratureSearchResult
from schemas.report import RiskAssessment
from schemas.symptoms import SymptomInput
from schemas.vitals import VitalSigns


class AgentState(TypedDict, total=False):
    """
    LangGraph 에이전트 공유 상태.

    입력, 중간 분석 결과, 최종 출력을 모두 포함.
    total=False로 설정하여 부분 업데이트 가능.
    """

    # === 입력 ===
    vitals: VitalSigns
    symptoms: SymptomInput
    auscultation: Optional[AuscultationResult]
    user_mode: Literal["general", "professional"]

    # === 중간 분석 결과 ===
    auscultation_analysis: Optional[str]
    vitals_evaluation: Optional[str]
    symptom_analysis: Optional[str]

    # === 종합 및 위험도 ===
    synthesis: Optional[str]
    risk_assessment: Optional[RiskAssessment]

    # === 최종 출력 ===
    recommendation: Optional[str]
    literature_references: Optional[LiteratureSearchResult]
