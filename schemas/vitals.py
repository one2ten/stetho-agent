"""생체 신호 입력 스키마"""
from __future__ import annotations

from pydantic import BaseModel, Field


class VitalSigns(BaseModel):
    """생체 신호 입력 스키마 (디폴트 값 포함)"""

    heart_rate: int = Field(
        default=75,
        ge=30,
        le=250,
        description="심박수 (bpm)",
    )
    blood_pressure_sys: int = Field(
        default=120,
        ge=60,
        le=300,
        description="수축기 혈압 (mmHg)",
    )
    blood_pressure_dia: int = Field(
        default=80,
        ge=30,
        le=200,
        description="이완기 혈압 (mmHg)",
    )
    body_temperature: float = Field(
        default=36.5,
        ge=34.0,
        le=43.0,
        description="체온 (°C)",
    )
