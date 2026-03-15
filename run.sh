#!/bin/bash
# StethoAgent 실행 스크립트
# 사용법: ./run.sh [명령어]
#
# 명령어:
#   app       — Streamlit 웹 UI 실행 (기본값)
#   test      — 전체 테스트 실행
#   workflow  — 에이전트 워크플로우 CLI 테스트 (실제 Ollama 연동)
#   lint      — 코드 린트 (ruff)
#   check     — Ollama 서버 + 모델 + 의존성 상태 확인
#   all       — check → test → app 순서로 실행

set -e

# ── conda 환경 활성화 ──
_activate_conda() {
    if command -v conda &> /dev/null; then
        eval "$(conda shell.zsh hook 2>/dev/null || conda shell.bash hook 2>/dev/null)"
    else
        source /opt/miniconda3/etc/profile.d/conda.sh 2>/dev/null || \
        source ~/miniforge3/etc/profile.d/conda.sh 2>/dev/null || \
        source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || {
            echo "[오류] conda를 찾을 수 없습니다. setup_mac.sh를 먼저 실행하세요."
            exit 1
        }
    fi
    conda activate stetho-agent
}

# ── 프로젝트 루트로 이동 ──
cd "$(dirname "$0")"
_activate_conda

# ── Ollama 상태 확인 ──
_check_ollama() {
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "[✓] Ollama 서버 실행 중"
        return 0
    else
        echo "[✗] Ollama 서버가 실행 중이 아닙니다"
        echo "    → Ollama 앱을 실행하거나 'ollama serve'를 먼저 실행하세요"
        return 1
    fi
}

_check_model() {
    local model=$(python -c "from utils.config_loader import get_llm_config; print(get_llm_config().get('ollama',{}).get('model','qwen3:8b'))" 2>/dev/null || echo "qwen3:8b")
    if ollama list 2>/dev/null | grep -q "${model%%:*}"; then
        echo "[✓] LLM 모델 준비됨: $model"
        return 0
    else
        echo "[✗] LLM 모델 없음: $model"
        echo "    → 'ollama pull $model'을 실행하세요"
        return 1
    fi
}

# ── 명령어 정의 ──
cmd_check() {
    echo "========================================="
    echo " StethoAgent 환경 상태 확인"
    echo "========================================="
    echo ""

    # conda 환경
    echo "[✓] conda 환경: stetho-agent"

    # Python 의존성
    python -c "
import torch, streamlit, langgraph, pydantic, librosa, plotly
print(f'[✓] Python 의존성 OK')
print(f'    PyTorch={torch.__version__} (MPS={torch.backends.mps.is_available()})')
print(f'    Streamlit={streamlit.__version__}, Pydantic={pydantic.__version__}')
" 2>/dev/null || echo "[✗] Python 의존성 문제 — 'conda env update -f environment.yml' 실행"

    # Ollama
    _check_ollama
    _check_model

    # AST 모델 캐시
    if python -c "from pathlib import Path; import sys; sys.exit(0 if any(Path.home().joinpath('.cache/huggingface/hub').glob('models--MIT--ast-*')) else 1)" 2>/dev/null; then
        echo "[✓] AST 모델 캐시 존재"
    else
        echo "[!] AST 모델 미다운로드 (첫 실행 시 자동 다운로드, ~300MB)"
    fi

    echo ""
    echo "========================================="
}

cmd_app() {
    echo "🩺 StethoAgent 웹 UI 시작..."
    echo "   브라우저에서 http://localhost:8501 로 접속하세요"
    echo "   (Ctrl+C로 종료)"
    echo ""
    streamlit run app/main.py
}

cmd_test() {
    echo "🧪 전체 테스트 실행..."
    echo ""
    pytest tests/ -v
}

cmd_workflow() {
    echo "🔬 에이전트 워크플로우 CLI 테스트 (실제 Ollama 연동)..."
    echo "   ⏱️  약 1~2분 소요됩니다"
    echo ""
    if ! _check_ollama; then
        exit 1
    fi
    python -m agents.graph --test
}

cmd_lint() {
    echo "🔍 코드 린트 (ruff)..."
    echo ""
    ruff check agents/ app/ models/ schemas/ utils/ tests/
    echo ""
    echo "[✓] 린트 통과!"
}

cmd_all() {
    cmd_check
    echo ""
    cmd_test
    echo ""
    cmd_app
}

cmd_help() {
    echo "StethoAgent 실행 스크립트"
    echo ""
    echo "사용법: ./run.sh [명령어]"
    echo ""
    echo "명령어:"
    echo "  app       Streamlit 웹 UI 실행 (기본값)"
    echo "  test      전체 테스트 실행 (pytest)"
    echo "  workflow  에이전트 워크플로우 CLI 테스트 (실제 Ollama 연동)"
    echo "  lint      코드 린트 (ruff)"
    echo "  check     환경 상태 확인 (Ollama, 모델, 의존성)"
    echo "  all       check → test → app 순서로 실행"
    echo "  help      이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  ./run.sh              # 웹 UI 실행"
    echo "  ./run.sh test         # 테스트만 실행"
    echo "  ./run.sh workflow     # Ollama 연동 CLI 테스트"
    echo "  ./run.sh check        # 환경 확인만"
}

# ── 메인 ──
case "${1:-app}" in
    app)      cmd_app ;;
    test)     cmd_test ;;
    workflow) cmd_workflow ;;
    lint)     cmd_lint ;;
    check)    cmd_check ;;
    all)      cmd_all ;;
    help|-h|--help) cmd_help ;;
    *)
        echo "[오류] 알 수 없는 명령어: $1"
        echo ""
        cmd_help
        exit 1
        ;;
esac
