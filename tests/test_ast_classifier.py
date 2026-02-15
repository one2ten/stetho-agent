"""AST 청진음 분류기 테스트"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from schemas.auscultation import AUSCULTATION_CLASSES, AuscultationResult


SAMPLE_WAV = Path(__file__).resolve().parent.parent / "sample" / "sample.wav"


class TestAuscultationClasses:
    """분류 클래스 정의 테스트"""

    def test_4클래스_정의(self):
        """4-class 분류 클래스가 올바르게 정의되었는지 확인"""
        assert len(AUSCULTATION_CLASSES) == 4
        assert "Normal" in AUSCULTATION_CLASSES
        assert "Crackle" in AUSCULTATION_CLASSES
        assert "Wheeze" in AUSCULTATION_CLASSES
        assert "Both" in AUSCULTATION_CLASSES


class TestASTClassifierUnit:
    """ASTClassifier 단위 테스트 (모델 로딩 없이)"""

    def test_결과_스키마_생성(self):
        """AuscultationResult 스키마 생성 확인"""
        result = AuscultationResult(
            file_name="test.wav",
            classification="Normal",
            confidence=0.85,
            probabilities={
                "Normal": 0.85,
                "Crackle": 0.08,
                "Wheeze": 0.05,
                "Both": 0.02,
            },
        )
        assert result.classification == "Normal"
        assert result.confidence == 0.85
        assert len(result.probabilities) == 4

    def test_확률_합계(self):
        """확률 합계가 약 1.0인지 확인"""
        probs = {"Normal": 0.85, "Crackle": 0.08, "Wheeze": 0.05, "Both": 0.02}
        assert abs(sum(probs.values()) - 1.0) < 0.01

    def test_모든_클래스_포함(self):
        """모든 4개 클래스가 결과에 포함되는지 확인"""
        probs = {"Normal": 0.7, "Crackle": 0.15, "Wheeze": 0.1, "Both": 0.05}
        for cls in AUSCULTATION_CLASSES:
            assert cls in probs


@pytest.mark.slow
class TestASTClassifierIntegration:
    """ASTClassifier 통합 테스트 (모델 로딩 포함)"""

    @pytest.fixture(autouse=True)
    def _check_sample(self):
        """샘플 파일 존재 여부 확인"""
        if not SAMPLE_WAV.exists():
            pytest.skip("샘플 WAV 파일 없음")

    def test_모델_로딩(self):
        """AST 모델이 정상적으로 로딩되는지 확인"""
        from models.ast_classifier import ASTClassifier

        classifier = ASTClassifier()
        assert classifier.model is not None
        assert classifier.feature_extractor is not None

    def test_분류_실행(self):
        """샘플 오디오 분류 실행 확인"""
        from models.ast_classifier import ASTClassifier

        classifier = ASTClassifier()
        result = classifier.classify(str(SAMPLE_WAV))

        assert isinstance(result, AuscultationResult)
        assert result.file_name == "sample.wav"
        assert result.classification in AUSCULTATION_CLASSES
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.probabilities) == 4
        # 확률 합계 약 1.0
        assert abs(sum(result.probabilities.values()) - 1.0) < 0.01

    def test_분류_결과_4클래스(self):
        """분류 결과가 4개 클래스를 모두 포함하는지 확인"""
        from models.ast_classifier import ASTClassifier

        classifier = ASTClassifier()
        result = classifier.classify(str(SAMPLE_WAV))

        for cls in AUSCULTATION_CLASSES:
            assert cls in result.probabilities
