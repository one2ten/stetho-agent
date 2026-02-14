"""증상 입력 스키마"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# 폐/심장 관련 증상 옵션
SYMPTOM_OPTIONS: list[str] = [
    "기침",
    "가래",
    "호흡곤란",
    "천명음(쌕쌕거림)",
    "가슴 통증",
    "가슴 압박감",
    "심계항진(두근거림)",
    "객혈(피 섞인 가래)",
    "야간 호흡곤란",
    "운동 시 숨참",
    "발열",
    "피로감",
]

DURATION_OPTIONS: list[str] = [
    "1-2일", "3-7일", "1-2주", "2주 이상", "1개월 이상",
]

SEVERITY_OPTIONS: list[str] = [
    "경미", "중간", "심함", "매우 심함",
]


class SymptomInput(BaseModel):
    """증상 입력 스키마 (디폴트 값 포함)"""

    free_text: str = Field(
        default="며칠 전부터 마른 기침이 나고, 계단을 오를 때 숨이 차며 가슴이 답답합니다.",
        description="자유 텍스트 증상 설명 (사용자가 직접 작성)",
    )
    checklist: list[str] = Field(
        default=["기침", "호흡곤란", "가슴 압박감"],
        description="체크리스트 증상 선택 (폐/심장 관련)",
    )
    duration: str = Field(
        default="3-7일",
        description="증상 지속 기간",
    )
    severity: Literal["경미", "중간", "심함", "매우 심함"] = Field(
        default="경미",
        description="증상 강도",
    )
