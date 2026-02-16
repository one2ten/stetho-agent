"""의학 문헌 검색 모듈 — 통합 인터페이스 + PubMed 프로바이더"""
from __future__ import annotations

import abc
import logging
import os
from typing import Optional

import httpx

from schemas.auscultation import AuscultationResult
from schemas.literature import LiteratureSearchResult, MedicalReference
from schemas.symptoms import SymptomInput
from schemas.vitals import VitalSigns
from utils.config_loader import get_literature_config, get_vitals_reference

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 추상 프로바이더 인터페이스
# ---------------------------------------------------------------------------


class BaseMedicalSearchProvider(abc.ABC):
    """
    의학 문헌 검색 프로바이더 추상 클래스.

    새로운 소스를 추가하려면 이 클래스를 상속하고
    `source_name`과 `search()` 메서드를 구현하세요.
    """

    @property
    @abc.abstractmethod
    def source_name(self) -> str:
        """소스 식별자 (예: 'pubmed', 'pmc', 'google_scholar')"""
        ...

    @abc.abstractmethod
    def search(self, query: str, max_results: int, timeout: int) -> list[MedicalReference]:
        """
        검색 실행.

        Args:
            query: 검색 쿼리 (영문)
            max_results: 최대 결과 수
            timeout: 요청 타임아웃 (초)

        Returns:
            MedicalReference 리스트

        Raises:
            RuntimeError: 검색 실패 시
        """
        ...


# ---------------------------------------------------------------------------
# PubMed 프로바이더
# ---------------------------------------------------------------------------


class PubMedProvider(BaseMedicalSearchProvider):
    """
    PubMed E-utilities 검색 프로바이더.

    - ESearch (PMID 검색) + ESummary (메타데이터 조회) 2단계 파이프라인
    - NCBI_API_KEY 환경변수 지원 (선택, 없으면 기본 rate limit)
    """

    @property
    def source_name(self) -> str:
        return "pubmed"

    def __init__(self) -> None:
        config = get_literature_config()
        pubmed_config = config.get("pubmed", {})
        self.base_url: str = pubmed_config.get("base_url", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils")
        self.min_year: int = pubmed_config.get("min_year", 2019)
        self.language: str = pubmed_config.get("language", "english")
        self.sort: str = pubmed_config.get("sort", "relevance")
        self.url_template: str = pubmed_config.get("url_template", "https://pubmed.ncbi.nlm.nih.gov/{id}/")
        self._api_key: Optional[str] = os.environ.get("NCBI_API_KEY")
        logger.info("PubMedProvider 초기화: base_url=%s, min_year=%d", self.base_url, self.min_year)

    def _make_request(self, url: str, params: dict, timeout: int, max_retries: int = 2) -> dict:
        """HTTP GET 요청 + 재시도 처리"""
        if self._api_key:
            params["api_key"] = self._api_key

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                response = httpx.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                last_error = e
                logger.warning("PubMed 요청 실패 (시도 %d/%d): %s", attempt, max_retries, e)

        raise RuntimeError(f"PubMed API 요청이 {max_retries}회 모두 실패했습니다: {last_error}")

    def search(self, query: str, max_results: int = 5, timeout: int = 15) -> list[MedicalReference]:
        """
        PubMed 검색 실행: ESearch → ESummary 2단계.

        Args:
            query: 영문 검색 쿼리
            max_results: 최대 결과 수
            timeout: 요청 타임아웃 (초)

        Returns:
            MedicalReference 리스트
        """
        # 1단계: ESearch — PMID 목록 조회
        esearch_params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
            "sort": self.sort,
            "mindate": str(self.min_year),
            "datetype": "pdat",
        }
        esearch_data = self._make_request(f"{self.base_url}/esearch.fcgi", esearch_params, timeout)

        id_list = esearch_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            logger.info("PubMed 검색 결과 없음: query='%s'", query)
            return []

        logger.info("PubMed ESearch: %d건 PMID 조회 완료", len(id_list))

        # 2단계: ESummary — 논문 메타데이터 조회
        esummary_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json",
        }
        esummary_data = self._make_request(f"{self.base_url}/esummary.fcgi", esummary_params, timeout)

        result_data = esummary_data.get("result", {})
        references: list[MedicalReference] = []

        for i, pmid in enumerate(id_list):
            article = result_data.get(pmid, {})
            if not article or isinstance(article, str):
                continue

            # 저자 추출
            authors_raw = article.get("authors", [])
            authors = [a.get("name", "") for a in authors_raw if isinstance(a, dict)]

            # DOI 추출 (elocationid 필드: "doi: 10.xxxx/...")
            doi = None
            elocation = article.get("elocationid", "")
            if elocation.startswith("doi:"):
                doi = elocation.replace("doi:", "").strip()

            # 연도 추출 (pubdate: "2024 Jan 15" → "2024")
            pubdate = article.get("pubdate", "")
            year = pubdate.split()[0] if pubdate else ""

            # 관련성 점수: 검색 순위 기반 (1위 = 1.0, 선형 감소)
            relevance = round(1.0 - (i / max(len(id_list), 1)) * 0.5, 2)

            references.append(MedicalReference(
                source="pubmed",
                source_id=pmid,
                title=article.get("title", ""),
                authors=authors,
                journal=article.get("source", ""),
                year=year,
                doi=doi,
                url=self.url_template.format(id=pmid),
                relevance_score=relevance,
            ))

        logger.info("PubMed ESummary: %d건 메타데이터 조회 완료", len(references))
        return references


