# StethoAgent 개발 계획서

## 1. 프로젝트 개요

**StethoAgent** (Stethoscope + Agent) — 폐 청진음(.wav), 생체 신호(심박수/혈압/체온), 증상 입력을 종합 분석하여 건강 가이드를 제공하는 AI 웹 프로토타입.

### 목표
- 폐 청진음을 AI로 분류하고, 생체 신호 및 증상과 종합 분석하여 건강 가이드를 제공
- LangGraph 기반 멀티 에이전트 워크플로우로 병렬 분석 → 종합 판단 → 위험도 라우팅 구현
- Mac Apple Silicon 환경에서 완전한 로컬 실행 (Ollama LLM + PyTorch MPS)
- 디폴트 값이 모두 채워진 상태로, 아무 입력 없이도 데모가 가능한 프로토타입

### 타겟 사용자

| 사용자 유형 | 설명 | 모드 |
|---|---|---|
| **일반 사용자** | 셀프 건강관리, 증상 기록, 사전 가이드 | `general` — 쉬운 한국어 설명 |
| **의료 전문가** | 청진음 분류 결과 + 생체 신호 기반 진단 보조 리포트 | `professional` — 전문 용어 사용 |

### 면책 조항
> ⚠️ 본 분석 결과는 AI 기반 참고 정보이며 의료 진단이 아닙니다. 정확한 진단은 반드시 의료 전문가와 상담하세요.

---

## 2. 4일 개발 스케줄

### 마일스톤 요약

```
Day 1 ──────── Day 2 ──────── Day 3 ──────── Day 4
기반 구축       핵심 모델       에이전트+UI     통합+마무리
              레이어
   ▼              ▼              ▼              ▼
 환경 구축      AST 분류기     LangGraph      E2E 파이프라인
 스키마 정의    LLM 클라이언트  Streamlit UI   대시보드 시각화
 Config 설정   오디오 전처리    워크플로우       전체 테스트
 Ollama 연동                                  버그 수정
```

---

### Day 1: 프로젝트 초기화 + 기반 구축

**목표**: 개발 환경 완성, 프로젝트 뼈대 구축, 핵심 스키마 정의, Ollama LLM 연동 확인

#### 작업 항목

| # | 작업 | 상세 | 산출물 |
|---|------|------|--------|
| 1-1 | 프로젝트 디렉토리 구조 생성 | 전체 폴더/파일 뼈대 생성 (`app/`, `agents/`, `models/`, `schemas/`, `config/`, `utils/`, `tests/`, `prompts/`, `data/`) | 디렉토리 트리 |
| 1-2 | 환경 설정 파일 작성 | `environment.yml` (conda), `pyproject.toml`, `.env.example`, `.gitignore` | 환경 파일들 |
| 1-3 | conda 환경 생성 + 패키지 설치 | Python 3.11, PyTorch(MPS), Streamlit, LangChain, LangGraph, Pydantic 등 | 활성화된 conda 환경 |
| 1-4 | Ollama 설치 + LLM 모델 다운로드 | Ollama 설치, `qwen3:8b` 다운로드, 한국어 응답 테스트 | Ollama 실행 확인 |
| 1-5 | 설정 파일 작성 (YAML) | `config/llm.yaml`, `config/ast_model.yaml`, `config/vitals_reference.yaml`, `config/app.yaml` | Config 파일들 |
| 1-6 | Pydantic 스키마 정의 | `schemas/vitals.py`, `schemas/symptoms.py`, `schemas/auscultation.py`, `schemas/report.py` (디폴트 값 포함) | 스키마 모듈들 |
| 1-7 | 유틸리티 기반 모듈 | `utils/device_utils.py` (MPS/CPU 자동 감지), `utils/config_loader.py` (YAML 로더) | 유틸리티 모듈들 |
| 1-8 | 기반 테스트 작성 + 실행 | `tests/conftest.py`, `tests/test_schemas.py`, `tests/test_config.py`, `tests/test_device.py` | 테스트 통과 |
| 1-9 | setup_mac.sh 작성 | 원커맨드 환경 셋업 스크립트 (conda 환경 생성 → 패키지 설치 → Ollama 설치 → 모델 다운로드) | 셋업 스크립트 |

