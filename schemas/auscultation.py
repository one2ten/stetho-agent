"""청진음 분류 결과 스키마"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

AUSCULTATION_CLASSES: list[str] = [
    "Normal", "Murmur", "Extrahls", "Artifact", "Extrastole",
]


class AuscultationResult(BaseModel):
    """청진음 분류 결과 스키마"""

    file_name: str = Field(description="업로드된 오디오 파일명")
    classification: str = Field(description="최종 분류 결과 (최고 확률 클래스)")
    confidence: float = Field(ge=0.0, le=1.0, description="최고 확률 (0-1)")
    probabilities: dict[str, float] = Field(
        description="클래스별 확률 딕셔너리",
    )
    spectrogram_path: Optional[str] = Field(
        default=None,
        description="Mel Spectrogram 이미지 경로",
    )
