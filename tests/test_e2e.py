"""E2E 시나리오 테스트 — 전체 워크플로우 통합 검증"""
from __future__ import annotations

from unittest.mock import MagicMock, patch


from schemas.auscultation import AuscultationResult
from schemas.symptoms import SymptomInput
from schemas.vitals import VitalSigns


def _mock_all_llm_calls():
    """모든 LLM 호출을 모킹하는 데코레이터용 패치 목록"""
    return [
        patch("agents.nodes.auscultation_node.LLMClient"),
        patch("agents.nodes.vitals_node.LLMClient"),
        patch("agents.nodes.symptoms_node.LLMClient"),
        patch("agents.nodes.synthesis_node.LLMClient"),
        patch("agents.nodes.synthesis_node.MedicalSearchClient"),
        patch("agents.nodes.risk_node.LLMClient"),
        patch("agents.nodes.recommendation_node.LLMClient"),
    ]


def _setup_llm_mocks(mocks: list) -> None:
    """LLM 모킹 응답 설정"""
    # auscultation, vitals, symptoms, synthesis, search, risk, recommendation
    responses = [
        "[1단계] 분류 결과 확인: Normal (85%)\n[4단계] 종합: 정상 청진음입니다.",
        "[1단계] 심박수 75bpm 정상\n[4단계] 모든 생체신호 정상 범위입니다.",
        "[1단계] 기침, 호흡곤란 증상\n[4단계] 경미한 호흡기 증상입니다.",
        "[사고 1] 핵심 소견: 정상\n[결론] 전반적으로 양호합니다.",
        None,  # search client (별도 처리)
        '{"reasoning": "모든 지표 정상", "level": "low", "factors": ["특이 소견 없음"], "confidence": 0.9}',
        "현재 건강 상태가 양호합니다. 정기 검진을 권장합니다.",
    ]

    for i, mock_cls in enumerate(mocks):
        if i == 4:  # MedicalSearchClient
            mock_search = MagicMock()
            mock_search.search_from_analysis.return_value = MagicMock(
                total_count=0, references=[], search_successful=True, error_message=None
            )
            mock_cls.return_value = mock_search
            mock_cls.format_references_for_llm.return_value = ""
        else:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = responses[i]
            mock_cls.return_value = mock_instance


class TestE2EDefaultInputs:
    """디폴트 입력 E2E 테스트"""

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.risk_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_디폴트_입력_전체_흐름(self, *mocks):
        """디폴트 값만으로 전체 워크플로우 실행 (데모 모드)"""
        from agents.graph import build_graph

        _setup_llm_mocks(list(mocks))

        workflow = build_graph()
        compiled = workflow.compile()
        result = compiled.invoke({})

        # 입력 검증 — 디폴트 적용
        assert result["vitals"].heart_rate == 75
        assert result["vitals"].blood_pressure_sys == 120
        assert result["vitals"].body_temperature == 36.5
        assert "기침" in result["symptoms"].checklist
        assert result["user_mode"] == "general"

        # 분석 결과 존재
        assert result.get("auscultation_analysis") is not None
        assert result.get("vitals_evaluation") is not None
        assert result.get("symptom_analysis") is not None
        assert result.get("synthesis") is not None
        assert result.get("risk_assessment") is not None
        assert result.get("recommendation") is not None

        # 위험도 — 정상 입력이면 low
        assert result["risk_assessment"].level == "low"
        assert result["risk_assessment"].immediate_action_needed is False


class TestE2EWithAuscultation:
    """청진음 포함 E2E 테스트"""

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.risk_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_청진음_업로드_전체_흐름(self, *mocks):
        """청진음 포함 전체 워크플로우"""
        from agents.graph import build_graph

        _setup_llm_mocks(list(mocks))

        auscultation = AuscultationResult(
            file_name="test.wav",
            classification="Crackle",
            confidence=0.85,
            probabilities={"Normal": 0.10, "Crackle": 0.85, "Wheeze": 0.03, "Both": 0.02},
        )

        workflow = build_graph()
        compiled = workflow.compile()
        result = compiled.invoke({
            "vitals": VitalSigns(),
            "symptoms": SymptomInput(),
            "auscultation": auscultation,
            "user_mode": "general",
        })

        # 청진음 데이터 전달 확인
        assert result["auscultation"] is not None
        assert result["auscultation"].classification == "Crackle"

        # 위험도 — 비정상 청진음이므로 moderate 이상
        assert result["risk_assessment"].score >= 20

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.risk_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_오디오_없이_분석(self, *mocks):
        """청진음 없이 생체신호+증상만으로 분석"""
        from agents.graph import build_graph

        _setup_llm_mocks(list(mocks))

        workflow = build_graph()
        compiled = workflow.compile()
        result = compiled.invoke({
            "vitals": VitalSigns(heart_rate=90, body_temperature=37.5),
            "symptoms": SymptomInput(severity="중간"),
            "user_mode": "general",
        })

        # 청진음 없음 확인
        assert result.get("auscultation") is None
        assert "제공되지 않았습니다" in result["auscultation_analysis"]

        # 나머지 결과 정상
        assert result.get("recommendation") is not None


