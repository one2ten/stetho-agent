# StethoAgent 개발 체크리스트

> 각 항목을 완료하면 `[ ]`를 `[x]`로 변경하세요.

---

## Day 1: 프로젝트 초기화 + 기반 구축

### 프로젝트 구조
- [x] 전체 디렉토리 구조 생성 (`app/`, `agents/`, `models/`, `schemas/`, `config/`, `utils/`, `tests/`, `prompts/`, `data/`)
- [x] 모든 디렉토리에 `__init__.py` 생성
- [x] `.gitignore` 작성

### 환경 설정 파일
- [x] `environment.yml` 작성 (conda 환경 정의)
- [x] `pyproject.toml` 작성 (프로젝트 메타데이터 + 의존성)
- [x] `.env.example` 작성 (환경 변수 템플릿)
- [x] `setup_mac.sh` 작성 (원커맨드 셋업 스크립트)

### 환경 구축
- [x] conda 환경 생성 (`conda env create -f environment.yml`)
- [x] 환경 활성화 확인 (`conda activate stetho-agent`)
- [x] 모든 의존성 임포트 확인

### Ollama 설정
- [x] Ollama 설치 (0.16.1 업데이트 완료)
- [x] Ollama 서버 시작 (`ollama serve`)
- [x] `qwen3:8b` 모델 다운로드 (`ollama pull qwen3:8b`)
- [x] 한국어 응답 확인 (`ollama run qwen3:8b "안녕하세요"`)

### Config 파일 (YAML)
- [x] `config/llm.yaml` 작성
- [x] `config/ast_model.yaml` 작성
- [x] `config/vitals_reference.yaml` 작성
- [x] `config/app.yaml` 작성

### Pydantic 스키마
- [x] `schemas/__init__.py` 작성
- [x] `schemas/vitals.py` — `VitalSigns` 모델 (디폴트: HR=75, BP=120/80, Temp=36.5)
- [x] `schemas/symptoms.py` — `SymptomInput` 모델 (폐/심장 관련 증상 12개, 자유텍스트 디폴트 포함)
- [x] `schemas/auscultation.py` — `AuscultationResult` 모델
- [x] `schemas/report.py` — `RiskAssessment`, `AnalysisReport` 모델

### 유틸리티
- [x] `utils/device_utils.py` — MPS/CPU 자동 감지
- [x] `utils/config_loader.py` — YAML 설정 로더

### 테스트 (Day 1)
- [x] `tests/conftest.py` — pytest 공통 픽스처
- [x] `tests/test_schemas.py` — 스키마 디폴트 값, 유효성 검사 테스트 (44 passed)
- [x] `tests/test_config.py` — Config 로딩 테스트
- [x] `tests/test_device.py` — 디바이스 감지 테스트

### Day 1 확인 테스트
- [x] `conda activate stetho-agent` → 환경 활성화 성공
- [x] `ollama run qwen3:8b "안녕하세요"` → 한국어 응답
- [x] `python -c "import torch; print(torch.backends.mps.is_available())"` → `True`
- [x] `python -c "from schemas.vitals import VitalSigns; print(VitalSigns())"` → 디폴트 값 출력
- [x] `pytest tests/test_schemas.py -v` → PASSED
- [x] `pytest tests/test_config.py -v` → PASSED
- [x] `pytest tests/test_device.py -v` → PASSED

---

## Day 2: 핵심 모델 레이어

### 오디오 전처리
- [x] `models/audio_preprocessor.py` — AudioPreprocessor 클래스
  - [x] .wav 로딩 (librosa)
  - [x] 16kHz 리샘플링
  - [x] 모노 변환
  - [x] 최대 30초 트리밍
  - [x] Mel Spectrogram 생성 및 이미지 저장
  - [x] 오디오 유효성 검사

### AST 청진음 분류기
- [x] `models/ast_classifier.py` — ASTClassifier 클래스
  - [x] HuggingFace 모델 로딩 (`MIT/ast-finetuned-audioset-10-10-0.4593`)
  - [x] MPS 디바이스 배치 (폴백: CPU)
  - [x] 오디오 → 피처 추출 → 추론 파이프라인
  - [x] 4-class 확률 반환 (Normal, Crackle, Wheeze, Both)
  - [x] `--test` CLI 모드 구현

