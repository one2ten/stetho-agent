# StethoAgent 개발 명세서

## 1. 프로젝트 디렉토리 구조

```
stetho-agent/
│
├── CLAUDE.md                          # Claude Code 참조 규칙
├── README.md                          # 프로젝트 소개 및 시작 가이드
├── pyproject.toml                     # 프로젝트 메타데이터 + 의존성
├── environment.yml                    # conda 환경 정의
├── setup_mac.sh                       # Mac 원커맨드 셋업 스크립트
├── .env.example                       # 환경 변수 템플릿
├── .gitignore                         # Git 무시 파일 목록
│
├── docs/                              # 프로젝트 문서
│   ├── 01_project_plan.md             # 개발 계획서
│   ├── 02_architecture.md             # 시스템 아키텍처
│   ├── 03_spec.md                     # 개발 명세서 (이 파일)
│   ├── 04_environment.md              # 환경 구성 가이드
│   └── 05_checklist.md                # 작업 체크리스트
│
├── app/                               # Streamlit UI 레이어
│   ├── __init__.py
│   ├── main.py                        # Streamlit 앱 진입점
│   ├── pages/                         # 멀티 페이지 (필요 시 확장)
│   │   └── __init__.py
│   └── components/                    # UI 재사용 컴포넌트
│       ├── __init__.py
│       ├── audio_uploader.py          # 청진음 업로드 컴포넌트
│       ├── vitals_input.py            # 생체신호 입력 컴포넌트
│       ├── symptom_input.py           # 증상 입력 컴포넌트
│       └── result_dashboard.py        # 결과 대시보드 컴포넌트
│
├── agents/                            # LangGraph 에이전트 레이어
│   ├── __init__.py
│   ├── graph.py                       # LangGraph 그래프 정의 + 컴파일
│   ├── state.py                       # AgentState TypedDict 정의
│   ├── nodes/                         # 그래프 노드 (분석 단위)
│   │   ├── __init__.py
│   │   ├── input_validator.py         # 입력 검증 노드
│   │   ├── auscultation_node.py       # 청진음 분석 노드
│   │   ├── vitals_node.py             # 생체신호 평가 노드
│   │   ├── symptoms_node.py           # 증상 분석 노드
│   │   ├── synthesis_node.py          # 종합 판단 노드
│   │   ├── risk_node.py               # 위험도 평가 노드
│   │   └── recommendation_node.py     # 응답 생성 노드
│   └── edges/                         # 그래프 엣지 (라우팅)
│       ├── __init__.py
│       └── risk_router.py             # 위험도 기반 조건부 라우팅
│
├── models/                            # AI 모델 레이어
│   ├── __init__.py
│   ├── ast_classifier.py              # HuggingFace AST 청진음 분류기
│   ├── llm_client.py                  # Ollama LLM 클라이언트
│   └── audio_preprocessor.py          # 오디오 전처리 파이프라인
│
├── schemas/                           # Pydantic 데이터 스키마
│   ├── __init__.py
│   ├── vitals.py                      # VitalSigns 모델
│   ├── symptoms.py                    # SymptomInput 모델
│   ├── auscultation.py                # AuscultationResult 모델
│   └── report.py                      # RiskAssessment, AnalysisReport 모델
│
├── prompts/                           # LLM 프롬프트 템플릿
│   ├── auscultation_analysis.md       # 청진음 분석 프롬프트
│   ├── vitals_evaluation.md           # 생체신호 평가 프롬프트
│   ├── symptom_analysis.md            # 증상 분석 프롬프트
│   ├── synthesis.md                   # 종합 판단 프롬프트
│   ├── recommendation_general.md      # 일반 사용자 응답 프롬프트
│   └── recommendation_professional.md # 의료 전문가 응답 프롬프트
│
├── config/                            # 설정 파일 (YAML)
│   ├── llm.yaml                       # LLM 모델 설정
│   ├── ast_model.yaml                 # AST 분류 모델 설정
│   ├── vitals_reference.yaml          # 생체신호 정상 범위 기준
│   └── app.yaml                       # 앱 일반 설정
│
├── data/                              # 데이터 디렉토리
│   ├── sample_audio/                  # 테스트용 샘플 오디오
│   │   └── sample.wav                 # 샘플 청진음 파일
│   └── sample_vitals/                 # 테스트용 샘플 생체신호
│       └── default_vitals.json        # 디폴트 생체신호 데이터
│
├── utils/                             # 유틸리티 모듈
│   ├── __init__.py
│   ├── device_utils.py                # MPS/CPU 디바이스 감지
│   ├── config_loader.py               # YAML 설정 로더
│   ├── audio_utils.py                 # 오디오 파일 유틸리티
│   └── visualization.py              # Plotly 시각화 함수
│
└── tests/                             # 테스트 스위트
    ├── __init__.py
    ├── conftest.py                    # pytest 공통 픽스처
    ├── test_schemas.py                # 스키마 테스트 (Day 1)
    ├── test_config.py                 # Config 로딩 테스트 (Day 1)
    ├── test_device.py                 # 디바이스 감지 테스트 (Day 1)
    ├── test_ast_classifier.py         # AST 분류기 테스트 (Day 2)
    ├── test_llm_client.py             # LLM 클라이언트 테스트 (Day 2)
    ├── test_audio_preprocessor.py     # 오디오 전처리 테스트 (Day 2)
    ├── test_agent_graph.py            # 에이전트 그래프 테스트 (Day 3)
    ├── test_nodes.py                  # 노드 단위 테스트 (Day 3)
    └── test_e2e.py                    # E2E 통합 테스트 (Day 4)
```

