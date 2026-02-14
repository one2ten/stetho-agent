"""pytest 공통 픽스처"""
from __future__ import annotations

import pytest

from schemas.vitals import VitalSigns
from schemas.symptoms import SymptomInput
from schemas.auscultation import AuscultationResult
from schemas.report import RiskAssessment, AnalysisReport


@pytest.fixture
def default_vitals() -> VitalSigns:
    """디폴트 생체신호 픽스처"""
    return VitalSigns()


@pytest.fixture
def default_symptoms() -> SymptomInput:
    """디폴트 증상 입력 픽스처"""
    return SymptomInput()


@pytest.fixture
def sample_auscultation() -> AuscultationResult:
    """샘플 청진음 분류 결과 픽스처"""
    return AuscultationResult(
        file_name="sample.wav",
        classification="Normal",
        confidence=0.85,
        probabilities={
            "Normal": 0.85,
            "Murmur": 0.07,
            "Extrahls": 0.04,
            "Artifact": 0.02,
            "Extrastole": 0.02,
        },
    )


@pytest.fixture
def sample_risk_assessment() -> RiskAssessment:
    """샘플 위험도 평가 픽스처"""
    return RiskAssessment(
        level="low",
        score=15.0,
        factors=["경미한 기침"],
        immediate_action_needed=False,
    )