### 샘플 데이터
- [x] `sample/sample.wav` — 테스트용 오디오 파일 (4kHz, 모노, 15초)

### LLM 클라이언트
- [x] `models/llm_client.py` — LLMClient 클래스
  - [x] `config/llm.yaml` 기반 ChatOllama 초기화
  - [x] `generate()` — 비스트리밍 텍스트 생성
  - [x] `stream()` — 스트리밍 생성
  - [x] `is_available()` — Ollama 서버 연결 확인
  - [x] 타임아웃/재시도 처리
  - [x] `--test` CLI 모드 구현

### 시각화 유틸리티
- [x] `utils/visualization.py`
  - [x] `create_vitals_gauges()` — 생체신호 Plotly 게이지 차트
  - [x] `create_classification_bar_chart()` — 분류 확률 바 차트
  - [x] `create_risk_indicator()` — 위험도 인디케이터

### 오디오 유틸리티
- [x] `utils/audio_utils.py` — 오디오 파일 검증, 메타데이터 추출

### 테스트 (Day 2)
- [x] `tests/test_audio_preprocessor.py` — 전처리 파이프라인 테스트 (14 passed)
- [x] `tests/test_ast_classifier.py` — AST 분류기 테스트 (7 passed)
- [x] `tests/test_llm_client.py` — LLM 클라이언트 테스트 (8 passed)

### Day 2 확인 테스트
- [x] `python -m models.audio_preprocessor --test` → Mel Spectrogram 이미지 생성 완료
- [x] `python -m models.ast_classifier --test` → 4개 클래스별 확률 출력 (Normal 70.47%, Wheeze 24.74%, Crackle 3.19%, Both 1.60%)
- [x] `python -m models.llm_client --test` → 한국어 응답 수신 완료
- [x] `pytest tests/test_ast_classifier.py -v` → 7 PASSED
- [x] `pytest tests/test_llm_client.py -v` → 8 PASSED
- [x] `pytest tests/test_audio_preprocessor.py -v` → 14 PASSED
- [x] `pytest tests/ -v` → 전체 73 PASSED

---

## Day 3: LangGraph 에이전트 + Streamlit UI

### 에이전트 상태
- [ ] `agents/state.py` — `AgentState` TypedDict 정의

### 분석 노드
- [ ] `agents/nodes/__init__.py`
- [ ] `agents/nodes/input_validator.py` — 입력 검증 노드
- [ ] `agents/nodes/auscultation_node.py` — 청진음 분석 노드
- [ ] `agents/nodes/vitals_node.py` — 생체신호 평가 노드
- [ ] `agents/nodes/symptoms_node.py` — 증상 분석 노드
- [ ] `agents/nodes/synthesis_node.py` — 종합 판단 노드
- [ ] `agents/nodes/risk_node.py` — 위험도 평가 노드
- [ ] `agents/nodes/recommendation_node.py` — 응답 생성 노드 (mode별 분기)

### 라우팅 엣지
- [ ] `agents/edges/__init__.py`
- [ ] `agents/edges/risk_router.py` — 위험도 기반 조건부 라우팅

### LangGraph 그래프
- [ ] `agents/graph.py` — 그래프 정의 + 컴파일
  - [ ] 입력 검증 → 병렬(3개 분석) → 종합 → 위험도 → 응답 워크플로우
  - [ ] `--test` CLI 모드 구현

### LLM 프롬프트 템플릿
- [ ] `prompts/auscultation_analysis.md`
- [ ] `prompts/vitals_evaluation.md`
- [ ] `prompts/symptom_analysis.md`
- [ ] `prompts/synthesis.md`
- [ ] `prompts/recommendation_general.md`
- [ ] `prompts/recommendation_professional.md`

