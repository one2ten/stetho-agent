"""의학 문헌 검색 결과 스키마"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class MedicalReference(BaseModel):
    """의학 문헌 참조 스키마 (소스 무관 통합 포맷)"""

    source: str = Field(
        default="pubmed",
        description="검색 소스 (pubmed, pmc, google_scholar 등)",
    )
    source_id: str = Field(
        description="소스별 고유 식별자 (PMID, PMC ID 등)",
    )
    title: str = Field(
        description="논문 제목",
    )
    authors: list[str] = Field(
        default_factory=list,
        description="저자 목록",
    )
    journal: str = Field(
        default="",
        description="게재 저널명",
    )
    year: str = Field(
        default="",
        description="출판 연도",
    )
    doi: Optional[str] = Field(
        default=None,
        description="DOI 식별자",
    )
    url: str = Field(
        default="",
        description="논문 URL",
    )
    relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="검색 관련성 점수 (0-1)",
    )


class LiteratureSearchResult(BaseModel):
    """통합 문헌 검색 결과 스키마"""

    query: str = Field(
        default="",
        description="실행된 검색 쿼리",
    )
    total_count: int = Field(
        default=0,
        ge=0,
        description="총 검색 결과 수 (모든 소스 합계)",
    )
    references: list[MedicalReference] = Field(
        default_factory=list,
        description="검색된 의학 문헌 목록 (모든 소스 통합)",
    )
    sources_used: list[str] = Field(
        default_factory=list,
        description="검색에 사용된 소스 목록",
    )
    search_successful: bool = Field(
        default=True,
        description="검색 성공 여부 (하나라도 성공하면 True)",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="검색 실패 시 에러 메시지",
    )
