"""시각화 유틸리티 — Plotly 차트 생성"""
from __future__ import annotations

import logging

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from schemas.vitals import VitalSigns
from utils.config_loader import get_vitals_reference

logger = logging.getLogger(__name__)


def create_vitals_gauges(vitals: VitalSigns) -> go.Figure:
    """
    생체신호 Plotly 게이지 차트 생성.

    Args:
        vitals: 생체신호 데이터

    Returns:
        Plotly Figure 객체
    """
    ref = get_vitals_reference()

    # 심박수 범위
    hr_ref = ref.get("heart_rate", {}).get("normal", {})
    hr_min = hr_ref.get("min", 60)
    hr_max = hr_ref.get("max", 100)

    # 체온 범위
    temp_ref = ref.get("body_temperature", {}).get("normal", {})
    temp_min = temp_ref.get("min", 36.1)
    temp_max = temp_ref.get("max", 37.2)

    # 수축기 혈압 범위
    bp_ref = ref.get("blood_pressure", {}).get("normal", {})
    sys_max = bp_ref.get("systolic_max", 120)

    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]],
        subplot_titles=["심박수 (bpm)", "혈압 (mmHg)", "체온 (°C)"],
    )

    # 심박수 게이지
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=vitals.heart_rate,
            gauge=dict(
                axis=dict(range=[30, 200]),
                bar=dict(color="#1E88E5"),
                steps=[
                    dict(range=[30, hr_min], color="#FFCDD2"),
                    dict(range=[hr_min, hr_max], color="#C8E6C9"),
                    dict(range=[hr_max, 200], color="#FFCDD2"),
                ],
                threshold=dict(line=dict(color="red", width=2), thickness=0.75, value=vitals.heart_rate),
            ),
        ),
        row=1, col=1,
    )

    # 혈압 게이지 (수축기)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=vitals.blood_pressure_sys,
            number=dict(suffix=f"/{vitals.blood_pressure_dia}"),
            gauge=dict(
                axis=dict(range=[60, 250]),
                bar=dict(color="#43A047"),
                steps=[
                    dict(range=[60, 90], color="#FFCDD2"),
                    dict(range=[90, sys_max], color="#C8E6C9"),
                    dict(range=[sys_max, 140], color="#FFF9C4"),
                    dict(range=[140, 250], color="#FFCDD2"),
                ],
            ),
        ),
        row=1, col=2,
    )

    # 체온 게이지
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=vitals.body_temperature,
            number=dict(suffix="°C"),
            gauge=dict(
                axis=dict(range=[34.0, 42.0]),
                bar=dict(color="#FF7043"),
                steps=[
                    dict(range=[34.0, temp_min], color="#BBDEFB"),
                    dict(range=[temp_min, temp_max], color="#C8E6C9"),
                    dict(range=[temp_max, 38.0], color="#FFF9C4"),
                    dict(range=[38.0, 42.0], color="#FFCDD2"),
                ],
            ),
        ),
        row=1, col=3,
    )

    fig.update_layout(
        height=300,
        margin=dict(t=60, b=20, l=30, r=30),
        font=dict(family="sans-serif"),
    )

    return fig


def create_classification_bar_chart(probabilities: dict[str, float]) -> go.Figure:
    """
    청진음 분류 확률 바 차트 생성.

    Args:
        probabilities: 클래스별 확률 딕셔너리

    Returns:
        Plotly Figure 객체
    """
    classes = list(probabilities.keys())
    probs = [probabilities[c] for c in classes]

    # 한국어 레이블 매핑
    label_map = {
        "Normal": "정상",
        "Crackle": "수포음",
        "Wheeze": "천명음",
        "Both": "수포음+천명음",
    }
    labels = [label_map.get(c, c) for c in classes]

    # 색상 매핑
    color_map = {
        "Normal": "#4CAF50",
        "Crackle": "#FF9800",
        "Wheeze": "#2196F3",
        "Both": "#F44336",
    }
    colors = [color_map.get(c, "#9E9E9E") for c in classes]

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=probs,
                marker_color=colors,
                text=[f"{p:.1%}" for p in probs],
                textposition="auto",
            )
        ]
    )

    fig.update_layout(
        title="청진음 분류 확률",
        yaxis=dict(title="확률", range=[0, 1], tickformat=".0%"),
        xaxis=dict(title="분류"),
        height=350,
        margin=dict(t=50, b=50, l=50, r=30),
    )

    return fig


def create_risk_indicator(level: str, score: float) -> go.Figure:
    """
    위험도 인디케이터 생성.

    Args:
        level: 위험도 레벨 (low, moderate, high, critical)
        score: 위험도 점수 (0-100)

    Returns:
        Plotly Figure 객체
    """
    color_map = {
        "low": "#4CAF50",
        "moderate": "#FFC107",
        "high": "#FF9800",
        "critical": "#F44336",
    }
    label_map = {
        "low": "낮음",
        "moderate": "보통",
        "high": "높음",
        "critical": "위험",
    }

    color = color_map.get(level, "#9E9E9E")
    label = label_map.get(level, level)

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            title=dict(text=f"위험도: {label}", font=dict(size=20)),
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color=color),
                steps=[
                    dict(range=[0, 25], color="#E8F5E9"),
                    dict(range=[25, 50], color="#FFF8E1"),
                    dict(range=[50, 75], color="#FFF3E0"),
                    dict(range=[75, 100], color="#FFEBEE"),
                ],
                threshold=dict(
                    line=dict(color="red", width=3),
                    thickness=0.8,
                    value=75,
                ),
            ),
            number=dict(suffix="점"),
        )
    )

    fig.update_layout(
        height=300,
        margin=dict(t=50, b=20, l=30, r=30),
    )

    return fig
