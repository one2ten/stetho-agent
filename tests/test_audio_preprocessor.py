"""오디오 전처리 파이프라인 테스트"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from models.audio_preprocessor import AudioPreprocessor


SAMPLE_WAV = Path(__file__).resolve().parent.parent / "sample" / "sample.wav"


@pytest.fixture
def preprocessor() -> AudioPreprocessor:
    """AudioPreprocessor 인스턴스 픽스처"""
    return AudioPreprocessor()


@pytest.fixture
def temp_wav() -> Path:
    """테스트용 임시 WAV 파일 생성 픽스처"""
    sr = 16000
    duration = 3.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 440Hz 사인파
    waveform = 0.5 * np.sin(2 * np.pi * 440 * t)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, waveform, sr)
        return Path(f.name)


class TestAudioPreprocessor:
    """AudioPreprocessor 클래스 테스트"""

    def test_초기화(self, preprocessor: AudioPreprocessor):
        """초기화 시 config 값이 올바르게 설정되는지 확인"""
        assert preprocessor.sample_rate == 16000
        assert preprocessor.max_duration == 30
        assert preprocessor.mono is True

    def test_오디오_로딩_임시파일(self, preprocessor: AudioPreprocessor, temp_wav: Path):
        """임시 WAV 파일 로딩 확인"""
        waveform, sr = preprocessor.load_audio(temp_wav)
        assert sr == 16000
        assert isinstance(waveform, np.ndarray)
        assert len(waveform) > 0

    @pytest.mark.skipif(not SAMPLE_WAV.exists(), reason="샘플 WAV 파일 없음")
    def test_샘플_오디오_로딩(self, preprocessor: AudioPreprocessor):
        """sample/sample.wav 로딩 확인"""
        waveform, sr = preprocessor.load_audio(SAMPLE_WAV)
        assert sr == 16000
        assert isinstance(waveform, np.ndarray)
        # 15초 원본 → 리샘플링 후에도 적절한 길이
        assert len(waveform) > 0

    def test_파일_없음_에러(self, preprocessor: AudioPreprocessor):
        """존재하지 않는 파일 시 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            preprocessor.load_audio("non_existent.wav")

    def test_mel_스펙트로그램_생성(self, preprocessor: AudioPreprocessor, temp_wav: Path):
        """Mel Spectrogram 생성 확인"""
        waveform, sr = preprocessor.load_audio(temp_wav)
        mel_spec = preprocessor.create_mel_spectrogram(waveform, sr)
        assert isinstance(mel_spec, np.ndarray)
        assert mel_spec.ndim == 2
        # 128 mel bins
        assert mel_spec.shape[0] == 128

    def test_mel_스펙트로그램_이미지_저장(self, preprocessor: AudioPreprocessor, temp_wav: Path):
        """Mel Spectrogram 이미지 저장 확인"""
        waveform, sr = preprocessor.load_audio(temp_wav)
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "mel.png"
            preprocessor.create_mel_spectrogram(waveform, sr, save_path)
            assert save_path.exists()
            assert save_path.stat().st_size > 0

    def test_전처리_파이프라인(self, preprocessor: AudioPreprocessor, temp_wav: Path):
        """전체 전처리 파이프라인 실행 확인"""
        result = preprocessor.process(temp_wav)
        assert "waveform" in result
        assert "sample_rate" in result
        assert "duration" in result
        assert "mel_spectrogram" in result
        assert result["sample_rate"] == 16000
        assert result["duration"] > 0

    def test_트리밍(self, preprocessor: AudioPreprocessor):
        """최대 길이 트리밍 확인"""
        # 60초짜리 오디오 생성
        sr = 16000
        long_waveform = np.zeros(sr * 60)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, long_waveform, sr)
            waveform, _ = preprocessor.load_audio(f.name)
            max_samples = preprocessor.max_duration * sr
            assert len(waveform) <= max_samples

    def test_정규화(self, preprocessor: AudioPreprocessor, temp_wav: Path):
        """정규화 후 최대값이 1.0인지 확인"""
        waveform, _ = preprocessor.load_audio(temp_wav)
        assert np.max(np.abs(waveform)) <= 1.0 + 1e-6


class TestAudioUtils:
    """utils/audio_utils.py 테스트"""

    def test_메타데이터_추출(self, temp_wav: Path):
        """오디오 메타데이터 추출 확인"""
        from utils.audio_utils import get_audio_metadata

        metadata = get_audio_metadata(temp_wav)
        assert metadata.sample_rate == 16000
        assert metadata.channels == 1
        assert metadata.duration > 0

    def test_파일_검증_성공(self, temp_wav: Path):
        """유효한 WAV 파일 검증 통과"""
        from utils.audio_utils import validate_audio_file

        valid, msg = validate_audio_file(temp_wav)
        assert valid is True

    def test_파일_검증_존재하지_않음(self):
        """존재하지 않는 파일 검증 실패"""
        from utils.audio_utils import validate_audio_file

        valid, msg = validate_audio_file("non_existent.wav")
        assert valid is False

    def test_파일_검증_잘못된_확장자(self):
        """WAV가 아닌 파일 검증 실패"""
        from utils.audio_utils import validate_audio_file

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake data")
            valid, msg = validate_audio_file(f.name)
            assert valid is False
            assert "WAV" in msg

    @pytest.mark.skipif(not SAMPLE_WAV.exists(), reason="샘플 WAV 파일 없음")
    def test_샘플_파일_검증(self):
        """sample/sample.wav 검증 통과"""
        from utils.audio_utils import validate_audio_file

        valid, msg = validate_audio_file(SAMPLE_WAV)
        assert valid is True
