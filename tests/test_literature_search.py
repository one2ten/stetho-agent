"""의학 문헌 검색 테스트"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from schemas.literature import MedicalReference, LiteratureSearchResult
from schemas.auscultation import AuscultationResult
from schemas.symptoms import SymptomInput
from schemas.vitals import VitalSigns


# ---------------------------------------------------------------------------
# 스키마 단위 테스트
# ---------------------------------------------------------------------------


class TestMedicalReference:
    """MedicalReference 스키마 테스트"""

    def test_생성(self):
        """필수 필드로 생성 확인"""
        ref = MedicalReference(
            source_id="12345678",
            title="Test Article",
        )
        assert ref.source_id == "12345678"
        assert ref.title == "Test Article"
        assert ref.source == "pubmed"

    def test_디폴트_값(self):
        """선택 필드 디폴트 값 확인"""
        ref = MedicalReference(source_id="1", title="Test")
        assert ref.authors == []
        assert ref.journal == ""
        assert ref.year == ""
        assert ref.doi is None
        assert ref.url == ""
        assert ref.relevance_score == 0.0

    def test_소스_지정(self):
        """소스 필드 커스텀 값 확인"""
        ref = MedicalReference(source="pmc", source_id="PMC123", title="Test")
        assert ref.source == "pmc"
        assert ref.source_id == "PMC123"

    def test_관련성_점수_범위(self):
        """관련성 점수 0-1 범위 검증"""
        ref = MedicalReference(source_id="1", title="Test", relevance_score=0.5)
        assert ref.relevance_score == 0.5

        with pytest.raises(Exception):
            MedicalReference(source_id="1", title="Test", relevance_score=1.5)

        with pytest.raises(Exception):
            MedicalReference(source_id="1", title="Test", relevance_score=-0.1)


class TestLiteratureSearchResult:
    """LiteratureSearchResult 스키마 테스트"""

    def test_디폴트_값(self):
        """빈 검색 결과 디폴트 확인"""
        result = LiteratureSearchResult()
        assert result.query == ""
        assert result.total_count == 0
        assert result.references == []
        assert result.sources_used == []
        assert result.search_successful is True
        assert result.error_message is None

    def test_실패_상태(self):
        """검색 실패 상태 확인"""
        result = LiteratureSearchResult(
            search_successful=False,
            error_message="네트워크 연결 실패",
        )
        assert result.search_successful is False
        assert result.error_message == "네트워크 연결 실패"

    def test_소스_목록(self):
        """사용된 소스 목록 확인"""
        result = LiteratureSearchResult(
            sources_used=["pubmed", "pmc"],
            total_count=10,
        )
        assert "pubmed" in result.sources_used
        assert "pmc" in result.sources_used

    def test_픽스처_생성(self, sample_literature_result: LiteratureSearchResult):
        """conftest 픽스처 정상 생성 확인"""
        assert sample_literature_result.total_count == 2
        assert len(sample_literature_result.references) == 2
        assert sample_literature_result.search_successful is True


# ---------------------------------------------------------------------------
# Config 테스트
# ---------------------------------------------------------------------------


class TestLiteratureConfig:
    """문헌 검색 설정 테스트"""

    def test_설정_로딩(self):
        """literature.yaml 로딩 확인"""
        from utils.config_loader import get_literature_config

        config = get_literature_config()
        assert "pubmed" in config
        assert "query_mapping" in config
        assert "active_sources" in config
        assert "common" in config

    def test_활성_소스_설정(self):
        """active_sources에 pubmed 포함 확인"""
        from utils.config_loader import get_literature_config

        config = get_literature_config()
        assert "pubmed" in config["active_sources"]

    def test_쿼리_매핑_청진음(self):
        """청진음 분류별 검색어 매핑 확인"""
        from utils.config_loader import get_literature_config

        config = get_literature_config()
        aus_mapping = config["query_mapping"]["auscultation"]
        assert "Normal" in aus_mapping
        assert "Crackle" in aus_mapping
        assert "Wheeze" in aus_mapping
        assert "Both" in aus_mapping

    def test_쿼리_매핑_증상_완전성(self):
        """12개 증상 모두 매핑되어 있는지 확인"""
        from utils.config_loader import get_literature_config
        from schemas.symptoms import SYMPTOM_OPTIONS

        config = get_literature_config()
        sym_mapping = config["query_mapping"]["symptoms"]
        for symptom in SYMPTOM_OPTIONS:
            assert symptom in sym_mapping, f"증상 '{symptom}'의 매핑이 없습니다"

    def test_공통_설정(self):
        """공통 설정 값 확인"""
        from utils.config_loader import get_literature_config

        config = get_literature_config()
        common = config["common"]
        assert common["max_results_per_source"] > 0
        assert common["timeout"] > 0


# ---------------------------------------------------------------------------
# 쿼리 빌드 테스트
# ---------------------------------------------------------------------------


class TestBuildSearchQuery:
    """MedicalSearchClient.build_search_query() 테스트"""

    def test_청진음만(self):
        """청진음 분류만으로 쿼리 생성"""
        from models.literature_search import MedicalSearchClient

        client = MedicalSearchClient()
        aus = AuscultationResult(
            file_name="test.wav",
            classification="Crackle",
            confidence=0.9,
            probabilities={"Normal": 0.05, "Crackle": 0.9, "Wheeze": 0.03, "Both": 0.02},
        )
        query = client.build_search_query(auscultation=aus)
        assert "crackle" in query.lower()

    def test_증상만(self):
        """증상만으로 쿼리 생성"""
        from models.literature_search import MedicalSearchClient

        client = MedicalSearchClient()
        symptoms = SymptomInput(checklist=["기침", "호흡곤란"])
        query = client.build_search_query(symptoms=symptoms)
        assert "cough" in query.lower()
        assert "dyspnea" in query.lower()

    def test_증상_최대3개_제한(self):
        """증상 키워드 최대 3개까지만 포함"""
        from models.literature_search import MedicalSearchClient

        client = MedicalSearchClient()
        symptoms = SymptomInput(
            checklist=["기침", "호흡곤란", "가슴 통증", "발열", "피로감"],
        )
        query = client.build_search_query(symptoms=symptoms)
        # 검색어에 영문 증상 키워드가 3개까지만 포함
        terms = query.split()
        symptom_keywords = {"cough", "dyspnea", "chest", "pain", "fever", "fatigue"}
        matched = sum(1 for t in terms if t.lower() in symptom_keywords)
        assert matched <= 5  # "chest pain"은 2단어이므로 3개 증상 = 최대 5단어

    def test_비정상_생체신호_빈맥(self):
        """빈맥(HR>100) 시 tachycardia 포함"""
        from models.literature_search import MedicalSearchClient

        client = MedicalSearchClient()
        vitals = VitalSigns(heart_rate=120)
        query = client.build_search_query(vitals=vitals)
        assert "tachycardia" in query.lower()

    def test_비정상_생체신호_고혈압(self):
        """고혈압(SYS>140) 시 hypertension 포함"""
        from models.literature_search import MedicalSearchClient

        client = MedicalSearchClient()
        vitals = VitalSigns(blood_pressure_sys=160, blood_pressure_dia=100)
        query = client.build_search_query(vitals=vitals)
        assert "hypertension" in query.lower()

    def test_비정상_생체신호_발열(self):
        """발열(>37.5) 시 fever 포함"""
        from models.literature_search import MedicalSearchClient

        client = MedicalSearchClient()
        vitals = VitalSigns(body_temperature=38.5)
        query = client.build_search_query(vitals=vitals)
        assert "fever" in query.lower()

    def test_정상_생체신호_무추가(self):
        """정상 생체신호에서는 vitals 키워드 미추가"""
        from models.literature_search import MedicalSearchClient

        client = MedicalSearchClient()
        vitals = VitalSigns()  # 디폴트: HR=75, BP=120/80, Temp=36.5
        aus = AuscultationResult(
            file_name="test.wav",
            classification="Normal",
            confidence=0.9,
            probabilities={"Normal": 0.9, "Crackle": 0.05, "Wheeze": 0.03, "Both": 0.02},
        )
        query = client.build_search_query(auscultation=aus, vitals=vitals)
        assert "tachycardia" not in query.lower()
        assert "hypertension" not in query.lower()
        assert "fever" not in query.lower()

    def test_빈_입력_기본_쿼리(self):
        """아무 입력 없을 때 기본 쿼리 생성"""
        from models.literature_search import MedicalSearchClient

        client = MedicalSearchClient()
        query = client.build_search_query()
        assert len(query) > 0

    def test_종합_쿼리(self):
        """청진음 + 증상 + 생체신호 종합 쿼리"""
        from models.literature_search import MedicalSearchClient

        client = MedicalSearchClient()
        aus = AuscultationResult(
            file_name="test.wav",
            classification="Wheeze",
            confidence=0.8,
            probabilities={"Normal": 0.1, "Crackle": 0.05, "Wheeze": 0.8, "Both": 0.05},
        )
        symptoms = SymptomInput(checklist=["기침", "호흡곤란"])
        vitals = VitalSigns(heart_rate=110)  # 빈맥

        query = client.build_search_query(aus, symptoms, vitals)
        assert "wheez" in query.lower()
        assert "cough" in query.lower()
        assert "tachycardia" in query.lower()


# ---------------------------------------------------------------------------
# 포맷팅 테스트
# ---------------------------------------------------------------------------


class TestFormatReferences:
    """참고 문헌 포맷팅 테스트"""

    def test_llm_포맷(self, sample_literature_result: LiteratureSearchResult):
        """LLM 프롬프트용 포맷팅 확인"""
        from models.literature_search import MedicalSearchClient

        text = MedicalSearchClient.format_references_for_llm(sample_literature_result)
        assert "[참고 의학 문헌]" in text
        assert "[1]" in text
        assert "[2]" in text
        assert "PUBMED" in text

    def test_llm_포맷_빈_결과(self):
        """빈 결과에 대한 LLM 포맷"""
        from models.literature_search import MedicalSearchClient

        empty_result = LiteratureSearchResult()
        text = MedicalSearchClient.format_references_for_llm(empty_result)
        assert text == ""

    def test_llm_포맷_실패_결과(self):
        """검색 실패 시 빈 문자열 반환"""
        from models.literature_search import MedicalSearchClient

        failed = LiteratureSearchResult(search_successful=False)
        text = MedicalSearchClient.format_references_for_llm(failed)
        assert text == ""

    def test_display_포맷(self, sample_literature_result: LiteratureSearchResult):
        """UI 표시용 포맷팅 확인"""
        from models.literature_search import MedicalSearchClient

        display = MedicalSearchClient.format_references_for_display(sample_literature_result)
        assert len(display) == 2
        assert "title" in display[0]
        assert "authors_str" in display[0]
        assert "journal" in display[0]
        assert "url" in display[0]
        assert "source" in display[0]

    def test_display_포맷_빈_결과(self):
        """빈 결과에 대한 UI 포맷"""
        from models.literature_search import MedicalSearchClient

        empty = LiteratureSearchResult()
        display = MedicalSearchClient.format_references_for_display(empty)
        assert display == []


# ---------------------------------------------------------------------------
# 모킹 검색 테스트
# ---------------------------------------------------------------------------


class TestPubMedProviderMock:
    """PubMedProvider 모킹 테스트 (네트워크 불필요)"""

    MOCK_ESEARCH_RESPONSE = {
        "esearchresult": {
            "count": "142",
            "retmax": "2",
            "idlist": ["39876543", "39812345"],
        }
    }

    MOCK_ESUMMARY_RESPONSE = {
        "result": {
            "uids": ["39876543", "39812345"],
            "39876543": {
                "uid": "39876543",
                "pubdate": "2024 Jan",
                "source": "Respiratory Medicine",
                "authors": [{"name": "Kim SH"}, {"name": "Park JW"}],
                "title": "Clinical significance of lung crackles",
                "elocationid": "doi: 10.1016/j.rmed.2024.01.001",
            },
            "39812345": {
                "uid": "39812345",
                "pubdate": "2023 Nov",
                "source": "Chest",
                "authors": [{"name": "Lee YS"}],
                "title": "Auscultation findings and pulmonary function",
                "elocationid": "doi: 10.1016/j.chest.2023.11.002",
            },
        }
    }

    @patch("models.literature_search.httpx.get")
    def test_검색_파이프라인(self, mock_get: MagicMock):
        """ESearch + ESummary 전체 파이프라인 테스트"""
        from models.literature_search import PubMedProvider

        # 첫 호출 = ESearch, 두 번째 호출 = ESummary
        mock_response_1 = MagicMock()
        mock_response_1.json.return_value = self.MOCK_ESEARCH_RESPONSE
        mock_response_1.raise_for_status = MagicMock()

        mock_response_2 = MagicMock()
        mock_response_2.json.return_value = self.MOCK_ESUMMARY_RESPONSE
        mock_response_2.raise_for_status = MagicMock()

        mock_get.side_effect = [mock_response_1, mock_response_2]

        provider = PubMedProvider()
        refs = provider.search("lung crackles", max_results=2, timeout=10)

        assert len(refs) == 2
        assert refs[0].source == "pubmed"
        assert refs[0].source_id == "39876543"
        assert refs[0].title == "Clinical significance of lung crackles"
        assert refs[0].journal == "Respiratory Medicine"
        assert refs[0].year == "2024"
        assert refs[0].doi == "10.1016/j.rmed.2024.01.001"
        assert "Kim SH" in refs[0].authors
        assert refs[0].relevance_score > refs[1].relevance_score

    @patch("models.literature_search.httpx.get")
    def test_빈_검색_결과(self, mock_get: MagicMock):
        """검색 결과 없을 때 빈 리스트 반환"""
        from models.literature_search import PubMedProvider

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "esearchresult": {"count": "0", "idlist": []}
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        provider = PubMedProvider()
        refs = provider.search("zzzznonexistent", max_results=5, timeout=10)
        assert refs == []

    @patch("models.literature_search.httpx.get")
    def test_네트워크_실패_에러(self, mock_get: MagicMock):
        """네트워크 실패 시 RuntimeError"""
        from models.literature_search import PubMedProvider

        mock_get.side_effect = Exception("Connection timeout")

        provider = PubMedProvider()
        with pytest.raises(RuntimeError, match="모두 실패"):
            provider.search("test", max_results=5, timeout=5)


# ---------------------------------------------------------------------------
# 통합 클라이언트 모킹 테스트
# ---------------------------------------------------------------------------


class TestMedicalSearchClientMock:
    """MedicalSearchClient 통합 테스트 (모킹)"""

    @patch("models.literature_search.httpx.get")
    def test_search_from_analysis(self, mock_get: MagicMock):
        """분석 결과 기반 자동 검색 테스트"""
        from models.literature_search import MedicalSearchClient

        mock_response_1 = MagicMock()
        mock_response_1.json.return_value = {
            "esearchresult": {"count": "1", "idlist": ["11111111"]}
        }
        mock_response_1.raise_for_status = MagicMock()

        mock_response_2 = MagicMock()
        mock_response_2.json.return_value = {
            "result": {
                "uids": ["11111111"],
                "11111111": {
                    "uid": "11111111",
                    "pubdate": "2024",
                    "source": "Test Journal",
                    "authors": [{"name": "Test A"}],
                    "title": "Test Article",
                    "elocationid": "",
                },
            }
        }
        mock_response_2.raise_for_status = MagicMock()

        mock_get.side_effect = [mock_response_1, mock_response_2]

        client = MedicalSearchClient()
        aus = AuscultationResult(
            file_name="test.wav",
            classification="Wheeze",
            confidence=0.9,
            probabilities={"Normal": 0.05, "Crackle": 0.02, "Wheeze": 0.9, "Both": 0.03},
        )
        result = client.search_from_analysis(auscultation=aus)

        assert result.search_successful is True
        assert result.total_count == 1
        assert "pubmed" in result.sources_used


# ---------------------------------------------------------------------------
# 프로바이더 레지스트리 테스트
# ---------------------------------------------------------------------------


class TestProviderRegistry:
    """프로바이더 레지스트리 테스트"""

    def test_pubmed_등록(self):
        """PubMed 프로바이더가 레지스트리에 등록되어 있는지"""
        from models.literature_search import PROVIDER_REGISTRY

        assert "pubmed" in PROVIDER_REGISTRY

    def test_추상_클래스(self):
        """BaseMedicalSearchProvider 인스턴스화 불가 확인"""
        from models.literature_search import BaseMedicalSearchProvider

        with pytest.raises(TypeError):
            BaseMedicalSearchProvider()


# ---------------------------------------------------------------------------
# 통합 테스트 (실제 네트워크 필요)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestMedicalSearchIntegration:
    """실제 PubMed API 통합 테스트"""

    def test_실제_검색(self):
        """실제 PubMed 검색 실행"""
        from models.literature_search import MedicalSearchClient

        client = MedicalSearchClient()
        try:
            result = client.search("lung crackles diagnosis", max_results=3)
        except RuntimeError:
            pytest.skip("PubMed API 접속 불가")

        assert result.search_successful is True
        assert result.total_count > 0
        assert len(result.references) <= 3
        # 각 레퍼런스 필드 확인
        for ref in result.references:
            assert ref.source == "pubmed"
            assert ref.source_id != ""
            assert ref.title != ""
            assert ref.url.startswith("https://")

    def test_디폴트_분석_기반_검색(self):
        """디폴트 입력으로 분석 기반 검색"""
        from models.literature_search import MedicalSearchClient

        client = MedicalSearchClient()
        try:
            result = client.search_from_analysis(
                symptoms=SymptomInput(),
                vitals=VitalSigns(),
            )
        except RuntimeError:
            pytest.skip("PubMed API 접속 불가")

        assert result.search_successful is True
