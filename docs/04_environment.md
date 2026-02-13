# StethoAgent 환경 구성 가이드

> Mac (Apple Silicon) 개발 환경 기준

## 1. 사전 요구사항

| 항목 | 최소 요구 | 권장 |
|------|----------|------|
| **Mac** | Apple Silicon (M1+) | M1 Pro 이상 |
| **RAM** | 16GB | 32GB |
| **macOS** | 13.0+ (Ventura) | 14.0+ (Sonoma) |
| **디스크** | 20GB 여유 | 40GB 여유 |
| **Homebrew** | 설치 필요 | 최신 버전 |

---

## 2. 원커맨드 셋업

```bash
# 프로젝트 루트에서 실행
chmod +x setup_mac.sh
./setup_mac.sh
```

`setup_mac.sh`가 아래 전체 과정을 자동 수행합니다. 개별 설치가 필요하면 아래 수동 절차를 따르세요.

---

## 3. 수동 셋업 절차

### 3.1 Miniforge (conda) 설치

```bash
# Homebrew로 Miniforge 설치 (Apple Silicon 네이티브)
brew install miniforge

# conda 초기화
conda init zsh  # 또는 conda init bash
source ~/.zshrc
```

> Miniforge는 Apple Silicon에 최적화된 conda 배포판입니다. Anaconda/Miniconda 대신 권장합니다.

### 3.2 conda 환경 생성

```bash
# 프로젝트 루트에서
conda env create -f environment.yml

# 환경 활성화
conda activate stetho-agent

# 확인
python --version  # Python 3.11.x
which python      # .../envs/stetho-agent/bin/python
```

#### environment.yml 구조

```yaml
name: stetho-agent
channels:
  - conda-forge
  - pytorch
dependencies:
  - python=3.11
  - pip
  - pip:
    - streamlit>=1.40
    - langchain>=0.3
    - langchain-ollama>=0.2
    - langgraph>=0.2
    - torch>=2.2
    - transformers>=4.40
    - librosa>=0.10
    - soundfile>=0.12
    - plotly>=5.20
    - pydantic>=2.0
    - pyyaml>=6.0
    - python-dotenv>=1.0
    - pytest>=8.0
    - pytest-asyncio>=0.23
```

### 3.3 PyTorch MPS 확인

```bash
# MPS 백엔드 사용 가능 여부 확인
python -c "
import torch
print(f'PyTorch 버전: {torch.__version__}')
print(f'MPS 사용 가능: {torch.backends.mps.is_available()}')
print(f'MPS 빌드: {torch.backends.mps.is_built()}')
"
```

기대 출력:
```
PyTorch 버전: 2.x.x
MPS 사용 가능: True
MPS 빌드: True
```

### 3.4 Ollama 설치 및 LLM 모델 다운로드

```bash
# Ollama 설치 (Apple Silicon 네이티브)
brew install ollama

# Ollama 서버 시작 (별도 터미널 또는 백그라운드)
ollama serve &

# 기본 모델 다운로드 (qwen3:8b, ~5GB)
ollama pull qwen3:8b

# 한국어 응답 테스트
ollama run qwen3:8b "안녕하세요, 간단한 건강 관리 팁을 알려주세요."
```

#### 모델별 다운로드 명령

```bash
# 기본 (16GB Mac) — 권장
ollama pull qwen3:8b

# 경량 (8GB Mac)
ollama pull qwen3:4b

# 한국어 특화
ollama pull exaone3.5:7.8b

# 고성능 (32GB+ Mac)
ollama pull qwen3:30b-a3b
```

#### Ollama 서버 관리

```bash
# 서버 시작
ollama serve

# 설치된 모델 목록
ollama list

# 모델 삭제
ollama rm <model-name>

# 서버 상태 확인
curl http://localhost:11434/api/tags
```

### 3.5 HuggingFace AST 모델 사전 다운로드

```bash
# 첫 실행 시 자동 다운로드되지만, 사전 다운로드 권장
python -c "
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

model_name = 'MIT/ast-finetuned-audioset-10-10-0.4593'
print('피처 추출기 다운로드 중...')
extractor = AutoFeatureExtractor.from_pretrained(model_name)
print('모델 다운로드 중...')
model = AutoModelForAudioClassification.from_pretrained(model_name)
print(f'모델 다운로드 완료! 파라미터 수: {sum(p.numel() for p in model.parameters()):,}')
"
```

### 3.6 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필요 시 편집
# vim .env
```

### 3.7 설치 검증

```bash
# 전체 의존성 임포트 확인
python -c "
import streamlit
import langchain
import langgraph
import torch
import transformers
import librosa
import plotly
import pydantic
import yaml
print('모든 의존성 임포트 성공!')
"
```

---

## 4. HuggingFace AST 모델의 Mac MPS 호환 설정

### 4.1 MPS 폴백 환경변수

AST 모델의 일부 연산이 MPS에서 지원되지 않을 수 있습니다. 이를 위해 CPU 폴백을 활성화합니다.

```bash
# .env에 추가 (또는 쉘 프로필에)
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

