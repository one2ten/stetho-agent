"""오디오 전처리 모듈 — 청진음 오디오를 모델 입력으로 변환"""
from __future__ import annotations

import logging
from pathlib import Path

import librosa
import matplotlib
matplotlib.use("Agg")  # GUI 없이 이미지 저장
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

from utils.config_loader import get_ast_config

logger = logging.getLogger(__name__)


class AudioPreprocessor:
    """
    청진음 오디오 전처리기.

    - WAV 로딩
    - 리샘플링 (16kHz)
    - 모노 변환
    - 최대 30초 트리밍
    - Mel Spectrogram 생성 및 이미지 저장
    - 오디오 유효성 검사
    """

    def __init__(self) -> None:
        config = get_ast_config()
        audio_config = config.get("audio", {})
        self.sample_rate: int = audio_config.get("sample_rate", 16000)
        self.max_duration: int = audio_config.get("max_duration", 30)
        self.mono: bool = audio_config.get("mono", True)
        self.normalize: bool = audio_config.get("normalize", True)
        logger.info(
            "AudioPreprocessor 초기화: sr=%d, max_dur=%ds, mono=%s",
            self.sample_rate, self.max_duration, self.mono,
        )

    def load_audio(self, file_path: str | Path) -> tuple[np.ndarray, int]:
        """
        WAV 파일 로딩 + 리샘플링 + 모노 변환 + 트리밍.

        Args:
            file_path: 오디오 파일 경로

        Returns:
            (오디오 배열, 샘플레이트) 튜플

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            RuntimeError: 오디오 로딩 실패 시
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {path}")

        try:
            # librosa로 로딩 (자동으로 모노 변환 + 리샘플링)
            waveform, sr = librosa.load(
                str(path),
                sr=self.sample_rate,
                mono=self.mono,
            )
            logger.info("오디오 로딩 완료: %s (원본 → %dHz 리샘플링)", path.name, sr)
        except Exception as e:
            raise RuntimeError(f"오디오 로딩 실패: {e}") from e

        # 최대 길이 트리밍
        max_samples = self.max_duration * self.sample_rate
        if len(waveform) > max_samples:
            waveform = waveform[:max_samples]
            logger.info("오디오 트리밍: %d초로 제한", self.max_duration)

        # 정규화
        if self.normalize:
            max_val = np.max(np.abs(waveform))
            if max_val > 0:
                waveform = waveform / max_val

        return waveform, sr

    def create_mel_spectrogram(
        self,
        waveform: np.ndarray,
        sr: int,
        save_path: str | Path | None = None,
    ) -> np.ndarray:
        """
        Mel Spectrogram 생성 및 이미지 저장.

        Args:
            waveform: 오디오 배열
            sr: 샘플레이트
            save_path: 이미지 저장 경로 (None이면 저장하지 않음)

        Returns:
            Mel Spectrogram 배열 (dB 스케일)
        """
        mel_spec = librosa.feature.melspectrogram(
            y=waveform,
            sr=sr,
            n_mels=128,
            fmax=sr // 2,
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

        if save_path is not None:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)

            fig, ax = plt.subplots(1, 1, figsize=(10, 4))
            img = librosa.display.specshow(
                mel_spec_db,
                sr=sr,
                x_axis="time",
                y_axis="mel",
                ax=ax,
                cmap="magma",
            )
            ax.set_title("Mel Spectrogram")
            ax.set_xlabel("시간 (초)")
            ax.set_ylabel("주파수 (Hz)")
            fig.colorbar(img, ax=ax, format="%+2.0f dB")
            fig.tight_layout()
            fig.savefig(str(save_path), dpi=150, bbox_inches="tight")
            plt.close(fig)
            logger.info("Mel Spectrogram 이미지 저장: %s", save_path)

        return mel_spec_db

    def process(self, file_path: str | Path, spectrogram_save_path: str | Path | None = None) -> dict:
        """
        전체 전처리 파이프라인 실행.

        Args:
            file_path: 오디오 파일 경로
            spectrogram_save_path: 스펙트로그램 이미지 저장 경로

        Returns:
            전처리 결과 딕셔너리:
            - waveform: np.ndarray
            - sample_rate: int
            - duration: float
            - mel_spectrogram: np.ndarray
            - spectrogram_path: str | None
        """
        waveform, sr = self.load_audio(file_path)
        mel_spec_db = self.create_mel_spectrogram(waveform, sr, spectrogram_save_path)

        duration = len(waveform) / sr
        spec_path = str(spectrogram_save_path) if spectrogram_save_path else None

        logger.info("전처리 완료: %.1f초, %d 샘플", duration, len(waveform))

        return {
            "waveform": waveform,
            "sample_rate": sr,
            "duration": duration,
            "mel_spectrogram": mel_spec_db,
            "spectrogram_path": spec_path,
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="오디오 전처리 테스트")
    parser.add_argument("--test", action="store_true", help="테스트 모드 실행")
    parser.add_argument("--file", type=str, default="sample/sample.wav", help="오디오 파일 경로")
    args = parser.parse_args()

    if args.test:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        print("=" * 60)
        print("AudioPreprocessor 테스트")
        print("=" * 60)

        preprocessor = AudioPreprocessor()
        try:
            result = preprocessor.process(
                args.file,
                spectrogram_save_path="data/sample_audio/mel_spectrogram.png",
            )
            print(f"✓ 샘플레이트: {result['sample_rate']}Hz")
            print(f"✓ 길이: {result['duration']:.2f}초")
            print(f"✓ 파형 크기: {result['waveform'].shape}")
            print(f"✓ Mel Spectrogram 크기: {result['mel_spectrogram'].shape}")
            print(f"✓ 스펙트로그램 저장: {result['spectrogram_path']}")
            print("\n테스트 성공!")
        except Exception as e:
            print(f"✗ 테스트 실패: {e}")
