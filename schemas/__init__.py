"""Pydantic 데이터 스키마 패키지"""
from __future__ import annotations

from schemas.vitals import VitalSigns
from schemas.symptoms import SymptomInput, SYMPTOM_OPTIONS, DURATION_OPTIONS, SEVERITY_OPTIONS
from schemas.auscultation import AuscultationResult, AUSCULTATION_CLASSES
from schemas.report import RiskAssessment, AnalysisReport
from schemas.literature import MedicalReference, LiteratureSearchResult

__all__ = [
    "VitalSigns",
    "SymptomInput",
    "SYMPTOM_OPTIONS",
    "DURATION_OPTIONS",
    "SEVERITY_OPTIONS",
    "AuscultationResult",
    "AUSCULTATION_CLASSES",
    "RiskAssessment",
    "AnalysisReport",
    "MedicalReference",
    "LiteratureSearchResult",
]
