# StethoAgent

**AI 기반 건강 가이드 프로토타입** — 폐 청진음, 생체 신호, 증상을 종합 분석하여 건강 가이드를 제공합니다.

> ⚠️ 본 분석 결과는 AI 기반 참고 정보이며 의료 진단이 아닙니다. 정확한 진단은 반드시 의료 전문가와 상담하세요.

## 주요 기능

- **폐 청진음 분류**: .wav 파일 업로드 → HuggingFace AST 모델로 5개 클래스 분류 (Normal, Murmur, Extrahls, Artifact, Extrastole)
- **생체 신호 분석**: 심박수, 혈압, 체온 입력 → 정상 범위 비교 및 이상 소견 평가
- **증상 종합 분석**: 자연어 설명 + 체크리스트 → LLM 기반 증상 해석
- **AI 종합 판단**: LangGraph 에이전트가 병렬 분석 → 위험도 평가 → 맞춤 건강 가이드 생성
- **대시보드 시각화**: Plotly 게이지 차트, 확률 바 차트, Mel Spectrogram

## 빠른 시작

### 사전 요구사항

- Mac (Apple Silicon, 16GB+ RAM 권장)
- [Homebrew](https://brew.sh)

### 원커맨드 셋업

```bash
git clone https://github.com/<your-username>/stetho-agent.git
cd stetho-agent
chmod +x setup_mac.sh
./setup_mac.sh
```

### 수동 셋업

```bash
# 1. conda 환경 생성
conda env create -f environment.yml
conda activate stetho-agent

# 2. Ollama 설치 + 모델 다운로드
brew install ollama
ollama serve &
ollama pull qwen3:8b

# 3. 환경 변수 설정
cp .env.example .env

# 4. 앱 실행
streamlit run app/main.py
```

### 확인

```bash
# MPS 사용 가능 확인
python -c "import torch; print(torch.backends.mps.is_available())"

# Ollama 연결 확인
curl http://localhost:11434/api/tags

# 테스트 실행
pytest tests/ -v
```

## 기술 스택

| 카테고리 | 기술 |
|----------|------|
| UI | Streamlit |
| LLM | Ollama (qwen3:8b, 로컬) |
| 에이전트 | LangGraph + LangChain |
| 청진음 분류 | HuggingFace AST (PyTorch MPS) |
| 오디오 처리 | librosa |
| 시각화 | Plotly |
| 데이터 검증 | Pydantic |
| 환경 관리 | conda (Miniforge) |
| 언어 | Python 3.11+ |

## 프로젝트 구조

```
stetho-agent/
├── app/                    # Streamlit UI
│   ├── main.py
│   └── components/         # UI 컴포넌트
├── agents/                 # LangGraph 에이전트
│   ├── graph.py            # 워크플로우 그래프
│   ├── state.py            # 에이전트 상태
│   ├── nodes/              # 분석 노드
│   └── edges/              # 라우팅 엣지
├── models/                 # AI 모델
│   ├── ast_classifier.py   # 청진음 분류기
│   ├── llm_client.py       # LLM 클라이언트
│   └── audio_preprocessor.py
├── schemas/                # Pydantic 스키마
├── config/                 # YAML 설정
├── prompts/                # LLM 프롬프트 템플릿
├── utils/                  # 유틸리티
├── data/                   # 샘플 데이터
├── tests/                  # 테스트
└── docs/                   # 프로젝트 문서
```

## 사용자 모드

| 모드 | 대상 | 설명 |
|------|------|------|
| **일반 사용자** | 건강 관심자 | 쉬운 한국어로 건강 가이드 제공 |
| **의료 전문가** | 의료진 | 전문 용어를 사용한 진단 보조 리포트 |

## LLM 모델 교체

`config/llm.yaml`에서 모델명을 변경하면 됩니다:

```yaml
ollama:
  model: "qwen3:8b"        # 기본 (16GB Mac)
  # model: "qwen3:4b"      # 경량 (8GB Mac)
  # model: "exaone3.5:7.8b" # 한국어 특화
  # model: "qwen3:30b-a3b"  # 고성능 (32GB+ Mac)
```

## 문서

- [개발 계획서](docs/01_project_plan.md)
- [시스템 아키텍처](docs/02_architecture.md)
- [개발 명세서](docs/03_spec.md)
- [환경 구성 가이드](docs/04_environment.md)
- [작업 체크리스트](docs/05_checklist.md)

## 테스트

```bash
# 전체 테스트
pytest tests/ -v

# 개별 테스트
pytest tests/test_schemas.py -v      # 스키마
pytest tests/test_ast_classifier.py -v  # AST 분류기
pytest tests/test_agent_graph.py -v     # 에이전트 워크플로우
pytest tests/test_e2e.py -v             # E2E 통합
```

## 기여 가이드

1. 이 저장소를 fork 합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/기능명`)
3. 변경사항을 커밋합니다 (`git commit -m '기능 추가: ...'`)
4. 브랜치에 push 합니다 (`git push origin feature/기능명`)
5. Pull Request를 생성합니다

### 코드 스타일

- Python PEP 8 준수
- 타입 힌트 필수
- 한국어 주석 및 독스트링
- Pydantic 모델 사용
- 설정은 `config/` YAML에서 로딩 (하드코딩 금지)

## 라이선스

MIT License
