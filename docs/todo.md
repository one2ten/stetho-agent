# StethoAgent 미래 의료 에이전트 통합 계획

> 본 문서는 StethoAgent의 향후 확장 방향을 기록합니다.
> 현재 PubMed 기본 검색이 구현되었으며, 아래는 추후 연동 가능한 의료 전문 에이전트 및 데이터 소스입니다.

---

## 1. 의학 문헌 검색 소스 확장

### 1.1 현재 구현: PubMed (E-utilities)
- ESearch + ESummary 2단계 검색
- `BaseMedicalSearchProvider` 추상 인터페이스로 확장 가능
- `PROVIDER_REGISTRY`에 새 프로바이더 등록만으로 소스 추가

### 1.2 PMC Open Access (P1)
- PubMed Central 전문(full-text) 논문 검색
- 무료 전문 접근 가능한 논문만 필터링
- `PmcProvider(BaseMedicalSearchProvider)` 구현
- ESearch(`db=pmc`) + EFetch(XML) 파이프라인

### 1.3 Google Scholar (P2)
- SerpAPI 또는 scholarly 라이브러리 활용
- 인용 수 기반 논문 중요도 평가
- `GoogleScholarProvider(BaseMedicalSearchProvider)` 구현

### 1.4 Cochrane Library (P2)
- 체계적 문헌 고찰(Systematic Review) 전문
- 근거중심의학(EBM) 최고 수준 근거 제공
- REST API 연동

### 1.5 UpToDate / DynaMed (P3)
- 임상 의사결정 지원 시스템
- 유료 API — 기관 라이선스 필요
- 최신 임상 가이드라인 실시간 참조

---

## 2. 전문 의료 에이전트 연동

### 2.1 호흡기내과 전문 에이전트
- **입력**: Crackle/Wheeze 분류 결과 + 증상 + 생체신호
- **기능**: COPD/천식/폐렴/간질성 폐질환 감별 진단 보조
- **추가 데이터**: 폐기능 검사(PFT), 흉부 X-ray/CT 소견
- **구현 방식**: LangGraph 서브그래프 또는 독립 에이전트 호출

### 2.2 심장내과 전문 에이전트
- **입력**: 심음 분류 결과 + 심박수 + 혈압
- **기능**: 심잡음/부정맥/심부전 위험도 평가
- **추가 데이터**: 심전도(ECG), 심초음파, BNP/NT-proBNP
- **구현 방식**: 별도 AST 모델(심음 전용) + 전문 LLM 프롬프트

### 2.3 응급의학 전문 에이전트
- **트리거**: `RiskAssessment.level == "critical"`
- **기능**: 응급 프로토콜 가이드, 트리아지(Triage) 레벨 분류
- **출력**: 즉시 행동 지침, 응급실 방문 권고
- **구현 방식**: 조건부 라우팅 → 응급 에이전트 분기

### 2.4 약물 상호작용 에이전트
- **입력**: 현재 복용 약물 목록 + 진단 추정
- **기능**: 약물 간 상호작용 확인, 금기 약물 경고
- **데이터 소스**: DrugBank API, OpenFDA
- **구현 방식**: 독립 에이전트 → 권장사항에 약물 정보 반영

---

## 3. 외부 의학 데이터베이스 연동

### 3.1 ClinicalTrials.gov
- 관련 임상 시험 검색 (NCT ID 기반)
- REST API 무료 제공
- 참여 가능한 임상 시험 추천

### 3.2 ICD-11 코드 매핑
- 증상/진단 → ICD-11 코드 자동 매핑
- WHO ICD API 연동
- 의료 기관 간 표준 코딩 지원

### 3.3 SNOMED CT
- 의학 용어 표준화
- 증상/소견/진단의 체계적 분류
- 다국어 지원 (한국어 포함)

---

## 4. 멀티 에이전트 오케스트레이션

### 4.1 현재 구조
```
단일 LangGraph → 다중 노드 (순차/병렬)
```

### 4.2 목표 구조
```
오케스트레이터 에이전트
├── 청진음 분석 에이전트
├── 생체신호 분석 에이전트
├── 증상 분석 에이전트
├── 문헌 검색 에이전트 (다중 소스)
├── 전문 진료과 에이전트 (조건부)
└── 종합 판단 에이전트
```

### 4.3 에이전트 간 통신
- **프로토콜**: JSON-RPC 또는 Google A2A Protocol
- **상태 공유**: 공유 AgentState TypedDict
- **비동기 수집**: asyncio 기반 병렬 에이전트 실행
- **합의 메커니즘**: 다수 에이전트 소견 종합, 의견 일치도 산정

---

## 5. FHIR 표준 호환 (장기)

### 5.1 HL7 FHIR R4 리소스 매핑
| StethoAgent 스키마 | FHIR 리소스 |
|---|---|
| `VitalSigns` | `Observation` (vital-signs) |
| `SymptomInput` | `Condition` |
| `AuscultationResult` | `Observation` (exam) |
| `AnalysisReport` | `DiagnosticReport` |
| `RiskAssessment` | `RiskAssessment` |

### 5.2 EHR 시스템 연동
- SMART on FHIR 인증
- 환자 컨텍스트 자동 로딩
- 분석 결과를 EHR에 기록

---

## 6. 우선순위 로드맵

| 우선순위 | 항목 | 난이도 | 상태 |
|---------|------|--------|------|
| **P0** | PubMed 기본 검색 | 완료 | ✅ 구현 완료 |
| **P1** | PMC 전문 논문 검색 | 중 | 대기 |
| **P1** | ClinicalTrials.gov 연동 | 중 | 대기 |
| **P1** | 호흡기내과 전문 에이전트 | 고 | 대기 |
| **P2** | Google Scholar 연동 | 중 | 대기 |
| **P2** | ICD-11 코드 매핑 | 중 | 대기 |
| **P2** | 약물 상호작용 에이전트 | 중 | 대기 |
| **P3** | 멀티 에이전트 오케스트레이션 | 고 | 대기 |
| **P3** | FHIR 표준 호환 | 고 | 대기 |
| **P3** | UpToDate/DynaMed 연동 | 중 | 대기 |

---

## 7. 새 검색 소스 추가 방법 (개발자 가이드)

```python
# 1. BaseMedicalSearchProvider를 상속하여 새 프로바이더 구현
class NewSourceProvider(BaseMedicalSearchProvider):
    @property
    def source_name(self) -> str:
        return "new_source"

    def search(self, query, max_results, timeout) -> list[MedicalReference]:
        # API 호출 구현
        ...

# 2. PROVIDER_REGISTRY에 등록 (models/literature_search.py)
PROVIDER_REGISTRY["new_source"] = NewSourceProvider

# 3. config/literature.yaml에 설정 추가
# active_sources:
#   - "pubmed"
#   - "new_source"
# new_source:
#   base_url: "..."
```
