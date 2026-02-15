"""AST 청진음 분류기 모듈 — HuggingFace AST 모델 기반 4-class 분류"""
from __future__ import annotations

import logging

import numpy as np
import torch
from transformers import ASTFeatureExtractor, ASTForAudioClassification

from models.audio_preprocessor import AudioPreprocessor
from schemas.auscultation import AUSCULTATION_CLASSES, AuscultationResult
from utils.config_loader import get_ast_config
from utils.device_utils import get_device

logger = logging.getLogger(__name__)


class ASTClassifier:
    """
    HuggingFace AST 기반 청진음 분류기.

    - MIT/ast-finetuned-audioset-10-10-0.4593 모델 사용
    - AudioSet 527 클래스 출력 → 4-class (Normal, Crackle, Wheeze, Both) 매핑
    - MPS 디바이스 우선, CPU 폴백
    """

    # AudioSet 레이블 → 폐 청진음 매핑
    # 참고: AudioSet 527개 클래스 중 관련 레이블 ID 사용
    CRACKLE_KEYWORDS = ["crackle", "crack", "static", "fire"]
    WHEEZE_KEYWORDS = ["wheeze", "whistle", "squeal", "hiss"]
    NORMAL_KEYWORDS = ["breathing", "silence", "white noise"]

    def __init__(self) -> None:
        config = get_ast_config()
        model_config = config.get("model", {})
        self.model_name: str = model_config.get("name", "MIT/ast-finetuned-audioset-10-10-0.4593")
        cache_dir = model_config.get("cache_dir")

        self.device = get_device()
        self.preprocessor = AudioPreprocessor()

        logger.info("AST 모델 로딩 중: %s", self.model_name)
        try:
            self.feature_extractor = ASTFeatureExtractor.from_pretrained(
                self.model_name,
                cache_dir=cache_dir,
            )
            self.model = ASTForAudioClassification.from_pretrained(
                self.model_name,
                cache_dir=cache_dir,
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info("AST 모델 로딩 완료 (디바이스: %s)", self.device)
        except Exception as e:
            logger.error("AST 모델 로딩 실패: %s", e)
            raise RuntimeError(f"AST 모델 로딩 실패: {e}") from e

        # AudioSet 레이블 로딩
        self._label_names: list[str] = list(self.model.config.id2label.values())
        self._build_label_mapping()

    def _build_label_mapping(self) -> None:
        """AudioSet 레이블 → 4-class 매핑 인덱스 구축"""
        self._crackle_ids: list[int] = []
        self._wheeze_ids: list[int] = []
        self._normal_ids: list[int] = []

        for idx, label in enumerate(self._label_names):
            label_lower = label.lower()
            if any(kw in label_lower for kw in self.CRACKLE_KEYWORDS):
                self._crackle_ids.append(idx)
            elif any(kw in label_lower for kw in self.WHEEZE_KEYWORDS):
                self._wheeze_ids.append(idx)
            elif any(kw in label_lower for kw in self.NORMAL_KEYWORDS):
                self._normal_ids.append(idx)

        logger.info(
            "레이블 매핑 구축: Normal=%d, Crackle=%d, Wheeze=%d개 AudioSet 레이블",
            len(self._normal_ids), len(self._crackle_ids), len(self._wheeze_ids),
        )

    def _map_to_4class(self, logits: np.ndarray) -> dict[str, float]:
        """
        AudioSet 527개 로짓을 4-class 확률로 매핑.

        Args:
            logits: 모델 출력 로짓 (527차원)

        Returns:
            4-class 확률 딕셔너리
        """
        # 소프트맥스 적용
        probs = np.exp(logits - np.max(logits))
        probs = probs / probs.sum()

        # 관련 클래스별 확률 합산
        crackle_prob = float(np.sum(probs[self._crackle_ids])) if self._crackle_ids else 0.0
        wheeze_prob = float(np.sum(probs[self._wheeze_ids])) if self._wheeze_ids else 0.0
        normal_prob = float(np.sum(probs[self._normal_ids])) if self._normal_ids else 0.0

        # Both = crackle과 wheeze가 동시에 높은 경우
        both_prob = min(crackle_prob, wheeze_prob) * 0.5

        # 확률 정규화
        raw = {
            "Normal": normal_prob,
            "Crackle": crackle_prob,
            "Wheeze": wheeze_prob,
            "Both": both_prob,
        }
        total = sum(raw.values())
        if total > 0:
            return {k: round(v / total, 4) for k, v in raw.items()}
        # 매핑 실패 시 기본값
        return {"Normal": 0.7, "Crackle": 0.1, "Wheeze": 0.1, "Both": 0.1}

    def classify(self, file_path: str, spectrogram_save_path: str | None = None) -> AuscultationResult:
        """
        오디오 파일 분류 실행.

        Args:
            file_path: 오디오 파일 경로
            spectrogram_save_path: 스펙트로그램 이미지 저장 경로

        Returns:
            AuscultationResult 스키마
        """
        from pathlib import Path

        # 1. 전처리
        result = self.preprocessor.process(file_path, spectrogram_save_path)
        waveform = result["waveform"]
        sr = result["sample_rate"]

        # 2. 피처 추출
        try:
            inputs = self.feature_extractor(
                waveform,
                sampling_rate=sr,
                return_tensors="pt",
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        except Exception as e:
            raise RuntimeError(f"피처 추출 실패: {e}") from e

        # 3. 추론
        try:
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits.cpu().numpy()[0]
        except Exception as e:
            raise RuntimeError(f"모델 추론 실패: {e}") from e

        # 4. 4-class 매핑
        probabilities = self._map_to_4class(logits)
        classification = max(probabilities, key=probabilities.get)
        confidence = probabilities[classification]

        file_name = Path(file_path).name
        logger.info("분류 완료: %s → %s (%.2f%%)", file_name, classification, confidence * 100)

        return AuscultationResult(
            file_name=file_name,
            classification=classification,
            confidence=confidence,
            probabilities=probabilities,
            spectrogram_path=result.get("spectrogram_path"),
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AST 청진음 분류기 테스트")
    parser.add_argument("--test", action="store_true", help="테스트 모드 실행")
    parser.add_argument("--file", type=str, default="sample/sample.wav", help="오디오 파일 경로")
    args = parser.parse_args()

    if args.test:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        print("=" * 60)
        print("ASTClassifier 테스트")
        print("=" * 60)

        try:
            classifier = ASTClassifier()

            result = classifier.classify(
                args.file,
                spectrogram_save_path="data/sample_audio/mel_spectrogram.png",
            )

            print(f"\n✓ 파일: {result.file_name}")
            print(f"✓ 분류: {result.classification}")
            print(f"✓ 신뢰도: {result.confidence:.2%}")
            print("✓ 클래스별 확률:")
            for cls, prob in result.probabilities.items():
                bar = "█" * int(prob * 30)
                print(f"  {cls:10s}: {prob:.4f} {bar}")
            if result.spectrogram_path:
                print(f"✓ 스펙트로그램: {result.spectrogram_path}")
            print("\n테스트 성공!")
        except Exception as e:
            print(f"✗ 테스트 실패: {e}")