---

## 2. 핵심 데이터 스키마 (Pydantic 모델)

### 2.1 schemas/vitals.py — 생체 신호

```python
from pydantic import BaseModel, Field

class VitalSigns(BaseModel):
    """생체 신호 입력 스키마 (디폴트 값 포함)"""
    heart_rate: int = Field(
        default=75,
        ge=30, le=250,
        description="심박수 (bpm)"
    )
    blood_pressure_sys: int = Field(
        default=120,
        ge=60, le=300,
        description="수축기 혈압 (mmHg)"
    )
    blood_pressure_dia: int = Field(
        default=80,
        ge=30, le=200,
        description="이완기 혈압 (mmHg)"
    )
    body_temperature: float = Field(
        default=36.5,
        ge=34.0, le=43.0,
        description="체온 (°C)"
    )
```

### 2.2 schemas/symptoms.py — 증상 입력

```python
from pydantic import BaseModel, Field
from typing import Literal

SYMPTOM_OPTIONS: list[str] = [
    "기침", "호흡곤란", "가슴 통증", "가래", "발열",
    "피로감", "두통", "어지러움", "심계항진", "부종"
]

DURATION_OPTIONS: list[str] = ["1-2일", "3-7일", "1-2주", "2주 이상", "1개월 이상"]
SEVERITY_OPTIONS: list[str] = ["경미", "중간", "심함", "매우 심함"]

class SymptomInput(BaseModel):
    """증상 입력 스키마 (디폴트 값 포함)"""
    free_text: str = Field(
        default="가벼운 기침이 있고 가끔 숨이 찹니다",
        description="자유 텍스트 증상 설명"
    )
    checklist: list[str] = Field(
        default=["기침", "호흡곤란"],
        description="체크리스트 증상 선택"
    )
    duration: str = Field(
        default="3-7일",
        description="증상 지속 기간"
    )
    severity: Literal["경미", "중간", "심함", "매우 심함"] = Field(
        default="경미",
        description="증상 강도"
    )
```

### 2.3 schemas/auscultation.py — 청진음 분류 결과

```python
from pydantic import BaseModel, Field
from typing import Optional

AUSCULTATION_CLASSES: list[str] = [
    "Normal", "Murmur", "Extrahls", "Artifact", "Extrastole"
]

class AuscultationResult(BaseModel):
    """청진음 분류 결과 스키마"""
    file_name: str = Field(description="업로드된 오디오 파일명")
    classification: str = Field(description="최종 분류 결과 (최고 확률 클래스)")
    confidence: float = Field(ge=0.0, le=1.0, description="최고 확률 (0-1)")
    probabilities: dict[str, float] = Field(
        description="클래스별 확률 딕셔너리"
    )
    spectrogram_path: Optional[str] = Field(
        default=None,
        description="Mel Spectrogram 이미지 경로"
    )
```

### 2.4 schemas/report.py — 위험도 평가 및 분석 리포트

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class RiskAssessment(BaseModel):
    """위험도 평가 스키마"""
    level: Literal["low", "moderate", "high", "critical"] = Field(
        description="위험도 레벨"
    )
    score: float = Field(
        ge=0.0, le=100.0,
        description="위험도 점수 (0-100)"
    )
    factors: list[str] = Field(
        default_factory=list,
        description="위험 요인 목록"
    )
    immediate_action_needed: bool = Field(
        default=False,
        description="즉시 조치 필요 여부"
    )

