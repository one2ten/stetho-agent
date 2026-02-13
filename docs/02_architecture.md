# StethoAgent 시스템 아키텍처

## 1. 전체 시스템 구조도

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Streamlit Web UI                             │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ 청진음    │  │ 생체신호      │  │ 증상      │  │ 결과 대시보드  │  │
│  │ 업로더    │  │ 입력 패널     │  │ 입력 패널  │  │ (Plotly)      │  │
│  └────┬─────┘  └──────┬───────┘  └────┬─────┘  └───────▲───────┘  │
│       │               │               │                │           │
│  ┌────▼───────────────▼───────────────▼────────────────┤           │
│  │              세션 상태 관리 (st.session_state)        │           │
│  └────────────────────────┬────────────────────────────┘           │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                    LangGraph 에이전트 레이어                       │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    AgentState (TypedDict)                    │  │
│  └─────────────────────────────┬───────────────────────────────┘  │
│                                │                                  │
│  ┌────────────────── 병렬 분석 ─┼──────────────────────┐          │
│  │                             │                       │          │
│  ▼                             ▼                       ▼          │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │ 청진음 분석   │  │ 생체신호 평가     │  │ 증상 분석         │    │
│  │ 노드          │  │ 노드             │  │ 노드             │    │
│  └──────┬───────┘  └────────┬─────────┘  └────────┬─────────┘    │
│         │                   │                      │              │
│         └───────────────────┼──────────────────────┘              │
│                             ▼                                     │
│                   ┌──────────────────┐                            │
│                   │ 종합 판단 노드    │                            │
│                   └────────┬─────────┘                            │
│                            │                                      │
│                   ┌────────▼─────────┐                            │
│                   │ 위험도 라우팅     │                            │
│                   │ (조건부 엣지)     │                            │
│                   └───┬──────────┬───┘                            │
│              high/    │          │    low/                         │
│              critical │          │    moderate                     │
│                   ┌───▼──┐  ┌───▼──────┐                         │
│                   │ 긴급  │  │ 일반      │                         │
│                   │ 응답  │  │ 가이드    │                         │
│                   └───┬──┘  └───┬──────┘                         │
│                       └────┬────┘                                 │
│                            ▼                                      │
│                   ┌──────────────────┐                            │
│                   │ 응답 생성 노드    │                            │
│                   │ (user_mode 분기)  │                            │
│                   └──────────────────┘                            │
└───────────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
┌──────────────────┐ ┌───────────┐ ┌──────────────┐
│  모델 레이어      │ │ Ollama    │ │ Config       │
│                  │ │ LLM 서버  │ │ (YAML)       │
│ ┌──────────────┐ │ │           │ │              │
│ │ AST 분류기   │ │ │ qwen3:8b  │ │ llm.yaml     │
│ │ (HuggingFace)│ │ │ (로컬)    │ │ ast_model.yaml│
│ │ MPS/CPU      │ │ └───────────┘ │ vitals_ref.yaml│
│ ├──────────────┤ │               │ app.yaml     │
│ │ 오디오 전처리 │ │               └──────────────┘
│ │ (librosa)    │ │
│ ├──────────────┤ │
│ │ LLM 클라이언트│ │
│ │ (ChatOllama) │ │
│ └──────────────┘ │
└──────────────────┘
```

---

## 2. LangGraph 에이전트 워크플로우

### 2.1 상태 그래프 설계

```
                    ┌───────────┐
                    │   START   │
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │  입력 검증  │
                    │  & 준비    │
                    └─────┬─────┘
                          │
            ┌─────────────┼─────────────┐
            │ (Fan-out)   │             │
      ┌─────▼─────┐ ┌────▼────┐ ┌─────▼─────┐
      │ 청진음     │ │ 생체신호 │ │ 증상       │
      │ 분석 노드  │ │ 평가    │ │ 분석 노드  │
      │           │ │ 노드    │ │           │
      └─────┬─────┘ └────┬────┘ └─────┬─────┘
            │ (Fan-in)    │            │
            └─────────────┼────────────┘
                          │
                    ┌─────▼─────┐
                    │  종합 판단  │
                    │  노드      │
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │  위험도    │
                    │  평가 노드  │
                    └─────┬─────┘
                          │
               ┌──────────┼──────────┐
               │ conditional_edge    │
               │                     │
        ┌──────▼──────┐      ┌──────▼──────┐
        │ high/critical│      │ low/moderate │
        │ 긴급 경고    │      │ 일반 가이드   │
        └──────┬──────┘      └──────┬──────┘
               │                    │
               └────────┬───────────┘
                        │
                  ┌─────▼─────┐
                  │  응답 생성  │
                  │  노드      │
                  │ (mode별)   │
                  └─────┬─────┘
                        │
                  ┌─────▼─────┐
                  │    END     │
                  └───────────┘