# ---------------------------------------------------------------------------
# 프로바이더 레지스트리
# ---------------------------------------------------------------------------

# 새 프로바이더를 추가하려면 여기에 등록
PROVIDER_REGISTRY: dict[str, type[BaseMedicalSearchProvider]] = {
    "pubmed": PubMedProvider,
}


# ---------------------------------------------------------------------------
# 통합 검색 클라이언트
# ---------------------------------------------------------------------------


class MedicalSearchClient:
    """
    의학 문헌 통합 검색 클라이언트.

    - config/literature.yaml의 active_sources 기반으로 프로바이더 활성화
    - 여러 소스 결과를 통합하여 LiteratureSearchResult로 반환
    - 분석 결과(청진음, 증상, 생체신호)를 검색 쿼리로 변환
    - LLM 프롬프트 및 UI 표시용 포맷팅 제공
    """

    def __init__(self) -> None:
        config = get_literature_config()
        self._config = config
        common = config.get("common", {})
        self.max_results: int = common.get("max_results_per_source", 5)
        self.timeout: int = common.get("timeout", 15)
        self.max_retries: int = common.get("max_retries", 2)

        # 활성 소스에 해당하는 프로바이더 인스턴스 생성
        active_sources = config.get("active_sources", ["pubmed"])
        self._providers: list[BaseMedicalSearchProvider] = []
        for source_name in active_sources:
            provider_cls = PROVIDER_REGISTRY.get(source_name)
            if provider_cls:
                try:
                    self._providers.append(provider_cls())
                except Exception as e:
                    logger.warning("%s 프로바이더 초기화 실패: %s", source_name, e)
            else:
                logger.warning("알 수 없는 검색 소스: %s (무시됨)", source_name)

        # 쿼리 매핑 로딩
        self._query_mapping = config.get("query_mapping", {})

        logger.info(
            "MedicalSearchClient 초기화: 활성 소스=%s",
            [p.source_name for p in self._providers],
        )

    def build_search_query(
        self,
        auscultation: Optional[AuscultationResult] = None,
        symptoms: Optional[SymptomInput] = None,
        vitals: Optional[VitalSigns] = None,
    ) -> str:
        """
        분석 결과를 PubMed 영문 검색 쿼리로 변환.

        Args:
            auscultation: 청진음 분류 결과
            symptoms: 증상 입력
            vitals: 생체신호

        Returns:
            영문 검색 쿼리 문자열
        """
        terms: list[str] = []

        # 1. 청진음 분류 → 검색어
        if auscultation:
            aus_mapping = self._query_mapping.get("auscultation", {})
            mapped = aus_mapping.get(auscultation.classification, "")
            if mapped:
                terms.append(mapped)

        # 2. 증상 → 검색어 (최대 3개)
        if symptoms and symptoms.checklist:
            sym_mapping = self._query_mapping.get("symptoms", {})
            count = 0
            for symptom in symptoms.checklist:
                mapped = sym_mapping.get(symptom, "")
                if mapped and count < 3:
                    terms.append(mapped)
                    count += 1

        # 3. 생체신호 이상 → 검색어
        if vitals:
            vitals_mapping = self._query_mapping.get("vitals", {})
            vitals_ref = get_vitals_reference()
            hr_ref = vitals_ref.get("heart_rate", {}).get("normal", {})
            bp_ref = vitals_ref.get("blood_pressure", {}).get("systolic", {}).get("normal", {})
            temp_ref = vitals_ref.get("body_temperature", {})

            if vitals.heart_rate > hr_ref.get("max", 100):
                terms.append(vitals_mapping.get("tachycardia", "tachycardia"))
            elif vitals.heart_rate < hr_ref.get("min", 60):
                terms.append(vitals_mapping.get("bradycardia", "bradycardia"))

            if vitals.blood_pressure_sys > 140:
                terms.append(vitals_mapping.get("hypertension", "hypertension"))
            elif vitals.blood_pressure_sys < 90:
                terms.append(vitals_mapping.get("hypotension", "hypotension"))

            if vitals.body_temperature > temp_ref.get("low_grade_fever", {}).get("min", 37.5):
                terms.append(vitals_mapping.get("fever", "fever"))
            elif vitals.body_temperature < temp_ref.get("hypothermia", {}).get("max", 35.0):
                terms.append(vitals_mapping.get("hypothermia", "hypothermia"))

        # 기본 컨텍스트 추가
        if not terms:
            terms = ["lung auscultation respiratory diagnosis"]

        query = " ".join(terms)
        logger.info("검색 쿼리 생성: '%s'", query)
        return query

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
    ) -> LiteratureSearchResult:
        """
        모든 활성 소스에서 통합 검색 실행.

        Args:
            query: 영문 검색 쿼리
            max_results: 소스당 최대 결과 수 (None이면 config 기본값)

        Returns:
            LiteratureSearchResult (모든 소스 통합 결과)
        """
        max_results = max_results or self.max_results
        all_references: list[MedicalReference] = []
        sources_used: list[str] = []
        errors: list[str] = []

        for provider in self._providers:
            try:
                refs = provider.search(query, max_results, self.timeout)
                all_references.extend(refs)
                sources_used.append(provider.source_name)
                logger.info("%s: %d건 검색 완료", provider.source_name, len(refs))
            except Exception as e:
                error_msg = f"{provider.source_name} 검색 실패: {e}"
                errors.append(error_msg)
                logger.warning(error_msg)

        # 관련성 점수 기준 정렬
        all_references.sort(key=lambda r: r.relevance_score, reverse=True)

        search_successful = len(sources_used) > 0
        error_message = "; ".join(errors) if errors else None

        return LiteratureSearchResult(
            query=query,
            total_count=len(all_references),
            references=all_references,
            sources_used=sources_used,
            search_successful=search_successful,
            error_message=error_message,
        )

    def search_from_analysis(
        self,
        auscultation: Optional[AuscultationResult] = None,
        symptoms: Optional[SymptomInput] = None,
        vitals: Optional[VitalSigns] = None,
    ) -> LiteratureSearchResult:
        """
        분석 결과 기반 자동 검색 (쿼리 빌드 + 검색 통합).

        Args:
            auscultation: 청진음 분류 결과
            symptoms: 증상 입력
            vitals: 생체신호

        Returns:
            LiteratureSearchResult
        """
        query = self.build_search_query(auscultation, symptoms, vitals)
        return self.search(query)

    @staticmethod
    def format_references_for_llm(result: LiteratureSearchResult) -> str:
        """
        LLM 프롬프트에 삽입할 참고 문헌 텍스트 포맷팅.

        Args:
            result: 검색 결과

        Returns:
            포맷팅된 참고 문헌 텍스트 (비어있으면 빈 문자열)
        """
        if not result.search_successful or not result.references:
            return ""

        lines = ["[참고 의학 문헌]"]
        for i, ref in enumerate(result.references, 1):
            first_author = ref.authors[0] if ref.authors else "Unknown"
            et_al = " et al." if len(ref.authors) > 1 else ""
            lines.append(
                f"[{i}] {ref.title}. {first_author}{et_al}. "
                f"{ref.journal}, {ref.year}. ({ref.source.upper()}: {ref.source_id})"
            )
        return "\n".join(lines)

    @staticmethod
    def format_references_for_display(result: LiteratureSearchResult) -> list[dict]:
        """
        UI 표시용 참고 문헌 딕셔너리 리스트 포맷팅.

        Args:
            result: 검색 결과

        Returns:
            딕셔너리 리스트 (각 항목: title, authors_str, journal, year, url, source, source_id)
        """
        if not result.search_successful or not result.references:
            return []

        display_list = []
        for ref in result.references:
            authors_str = ", ".join(ref.authors[:3])
            if len(ref.authors) > 3:
                authors_str += f" 외 {len(ref.authors) - 3}명"

            display_list.append({
                "title": ref.title,
                "authors_str": authors_str,
                "journal": ref.journal,
                "year": ref.year,
                "url": ref.url,
                "source": ref.source,
                "source_id": ref.source_id,
            })
        return display_list


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="의학 문헌 검색 테스트")
    parser.add_argument("--test", action="store_true", help="테스트 모드 실행")
    parser.add_argument("--query", type=str, default=None, help="직접 검색 쿼리")
    args = parser.parse_args()

    if args.test:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        print("=" * 60)
        print("MedicalSearchClient 테스트")
        print("=" * 60)

        client = MedicalSearchClient()
        print(f"✓ 활성 소스: {[p.source_name for p in client._providers]}")

        # 1. 쿼리 빌드 테스트 (디폴트 값 사용)
        from schemas.auscultation import AuscultationResult

        sample_aus = AuscultationResult(
            file_name="sample.wav",
            classification="Crackle",
            confidence=0.85,
            probabilities={"Normal": 0.10, "Crackle": 0.85, "Wheeze": 0.03, "Both": 0.02},
        )
        sample_symptoms = SymptomInput()
        sample_vitals = VitalSigns()

        query = client.build_search_query(sample_aus, sample_symptoms, sample_vitals)
        print(f"✓ 생성된 쿼리: '{query}'")

        # 2. 실제 검색 테스트
        search_query = args.query or query
        print(f"\n--- PubMed 검색: '{search_query}' ---")
        try:
            result = client.search(search_query)
            print(f"✓ 검색 성공: {result.search_successful}")
            print(f"✓ 사용 소스: {result.sources_used}")
            print(f"✓ 총 결과: {result.total_count}건")

            if result.references:
                print("\n--- 검색 결과 ---")
                for i, ref in enumerate(result.references, 1):
                    first_author = ref.authors[0] if ref.authors else "N/A"
                    print(f"  [{i}] {ref.title[:80]}...")
                    print(f"      {first_author} | {ref.journal} ({ref.year})")
                    print(f"      {ref.url}")

                # 3. LLM 포맷 테스트
                llm_text = MedicalSearchClient.format_references_for_llm(result)
                print(f"\n--- LLM 프롬프트 포맷 ---\n{llm_text}")
            else:
                print("  검색 결과가 없습니다.")

            print("\n테스트 성공!")
        except Exception as e:
            print(f"✗ 검색 실패: {e}")