#### 완료 기준 / 확인 테스트

```bash
# 1. conda 환경 활성화 확인
conda activate stetho-agent
# 기대: 프롬프트에 (stetho-agent) 표시

# 2. Ollama LLM 한국어 응답 확인
ollama run qwen3:8b "안녕하세요"
# 기대: 한국어로 자연스러운 인사 응답

# 3. PyTorch MPS 백엔드 확인
python -c "import torch; print(torch.backends.mps.is_available())"
# 기대: True

# 4. 스키마 디폴트 값 출력 확인
python -c "from schemas.vitals import VitalSigns; print(VitalSigns())"
# 기대: heart_rate=75 blood_pressure_sys=120 blood_pressure_dia=80 body_temperature=36.5

python -c "from schemas.symptoms import SymptomInput; print(SymptomInput())"
# 기대: free_text='가벼운 기침이 있고 가끔 숨이 찹니다' checklist=['기침', '호흡곤란'] ...

# 5. Config 로딩 확인
python -c "from utils.config_loader import load_config; print(load_config('llm'))"
# 기대: LLM 설정 딕셔너리 출력

# 6. 스키마 테스트 통과
pytest tests/test_schemas.py -v
# 기대: 모든 테스트 PASSED

# 7. 디바이스 감지 테스트
pytest tests/test_device.py -v
# 기대: MPS 또는 CPU 디바이스 감지 PASSED
```

**체크포인트**: 환경에서 `import`가 모두 성공하고, 스키마 인스턴스 생성 시 디폴트 값이 올바르게 출력되면 Day 1 완료.

---

### Day 2: 핵심 모델 레이어

**목표**: AST 청진음 분류기, Ollama LLM 클라이언트, 오디오 전처리 파이프라인 완성

#### 작업 항목

| # | 작업 | 상세 | 산출물 |
|---|------|------|--------|
| 2-1 | 오디오 전처리 파이프라인 | `models/audio_preprocessor.py` — librosa로 .wav 로딩, 16kHz 리샘플링, 모노 변환, 최대 30초 트리밍, Mel Spectrogram 생성 및 이미지 저장 | 전처리 모듈 |
| 2-2 | AST 청진음 분류기 | `models/ast_classifier.py` — HuggingFace `MIT/ast-finetuned-audioset-10-10-0.4593` 모델 로딩 (MPS 우선, CPU 폴백), .wav 입력 → 5개 클래스 분류 확률 반환 | 분류기 모듈 |
| 2-3 | 샘플 오디오 데이터 준비 | `data/sample_audio/` — 테스트용 .wav 파일 (정상 폐음 또는 합성 테스트 오디오), 없으면 합성 오디오 생성 스크립트 작성 | 샘플 데이터 |
| 2-4 | Ollama LLM 클라이언트 | `models/llm_client.py` — config/llm.yaml 기반 Ollama 연동, LangChain `ChatOllama` 래퍼, 스트리밍/비스트리밍 지원, 타임아웃/재시도 처리 | LLM 클라이언트 |
| 2-5 | 시각화 유틸리티 | `utils/visualization.py` — Plotly 게이지 차트(생체신호), 바 차트(분류 확률), Mel Spectrogram 표시 함수 | 시각화 모듈 |
| 2-6 | 오디오 유틸리티 | `utils/audio_utils.py` — 오디오 파일 유효성 검사, 메타데이터 추출, 포맷 변환 | 유틸리티 |
| 2-7 | 모델 레이어 테스트 | `tests/test_ast_classifier.py`, `tests/test_llm_client.py`, `tests/test_audio_preprocessor.py` | 테스트 통과 |

