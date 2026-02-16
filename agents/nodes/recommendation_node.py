"""응답 생성 노드 — 사용자 모드에 맞는 최종 권고 생성"""
from __future__ import annotations

import logging
from pathlib import Path

from agents.state import AgentState
from models.llm_client import LLMClient
from models.literature_search import MedicalSearchClient

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_prompt(user_mode: str) -> str:
    """모드별 프롬프트 템플릿 로딩"""
    if user_mode == "professional":
        path = _PROMPTS_DIR / "recommendation_professional.md"
    else:
        path = _PROMPTS_DIR / "recommendation_general.md"

    if path.exists():
        return path.read_text(encoding="utf-8")

    if user_mode == "professional":
        return "당신은 의료 전문가에게 보고하는 AI입니다. 전문 의학 용어를 사용하세요."
    return "당신은 일반인에게 건강 정보를 전달하는 AI입니다. 쉬운 한국어로 설명하세요."


def recommendation_node(state: AgentState) -> dict:
    """
    응답 생성 노드.

    - user_mode에 따라 프롬프트 선택 (general / professional)
    - 위험도 high/critical 시 즉시 의료 상담 권고 추가
    - 문헌 참조 정보 포함
    """
    user_mode = state.get("user_mode", "general")
    synthesis = state.get("synthesis", "")
    risk = state.get("risk_assessment")
    literature = state.get("literature_references")

    logger.info("응답 생성 시작: mode=%s, risk=%s", user_mode, risk.level if risk else "N/A")

    # 위험도 경고 문구
    risk_warning = ""
    if risk and risk.level in ("high", "critical"):
        risk_warning = (
            "\n\n🚨 **중요**: 이 환자는 높은 위험도로 평가되었습니다. "
            "가능한 빨리 의료 전문가의 진료를 받으시기 바랍니다.\n"
        )

    # 문헌 참조 텍스트
    lit_text = ""
    if literature:
        lit_text = MedicalSearchClient.format_references_for_llm(literature)

    risk_info = ""
    if risk:
        risk_info = (
            f"위험도: {risk.level} ({risk.score:.0f}점)\n"
            f"위험 요인: {', '.join(risk.factors)}\n"
            f"즉시 조치 필요: {'예' if risk.immediate_action_needed else '아니오'}\n"
        )

    user_prompt = (
        f"=== 종합 분석 결과 ===\n{synthesis}\n\n"
        f"=== 위험도 평가 ===\n{risk_info}\n"
    )
    if lit_text:
        user_prompt += f"\n{lit_text}\n"

    user_prompt += (
        "\n위 분석 결과를 바탕으로 환자에게 전달할 최종 권고사항을 작성해주세요.\n"
        "포함할 내용: 1) 현재 상태 요약 2) 권장 조치 3) 생활 습관 조언 4) 추가 검사 필요 여부"
    )

    try:
        llm = LLMClient()
        system_prompt = _load_prompt(user_mode)
        recommendation = llm.generate(user_prompt, system_prompt=system_prompt)

        # 위험도 경고 추가
        if risk_warning:
            recommendation = risk_warning + recommendation

        logger.info("응답 생성 완료: %d자", len(recommendation))
        return {"recommendation": recommendation}
    except Exception as e:
        error_msg = f"응답 생성 중 오류가 발생했습니다: {e}"
        logger.error(error_msg)
        return {"recommendation": error_msg}
