# StethoAgent 향후 의료 에이전트 통합 계획

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

## 4. GraphRAG 기반 사용자 건강 이력 추적

> 그래프 데이터베이스를 활용하여 사용자의 건강 패턴, 생활 로그, 과거 분석 이력을 추적하고 진단에 참조합니다.

### 4.1 개요
- **GraphRAG (Graph Retrieval-Augmented Generation)**: 그래프 DB에서 관련 정보를 검색(Retrieval)하여 LLM 생성(Generation)에 반영
- 사용자 건강 데이터를 **노드(Node)와 관계(Edge)**로 구조화하여 저장
- 분석 시 과거 이력, 패턴 변화, 관련 질환 이력을 자동으로 참조

### 4.2 그래프 데이터 모델
```
(사용자)──[분석_기록]──→(분석 세션 2024-03-15)
                          ├──[청진음_결과]──→(Crackle, 92%)
                          ├──[생체신호]──→(HR:130, BP:160/95, Temp:39.0)
                          ├──[증상]──→(기침, 호흡곤란, 발열)
                          ├──[진단_추정]──→(폐렴)
                          └──[위험도]──→(HIGH, 65점)

(사용자)──[생활_로그]──→(수면 5시간, 운동 없음, 스트레스 높음)
(사용자)──[복용_약물]──→(아테놀롤)──[상호작용]──→(천식 악화)
(사용자)──[과거_이력]──→(2023년 천식 진단)──[관련]──→(Wheeze 패턴)
```

### 4.3 활용 시나리오
- **패턴 변화 감지**: "3개월 전 대비 심박수가 지속적으로 상승 추세"
- **과거 이력 참조**: "이전 분석에서 Crackle이 2회 감지 → 만성 호흡기 질환 가능성"
- **생활 로그 상관분석**: "수면 부족 기간과 증상 악화 시기가 일치"
- **약물 이력 추적**: "약물 변경 후 증상 변화 추적"

### 4.4 기술 스택 (후보)
- **그래프 DB**: Neo4j (로컬 또는 클라우드) 또는 경량 대안(Memgraph, KùzuDB)
- **임베딩**: 의학 텍스트 → 벡터 임베딩 (증상/진단 유사도 검색)
- **검색**: Cypher 쿼리 + 벡터 유사도 검색 결합
- **LLM 연동**: 검색된 이력을 프롬프트 컨텍스트에 주입

### 4.5 구현 방식
- `GraphRAGProvider` 클래스 → 에이전트 노드에서 호출
- 종합 판단 노드의 ReAct 패턴에 "[행동] 사용자 이력 검색" 단계 추가
- 분석 완료 후 결과를 자동으로 그래프 DB에 저장

---

## 5. 분산 멀티 에이전트 오케스트레이션

> 현재 StethoAgent는 이미 LangGraph 오케스트레이터가 7개 에이전트를 조율하는 멀티 에이전트 시스템입니다.
> 아래는 각 에이전트를 독립 서비스로 분리하여 분산 배포하는 장기 목표입니다.

### 4.1 현재 구조 (멀티 에이전트)
```
LangGraph 오케스트레이터 → 7개 전문 에이전트 (순차/병렬, 단일 프로세스)
```

### 4.2 목표 구조 (분산 멀티 에이전트)
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
| **P2** | GraphRAG 사용자 건강 이력 추적 | 고 | 대기 |
| **P3** | 분산 멀티 에이전트 오케스트레이션 | 고 | 대기 |
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