#### 완료 기준 / 확인 테스트

```bash
# 1. 오디오 전처리 확인
python -m models.audio_preprocessor --test
# 기대: 샘플 .wav → Mel Spectrogram 이미지 생성, 파일 경로 출력

# 2. AST 분류기 확인
python -m models.ast_classifier --test
# 기대: 샘플 .wav 파일 → 5개 클래스별 확률 출력
# 예시 출력:
#   Normal: 0.72
#   Murmur: 0.12
#   Extrahls: 0.08
#   Artifact: 0.05
#   Extrastole: 0.03

# 3. LLM 클라이언트 확인
python -m models.llm_client --test
# 기대: Ollama에 "폐 청진음에서 정상 소견이 나왔습니다. 간단히 설명해주세요." 전송
#       → 한국어 응답 수신 및 출력

# 4. Mel Spectrogram 생성 확인
python -c "
from models.audio_preprocessor import AudioPreprocessor
ap = AudioPreprocessor()
result = ap.process('data/sample_audio/sample.wav')
print(f'Spectrogram saved: {result.spectrogram_path}')
"
# 기대: Spectrogram 이미지 파일 경로 출력

# 5. 분류기 테스트 스위트
pytest tests/test_ast_classifier.py -v
# 기대: 모든 테스트 PASSED

# 6. LLM 클라이언트 테스트
pytest tests/test_llm_client.py -v
# 기대: 연결 및 응답 테스트 PASSED
```

**체크포인트**: AST 분류기가 .wav를 받아 확률을 반환하고, LLM이 한국어 응답을 생성하면 Day 2 완료.

---

### Day 3: LangGraph 에이전트 + Streamlit UI

**목표**: LangGraph 멀티 에이전트 워크플로우 완성, Streamlit 멀티 페이지 UI 구축

#### 작업 항목

| # | 작업 | 상세 | 산출물 |
|---|------|------|--------|
| 3-1 | 에이전트 상태 정의 | `agents/state.py` — `AgentState` TypedDict 정의 (모든 필드, 디폴트 값) | 상태 모듈 |
| 3-2 | 분석 노드 구현 | `agents/nodes/` — `auscultation_node.py` (청진음 분석), `vitals_node.py` (생체신호 평가), `symptoms_node.py` (증상 분석), `synthesis_node.py` (종합 판단), `recommendation_node.py` (응답 생성) | 노드 모듈들 |
| 3-3 | 라우팅 엣지 구현 | `agents/edges/risk_router.py` — 위험도 기반 라우팅 (high/critical → 즉시 의료 상담, low/moderate → 일반 가이드) | 엣지 모듈 |
| 3-4 | LangGraph 그래프 조립 | `agents/graph.py` — 입력 수집 → 병렬(3개 분석 노드) → 종합 → 라우팅 → 응답 생성 | 그래프 모듈 |
| 3-5 | LLM 프롬프트 템플릿 | `prompts/auscultation_analysis.md`, `prompts/vitals_evaluation.md`, `prompts/symptom_analysis.md`, `prompts/synthesis.md`, `prompts/recommendation_general.md`, `prompts/recommendation_professional.md` | 프롬프트 파일들 |
| 3-6 | Streamlit 메인 페이지 | `app/main.py` — 사이드바 (모드 선택, 면책 조항), 메인 영역 (입력 탭 + 결과 탭) | 메인 UI |
| 3-7 | 입력 컴포넌트 | `app/components/` — `audio_uploader.py` (청진음 업로드), `vitals_input.py` (생체신호 입력, 디폴트 채워짐), `symptom_input.py` (증상 입력, 디폴트 채워짐) | UI 컴포넌트들 |
| 3-8 | 결과 대시보드 컴포넌트 | `app/components/result_dashboard.py` — 분석 결과 표시 영역 (Day 4에서 Plotly 차트 연결) | 대시보드 뼈대 |
| 3-9 | 에이전트 + UI 테스트 | `tests/test_agent_graph.py`, `tests/test_nodes.py` | 테스트 통과 |

