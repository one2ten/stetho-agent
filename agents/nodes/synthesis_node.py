"""종합 판단 노드 — ReAct 패턴으로 3개 분석 결과 통합 + 의학 문헌 검색"""
from __future__ import annotations

import logging
from pathlib import Path

from agents.state import AgentState
from models.llm_client import LLMClient
from models.literature_search import MedicalSearchClient

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "synthesis.md"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return "당신은 의료 종합 분석 전문가입니다. 여러 분석 결과를 종합하여 판단해주세요."


def synthesis_node(state: AgentState) -> dict:
    """
    종합 판단 노드 (ReAct 패턴 적용).

    ReAct 흐름:
    1. [사고] 3개 분석에서 핵심 소견 추출
    2. [행동] 의학 문헌 검색으로 근거 확보
    3. [관찰] 문헌 검색 결과 확인
    4. [사고] 소견 간 교차 검증 + 가설 수립
    5. [결론] 종합 판단 생성
    """
    aus_analysis = state.get("auscultation_analysis", "분석 없음")
    vitals_eval = state.get("vitals_evaluation", "평가 없음")
    symptom_analysis = state.get("symptom_analysis", "분석 없음")

    logger.info("종합 판단 시작 (ReAct 패턴)")

    # 추론 추적 초기화
    reasoning_trace = list(state.get("reasoning_trace") or [])
    reasoning_trace.append("[사고] 청진음, 생체신호, 증상 분석 결과에서 핵심 소견을 추출합니다.")

    # [행동] 의학 문헌 검색
    literature_result = None
    literature_context = ""
    try:
        reasoning_trace.append("[행동] 분석 결과 기반 의학 문헌 검색을 실행합니다.")
        search_client = MedicalSearchClient()
        literature_result = search_client.search_from_analysis(
            auscultation=state.get("auscultation"),
            symptoms=state.get("symptoms"),
            vitals=state.get("vitals"),
        )
        literature_context = MedicalSearchClient.format_references_for_llm(literature_result)
        if literature_context:
            reasoning_trace.append(f"[관찰] 문헌 검색 완료: {literature_result.total_count}건의 관련 문헌을 확인했습니다.")
            logger.info("문헌 검색 완료: %d건", literature_result.total_count)
        else:
            reasoning_trace.append("[관찰] 관련 문헌을 찾지 못했습니다. 기존 분석만으로 판단합니다.")
    except Exception as e:
        reasoning_trace.append(f"[관찰] 문헌 검색 실패: {e}. 기존 분석만으로 판단합니다.")
        logger.warning("문헌 검색 실패 (계속 진행): %s", e)

    # ReAct 프레이밍으로 프롬프트 구성
    user_prompt = (
        "다음 분석 결과들을 ReAct(사고-행동-관찰) 패턴으로 종합 판단해주세요.\n\n"
        f"=== 청진음 분석 ===\n{aus_analysis}\n\n"
        f"=== 생체신호 평가 ===\n{vitals_eval}\n\n"
        f"=== 증상 분석 ===\n{symptom_analysis}\n\n"
    )
    if literature_context:
        user_prompt += f"{literature_context}\n\n"

    user_prompt += (
        "위 분석 결과들을 [사고]/[행동]/[관찰]/[결론] 단계로 종합하여:\n"
        "1. 전체적인 건강 상태 요약\n"
        "2. 주요 소견 및 관련성 (일치/불일치 교차 검증)\n"
        "3. 주의가 필요한 사항\n"
        "을 정리해주세요."
    )

    try:
        llm = LLMClient()
        system_prompt = _load_prompt()
        synthesis = llm.generate(user_prompt, system_prompt=system_prompt)
        reasoning_trace.append("[결론] 종합 판단이 완료되었습니다.")
        logger.info("종합 판단 완료: %d자", len(synthesis))
        return {
            "synthesis": synthesis,
            "literature_references": literature_result,
            "reasoning_trace": reasoning_trace,
        }
    except Exception as e:
        error_msg = f"종합 판단 중 오류가 발생했습니다: {e}"
        reasoning_trace.append(f"[오류] {error_msg}")
        logger.error(error_msg)
        return {
            "synthesis": error_msg,
            "literature_references": literature_result,
            "reasoning_trace": reasoning_trace,
        }