class AnalysisReport(BaseModel):
    """최종 분석 리포트 스키마"""
    timestamp: datetime = Field(default_factory=datetime.now)
    auscultation_analysis: Optional[str] = None
    vitals_evaluation: Optional[str] = None
    symptom_analysis: Optional[str] = None
    risk_assessment: Optional[RiskAssessment] = None
    synthesis: Optional[str] = None
    recommendation: Optional[str] = None
    user_mode: Literal["general", "professional"] = "general"
    disclaimer: str = "⚠️ 본 분석 결과는 AI 기반 참고 정보이며 의료 진단이 아닙니다."
```

### 2.5 agents/state.py — 에이전트 상태

```python
from typing import TypedDict, Optional, Literal
from schemas.auscultation import AuscultationResult
from schemas.vitals import VitalSigns
from schemas.symptoms import SymptomInput
from schemas.report import RiskAssessment

class AgentState(TypedDict):
    """LangGraph 에이전트 상태 정의"""
    # 입력 데이터
    auscultation: Optional[AuscultationResult]
    vitals: Optional[VitalSigns]
    symptoms: Optional[SymptomInput]
    user_mode: Literal["general", "professional"]

    # 분석 결과
    auscultation_analysis: Optional[str]
    vitals_evaluation: Optional[str]
    symptom_analysis: Optional[str]

    # 종합 판단
    risk_assessment: Optional[RiskAssessment]
    synthesis: Optional[str]
    recommendation: Optional[str]

    # 대화 이력
    chat_history: list[dict]
```

---

## 3. API / 모듈별 인터페이스 명세

### 3.1 models/ast_classifier.py

```python
class ASTClassifier:
    """HuggingFace AST 기반 청진음 분류기"""

    def __init__(self, config: dict | None = None):
        """
        분류기 초기화
        - config: ast_model.yaml에서 로딩된 설정
        - 디바이스 자동 감지 (MPS → CPU)
        - 모델 + 피처 추출기 로딩
        """

    def classify(self, audio_path: str) -> AuscultationResult:
        """
        오디오 파일 분류
        - audio_path: .wav 파일 경로
        - 반환: AuscultationResult (분류 결과 + 확률)
        - 예외: FileNotFoundError, RuntimeError
        """

    def _load_model(self) -> None:
        """모델 로딩 (내부 메서드)"""

    def _preprocess_audio(self, audio_path: str) -> torch.Tensor:
        """오디오 전처리 (내부 메서드)"""