#### 완료 기준 / 확인 테스트

```bash
# 1. 에이전트 워크플로우 단독 실행
python -m agents.graph --test
# 기대: 디폴트 입력 값으로 전체 워크플로우 실행
#   → 청진음 분석 결과, 생체신호 평가, 증상 분석, 종합 판단, 최종 응답 순서로 출력
#   → "위험도: low" 또는 "moderate" 표시

# 2. Streamlit UI 실행 확인
streamlit run app/main.py
# 기대: 브라우저에서 UI 렌더링
#   → 사이드바에 모드 선택(일반/의료진), 면책 조항 표시
#   → 메인 영역에 청진음 업로드, 생체신호 입력(디폴트 채워짐), 증상 입력(디폴트 채워짐)
#   → "분석 시작" 버튼 존재

# 3. UI 디폴트 값 확인
# 브라우저에서:
#   심박수 필드: 75
#   혈압 수축기: 120, 이완기: 80
#   체온: 36.5
#   증상 텍스트: "가벼운 기침이 있고 가끔 숨이 찹니다"
#   체크리스트: "기침", "호흡곤란" 선택됨

# 4. "분석 시작" 클릭
# 기대: 워크플로우 실행 → 결과 표시 (LLM 연동 완료 시 실제 응답, 아니면 목업)

# 5. 에이전트 그래프 테스트
pytest tests/test_agent_graph.py -v
# 기대: 워크플로우 실행 테스트 PASSED

# 6. 노드 단위 테스트
pytest tests/test_nodes.py -v
# 기대: 각 노드 개별 테스트 PASSED
```

**체크포인트**: `streamlit run app/main.py`로 UI가 뜨고, 디폴트 값 상태에서 "분석 시작" 시 결과가 표시되면 Day 3 완료.

---

### Day 4: 통합 + 마무리

**목표**: 전체 E2E 파이프라인 연결, 대시보드 시각화, 전체 테스트, 버그 수정

#### 작업 항목

| # | 작업 | 상세 | 산출물 |
|---|------|------|--------|
| 4-1 | E2E 파이프라인 통합 | 청진음 업로드 → AST 분류 → LangGraph 워크플로우 → 결과 표시까지 전체 연결 | 통합 완료 |
| 4-2 | Plotly 대시보드 시각화 | 생체신호 게이지 차트, 청진음 분류 확률 바 차트, 위험도 인디케이터, Mel Spectrogram 표시 연결 | 대시보드 완성 |
| 4-3 | 모드별 응답 분기 | `general` 모드: 쉬운 한국어, `professional` 모드: 전문 용어 — LLM 프롬프트 분기 확인 | 모드 전환 작동 |
| 4-4 | 에러 핸들링 강화 | Ollama 연결 실패, 오디오 파일 오류, LLM 타임아웃 등 예외 처리 및 사용자 친화적 에러 메시지 | 안정성 향상 |
| 4-5 | UI 폴리싱 | 로딩 스피너, 진행 상태 표시, 레이아웃 정리, 모바일 대응 기본, 면책 조항 표시 | UI 완성 |
| 4-6 | E2E 테스트 작성 | `tests/test_e2e.py` — 전체 파이프라인 시나리오 테스트 (디폴트 값 기반 + 커스텀 입력) | E2E 테스트 |
| 4-7 | 전체 테스트 스위트 실행 | `pytest tests/ -v` — 모든 테스트 통과 확인 | 전체 PASSED |
| 4-8 | 버그 수정 + 최종 정리 | 테스트 실패 항목 수정, 코드 정리, 불필요 파일 제거 | 최종 코드 |
| 4-9 | 문서 최종 업데이트 | README.md 최종 확인, 스크린샷 추가 (선택) | 문서 완성 |

