"""생체신호 입력 컴포넌트"""
from __future__ import annotations

import streamlit as st

from schemas.vitals import VitalSigns


def render_vitals_input() -> VitalSigns:
    """
    생체신호 슬라이더 UI 렌더링.

    디폴트 값이 미리 채워져 있어 바로 분석 가능.

    Returns:
        VitalSigns 객체
    """
    st.subheader("생체신호")

    heart_rate = st.slider(
        "심박수 (bpm)",
        min_value=30,
        max_value=250,
        value=75,
        step=1,
        help="정상 범위: 60-100 bpm",
        key="hr_slider",
    )

    col1, col2 = st.columns(2)
    with col1:
        bp_sys = st.slider(
            "수축기 혈압 (mmHg)",
            min_value=60,
            max_value=300,
            value=120,
            step=1,
            help="정상 범위: 90-120 mmHg",
            key="bp_sys_slider",
        )
    with col2:
        bp_dia = st.slider(
            "이완기 혈압 (mmHg)",
            min_value=30,
            max_value=200,
            value=80,
            step=1,
            help="정상 범위: 60-80 mmHg",
            key="bp_dia_slider",
        )

    body_temp = st.slider(
        "체온 (°C)",
        min_value=34.0,
        max_value=43.0,
        value=36.5,
        step=0.1,
        format="%.1f",
        help="정상 범위: 36.1-37.2 °C",
        key="temp_slider",
    )

    return VitalSigns(
        heart_rate=heart_rate,
        blood_pressure_sys=bp_sys,
        blood_pressure_dia=bp_dia,
        body_temperature=body_temp,
    )
