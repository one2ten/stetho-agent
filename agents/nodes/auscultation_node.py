"""청진음 분석 노드 — AST 분류 결과를 LLM으로 해석"""
from __future__ import annotations

import logging
from pathlib import Path

from agents.state import AgentState
from models.llm_client import LLMClient

logger = logging.getLogger(__name__)

# 프롬프트 템플릿 로딩
_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "auscultation_analysis.md"


def _load_prompt() -> str:
    """프롬프트 템플릿 로딩"""
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return "당신은 폐 청진음 분석 전문가입니다. 분류 결과를 해석해주세요."


def auscultation_node(state: AgentState) -> dict:
    """
    청진음 분석 노드.

    - 청진음 데이터가 없으면 스킵 메시지 반환
    - 있으면 AST 분류 결과를 LLM으로 해석
    """
    auscultation = state.get("auscultation")

    if auscultation is None:
        logger.info("청진음 데이터 없음 — 분석 스킵")
        return {"auscultation_analysis": "청진음 데이터가 제공되지 않았습니다. 생체신호와 증상만으로 분석을 진행합니다."}

    logger.info("청진음 분석 시작: %s (%.1f%%)", auscultation.classification, auscultation.confidence * 100)

    # 확률 텍스트 생성
    prob_text = "\n".join(
        f"  - {cls}: {prob:.1%}" for cls, prob in auscultation.probabilities.items()
    )

    user_prompt = (
        f"청진음 분류 결과:\n"
        f"- 최종 분류: {auscultation.classification}\n"
        f"- 신뢰도: {auscultation.confidence:.1%}\n"
        f"- 클래스별 확률:\n{prob_text}\n\n"
        f"이 청진음 분류 결과를 의학적으로 해석해주세요."
    )

    try:
        llm = LLMClient()
        system_prompt = _load_prompt()
        analysis = llm.generate(user_prompt, system_prompt=system_prompt)
        logger.info("청진음 분석 완료: %d자", len(analysis))
        return {"auscultation_analysis": analysis}
    except Exception as e:
        error_msg = f"청진음 분석 중 오류가 발생했습니다: {e}"
        logger.error(error_msg)
        return {"auscultation_analysis": error_msg}
