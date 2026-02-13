# StethoAgent — Claude Code 프로젝트 규칙

## 프로젝트 개요
AI 기반 건강 가이드 프로토타입. 폐 청진음 + 생체신호 + 증상을 종합 분석.
Mac Apple Silicon 로컬 환경에서 실행 (Ollama + PyTorch MPS).

## 핵심 규칙

### 언어
- **코드 주석, 독스트링, UI 텍스트: 모두 한국어**
- 변수명, 함수명, 클래스명: 영어 (PEP 8)
- Git 커밋 메시지: 한국어

### 디폴트 값 필수
- 모든 입력에 합리적 디폴트가 있어야 함 (아무것도 안 해도 데모 가능)
- 생체신호: HR=75, BP=120/80, Temp=36.5
- 증상: "가벼운 기침이 있고 가끔 숨이 찹니다", ["기침", "호흡곤란"]
- Pydantic `Field(default=...)` 사용

### 설정 분리
- **하드코딩 금지**. 모든 설정은 `config/*.yaml` 또는 `.env`에서 로딩
- LLM 모델명, 서버 URL, 정상 범위 기준값 등
- `utils/config_loader.py`의 `load_config()` 사용

### Mac 호환
- `utils/device_utils.py`의 `get_device()` 사용 (MPS 우선 → CPU 폴백)
- `PYTORCH_ENABLE_MPS_FALLBACK=1` 환경변수 설정 필수
- `torch.no_grad()` 컨텍스트에서 추론

### 에러 핸들링
- 외부 호출 (Ollama, HuggingFace, 파일 I/O) 모두 `try-except`
- 사용자 친화적 한국어 에러 메시지
- 로깅: `logging` 모듈 사용

### 타입 힌트
- 모든 함수에 타입 힌트 필수
- Pydantic 적극 활용
- `from __future__ import annotations` 사용

### 면책 조항
- 모든 결과 화면에 표시: `"⚠️ 본 분석 결과는 AI 기반 참고 정보이며 의료 진단이 아닙니다."`

## 프로젝트 구조

```
stetho-agent/
├── app/main.py, components/       # Streamlit UI
├── agents/graph.py, state.py, nodes/, edges/  # LangGraph
├── models/ast_classifier.py, llm_client.py, audio_preprocessor.py
├── schemas/vitals.py, symptoms.py, auscultation.py, report.py
├── prompts/*.md                   # LLM 프롬프트 템플릿
├── config/*.yaml                  # 설정 파일
├── utils/                         # 유틸리티
├── data/sample_audio/             # 샘플 데이터
└── tests/                         # 테스트
```

## 기술 스택
- UI: Streamlit
- LLM: Ollama (qwen3:8b, config에서 교체 가능)
- 에이전트: LangGraph + LangChain
- 청진음 분류: HuggingFace AST (MIT/ast-finetuned-audioset-10-10-0.4593)
- 오디오: librosa
- 시각화: Plotly
- 검증: Pydantic
- 환경: conda (Miniforge), Python 3.11+

## 주요 스키마
- `VitalSigns`: 심박수(75), 혈압(120/80), 체온(36.5)
- `SymptomInput`: 자유텍스트, 체크리스트, 기간, 강도
- `AuscultationResult`: 파일명, 분류, 확률, 스펙트로그램
- `RiskAssessment`: 레벨(low/moderate/high/critical), 점수, 요인
- `AgentState`: LangGraph 상태 (TypedDict)

## LangGraph 워크플로우
```
입력 검증 → 병렬(청진음 + 생체신호 + 증상 분석) → 종합 판단 → 위험도 라우팅 → 응답 생성
```
- 위험도 high/critical → 즉시 의료 상담 권고
- user_mode: general=쉬운 한국어, professional=전문 용어

## 명령어
```bash
conda activate stetho-agent          # 환경 활성화
streamlit run app/main.py            # 앱 실행
pytest tests/ -v                     # 전체 테스트
python -m models.ast_classifier --test  # AST 분류기 테스트
python -m models.llm_client --test      # LLM 클라이언트 테스트
python -m agents.graph --test           # 에이전트 워크플로우 테스트
```

## 개발 원칙
1. 한국어 우선 (주석, 독스트링, UI)
2. 디폴트 값 필수 (데모 가능)
3. Mac 호환 (MPS 자동 감지, CPU 폴백)
4. 설정 분리 (config/ YAML, .env)
5. LLM 교체 용이 (config 변경만)
6. 면책 조항 표시 필수
7. 에러 핸들링 (try-except, 한국어 메시지)
8. 타입 힌트 + Pydantic
