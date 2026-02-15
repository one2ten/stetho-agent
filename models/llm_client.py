"""LLM 클라이언트 모듈 — Ollama 기반 텍스트 생성"""
from __future__ import annotations

import logging
from typing import Generator

import httpx
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from utils.config_loader import get_llm_config

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Ollama 기반 LLM 클라이언트.

    - config/llm.yaml 기반 ChatOllama 초기화
    - 비스트리밍/스트리밍 텍스트 생성
    - 서버 연결 확인
    - 타임아웃/재시도 처리
    """

    def __init__(self) -> None:
        config = get_llm_config()
        ollama_config = config.get("ollama", {})

        self.model: str = ollama_config.get("model", "qwen3:8b")
        self.base_url: str = ollama_config.get("base_url", "http://localhost:11434")
        self.temperature: float = ollama_config.get("temperature", 0.7)
        self.top_p: float = ollama_config.get("top_p", 0.9)
        self.timeout: int = ollama_config.get("timeout", 120)
        self.max_retries: int = ollama_config.get("max_retries", 3)

        self._llm = ChatOllama(
            model=self.model,
            base_url=self.base_url,
            temperature=self.temperature,
            top_p=self.top_p,
            num_predict=-1,
        )
        logger.info("LLMClient 초기화: model=%s, base_url=%s", self.model, self.base_url)

    def is_available(self) -> bool:
        """
        Ollama 서버 연결 상태 확인.

        Returns:
            연결 가능 여부
        """
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            logger.warning("Ollama 서버에 연결할 수 없습니다: %s", self.base_url)
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """
        비스트리밍 텍스트 생성.

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택)

        Returns:
            생성된 텍스트

        Raises:
            RuntimeError: LLM 호출 실패 시
        """
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info("LLM 생성 요청 (시도 %d/%d)", attempt, self.max_retries)
                response = self._llm.invoke(messages)
                result = response.content
                logger.info("LLM 응답 수신: %d자", len(result))
                return result
            except Exception as e:
                last_error = e
                logger.warning("LLM 호출 실패 (시도 %d/%d): %s", attempt, self.max_retries, e)

        raise RuntimeError(f"LLM 호출이 {self.max_retries}회 모두 실패했습니다: {last_error}")

    def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> Generator[str, None, None]:
        """
        스트리밍 텍스트 생성.

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택)

        Yields:
            텍스트 청크
        """
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        try:
            for chunk in self._llm.stream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error("LLM 스트리밍 실패: %s", e)
            raise RuntimeError(f"LLM 스트리밍 호출 실패: {e}") from e


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM 클라이언트 테스트")
    parser.add_argument("--test", action="store_true", help="테스트 모드 실행")
    args = parser.parse_args()

    if args.test:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        print("=" * 60)
        print("LLMClient 테스트")
        print("=" * 60)

        client = LLMClient()

        # 1. 서버 연결 확인
        available = client.is_available()
        print(f"✓ Ollama 서버 연결: {'성공' if available else '실패'}")

        if not available:
            print("✗ Ollama 서버가 실행되지 않았습니다. `ollama serve`를 실행하세요.")
        else:
            # 2. 비스트리밍 생성
            print("\n--- 비스트리밍 생성 ---")
            try:
                response = client.generate(
                    prompt="폐 청진에서 수포음(crackle)이 들릴 때 의심할 수 있는 질환을 간단히 설명해주세요.",
                    system_prompt="당신은 한국어로 답변하는 의료 AI 어시스턴트입니다. 간결하게 답변하세요.",
                )
                print(f"✓ 응답: {response[:200]}...")
            except RuntimeError as e:
                print(f"✗ 생성 실패: {e}")

            # 3. 스트리밍 생성
            print("\n--- 스트리밍 생성 ---")
            try:
                print("✓ 응답: ", end="", flush=True)
                for chunk in client.stream("안녕하세요, 간단히 자기소개를 해주세요."):
                    print(chunk, end="", flush=True)
                print()
            except RuntimeError as e:
                print(f"\n✗ 스트리밍 실패: {e}")

        print("\n테스트 완료!")
