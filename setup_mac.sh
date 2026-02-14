#!/bin/bash
# StethoAgent Mac Apple Silicon 원커맨드 셋업 스크립트
set -e

echo "========================================="
echo " StethoAgent 환경 셋업 시작"
echo "========================================="

# 1. Homebrew 확인
if ! command -v brew &> /dev/null; then
    echo "[오류] Homebrew가 설치되어 있지 않습니다."
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi
echo "[✓] Homebrew 확인 완료"

# 2. Miniforge (conda) 확인 및 설치
if ! command -v conda &> /dev/null; then
    echo "[설치] Miniforge 설치 중..."
    brew install miniforge
    conda init zsh
    echo "[!] 쉘을 재시작한 후 이 스크립트를 다시 실행해주세요."
    echo "    source ~/.zshrc && ./setup_mac.sh"
    exit 0
fi
echo "[✓] conda 확인 완료"

# 3. conda 환경 생성
if conda info --envs | grep -q "stetho-agent"; then
    echo "[건너뜀] stetho-agent 환경이 이미 존재합니다."
else
    echo "[설치] conda 환경 생성 중..."
    conda env create -f environment.yml
fi
echo "[✓] conda 환경 준비 완료"

# 4. 환경 활성화
echo "[활성화] conda 환경 활성화..."
eval "$(conda shell.zsh hook)"
conda activate stetho-agent

# 5. Ollama 확인 및 설치
if ! command -v ollama &> /dev/null; then
    echo "[설치] Ollama 설치 중..."
    brew install ollama
fi
echo "[✓] Ollama 확인 완료"

# 6. Ollama 서버 시작
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[시작] Ollama 서버 시작 중..."
    ollama serve &
    sleep 3
fi
echo "[✓] Ollama 서버 실행 중"

# 7. LLM 모델 다운로드
if ! ollama list | grep -q "qwen3:8b"; then
    echo "[다운로드] qwen3:8b 모델 다운로드 중... (약 5GB)"
    ollama pull qwen3:8b
fi
echo "[✓] qwen3:8b 모델 준비 완료"

# 8. .env 파일 생성
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[✓] .env 파일 생성 완료"
else
    echo "[건너뜀] .env 파일이 이미 존재합니다."
fi

# 9. 검증
echo ""
echo "========================================="
echo " 환경 검증"
echo "========================================="

python -c "import torch; print(f'  PyTorch: {torch.__version__}, MPS: {torch.backends.mps.is_available()}')"
python -c "import streamlit; print(f'  Streamlit: {streamlit.__version__}')"
python -c "import pydantic; print(f'  Pydantic: {pydantic.__version__}')"

echo ""
echo "========================================="
echo " 셋업 완료!"
echo "========================================="
echo ""
echo "사용법:"
echo "  conda activate stetho-agent"
echo "  streamlit run app/main.py"
echo ""
