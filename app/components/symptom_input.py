"""증상 입력 컴포넌트"""
from __future__ import annotations

import streamlit as st

from schemas.symptoms import (
    DURATION_OPTIONS,
    SEVERITY_OPTIONS,
    SYMPTOM_OPTIONS,
    SymptomInput,
)
from utils.config_loader import get_app_config


def render_symptom_input() -> SymptomInput:
    """
    증상 텍스트 + 체크리스트 + 기간 + 강도 UI 렌더링.

    디폴트 값이 미리 채워져 있어 바로 분석 가능.

    Returns:
        SymptomInput 객체
    """
    st.subheader("증상 정보")

    # 자유 텍스트
    free_text = st.text_area(
        "증상을 자유롭게 설명해주세요",
        value="며칠 전부터 마른 기침이 나고, 계단을 오를 때 숨이 차며 가슴이 답답합니다.",
        height=100,
        help="현재 느끼는 증상을 자세히 작성해주세요.",
        key="symptom_text",
    )

    # 증상 체크리스트
    st.caption("해당하는 증상을 모두 선택하세요")
    checklist = st.multiselect(
        "증상 체크리스트",
        options=SYMPTOM_OPTIONS,
        default=["기침", "호흡곤란", "가슴 압박감"],
        key="symptom_checklist",
        label_visibility="collapsed",
    )

    col1, col2 = st.columns(2)
    with col1:
        duration = st.selectbox(
            "증상 지속 기간",
            options=DURATION_OPTIONS,
            index=1,  # "3-7일"
            key="symptom_duration",
        )
    with col2:
        severity = st.selectbox(
            "증상 강도",
            options=SEVERITY_OPTIONS,
            index=0,  # "경미"
            key="symptom_severity",
        )

    return SymptomInput(
        free_text=free_text,
        checklist=checklist,
        duration=duration,
        severity=severity,
    )
