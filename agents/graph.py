"""LangGraph 에이전트 워크플로우 정의 — 그래프 조립 + 컴파일"""
from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from agents.edges.risk_router import route_by_risk
from agents.nodes.auscultation_node import auscultation_node
from agents.nodes.input_validator import input_validator
from agents.nodes.recommendation_node import recommendation_node
from agents.nodes.risk_node import risk_node
from agents.nodes.symptoms_node import symptoms_node
from agents.nodes.synthesis_node import synthesis_node
from agents.nodes.vitals_node import vitals_node
from agents.state import AgentState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """
    StethoAgent 워크플로우 그래프 생성.

    워크플로우:
        입력 검증 → 병렬(청진음 + 생체신호 + 증상) → 종합 판단 → 위험도 → 응답 생성

    Returns:
        컴파일된 StateGraph
    """
    workflow = StateGraph(AgentState)

    # === 노드 등록 ===
    workflow.add_node("input_validator", input_validator)
    workflow.add_node("auscultation_node", auscultation_node)
    workflow.add_node("vitals_node", vitals_node)
    workflow.add_node("symptoms_node", symptoms_node)
    workflow.add_node("synthesis_node", synthesis_node)
    workflow.add_node("risk_node", risk_node)
    workflow.add_node("recommendation_node", recommendation_node)

    # === 엣지 정의 ===

    # 시작점
    workflow.set_entry_point("input_validator")

    # Fan-out: 입력 검증 → 3개 분석 노드 (병렬 실행)
    workflow.add_edge("input_validator", "auscultation_node")
    workflow.add_edge("input_validator", "vitals_node")
    workflow.add_edge("input_validator", "symptoms_node")

    # Fan-in: 3개 분석 노드 → 종합 판단 (모두 완료 후 실행)
    workflow.add_edge("auscultation_node", "synthesis_node")
    workflow.add_edge("vitals_node", "synthesis_node")
    workflow.add_edge("symptoms_node", "synthesis_node")

    # 순차: 종합 판단 → 위험도 평가
    workflow.add_edge("synthesis_node", "risk_node")

    # 조건부 라우팅: 위험도 → 응답 생성
    workflow.add_conditional_edges("risk_node", route_by_risk)

    # 종료
    workflow.add_edge("recommendation_node", END)

    logger.info("워크플로우 그래프 빌드 완료")
    return workflow


# 컴파일된 그래프 (앱에서 import하여 사용)
graph = build_graph().compile()


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="StethoAgent 워크플로우 테스트")
    parser.add_argument("--test", action="store_true", help="디폴트 입력으로 워크플로우 실행")
    args = parser.parse_args()

    if args.test:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
        print("=" * 60)
        print("StethoAgent 워크플로우 테스트 (디폴트 입력)")
        print("=" * 60)

        from schemas.symptoms import SymptomInput
        from schemas.vitals import VitalSigns

        # 디폴트 입력으로 실행
        input_state: AgentState = {
            "vitals": VitalSigns(),
            "symptoms": SymptomInput(),
            "user_mode": "general",
        }

        print(f"\n입력:")
        print(f"  - 심박수: {input_state['vitals'].heart_rate}bpm")
        print(f"  - 혈압: {input_state['vitals'].blood_pressure_sys}/{input_state['vitals'].blood_pressure_dia}mmHg")
        print(f"  - 체온: {input_state['vitals'].body_temperature}°C")
        print(f"  - 증상: {input_state['symptoms'].free_text[:50]}...")
        print(f"  - 모드: {input_state['user_mode']}")
        print()

        try:
            result = graph.invoke(input_state)

            print("=== 워크플로우 완료 ===\n")
            print(f"--- 청진음 분석 ---\n{result.get('auscultation_analysis', 'N/A')[:200]}\n")
            print(f"--- 생체신호 평가 ---\n{result.get('vitals_evaluation', 'N/A')[:200]}\n")
            print(f"--- 증상 분석 ---\n{result.get('symptom_analysis', 'N/A')[:200]}\n")
            print(f"--- 종합 판단 ---\n{result.get('synthesis', 'N/A')[:200]}\n")

            risk = result.get("risk_assessment")
            if risk:
                print(f"--- 위험도 ---")
                print(f"  레벨: {risk.level}, 점수: {risk.score:.0f}, 즉시조치: {risk.immediate_action_needed}")
                print(f"  요인: {', '.join(risk.factors)}\n")

            print(f"--- 최종 권고 ---\n{result.get('recommendation', 'N/A')[:300]}\n")

            lit = result.get("literature_references")
            if lit and lit.references:
                print(f"--- 참고 문헌 ({lit.total_count}건) ---")
                for ref in lit.references[:3]:
                    print(f"  [{ref.source_id}] {ref.title[:80]}")

            print("\n테스트 성공!")
        except Exception as e:
            print(f"\n테스트 실패: {e}")
            import traceback
            traceback.print_exc()
