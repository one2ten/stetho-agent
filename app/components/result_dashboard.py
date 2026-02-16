"""분석 결과 대시보드 컴포넌트"""
from __future__ import annotations

import logging
from typing import Optional

import streamlit as st

from agents.state import AgentState
from models.literature_search import MedicalSearchClient
from schemas.auscultation import AuscultationResult
from schemas.literature import LiteratureSearchResult
from schemas.report import RiskAssessment
from utils.visualization import (
    create_classification_bar_chart,
    create_risk_indicator,
    create_vitals_gauges,
)

logger = logging.getLogger(__name__)


def render_result_dashboard(result: AgentState) -> None:
    """
    워크플로우 결과를 대시보드로 표시.

    Args:
        result: 워크플로우 실행 완료된 AgentState
    """
    # === 위험도 인디케이터 ===
    risk: Optional[RiskAssessment] = result.get("risk_assessment")
    if risk:
        _render_risk_section(risk)

    st.divider()

    # === 최종 권고 ===
    recommendation = result.get("recommendation", "")
    if recommendation:
        st.subheader("최종 권고사항")
        st.markdown(recommendation)

    st.divider()

    # === 상세 분석 (접기) ===
    with st.expander("상세 분석 보기", expanded=False):
        _render_detail_tabs(result)

    # === 참고 문헌 ===
    literature: Optional[LiteratureSearchResult] = result.get("literature_references")
    if literature and literature.references:
        _render_literature_section(literature)


def _render_risk_section(risk: RiskAssessment) -> None:
    """위험도 인디케이터 + 요인 표시"""
    col1, col2 = st.columns([1, 1])
    with col1:
        fig = create_risk_indicator(risk.level, risk.score)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        level_labels = {
            "low": "낮음",
            "moderate": "보통",
            "high": "높음",
            "critical": "위험",
        }
        level_colors = {
            "low": "green",
            "moderate": "orange",
            "high": "orange",
            "critical": "red",
        }
        label = level_labels.get(risk.level, risk.level)
        color = level_colors.get(risk.level, "gray")

        st.markdown(f"### 위험도: :{color}[{label}]")
        st.metric("위험도 점수", f"{risk.score:.0f}점")

        if risk.immediate_action_needed:
            st.error("즉시 의료 전문가 상담이 필요합니다.")

        st.markdown("**위험 요인:**")
        for factor in risk.factors:
            st.markdown(f"- {factor}")


def _render_detail_tabs(result: AgentState) -> None:
    """청진음/생체신호/증상/종합 탭별 상세 분석"""
    tabs = st.tabs(["생체신호", "증상 분석", "청진음 분석", "종합 판단"])

    # 생체신호
    with tabs[0]:
        vitals = result.get("vitals")
        if vitals:
            fig = create_vitals_gauges(vitals)
            st.plotly_chart(fig, use_container_width=True)
        evaluation = result.get("vitals_evaluation", "")
        if evaluation:
            st.markdown(evaluation)

    # 증상 분석
    with tabs[1]:
        symptom_analysis = result.get("symptom_analysis", "")
        if symptom_analysis:
            st.markdown(symptom_analysis)

    # 청진음 분석
    with tabs[2]:
        auscultation: Optional[AuscultationResult] = result.get("auscultation")
        if auscultation:
            fig = create_classification_bar_chart(auscultation.probabilities)
            st.plotly_chart(fig, use_container_width=True)
        analysis = result.get("auscultation_analysis", "")
        if analysis:
            st.markdown(analysis)

    # 종합 판단
    with tabs[3]:
        synthesis = result.get("synthesis", "")
        if synthesis:
            st.markdown(synthesis)


def _render_literature_section(literature: LiteratureSearchResult) -> None:
    """참고 문헌 표시"""
    with st.expander(f"참고 의학 문헌 ({literature.total_count}건)", expanded=False):
        refs = MedicalSearchClient.format_references_for_display(literature)
        for ref in refs:
            st.markdown(
                f"**{ref['title']}**  \n"
                f"{ref['authors_str']} | *{ref['journal']}* ({ref['year']})  \n"
                f"[{ref['source'].upper()}: {ref['source_id']}]({ref['url']})"
            )
            st.divider()
