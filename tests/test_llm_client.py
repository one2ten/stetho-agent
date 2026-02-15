"""LLM 클라이언트 테스트"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestLLMClientUnit:
    """LLMClient 단위 테스트 (Ollama 서버 연결 없이)"""

    def test_config_로딩(self):
        """LLM config가 올바르게 로딩되는지 확인"""
        from utils.config_loader import get_llm_config

        config = get_llm_config()
        ollama = config["ollama"]
        assert "model" in ollama
        assert "base_url" in ollama
        assert "temperature" in ollama

    def test_모델명_설정(self):
        """config에서 모델명이 올바르게 설정되는지 확인"""
        from utils.config_loader import get_llm_config

        config = get_llm_config()
        assert config["ollama"]["model"] == "qwen3:8b"

    def test_타임아웃_설정(self):
        """타임아웃이 올바르게 설정되는지 확인"""
        from utils.config_loader import get_llm_config

        config = get_llm_config()
        assert config["ollama"]["timeout"] == 120

    def test_재시도_설정(self):
        """최대 재시도 횟수가 설정되어 있는지 확인"""
        from utils.config_loader import get_llm_config

        config = get_llm_config()
        assert config["ollama"]["max_retries"] == 3


@pytest.mark.slow
class TestLLMClientIntegration:
    """LLMClient 통합 테스트 (Ollama 서버 필요)"""

    def test_서버_연결_확인(self):
        """Ollama 서버 연결 확인"""
        from models.llm_client import LLMClient

        client = LLMClient()
        available = client.is_available()
        if not available:
            pytest.skip("Ollama 서버가 실행되지 않았습니다")
        assert available is True

    def test_비스트리밍_생성(self):
        """비스트리밍 텍스트 생성 확인"""
        from models.llm_client import LLMClient

        client = LLMClient()
        if not client.is_available():
            pytest.skip("Ollama 서버가 실행되지 않았습니다")

        response = client.generate(
            prompt="1 + 1은?",
            system_prompt="숫자만 답하세요.",
        )
        assert isinstance(response, str)
        assert len(response) > 0

    def test_스트리밍_생성(self):
        """스트리밍 텍스트 생성 확인"""
        from models.llm_client import LLMClient

        client = LLMClient()
        if not client.is_available():
            pytest.skip("Ollama 서버가 실행되지 않았습니다")

        chunks = list(client.stream("안녕"))
        assert len(chunks) > 0
        full_text = "".join(chunks)
        assert len(full_text) > 0

    def test_한국어_응답(self):
        """한국어 응답이 올바르게 생성되는지 확인"""
        from models.llm_client import LLMClient

        client = LLMClient()
        if not client.is_available():
            pytest.skip("Ollama 서버가 실행되지 않았습니다")

        response = client.generate(
            prompt="한국의 수도는 어디인가요? 한 단어로만 답해주세요.",
            system_prompt="한국어로 답변하세요.",
        )
        assert isinstance(response, str)
        assert len(response) > 0