### 4.2 디바이스 감지 코드 패턴

```python
import torch
import os

# MPS 폴백 환경변수 설정
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

def get_device() -> torch.device:
    """MPS 우선, CPU 폴백"""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")

device = get_device()
model = model.to(device)
```

### 4.3 AST 모델 MPS 추론 주의사항

| 연산 | MPS 지원 | 대응 |
|------|----------|------|
| Conv2d | O | MPS에서 직접 실행 |
| LayerNorm | O | MPS에서 직접 실행 |
| Softmax | O | MPS에서 직접 실행 |
| 일부 특수 연산 | X | `PYTORCH_ENABLE_MPS_FALLBACK=1`로 CPU 폴백 |

### 4.4 메모리 관리

```python
# 추론 시 메모리 최적화
with torch.no_grad():
    outputs = model(**inputs)

# MPS 캐시 정리 (필요 시)
if device.type == "mps":
    torch.mps.empty_cache()
```

---

## 5. 트러블슈팅 가이드

### 5.1 conda 환경 문제

#### `conda activate` 실패

```bash
# conda 초기화가 안 된 경우
conda init zsh  # 또는 bash
source ~/.zshrc

# 환경이 없는 경우
conda env create -f environment.yml
```

#### 패키지 충돌

```bash
# 환경 완전 재생성
conda deactivate
conda env remove -n stetho-agent
conda env create -f environment.yml
conda activate stetho-agent
```

### 5.2 Ollama 문제

#### "connection refused" 에러

```bash
# Ollama 서버가 실행 중인지 확인
pgrep ollama

# 실행 중이 아니면 시작
ollama serve &

# 포트 확인
lsof -i :11434
```

#### 모델 다운로드 실패/느림

```bash
# 다운로드 재시도
ollama pull qwen3:8b

# 프록시 환경이면
export HTTPS_PROXY=http://your-proxy:port
ollama pull qwen3:8b
```

#### 메모리 부족 (OOM)

```bash
# 경량 모델로 교체
ollama pull qwen3:4b
# config/llm.yaml에서 model: "qwen3:4b"로 변경

# 다른 Ollama 모델 언로드
ollama stop qwen3:8b
```

### 5.3 PyTorch MPS 문제

#### MPS 사용 불가 (`is_available()` = False)

```bash
# macOS 버전 확인 (12.3+ 필요)
sw_vers

# PyTorch 버전 확인 (2.0+ 필요)
python -c "import torch; print(torch.__version__)"

# PyTorch 재설치
pip install --force-reinstall torch
```

#### MPS 런타임 에러

```bash
# 폴백 환경변수 확인
echo $PYTORCH_ENABLE_MPS_FALLBACK
# "1"이어야 함

# .env 파일에 추가
echo 'PYTORCH_ENABLE_MPS_FALLBACK=1' >> .env
```

### 5.4 HuggingFace 모델 문제

#### 다운로드 타임아웃

```bash
# 캐시 확인
ls ~/.cache/huggingface/hub/

# 수동 다운로드
pip install huggingface-hub
huggingface-cli download MIT/ast-finetuned-audioset-10-10-0.4593
```

#### 모델 로딩 OOM

```bash
# 메모리 확인
python -c "
import psutil
gb = psutil.virtual_memory().total / (1024**3)
print(f'총 RAM: {gb:.1f}GB')
"

# 16GB 미만이면 CPU에서 float16 대신 float32
# config/ast_model.yaml에서 device.prefer_mps: false 설정
```

### 5.5 Streamlit 문제

#### 포트 충돌

```bash
# 다른 포트로 실행
streamlit run app/main.py --server.port 8502

# 기존 프로세스 확인
lsof -i :8501
```

#### 브라우저 자동 열기 비활성화

```bash
streamlit run app/main.py --server.headless true
```

### 5.6 오디오 처리 문제

#### librosa 설치 에러

```bash
# soundfile 백엔드 설치
brew install libsndfile
pip install soundfile librosa
```

#### .wav 파일 로딩 실패

```python
# 지원 포맷 확인
import soundfile as sf
print(sf.available_formats())

# ffmpeg 설치 (다양한 포맷 지원)
# brew install ffmpeg
```

---

## 6. 개발 도구 추천

| 도구 | 용도 | 설치 |
|------|------|------|
| **VS Code** | 코드 편집 | `brew install --cask visual-studio-code` |
| **Python 확장** | 린트, 포맷팅 | VS Code 마켓플레이스 |
| **Ruff** | Python 린터/포맷터 | `pip install ruff` |
| **httpie** | API 테스트 | `brew install httpie` |

---

## 7. 빠른 참조 명령어

```bash
# 환경 활성화
conda activate stetho-agent

# Ollama 서버 시작
ollama serve &

# 앱 실행
streamlit run app/main.py

# 테스트 실행
pytest tests/ -v

# MPS 확인
python -c "import torch; print(torch.backends.mps.is_available())"

# Ollama 상태 확인
curl -s http://localhost:11434/api/tags | python -m json.tool
```