```

### 2.2 노드 상세 설명

| 노드 | 파일 | 입력 | 출력 | 설명 |
|------|------|------|------|------|
| **입력 검증** | `nodes/input_validator.py` | 원시 입력 | 검증된 AgentState | Pydantic으로 입력 검증, 디폴트 값 채우기 |
| **청진음 분석** | `nodes/auscultation_node.py` | `.wav` 파일 경로 | `auscultation_analysis: str` | AST 모델 분류 → LLM이 결과 해석 |
| **생체신호 평가** | `nodes/vitals_node.py` | `VitalSigns` | `vitals_evaluation: str` | 정상 범위 비교 → LLM이 평가 |
| **증상 분석** | `nodes/symptoms_node.py` | `SymptomInput` | `symptom_analysis: str` | 증상 조합 분석 → LLM이 해석 |
| **종합 판단** | `nodes/synthesis_node.py` | 3개 분석 결과 | `synthesis: str` | 전체 소견 종합 |
| **위험도 평가** | `nodes/risk_node.py` | 종합 소견 | `RiskAssessment` | 위험도 점수 + 레벨 산정 |
| **응답 생성** | `nodes/recommendation_node.py` | 종합 + 위험도 + user_mode | `recommendation: str` | 최종 건강 가이드 생성 |

### 2.3 엣지 (라우팅) 설명

| 엣지 | 파일 | 조건 | 분기 |
|------|------|------|------|
| **위험도 라우터** | `edges/risk_router.py` | `risk_assessment.level` | `high/critical` → 긴급 경고 포함, `low/moderate` → 일반 가이드 |

### 2.4 병렬 실행 전략

LangGraph의 `Fan-out / Fan-in` 패턴 사용:

```python
# 병렬 분기 (Fan-out)
graph.add_edge("input_validator", ["auscultation_node", "vitals_node", "symptoms_node"])

# 합류 (Fan-in)
graph.add_edge(["auscultation_node", "vitals_node", "symptoms_node"], "synthesis_node")
```

- 3개 분석 노드는 독립적이므로 병렬 실행
- 모든 분석 완료 후 종합 판단 노드로 합류
- 청진음이 없는 경우(업로드 안 함) → 청진음 분석 노드 스킵

---

## 3. 모듈 간 데이터 흐름

### 3.1 전체 데이터 흐름

```
사용자 입력                    모델 레이어                 에이전트 레이어              UI 출력
──────────                    ──────────                 ──────────────              ────────

.wav 파일 ──→ AudioPreprocessor ──→ ASTClassifier ──→ AuscultationResult
                  │                      │                    │
                  ▼                      │                    ▼
            Mel Spectrogram              │            auscultation_node ──┐
            (이미지 저장)                 │                                │
                                         │                                │
심박수/혈압/체온 ──→ VitalSigns ──────────────────→ vitals_node ──────────┤
                                         │                                │
                                         │                                ▼
증상 텍스트/체크 ──→ SymptomInput ─────────────────→ symptoms_node ──→ synthesis_node
                                         │                                │
                                         │                                ▼
                                    Ollama LLM ◄──────────────── risk_node
                                    (qwen3:8b)                       │
                                         │                           ▼
                                         │                   recommendation_node
                                         │                           │
                                         ▼                           ▼
                                    LLM 응답 생성 ──────────→ 결과 대시보드
                                                              - Plotly 게이지
                                                              - 확률 바 차트
                                                              - Mel Spectrogram
                                                              - 종합 분석 텍스트
                                                              - 위험도 표시
```

### 3.2 데이터 변환 단계

```
1. 오디오 흐름:
   .wav (원본) → 16kHz 모노 (리샘플링) → Mel Spectrogram (시각화)
                                        → AST 피처 (분류 입력)
                                        → 5-class 확률 (분류 결과)

2. 생체신호 흐름:
   숫자 입력 → VitalSigns (Pydantic) → 정상 범위 비교 → 이상 소견 텍스트

3. 증상 흐름:
   텍스트 + 체크리스트 → SymptomInput (Pydantic) → 증상 조합 분석 텍스트

4. 종합 흐름:
   3개 분석 텍스트 → LLM 종합 → RiskAssessment → 최종 recommendation