### Streamlit UI
- [ ] `app/main.py` — 메인 페이지
  - [ ] 사이드바: 모드 선택 (일반/의료진), 면책 조항
  - [ ] 메인 영역: 입력 + 결과 탭
  - [ ] "분석 시작" 버튼
- [ ] `app/components/audio_uploader.py` — 청진음 업로드 UI
- [ ] `app/components/vitals_input.py` — 생체신호 입력 UI (디폴트 채워짐)
- [ ] `app/components/symptom_input.py` — 증상 입력 UI (디폴트 채워짐)
- [ ] `app/components/result_dashboard.py` — 결과 대시보드 뼈대

### 테스트 (Day 3)
- [ ] `tests/test_agent_graph.py` — 워크플로우 실행 테스트
- [ ] `tests/test_nodes.py` — 각 노드 단위 테스트

### Day 3 확인 테스트
- [ ] `python -m agents.graph --test` → 디폴트 입력으로 전체 워크플로우 실행, 최종 응답 출력
- [ ] `streamlit run app/main.py` → 브라우저에서 UI 렌더링
- [ ] UI에서 디폴트 값 채워진 상태 확인
- [ ] "분석 시작" 클릭 → 결과 표시
- [ ] `pytest tests/test_agent_graph.py -v` → PASSED
- [ ] `pytest tests/test_nodes.py -v` → PASSED

---

## Day 4: 통합 + 마무리

### E2E 통합
- [ ] 청진음 업로드 → AST 분류 → LangGraph 워크플로우 → 결과 표시 전체 연결
- [ ] 오디오 없이 생체신호+증상만으로도 분석 가능 확인

### 대시보드 시각화
- [ ] Plotly 게이지 차트 (생체신호) 연결
- [ ] Plotly 바 차트 (청진음 분류 확률) 연결
- [ ] Mel Spectrogram 표시 연결
- [ ] 위험도 인디케이터 연결
- [ ] 종합 분석 텍스트 표시

### 모드별 응답
- [ ] `general` 모드: 쉬운 한국어 응답 확인
- [ ] `professional` 모드: 전문 용어 응답 확인
- [ ] 모드 전환 시 응답 톤 변경 확인

### 에러 핸들링
- [ ] Ollama 연결 실패 시 사용자 친화적 에러 메시지
- [ ] 잘못된 오디오 파일 업로드 시 에러 처리
- [ ] LLM 타임아웃 시 처리
- [ ] 빈 입력 (청진음 미업로드) 시 그레이스풀 처리

### UI 폴리싱
- [ ] 로딩 스피너 (분석 진행 중)
- [ ] 진행 상태 표시
- [ ] 레이아웃 정리
- [ ] 면책 조항 눈에 띄게 표시

### 테스트 (Day 4)
- [ ] `tests/test_e2e.py` — E2E 시나리오 테스트 작성
- [ ] `pytest tests/ -v` → 전체 테스트 스위트 통과

### Day 4 확인 테스트
- [ ] E2E 시나리오: .wav 업로드 → 디폴트 값 유지 → "분석 시작" → 대시보드 결과 표시
- [ ] 모드 전환 (일반 ↔ 의료진) 후 재분석 → 응답 톤 변경
- [ ] `pytest tests/ -v` → 전체 PASSED
- [ ] `pytest tests/test_e2e.py -v` → E2E 테스트 PASSED
- [ ] Ollama 서버 정지 후 "분석 시작" → 에러 메시지 표시 (크래시 없음)

### 최종 정리
- [ ] 불필요한 파일 제거
- [ ] 코드 린트 (ruff)
- [ ] README.md 최종 확인
- [ ] Git 커밋 및 푸시

---

## 최종 산출물 확인

- [ ] 모든 문서 (`docs/`) 최신 상태
- [ ] 전체 테스트 통과 (`pytest tests/ -v`)
- [ ] `streamlit run app/main.py`로 앱 정상 실행
- [ ] 디폴트 값으로 데모 가능 (아무 입력 없이 "분석 시작")
- [ ] 일반/의료진 모드 전환 동작
- [ ] 면책 조항 표시 확인
- [ ] Git 저장소에 최종 코드 푸시 완료
