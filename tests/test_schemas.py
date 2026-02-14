"""Pydantic 스키마 디폴트 값 및 유효성 검사 테스트"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas.vitals import VitalSigns
from schemas.symptoms import SymptomInput, SYMPTOM_OPTIONS, DURATION_OPTIONS, SEVERITY_OPTIONS
from schemas.auscultation import AuscultationResult, AUSCULTATION_CLASSES
from schemas.report import RiskAssessment, AnalysisReport


class TestVitalSigns:
    """VitalSigns 스키마 테스트"""

    def test_디폴트_값_생성(self):
        """디폴트 값으로 인스턴스 생성 확인"""
        vitals = VitalSigns()
        assert vitals.heart_rate == 75
        assert vitals.blood_pressure_sys == 120
        assert vitals.blood_pressure_dia == 80
        assert vitals.body_temperature == 36.5

    def test_커스텀_값_생성(self):
        """커스텀 값으로 인스턴스 생성 확인"""
        vitals = VitalSigns(
            heart_rate=90,
            blood_pressure_sys=130,
            blood_pressure_dia=85,
            body_temperature=37.2,
        )
        assert vitals.heart_rate == 90
        assert vitals.blood_pressure_sys == 130

    def test_심박수_범위_초과(self):
        """심박수 유효 범위 초과 시 ValidationError"""
        with pytest.raises(ValidationError):
            VitalSigns(heart_rate=300)

    def test_심박수_범위_미만(self):
        """심박수 유효 범위 미만 시 ValidationError"""
        with pytest.raises(ValidationError):
            VitalSigns(heart_rate=10)

    def test_체온_범위_초과(self):
        """체온 유효 범위 초과 시 ValidationError"""
        with pytest.raises(ValidationError):
            VitalSigns(body_temperature=50.0)

    def test_혈압_범위_검증(self):
        """혈압 유효 범위 검증"""
        with pytest.raises(ValidationError):
            VitalSigns(blood_pressure_sys=400)
        with pytest.raises(ValidationError):
            VitalSigns(blood_pressure_dia=10)


class TestSymptomInput:
    """SymptomInput 스키마 테스트"""

    def test_디폴트_값_생성(self):
        """디폴트 값으로 인스턴스 생성 확인"""
        symptoms = SymptomInput()
        assert "기침" in symptoms.free_text
        assert "기침" in symptoms.checklist
        assert "호흡곤란" in symptoms.checklist
        assert symptoms.duration == "3-7일"
        assert symptoms.severity == "경미"

    def test_커스텀_자유텍스트_입력(self):
        """사용자가 자유롭게 작성한 증상 텍스트 확인"""
        symptoms = SymptomInput(
            free_text="밤에 누우면 숨이 차고 가슴에서 쌕쌕 소리가 납니다",
            checklist=["야간 호흡곤란", "천명음(쌕쌕거림)"],
            duration="1-2주",
            severity="심함",
        )
        assert "숨이 차고" in symptoms.free_text
        assert "야간 호흡곤란" in symptoms.checklist

    def test_증상_강도_잘못된_값(self):
        """허용되지 않는 증상 강도 값 시 ValidationError"""
        with pytest.raises(ValidationError):
            SymptomInput(severity="극심함")

    def test_증상_옵션_목록(self):
        """폐/심장 관련 증상 옵션이 올바르게 정의되었는지 확인"""
        assert len(SYMPTOM_OPTIONS) == 12
        assert "기침" in SYMPTOM_OPTIONS
        assert "호흡곤란" in SYMPTOM_OPTIONS
        assert "천명음(쌕쌕거림)" in SYMPTOM_OPTIONS
        assert "객혈(피 섞인 가래)" in SYMPTOM_OPTIONS

    def test_기간_옵션_목록(self):
        """기간 옵션 목록 확인"""
        assert len(DURATION_OPTIONS) == 5

    def test_강도_옵션_목록(self):
        """강도 옵션 목록 확인"""
        assert len(SEVERITY_OPTIONS) == 4


class TestAuscultationResult:
    """AuscultationResult 스키마 테스트"""

    def test_정상_생성(self, sample_auscultation):
        """정상적인 청진음 결과 생성 확인"""
        assert sample_auscultation.file_name == "sample.wav"
        assert sample_auscultation.classification == "Normal"
        assert sample_auscultation.confidence == 0.85

    def test_확률_합계_검증(self, sample_auscultation):
        """확률 합계가 약 1.0인지 확인"""
        total = sum(sample_auscultation.probabilities.values())
        assert abs(total - 1.0) < 0.01

    def test_신뢰도_범위(self):
        """신뢰도 범위 (0-1) 검증"""
        with pytest.raises(ValidationError):
            AuscultationResult(
                file_name="test.wav",
                classification="Normal",
                confidence=1.5,
                probabilities={"Normal": 1.0},
            )

    def test_분류_클래스_목록(self):
        """분류 클래스 5개 확인"""
        assert len(AUSCULTATION_CLASSES) == 5
        assert "Normal" in AUSCULTATION_CLASSES

    def test_스펙트로그램_경로_기본값(self, sample_auscultation):
        """스펙트로그램 경로 기본값 None 확인"""
        assert sample_auscultation.spectrogram_path is None


class TestRiskAssessment:
    """RiskAssessment 스키마 테스트"""

    def test_정상_생성(self, sample_risk_assessment):
        """정상적인 위험도 평가 생성 확인"""
        assert sample_risk_assessment.level == "low"
        assert sample_risk_assessment.score == 15.0
        assert sample_risk_assessment.immediate_action_needed is False

    def test_위험도_레벨_검증(self):
        """허용되지 않는 위험도 레벨 시 ValidationError"""
        with pytest.raises(ValidationError):
            RiskAssessment(level="unknown", score=50.0)

    def test_점수_범위_검증(self):
        """위험도 점수 범위 (0-100) 검증"""
        with pytest.raises(ValidationError):
            RiskAssessment(level="low", score=150.0)

    def test_긴급_조치_필요(self):
        """긴급 조치가 필요한 위험도 생성"""
        risk = RiskAssessment(
            level="critical",
            score=95.0,
            factors=["매우 높은 혈압", "심한 호흡곤란"],
            immediate_action_needed=True,
        )
        assert risk.immediate_action_needed is True
        assert len(risk.factors) == 2


class TestAnalysisReport:
    """AnalysisReport 스키마 테스트"""

    def test_디폴트_값_생성(self):
        """디폴트 값으로 리포트 생성 확인"""
        report = AnalysisReport()
        assert report.user_mode == "general"
        assert "의료 진단이 아닙니다" in report.disclaimer
        assert report.timestamp is not None

    def test_면책조항_포함(self):
        """면책 조항이 반드시 포함되어 있는지 확인"""
        report = AnalysisReport()
        assert "⚠️" in report.disclaimer

    def test_전문가_모드(self):
        """전문가 모드 설정 확인"""
        report = AnalysisReport(user_mode="professional")
        assert report.user_mode == "professional"
