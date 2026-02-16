"""오디오 파일 업로드 컴포넌트"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Optional

import streamlit as st

from models.ast_classifier import ASTClassifier
from schemas.auscultation import AuscultationResult
from utils.config_loader import get_app_config

logger = logging.getLogger(__name__)


def render_audio_uploader() -> Optional[AuscultationResult]:
    """
    WAV 오디오 파일 업로드 + AST 분류 실행.

    Returns:
        AuscultationResult 또는 None (업로드 안 한 경우)
    """
    config = get_app_config()
    audio_config = config.get("audio", {})
    max_size_mb = audio_config.get("max_file_size_mb", 10)

    st.subheader("청진음 업로드")
    st.caption(f"WAV 파일만 지원 | 최대 {max_size_mb}MB | 30초 이내")

    uploaded = st.file_uploader(
        "청진음 파일 (선택사항)",
        type=["wav"],
        help="폐 청진음 WAV 파일을 업로드하세요. 없으면 생체신호와 증상만으로 분석합니다.",
        key="audio_uploader",
    )

    if uploaded is None:
        st.info("청진음 파일 없이도 분석이 가능합니다.")
        return None

    # 파일 크기 검증
    file_size_mb = len(uploaded.getvalue()) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        st.error(f"파일 크기가 {max_size_mb}MB를 초과합니다 ({file_size_mb:.1f}MB).")
        return None

    # 임시 파일로 저장 후 분류 실행
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name

        st.audio(uploaded, format="audio/wav")

        with st.spinner("청진음 분석 중..."):
            classifier = _get_classifier()
            result = classifier.classify(tmp_path)

        st.success(f"분류 결과: **{result.classification}** (신뢰도: {result.confidence:.1%})")
        return result

    except Exception as e:
        st.error(f"청진음 분석 중 오류가 발생했습니다: {e}")
        logger.error("청진음 분류 실패: %s", e)
        return None


@st.cache_resource
def _get_classifier() -> ASTClassifier:
    """AST 분류기 캐싱 (모델 로딩 1회)"""
    return ASTClassifier()