```

---

## 4. 기술 스택 상세

### 4.1 프레임워크 & 라이브러리

| 카테고리 | 기술 | 버전 | 역할 |
|----------|------|------|------|
| **UI** | Streamlit | 1.40+ | 웹 인터페이스, 입력 폼, 대시보드 |
| **LLM 런타임** | Ollama | latest | 로컬 LLM 서빙 (REST API) |
| **LLM 모델** | qwen3:8b | - | 다국어 119개, 한국어 자연스러움, 16GB Mac |
| **에이전트** | LangGraph | 0.2+ | 상태 기반 그래프 워크플로우 |
| **LLM 통합** | LangChain | 0.3+ | ChatOllama, 프롬프트 템플릿, 체인 |
| **청진음 분류** | HuggingFace Transformers | 4.40+ | AST 모델 로딩 및 추론 |
| **AST 모델** | MIT/ast-finetuned-audioset-10-10-0.4593 | - | 오디오 스펙트로그램 트랜스포머 |
| **딥러닝** | PyTorch | 2.2+ | MPS 백엔드, 텐서 연산 |
| **오디오** | librosa | 0.10+ | .wav 로딩, 리샘플링, Mel Spectrogram |
| **시각화** | Plotly | 5.20+ | 게이지 차트, 바 차트, 인터랙티브 |
| **검증** | Pydantic | 2.0+ | 데이터 스키마, 디폴트 값, 타입 검증 |
| **설정** | PyYAML | 6.0+ | YAML 설정 파일 파싱 |
| **환경** | conda (Miniforge) | - | Python 환경 및 패키지 관리 |
| **테스트** | pytest | 8.0+ | 단위/통합/E2E 테스트 |

### 4.2 Mac Apple Silicon 최적화

```
PyTorch MPS 백엔드:
├── 자동 감지: torch.backends.mps.is_available()
├── 디바이스 선택: MPS → CPU 폴백
├── 환경 변수: PYTORCH_ENABLE_MPS_FALLBACK=1
└── AST 모델: MPS에서 추론, 비호환 연산은 CPU 폴백

Ollama:
├── Apple Silicon 네이티브 빌드
├── Metal GPU 가속 자동 활용
└── 모델 메모리: qwen3:8b ≈ 5-6GB VRAM
```

### 4.3 LLM 모델 교체 전략

`config/llm.yaml`에서 모델명만 변경하면 교체 가능:

```yaml
# config/llm.yaml
ollama:
  model: "qwen3:8b"        # ← 여기만 변경
  base_url: "http://localhost:11434"
  temperature: 0.7
  timeout: 120
```

| 모델 | RAM 요구 | 특징 | 설정값 |
|------|----------|------|--------|
| `qwen3:8b` | 16GB | 기본, 다국어, 한국어 자연스러움 | `model: "qwen3:8b"` |
| `exaone3.5:7.8b` | 16GB | LG AI, 한국어 특화 | `model: "exaone3.5:7.8b"` |
| `qwen3:4b` | 8GB | 경량, 저사양 Mac | `model: "qwen3:4b"` |
| `qwen3:30b-a3b` | 32GB+ | 고성능, MoE | `model: "qwen3:30b-a3b"` |

---

## 5. 외부 시스템 인터페이스

### 5.1 Ollama REST API

```
App ──HTTP──→ Ollama Server (localhost:11434)
              ├── POST /api/chat     (채팅 완성)
              ├── POST /api/generate (텍스트 생성)
              └── GET  /api/tags     (모델 목록)

LangChain ChatOllama가 내부적으로 Ollama REST API 호출
```

### 5.2 HuggingFace 모델 허브

```
최초 실행 시:
  App ──HTTPS──→ HuggingFace Hub
                  └── MIT/ast-finetuned-audioset-10-10-0.4593
                      ├── config.json
                      ├── model.safetensors
                      └── preprocessor_config.json

이후: 로컬 캐시 (~/.cache/huggingface/) 에서 로딩
```

---

## 6. 보안 및 제약 사항

| 항목 | 설명 |
|------|------|
| **데이터 프라이버시** | 모든 처리 로컬 수행 (Ollama 로컬, AST 로컬), 외부 서버 전송 없음 |
| **면책 조항** | 모든 결과 화면에 "AI 참고 정보, 의료 진단 아님" 표시 필수 |
| **입력 검증** | Pydantic으로 모든 입력 검증, 파일 타입/크기 제한 |
| **에러 격리** | 개별 노드 실패 시 전체 워크플로우 중단 방지, 그레이스풀 폴백 |
| **오디오 제한** | .wav만 허용, 최대 30초, 16kHz 모노로 변환 |
