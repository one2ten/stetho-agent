"""에이전트 그래프 통합 테스트"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents.state import AgentState
from schemas.auscultation import AuscultationResult
from schemas.symptoms import SymptomInput
from schemas.vitals import VitalSigns


class TestGraphBuild:
    """그래프 빌드 테스트"""

    def test_build_graph_compiles(self):
        """그래프 빌드 + 컴파일 성공"""
        from agents.graph import build_graph

        workflow = build_graph()
        compiled = workflow.compile()
        assert compiled is not None

    def test_graph_module_exports(self):
        """모듈 레벨 graph 객체 존재"""
        from agents.graph import graph

        assert graph is not None


class TestGraphWorkflow:
    """그래프 워크플로우 통합 테스트 (LLM 모킹)"""

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_full_workflow_default_inputs(
        self,
        mock_aus_llm,
        mock_vitals_llm,
        mock_symptoms_llm,
        mock_synthesis_llm,
        mock_search_cls,
        mock_rec_llm,
    ):
        """디폴트 입력으로 전체 워크플로우 실행"""
        from agents.graph import build_graph

        # LLM 모킹 (각 노드별)
        for mock_cls in [mock_aus_llm, mock_vitals_llm, mock_symptoms_llm, mock_synthesis_llm, mock_rec_llm]:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "테스트 분석 결과입니다."
            mock_cls.return_value = mock_instance

        # 문헌 검색 모킹
        mock_search = MagicMock()
        mock_search.search_from_analysis.return_value = MagicMock(
            total_count=0, references=[], search_successful=True, error_message=None
        )
        mock_search_cls.return_value = mock_search
        mock_search_cls.format_references_for_llm.return_value = ""

        # 그래프 실행
        workflow = build_graph()
        compiled = workflow.compile()

        input_state: AgentState = {
            "vitals": VitalSigns(),
            "symptoms": SymptomInput(),
            "user_mode": "general",
        }

        result = compiled.invoke(input_state)

        # 모든 필드가 채워졌는지 검증
        assert result.get("vitals") is not None
        assert result.get("symptoms") is not None
        assert result.get("user_mode") == "general"
        assert result.get("vitals_evaluation") is not None
        assert result.get("symptom_analysis") is not None
        assert result.get("auscultation_analysis") is not None
        assert result.get("synthesis") is not None
        assert result.get("risk_assessment") is not None
        assert result.get("recommendation") is not None

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_workflow_with_auscultation(
        self,
        mock_aus_llm,
        mock_vitals_llm,
        mock_symptoms_llm,
        mock_synthesis_llm,
        mock_search_cls,
        mock_rec_llm,
    ):
        """청진음 포함 워크플로우"""
        from agents.graph import build_graph

        for mock_cls in [mock_aus_llm, mock_vitals_llm, mock_symptoms_llm, mock_synthesis_llm, mock_rec_llm]:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "테스트 결과"
            mock_cls.return_value = mock_instance

        mock_search = MagicMock()
        mock_search.search_from_analysis.return_value = MagicMock(
            total_count=0, references=[], search_successful=True, error_message=None
        )
        mock_search_cls.return_value = mock_search
        mock_search_cls.format_references_for_llm.return_value = ""

        auscultation = AuscultationResult(
            file_name="test.wav",
            classification="Crackle",
            confidence=0.9,
            probabilities={"Normal": 0.05, "Crackle": 0.9, "Wheeze": 0.03, "Both": 0.02},
        )

        workflow = build_graph()
        compiled = workflow.compile()

        input_state: AgentState = {
            "vitals": VitalSigns(),
            "symptoms": SymptomInput(),
            "auscultation": auscultation,
            "user_mode": "professional",
        }

        result = compiled.invoke(input_state)

        assert result.get("auscultation") is not None
        assert result.get("user_mode") == "professional"
        assert result.get("risk_assessment") is not None
        # 비정상 청진음 → 위험도 상승
        assert result["risk_assessment"].score >= 20

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_workflow_empty_state_uses_defaults(
        self,
        mock_aus_llm,
        mock_vitals_llm,
        mock_symptoms_llm,
        mock_synthesis_llm,
        mock_search_cls,
        mock_rec_llm,
    ):
        """빈 상태 → 디폴트 적용 후 정상 실행"""
        from agents.graph import build_graph

        for mock_cls in [mock_aus_llm, mock_vitals_llm, mock_symptoms_llm, mock_synthesis_llm, mock_rec_llm]:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "디폴트 분석"
            mock_cls.return_value = mock_instance

        mock_search = MagicMock()
        mock_search.search_from_analysis.return_value = MagicMock(
            total_count=0, references=[], search_successful=True, error_message=None
        )
        mock_search_cls.return_value = mock_search
        mock_search_cls.format_references_for_llm.return_value = ""

        workflow = build_graph()
        compiled = workflow.compile()

        # 빈 상태로 실행
        result = compiled.invoke({})

        # input_validator가 디폴트 적용
        assert result.get("vitals") is not None
        assert result["vitals"].heart_rate == 75
        assert result.get("symptoms") is not None
        assert result.get("recommendation") is not None

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_high_risk_workflow(
        self,
        mock_aus_llm,
        mock_vitals_llm,
        mock_symptoms_llm,
        mock_synthesis_llm,
        mock_search_cls,
        mock_rec_llm,
    ):
        """고위험 입력 → 위험도 high 이상"""
        from agents.graph import build_graph

        for mock_cls in [mock_aus_llm, mock_vitals_llm, mock_symptoms_llm, mock_synthesis_llm]:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "긴급한 상태로 즉시 조치가 필요합니다."
            mock_cls.return_value = mock_instance

        mock_rec = MagicMock()
        mock_rec.generate.return_value = "즉시 병원 방문이 필요합니다."
        mock_rec_llm.return_value = mock_rec

        mock_search = MagicMock()
        mock_search.search_from_analysis.return_value = MagicMock(
            total_count=0, references=[], search_successful=True, error_message=None
        )
        mock_search_cls.return_value = mock_search
        mock_search_cls.format_references_for_llm.return_value = ""

        workflow = build_graph()
        compiled = workflow.compile()

        input_state: AgentState = {
            "vitals": VitalSigns(heart_rate=150, blood_pressure_sys=180, body_temperature=39.5),
            "symptoms": SymptomInput(severity="매우 심함"),
            "user_mode": "general",
        }

        result = compiled.invoke(input_state)

        risk = result["risk_assessment"]
        assert risk.level in ("high", "critical")
        assert risk.immediate_action_needed is True
        assert "중요" in result["recommendation"] or "병원" in result["recommendation"]