class TestE2EModeSwitch:
    """모드 전환 E2E 테스트"""

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.risk_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_general_모드(self, *mocks):
        """일반 사용자 모드 워크플로우"""
        from agents.graph import build_graph

        _setup_llm_mocks(list(mocks))

        workflow = build_graph()
        compiled = workflow.compile()
        result = compiled.invoke({"user_mode": "general"})

        assert result["user_mode"] == "general"
        assert result.get("recommendation") is not None

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.risk_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_professional_모드(self, *mocks):
        """의료 전문가 모드 워크플로우"""
        from agents.graph import build_graph

        _setup_llm_mocks(list(mocks))

        workflow = build_graph()
        compiled = workflow.compile()
        result = compiled.invoke({"user_mode": "professional"})

        assert result["user_mode"] == "professional"
        assert result.get("recommendation") is not None


class TestE2EHighRisk:
    """고위험 시나리오 E2E 테스트"""

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.risk_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_고위험_시나리오(self, *mocks):
        """고위험 입력 → 경고 포함 권고"""
        from agents.graph import build_graph

        # LLM 모킹 — 위험 키워드 포함
        mock_list = list(mocks)
        for i, mock_cls in enumerate(mock_list):
            if i == 4:  # search
                mock_search = MagicMock()
                mock_search.search_from_analysis.return_value = MagicMock(
                    total_count=0, references=[], search_successful=True, error_message=None
                )
                mock_cls.return_value = mock_search
                mock_cls.format_references_for_llm.return_value = ""
            elif i == 5:  # risk LLM
                mock_instance = MagicMock()
                mock_instance.generate.return_value = (
                    '{"reasoning": "빈맥+발열+수포음은 폐렴 가능성", '
                    '"level": "high", "factors": ["빈맥", "발열", "수포음"], "confidence": 0.85}'
                )
                mock_cls.return_value = mock_instance
            elif i == 6:  # recommendation
                mock_instance = MagicMock()
                mock_instance.generate.return_value = "즉시 병원 방문이 필요합니다."
                mock_cls.return_value = mock_instance
            else:
                mock_instance = MagicMock()
                mock_instance.generate.return_value = "긴급한 상태입니다. 즉시 조치가 필요합니다."
                mock_cls.return_value = mock_instance

        auscultation = AuscultationResult(
            file_name="urgent.wav",
            classification="Crackle",
            confidence=0.92,
            probabilities={"Normal": 0.03, "Crackle": 0.92, "Wheeze": 0.03, "Both": 0.02},
        )

        workflow = build_graph()
        compiled = workflow.compile()
        result = compiled.invoke({
            "vitals": VitalSigns(heart_rate=130, blood_pressure_sys=160, body_temperature=39.0),
            "symptoms": SymptomInput(severity="매우 심함"),
            "auscultation": auscultation,
            "user_mode": "general",
        })

        risk = result["risk_assessment"]
        assert risk.level in ("high", "critical")
        assert risk.immediate_action_needed is True
        assert "중요" in result["recommendation"] or "병원" in result["recommendation"]


class TestE2EReasoningTrace:
    """추론 과정(CoT/ReAct) 추적 테스트"""

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.risk_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_추론_추적_생성(self, *mocks):
        """워크플로우 실행 후 reasoning_trace 존재"""
        from agents.graph import build_graph

        _setup_llm_mocks(list(mocks))

        workflow = build_graph()
        compiled = workflow.compile()
        result = compiled.invoke({})

        # 추론 추적 확인
        trace = result.get("reasoning_trace")
        assert trace is not None
        assert len(trace) > 0
        # ReAct 패턴 태그 존재
        trace_text = " ".join(trace)
        assert "[사고]" in trace_text
        assert "[결론]" in trace_text


class TestE2EErrorHandling:
    """에러 핸들링 E2E 테스트"""

    @patch("agents.nodes.recommendation_node.LLMClient")
    @patch("agents.nodes.risk_node.LLMClient")
    @patch("agents.nodes.synthesis_node.MedicalSearchClient")
    @patch("agents.nodes.synthesis_node.LLMClient")
    @patch("agents.nodes.symptoms_node.LLMClient")
    @patch("agents.nodes.vitals_node.LLMClient")
    @patch("agents.nodes.auscultation_node.LLMClient")
    def test_LLM_실패_시_그레이스풀_처리(self, *mocks):
        """개별 LLM 실패 시에도 워크플로우 계속 진행"""
        from agents.graph import build_graph

        mock_list = list(mocks)
        for i, mock_cls in enumerate(mock_list):
            if i == 4:  # search
                mock_search = MagicMock()
                mock_search.search_from_analysis.return_value = MagicMock(
                    total_count=0, references=[], search_successful=False, error_message="timeout"
                )
                mock_cls.return_value = mock_search
                mock_cls.format_references_for_llm.return_value = ""
            elif i == 5:  # risk LLM — 실패해도 휴리스틱 사용
                mock_instance = MagicMock()
                mock_instance.generate.side_effect = RuntimeError("LLM 서버 연결 실패")
                mock_cls.return_value = mock_instance
            else:
                mock_instance = MagicMock()
                mock_instance.generate.return_value = "분석 결과입니다."
                mock_cls.return_value = mock_instance

        workflow = build_graph()
        compiled = workflow.compile()
        result = compiled.invoke({})

        # LLM 실패해도 휴리스틱으로 위험도 산출
        assert result.get("risk_assessment") is not None
        assert result.get("recommendation") is not None