```

### 3.2 models/llm_client.py

```python
class LLMClient:
    """Ollama LLM 클라이언트 (LangChain ChatOllama 래퍼)"""

    def __init__(self, config: dict | None = None):
        """
        LLM 클라이언트 초기화
        - config: llm.yaml에서 로딩된 설정
        - ChatOllama 인스턴스 생성
        """

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        텍스트 생성 (비스트리밍)
        - prompt: 사용자 프롬프트
        - system_prompt: 시스템 프롬프트
        - 반환: 생성된 텍스트
        - 예외: ConnectionError (Ollama 미실행), TimeoutError
        """

    async def agenerate(self, prompt: str, system_prompt: str = "") -> str:
        """비동기 텍스트 생성"""

    def stream(self, prompt: str, system_prompt: str = ""):
        """스트리밍 생성 (제너레이터)"""

    def is_available(self) -> bool:
        """Ollama 서버 연결 상태 확인"""
```

### 3.3 models/audio_preprocessor.py

```python
@dataclass
class PreprocessResult:
    """전처리 결과"""
    waveform: np.ndarray          # 전처리된 파형
    sample_rate: int              # 샘플링 레이트 (16000)
    duration: float               # 길이 (초)
    spectrogram_path: str | None  # Mel Spectrogram 이미지 경로

class AudioPreprocessor:
    """오디오 전처리 파이프라인"""

    def __init__(self, config: dict | None = None):
        """
        전처리기 초기화
        - config: ast_model.yaml의 audio 섹션
        - target_sr: 16000, max_duration: 30초
        """

    def process(self, audio_path: str, save_spectrogram: bool = True) -> PreprocessResult:
        """
        오디오 전처리 파이프라인
        - .wav 로딩 → 모노 변환 → 리샘플링(16kHz) → 트리밍(30초)
        - save_spectrogram=True: Mel Spectrogram 이미지 저장
        - 반환: PreprocessResult
        """

    def generate_mel_spectrogram(self, waveform: np.ndarray, sr: int, save_path: str) -> str:
        """Mel Spectrogram 이미지 생성 및 저장"""

    def validate_audio(self, audio_path: str) -> bool:
        """오디오 파일 유효성 검사 (.wav, 크기, 길이)"""
```

### 3.4 agents/graph.py

```python
def create_agent_graph() -> CompiledGraph:
    """
    LangGraph 에이전트 그래프 생성 및 컴파일
    - 노드: 입력 검증 → 병렬(청진음/생체신호/증상) → 종합 → 위험도 → 응답
    - 엣지: 위험도 기반 조건부 라우팅
    - 반환: 컴파일된 StateGraph
    """

async def run_analysis(
    vitals: VitalSigns | None = None,
    symptoms: SymptomInput | None = None,
    audio_path: str | None = None,
    user_mode: str = "general"
) -> dict:
    """
    분석 실행 (에이전트 그래프 호출)
    - 디폴트 값 자동 적용
    - 반환: 최종 AgentState (모든 분석 결과 포함)
    """
```

### 3.5 utils/device_utils.py

```python
def get_device() -> torch.device:
    """
    최적 디바이스 자동 감지
    - Apple Silicon: MPS 우선
    - 폴백: CPU
    - 환경변수 PYTORCH_ENABLE_MPS_FALLBACK=1 자동 설정
    """

def get_device_info() -> dict:
    """
    디바이스 정보 반환
    - device: "mps" | "cpu"
    - mps_available: bool
    - pytorch_version: str
    """
```

### 3.6 utils/config_loader.py

```python
def load_config(name: str) -> dict:
    """
    YAML 설정 파일 로딩
    - name: "llm", "ast_model", "vitals_reference", "app"
    - 경로: config/{name}.yaml
    - 반환: 파싱된 딕셔너리
    - 예외: FileNotFoundError
    """

def get_llm_config() -> dict:
    """LLM 설정 로딩 (편의 함수)"""

def get_ast_config() -> dict:
    """AST 모델 설정 로딩 (편의 함수)"""
```

### 3.7 utils/visualization.py

```python
def create_vitals_gauges(vitals: VitalSigns) -> go.Figure:
    """
    생체신호 게이지 차트 생성 (Plotly)
    - 심박수, 혈압(수축기/이완기), 체온 각각 게이지
    - 정상/주의/위험 범위 색상 표시
    """

def create_classification_bar_chart(probabilities: dict[str, float]) -> go.Figure:
    """
    청진음 분류 확률 바 차트 생성 (Plotly)
    - 5개 클래스별 확률 수평 바 차트
    - 최고 확률 클래스 강조
    """

def create_risk_indicator(risk: RiskAssessment) -> go.Figure:
    """
    위험도 인디케이터 생성 (Plotly)
    - 게이지 또는 트래픽 라이트 스타일
    - low=초록, moderate=노랑, high=주황, critical=빨강
    """
```

---

## 4. 설정 파일 구조 (YAML 스키마)

### 4.1 config/llm.yaml

```yaml
# LLM 모델 설정
ollama:
  model: "qwen3:8b"                    # Ollama 모델명 (교체 가능)
  base_url: "http://localhost:11434"   # Ollama 서버 URL
  temperature: 0.7                     # 생성 온도 (0.0-1.0)
  top_p: 0.9                           # Top-p 샘플링
  timeout: 120                         # 요청 타임아웃 (초)
  max_retries: 3                       # 최대 재시도 횟수
  streaming: false                     # 스트리밍 모드

# 대체 모델 설정 (주석 해제하여 사용)
# ollama:
#   model: "exaone3.5:7.8b"            # LG AI 한국어 특화
#   model: "qwen3:4b"                  # 경량 (8GB Mac)
#   model: "qwen3:30b-a3b"            # 고성능 (32GB+ Mac)
```

### 4.2 config/ast_model.yaml

```yaml
# AST 청진음 분류 모델 설정
model:
  name: "MIT/ast-finetuned-audioset-10-10-0.4593"
  cache_dir: null                      # null이면 기본 HuggingFace 캐시 사용

# 분류 클래스 매핑 (AudioSet → 청진음)
classes:
  - name: "Normal"
    description: "정상 폐음"
    label_ids: []                      # AudioSet 라벨 ID 매핑
  - name: "Murmur"
    description: "심잡음"
    label_ids: []
  - name: "Extrahls"
    description: "이상 심음"
    label_ids: []
  - name: "Artifact"
    description: "잡음/노이즈"
    label_ids: []
  - name: "Extrastole"
    description: "기외수축"
    label_ids: []

# 오디오 전처리 설정
audio:
  sample_rate: 16000                   # 목표 샘플링 레이트
  max_duration: 30                     # 최대 길이 (초)
  mono: true                           # 모노 변환 여부
  normalize: true                      # 정규화 여부

# 디바이스 설정
device:
  prefer_mps: true                     # MPS 우선 사용
  fallback_cpu: true                   # CPU 폴백 허용
  env:
    PYTORCH_ENABLE_MPS_FALLBACK: "1"   # MPS 폴백 환경변수
```

### 4.3 config/vitals_reference.yaml

```yaml
# 생체신호 정상 범위 기준
heart_rate:
  unit: "bpm"
  normal:
    min: 60
    max: 100
  warning:
    low: 50
    high: 110
  critical:
    low: 40
    high: 150
  default: 75

blood_pressure:
  unit: "mmHg"
  systolic:
    normal:
      min: 90
      max: 120
    elevated:
      min: 120
      max: 129
    high_stage1:
      min: 130
      max: 139
    high_stage2:
      min: 140
      max: 180
    crisis:
      min: 180
    default: 120
  diastolic:
    normal:
      min: 60
      max: 80
    elevated:
      max: 80
    high_stage1:
      min: 80
      max: 89
    high_stage2:
      min: 90
      max: 120
    crisis:
      min: 120
    default: 80

body_temperature:
  unit: "°C"
  normal:
    min: 36.1
    max: 37.2
  low_grade_fever:
    min: 37.3
    max: 38.0
  fever:
    min: 38.1
    max: 39.0
  high_fever:
    min: 39.1
    max: 41.0
  critical:
    min: 41.1
  hypothermia:
    max: 35.0
  default: 36.5
```

### 4.4 config/app.yaml

```yaml
# 애플리케이션 일반 설정
app:
  name: "StethoAgent"
  version: "0.1.0"
  description: "AI 기반 건강 가이드 프로토타입"
  language: "ko"                       # 기본 언어

# Streamlit 설정
streamlit:
  page_title: "StethoAgent - AI 건강 가이드"
  page_icon: "🩺"
  layout: "wide"
  theme:
    primary_color: "#1E88E5"
    background_color: "#FAFAFA"

# 사용자 모드
user_modes:
  general:
    label: "일반 사용자"
    description: "쉬운 한국어로 건강 가이드 제공"
  professional:
    label: "의료 전문가"
    description: "전문 용어를 사용한 진단 보조 리포트"

# 면책 조항
disclaimer: "⚠️ 본 분석 결과는 AI 기반 참고 정보이며 의료 진단이 아닙니다. 정확한 진단은 반드시 의료 전문가와 상담하세요."

# 증상 옵션
symptoms:
  options:
    - "기침"
    - "호흡곤란"
    - "가슴 통증"
    - "가래"
    - "발열"
    - "피로감"
    - "두통"
    - "어지러움"
    - "심계항진"
    - "부종"
  duration_options:
    - "1-2일"
    - "3-7일"
    - "1-2주"
    - "2주 이상"
    - "1개월 이상"
  severity_options:
    - "경미"
    - "중간"
    - "심함"
    - "매우 심함"

# 오디오 업로드 제한
audio:
  allowed_extensions: [".wav"]
  max_file_size_mb: 10
  max_duration_seconds: 30
```

---

## 5. 환경 변수 (.env.example)

```env
# StethoAgent 환경 변수

# Ollama 설정
OLLAMA_BASE_URL=http://localhost:11434

# PyTorch MPS 폴백
PYTORCH_ENABLE_MPS_FALLBACK=1

# HuggingFace 캐시 (선택)
# HF_HOME=~/.cache/huggingface

# 로그 레벨
LOG_LEVEL=INFO

# Streamlit 설정
STREAMLIT_SERVER_PORT=8501
```

---

## 6. 의존성 (pyproject.toml 핵심)

```toml
[project]
name = "stetho-agent"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # UI
    "streamlit>=1.40",
    # LLM
    "langchain>=0.3",
    "langchain-ollama>=0.2",
    "langgraph>=0.2",
    # AI 모델
    "torch>=2.2",
    "transformers>=4.40",
    # 오디오
    "librosa>=0.10",
    "soundfile>=0.12",
    # 시각화
    "plotly>=5.20",
    # 데이터 검증
    "pydantic>=2.0",
    # 설정
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]
```
