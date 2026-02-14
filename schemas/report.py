"""위험도 평가 및 분석 리포트 스키마"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RiskAssessment(BaseModel):
    """위험도 평가 스키마"""

    level: Literal["low", "moderate", "high", "critical"] = Field(
        description="위험도 레벨",
    )
    score: float = Field(
        ge=0.0,
        le=100.0,
        description="위험도 점수 (0-100)",
    )
    factors: list[str] = Field(
        default_factory=list,
        description="위험 요인 목록",
    )
    immediate_action_needed: bool = Field(
        default=False,
        description="즉시 조치 필요 여부",
    )


class AnalysisReport(BaseModel):
    """최종 분석 리포트 스키마"""

    timestamp: datetime = Field(default_factory=datetime.now)
    auscultation_analysis: Optional[str] = None
    vitals_evaluation: Optional[str] = None
    symptom_analysis: Optional[str] = None
    risk_assessment: Optional[RiskAssessment] = None
    synthesis: Optional[str] = None
    recommendation: Optional[str] = None
    user_mode: Literal["general", "professional"] = "general"
    disclaimer: str = "⚠️ 본 분석 결과는 AI 기반 참고 정보이며 의료 진단이 아닙니다."
