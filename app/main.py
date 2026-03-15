"""StethoAgent Streamlit 메인 애플리케이션"""
from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (Streamlit은 스크립트 디렉토리 기준)
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import logging  # noqa: E402

import streamlit as st  # noqa: E402

from agents.graph import graph  # noqa: E402
from agents.state import AgentState  # noqa: E402
from app.components.audio_uploader import render_audio_uploader  # noqa: E402
from app.components.result_dashboard import render_result_dashboard  # noqa: E402
from app.components.symptom_input import render_symptom_input  # noqa: E402
from app.components.vitals_input import render_vitals_input  # noqa: E402
from models.llm_client import LLMClient  # noqa: E402
from utils.config_loader import get_app_config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _check_ollama() -> bool:
    """Ollama 서버 연결 상태 확인"""
    try:
        client = LLMClient()
        return client.is_available()
    except Exception:
        return False


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

        # Ollama 상태 표시
        ollama_ok = _check_ollama()
        if ollama_ok:
            st.success("Ollama 서버 연결됨", icon="🟢")
        else:
            st.error("Ollama 서버 연결 실패", icon="🔴")
            st.caption("터미널에서 `ollama serve` 또는 Ollama 앱을 실행하세요.")

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
        if st.button("🔍 분석 실행", type="primary", use_container_width=True, disabled=not ollama_ok):
            _run_analysis(vitals, symptoms, auscultation, user_mode)

        if not ollama_ok:
            st.warning("Ollama 서버가 연결되지 않아 분석을 실행할 수 없습니다.")

    # === 결과 탭 ===
    with tab_result:
        if "analysis_result" in st.session_state:
            render_result_dashboard(st.session_state["analysis_result"])
        else:
            st.info("입력 탭에서 데이터를 입력하고 '분석 실행' 버튼을 눌러주세요.")


def _run_analysis(vitals, symptoms, auscultation, user_mode: str) -> None:
    """에이전트 워크플로우 실행 (진행 상태 표시)"""
    input_state: AgentState = {
        "vitals": vitals,
        "symptoms": symptoms,
        "user_mode": user_mode,
    }
    if auscultation is not None:
        input_state["auscultation"] = auscultation

    # 진행 상태 표시
    progress_bar = st.progress(0, text="분석을 시작합니다...")

    try:
        progress_bar.progress(10, text="입력 데이터 검증 중...")
        progress_bar.progress(20, text="청진음 · 생체신호 · 증상 병렬 분석 중... (CoT 추론)")
        result = graph.invoke(input_state)
        progress_bar.progress(90, text="결과 정리 중...")

        st.session_state["analysis_result"] = result
        progress_bar.progress(100, text="분석 완료!")
        st.success("분석이 완료되었습니다! '결과' 탭에서 확인하세요.")
        logger.info("워크플로우 실행 완료")

    except Exception as e:
        progress_bar.empty()
        st.error(f"분석 중 오류가 발생했습니다: {e}")
        logger.error("워크플로우 실행 실패: %s", e)


if __name__ == "__main__":
    main()
