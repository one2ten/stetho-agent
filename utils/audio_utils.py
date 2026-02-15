"""오디오 파일 검증 및 메타데이터 추출 유틸리티"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf

from utils.config_loader import get_ast_config

logger = logging.getLogger(__name__)


@dataclass
class AudioMetadata:
    """오디오 파일 메타데이터"""

    file_path: str
    sample_rate: int
    channels: int
    frames: int
    duration: float
    format: str
    subtype: str


def get_audio_metadata(file_path: str | Path) -> AudioMetadata:
    """
    오디오 파일 메타데이터 추출.

    Args:
        file_path: 오디오 파일 경로

    Returns:
        AudioMetadata 객체

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
        RuntimeError: 오디오 파일을 읽을 수 없을 때
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {path}")

    try:
        info = sf.info(str(path))
    except Exception as e:
        raise RuntimeError(f"오디오 파일을 읽을 수 없습니다: {e}") from e

    return AudioMetadata(
        file_path=str(path),
        sample_rate=info.samplerate,
        channels=info.channels,
        frames=info.frames,
        duration=info.duration,
        format=info.format,
        subtype=info.subtype,
    )


def validate_audio_file(file_path: str | Path) -> tuple[bool, str]:
    """
    오디오 파일 유효성 검사.

    Args:
        file_path: 오디오 파일 경로

    Returns:
        (유효 여부, 메시지) 튜플
    """
    path = Path(file_path)
    config = get_ast_config()
    audio_config = config.get("audio", {})
    max_duration = audio_config.get("max_duration", 30)

    # 파일 존재 여부
    if not path.exists():
        return False, f"파일을 찾을 수 없습니다: {path}"

    # 확장자 확인
    if path.suffix.lower() != ".wav":
        return False, f"지원하지 않는 파일 형식입니다: {path.suffix} (WAV만 지원)"

    # 파일 크기 확인 (10MB 제한)
    max_size_mb = 10
    file_size_mb = path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"파일 크기가 너무 큽니다: {file_size_mb:.1f}MB (최대 {max_size_mb}MB)"

    # 오디오 메타데이터 확인
    try:
        metadata = get_audio_metadata(path)
    except (FileNotFoundError, RuntimeError) as e:
        return False, str(e)

    # 길이 확인
    if metadata.duration > max_duration:
        return False, f"오디오 길이가 너무 깁니다: {metadata.duration:.1f}초 (최대 {max_duration}초)"

    # 최소 길이 확인 (0.5초 이상)
    if metadata.duration < 0.5:
        return False, f"오디오 길이가 너무 짧습니다: {metadata.duration:.1f}초 (최소 0.5초)"

    logger.info("오디오 파일 검증 통과: %s (%.1f초, %dHz)", path.name, metadata.duration, metadata.sample_rate)
    return True, "유효한 오디오 파일입니다."
