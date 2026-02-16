"""StethoAgent Streamlit 메인 애플리케이션"""
from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (Streamlit은 스크립트 디렉토리 기준)
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import logging

import streamlit as st

from agents.graph import graph
from agents.state import AgentState
from app.components.audio_uploader import render_audio_uploader
from app.components.result_dashboard import render_result_dashboard
from app.components.symptom_input import render_symptom_input
from app.components.vitals_input import render_vitals_input
from utils.config_loader import get_app_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Streamlit 메인 엔트리포인트"""
    config = get_app_config()
    st_config = config.get("streamlit", {})

    # 페이지 설정
    st.set_page_config(
        page_title=st_config.get("page_title", "StethoAgent"),
        page_icon=st_config.get("page_icon", "🩺"),
        layout=st_config.get("layout", "wide"),
    )

    # === 사이드바 ===
    with st.sidebar:
        st.title("🩺 StethoAgent")
        st.caption(config.get("app", {}).get("description", "AI 기반 건강 가이드"))

        st.divider()

        # 사용자 모드 선택
        user_modes = config.get("user_modes", {})
        mode_options = list(user_modes.keys())
        mode_labels = [user_modes[m].get("label", m) for m in mode_options]

        selected_idx = st.radio(
            "분석 모드",
            range(len(mode_options)),
            format_func=lambda i: mode_labels[i],
            help="일반 사용자: 쉬운 한국어 설명 | 의료 전문가: 전문 용어 리포트",
            key="mode_radio",
        )
        user_mode = mode_options[selected_idx]
        st.caption(user_modes[user_mode].get("description", ""))

        st.divider()

        # 면책 조항
        disclaimer = config.get("disclaimer", "")
        if disclaimer:
            st.warning(disclaimer)

    # === 메인 영역 ===
    st.title("🩺 StethoAgent — AI 건강 가이드")

    tab_input, tab_result = st.tabs(["📋 입력", "📊 결과"])

    # === 입력 탭 ===
    with tab_input:
        col_left, col_right = st.columns([1, 1])

        with col_left:
            vitals = render_vitals_input()
            st.divider()
            auscultation = render_audio_uploader()

        with col_right:
            symptoms = render_symptom_input()

        st.divider()

        # 분석 실행 버튼
        if st.button("🔍 분석 실행", type="primary", use_container_width=True):
            _run_analysis(vitals, symptoms, auscultation, user_mode)

    # === 결과 탭 ===
    with tab_result:
        if "analysis_result" in st.session_state:
            render_result_dashboard(st.session_state["analysis_result"])
        else:
            st.info("입력 탭에서 데이터를 입력하고 '분석 실행' 버튼을 눌러주세요.")


def _run_analysis(vitals, symptoms, auscultation, user_mode: str) -> None:
    """에이전트 워크플로우 실행"""
    input_state: AgentState = {
        "vitals": vitals,
        "symptoms": symptoms,
        "user_mode": user_mode,
    }
    if auscultation is not None:
        input_state["auscultation"] = auscultation

    with st.spinner("AI 분석을 진행하고 있습니다... (1-2분 소요될 수 있습니다)"):
        try:
            result = graph.invoke(input_state)
            st.session_state["analysis_result"] = result
            st.success("분석이 완료되었습니다! '결과' 탭에서 확인하세요.")
            logger.info("워크플로우 실행 완료")
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
            logger.error("워크플로우 실행 실패: %s", e)


if __name__ == "__main__":
    main()
