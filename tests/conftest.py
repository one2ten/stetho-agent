"""pytest 공통 픽스처"""
from __future__ import annotations

import pytest

from schemas.vitals import VitalSigns
from schemas.symptoms import SymptomInput
from schemas.auscultation import AuscultationResult
from schemas.report import RiskAssessment, AnalysisReport
from schemas.literature import MedicalReference, LiteratureSearchResult


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
            "Crackle": 0.08,
            "Wheeze": 0.05,
            "Both": 0.02,
        },
    )


@pytest.fixture
def sample_literature_result() -> LiteratureSearchResult:
    """샘플 문헌 검색 결과 픽스처"""
    return LiteratureSearchResult(
        query="pulmonary crackles cough dyspnea",
        total_count=2,
        references=[
            MedicalReference(
                source="pubmed",
                source_id="12345678",
                title="Lung Crackles: Classification and Clinical Significance",
                authors=["Smith J", "Kim S"],
                journal="Respiratory Medicine",
                year="2023",
                url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
                relevance_score=1.0,
            ),
            MedicalReference(
                source="pubmed",
                source_id="87654321",
                title="Auscultation Findings and Pulmonary Function",
                authors=["Lee Y", "Park J", "Choi H"],
                journal="Chest",
                year="2024",
                url="https://pubmed.ncbi.nlm.nih.gov/87654321/",
                relevance_score=0.75,
            ),
        ],
        sources_used=["pubmed"],
        search_successful=True,
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
