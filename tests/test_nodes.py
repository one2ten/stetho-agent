"""에이전트 노드 단위 테스트"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents.nodes.input_validator import input_validator
from agents.nodes.risk_node import risk_node, _calculate_risk
from agents.state import AgentState
from schemas.auscultation import AuscultationResult
from schemas.report import RiskAssessment
from schemas.symptoms import SymptomInput
from schemas.vitals import VitalSigns


# =====================================================================
# input_validator 테스트
# =====================================================================


class TestInputValidator:
    """입력 검증 노드 테스트"""

    def test_empty_state_applies_defaults(self):
        """빈 상태에서 디폴트 적용"""
        state: AgentState = {}
        result = input_validator(state)

        assert isinstance(result["vitals"], VitalSigns)
        assert result["vitals"].heart_rate == 75
        assert isinstance(result["symptoms"], SymptomInput)
        assert result["user_mode"] == "general"
        assert result["auscultation"] is None

    def test_existing_values_preserved(self, default_vitals, default_symptoms):
        """기존 값 유지"""
        state: AgentState = {
            "vitals": default_vitals,
            "symptoms": default_symptoms,
            "user_mode": "professional",
        }
        result = input_validator(state)

        assert result["vitals"] is default_vitals
        assert result["symptoms"] is default_symptoms
        assert result["user_mode"] == "professional"

    def test_auscultation_passed_through(self, sample_auscultation):
        """청진음 데이터 전달"""
        state: AgentState = {"auscultation": sample_auscultation}
        result = input_validator(state)
        assert result["auscultation"] is sample_auscultation


# =====================================================================
# auscultation_node 테스트
# =====================================================================


class TestAuscultationNode:
    """청진음 분석 노드 테스트"""

    def test_no_auscultation_returns_skip(self):
        """청진음 없으면 스킵 메시지"""
        from agents.nodes.auscultation_node import auscultation_node

        state: AgentState = {}
        result = auscultation_node(state)

        assert "auscultation_analysis" in result
        assert "제공되지 않았습니다" in result["auscultation_analysis"]

    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_with_auscultation_calls_llm(self, mock_llm_cls, sample_auscultation):
        """청진음 있으면 LLM 호출"""
        from agents.nodes.auscultation_node import auscultation_node

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "수포음이 감지되었습니다."
        mock_llm_cls.return_value = mock_llm

        state: AgentState = {"auscultation": sample_auscultation}
        result = auscultation_node(state)

        assert result["auscultation_analysis"] == "수포음이 감지되었습니다."
        mock_llm.generate.assert_called_once()

    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_llm_error_returns_error_msg(self, mock_llm_cls, sample_auscultation):
        """LLM 오류 시 에러 메시지 반환"""
        from agents.nodes.auscultation_node import auscultation_node

        mock_llm = MagicMock()
        mock_llm.generate.side_effect = RuntimeError("서버 연결 실패")
        mock_llm_cls.return_value = mock_llm

        state: AgentState = {"auscultation": sample_auscultation}
        result = auscultation_node(state)

        assert "오류" in result["auscultation_analysis"]


# =====================================================================
# vitals_node 테스트
# =====================================================================


class TestVitalsNode:
    """생체신호 평가 노드 테스트"""

    def test_no_vitals_returns_skip(self):
        """생체신호 없으면 스킵"""
        from agents.nodes.vitals_node import vitals_node

        state: AgentState = {}
        result = vitals_node(state)
        assert "제공되지 않았습니다" in result["vitals_evaluation"]

    @patch("agents.nodes.vitals_node.LLMClient")
    def test_normal_vitals(self, mock_llm_cls, default_vitals):
        """정상 생체신호 평가"""
        from agents.nodes.vitals_node import vitals_node

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "모든 생체신호가 정상 범위입니다."
        mock_llm_cls.return_value = mock_llm

        state: AgentState = {"vitals": default_vitals}
        result = vitals_node(state)

        assert result["vitals_evaluation"] == "모든 생체신호가 정상 범위입니다."


# =====================================================================
# symptoms_node 테스트
# =====================================================================


class TestSymptomsNode:
    """증상 분석 노드 테스트"""

    def test_no_symptoms_returns_skip(self):
        """증상 없으면 스킵"""
        from agents.nodes.symptoms_node import symptoms_node

        state: AgentState = {}
        result = symptoms_node(state)
        assert "제공되지 않았습니다" in result["symptom_analysis"]

    @patch("agents.nodes.symptoms_node.LLMClient")
    def test_with_symptoms(self, mock_llm_cls, default_symptoms):
        """증상 분석 실행"""
        from agents.nodes.symptoms_node import symptoms_node

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "기침과 호흡곤란 증상이 보입니다."
        mock_llm_cls.return_value = mock_llm

        state: AgentState = {"symptoms": default_symptoms}
        result = symptoms_node(state)

        assert result["symptom_analysis"] == "기침과 호흡곤란 증상이 보입니다."


# =====================================================================
# synthesis_node 테스트
# =====================================================================


class TestSynthesisNode:
    """종합 판단 노드 테스트"""

    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    def test_synthesis_with_all_inputs(self, mock_llm_cls, mock_search_cls):
        """3개 분석 + 문헌 종합"""
        from agents.nodes.synthesis_node import synthesis_node

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "종합 분석 결과입니다."
        mock_llm_cls.return_value = mock_llm

        mock_search = MagicMock()
        mock_search.search_from_analysis.return_value = MagicMock(
            total_count=0, references=[], search_successful=True, error_message=None
        )
        mock_search_cls.return_value = mock_search
        mock_search_cls.format_references_for_llm.return_value = ""

        state: AgentState = {
            "auscultation_analysis": "정상 청진음",
            "vitals_evaluation": "정상 생체신호",
            "symptom_analysis": "경미한 기침",
        }
        result = synthesis_node(state)

        assert result["synthesis"] == "종합 분석 결과입니다."


# =====================================================================
# risk_node 테스트
# =====================================================================


class TestRiskNode:
    """위험도 평가 노드 테스트"""

    def test_normal_inputs_low_risk(self, default_vitals, default_symptoms):
        """정상 입력 → 낮은 위험도"""
        state: AgentState = {
            "vitals": default_vitals,
            "symptoms": default_symptoms,
            "synthesis": "전반적으로 양호합니다.",
        }
        result = risk_node(state)
        risk = result["risk_assessment"]

        assert isinstance(risk, RiskAssessment)
        assert risk.level == "low"
        assert risk.score < 25

    def test_abnormal_vitals_increase_risk(self):
        """비정상 생체신호 → 위험도 상승"""
        abnormal_vitals = VitalSigns(
            heart_rate=130,
            blood_pressure_sys=160,
            body_temperature=39.0,
        )
        state: AgentState = {
            "vitals": abnormal_vitals,
            "symptoms": SymptomInput(severity="심함"),
            "synthesis": "긴급한 상태로 판단됩니다.",
        }
        result = risk_node(state)
        risk = result["risk_assessment"]

        assert risk.level in ("high", "critical")
        assert risk.score >= 50
        assert risk.immediate_action_needed is True

    def test_abnormal_auscultation_adds_risk(self):
        """비정상 청진음 → +20점"""
        auscultation = AuscultationResult(
            file_name="test.wav",
            classification="Crackle",
            confidence=0.9,
            probabilities={"Normal": 0.05, "Crackle": 0.9, "Wheeze": 0.03, "Both": 0.02},
        )
        state: AgentState = {
            "vitals": VitalSigns(),
            "auscultation": auscultation,
            "synthesis": "",
        }
        result = risk_node(state)
        risk = result["risk_assessment"]

        assert risk.score >= 20
        assert any("청진음" in f for f in risk.factors)

    def test_empty_state_low_risk(self):
        """빈 상태 → 낮은 위험도"""
        state: AgentState = {"synthesis": ""}
        result = risk_node(state)
        risk = result["risk_assessment"]

        assert risk.level == "low"


# =====================================================================
# recommendation_node 테스트
# =====================================================================


class TestRecommendationNode:
    """응답 생성 노드 테스트"""

    @patch("agents.nodes.recommendation_node.LLMClient")
    def test_general_mode(self, mock_llm_cls, sample_risk_assessment):
        """일반 모드 권고 생성"""
        from agents.nodes.recommendation_node import recommendation_node

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "건강 상태가 양호합니다."
        mock_llm_cls.return_value = mock_llm

        state: AgentState = {
            "user_mode": "general",
            "synthesis": "전반적으로 양호",
            "risk_assessment": sample_risk_assessment,
        }
        result = recommendation_node(state)

        assert "양호" in result["recommendation"]

    @patch("agents.nodes.recommendation_node.LLMClient")
    def test_high_risk_adds_warning(self, mock_llm_cls):
        """high 위험도 → 경고 문구 추가"""
        from agents.nodes.recommendation_node import recommendation_node

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "진단 결과입니다."
        mock_llm_cls.return_value = mock_llm

        high_risk = RiskAssessment(
            level="high", score=65, factors=["빈맥"], immediate_action_needed=True
        )
        state: AgentState = {
            "user_mode": "professional",
            "synthesis": "비정상 소견",
            "risk_assessment": high_risk,
        }
        result = recommendation_node(state)

        assert "중요" in result["recommendation"] or "위험" in result["recommendation"]


# =====================================================================
# risk_router 테스트
# =====================================================================


class TestRiskRouter:
    """위험도 라우팅 테스트"""

    def test_low_risk_routes_to_recommendation(self, sample_risk_assessment):
        """낮은 위험도 → recommendation_node"""
        from agents.edges.risk_router import route_by_risk

        state: AgentState = {"risk_assessment": sample_risk_assessment}
        assert route_by_risk(state) == "recommendation_node"

    def test_high_risk_routes_to_recommendation(self):
        """높은 위험도 → recommendation_node"""
        from agents.edges.risk_router import route_by_risk

        high_risk = RiskAssessment(
            level="critical", score=80, factors=["응급"], immediate_action_needed=True
        )
        state: AgentState = {"risk_assessment": high_risk}
        assert route_by_risk(state) == "recommendation_node"

    def test_no_risk_routes_to_recommendation(self):
        """위험도 없음 → recommendation_node"""
        from agents.edges.risk_router import route_by_risk

        state: AgentState = {}
        assert route_by_risk(state) == "recommendation_node"