#### 완료 기준 / 확인 테스트

```bash
# 1. 전체 E2E 시나리오 (수동 확인)
streamlit run app/main.py
# 브라우저에서:
#   1) .wav 파일 업로드 (또는 샘플 오디오 사용)
#   2) 생체신호 디폴트 값 유지 (심박수 75, 혈압 120/80, 체온 36.5)
#   3) 증상 디폴트 값 유지
#   4) "분석 시작" 클릭
#   5) 결과 확인:
#      - 청진음 분류 결과 + 확률 바 차트
#      - 생체신호 게이지 차트
#      - Mel Spectrogram 시각화
#      - 종합 분석 텍스트
#      - 위험도 표시
#      - 건강 가이드/권고사항

# 2. 모드 전환 확인
# 사이드바에서 "일반 사용자" → "의료 전문가" 전환 후 재분석
# 기대: 응답 톤이 변경됨
#   일반: "심장 박동이 정상 범위입니다" 스타일
#   전문가: "심박수 75bpm, 정상 동리듬(NSR) 범위 내" 스타일

# 3. 전체 테스트 스위트
pytest tests/ -v
# 기대: 모든 테스트 PASSED
#   tests/test_schemas.py ............ PASSED
#   tests/test_config.py ............. PASSED
#   tests/test_device.py ............. PASSED
#   tests/test_ast_classifier.py ..... PASSED
#   tests/test_llm_client.py ......... PASSED
#   tests/test_audio_preprocessor.py . PASSED
#   tests/test_agent_graph.py ........ PASSED
#   tests/test_nodes.py .............. PASSED
#   tests/test_e2e.py ................ PASSED

# 4. E2E 테스트 단독 실행
pytest tests/test_e2e.py -v
# 기대: 디폴트 입력 기반 전체 파이프라인 테스트 PASSED

# 5. 에러 핸들링 확인
# Ollama 서버 정지 후 "분석 시작" 클릭
# 기대: "Ollama 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요." 에러 메시지 표시 (크래시 없음)
```

**체크포인트**: .wav 업로드 → 분석 → 대시보드 시각화까지 한 번에 동작하고, 전체 테스트가 통과하면 Day 4 완료 (프로젝트 완성).

---

## 3. 마일스톤 체크포인트 요약

| Day | 마일스톤 | 핵심 확인 |
|-----|----------|-----------|
| **Day 1** | 기반 구축 완료 | `pytest tests/test_schemas.py` 통과, Ollama 한국어 응답, MPS 감지 |
| **Day 2** | 모델 레이어 완료 | AST 분류 확률 출력, LLM 한국어 응답, Mel Spectrogram 생성 |
| **Day 3** | 에이전트 + UI 완료 | `streamlit run app/main.py` 실행, 디폴트 값 표시, "분석 시작" 동작 |
| **Day 4** | 프로젝트 완성 | E2E 시나리오 통과, 전체 테스트 PASSED, 모드 전환 동작 |

---

## 4. 리스크 및 대응 계획

| 리스크 | 영향 | 대응 |
|--------|------|------|
| Ollama 모델 다운로드 지연 | Day 1 지연 | 사전 다운로드, 경량 모델(`qwen3:4b`)로 대체 |
| AST 모델 MPS 비호환 이슈 | Day 2 차질 | `PYTORCH_ENABLE_MPS_FALLBACK=1` 설정, CPU 폴백 |
| LangGraph 병렬 노드 오류 | Day 3 차질 | 순차 실행으로 우선 구현 후 병렬화 |
| Streamlit + Plotly 충돌 | Day 4 차질 | `st.plotly_chart` 대신 이미지 렌더링 폴백 |
| LLM 응답 품질/속도 이슈 | 전반 | 프롬프트 튜닝, 모델 교체(`exaone3.5:7.8b`) |
