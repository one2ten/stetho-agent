"""YAML 설정 파일 로더 유틸리티"""
from __future__ import annotations

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# 프로젝트 루트 기준 config 디렉토리 경로
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_config(name: str) -> dict:
    """
    YAML 설정 파일 로딩.

    Args:
        name: 설정 파일명 (확장자 제외). "llm", "ast_model", "vitals_reference", "app"

    Returns:
        파싱된 설정 딕셔너리

    Raises:
        FileNotFoundError: 설정 파일이 존재하지 않을 때
    """
    config_path = CONFIG_DIR / f"{name}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logger.info("설정 파일 로딩 완료: %s", config_path.name)
    return config


def get_llm_config() -> dict:
    """LLM 설정 로딩 (편의 함수)"""
    return load_config("llm")


def get_ast_config() -> dict:
    """AST 모델 설정 로딩 (편의 함수)"""
    return load_config("ast_model")


def get_vitals_reference() -> dict:
    """생체신호 정상 범위 기준 로딩 (편의 함수)"""
    return load_config("vitals_reference")


def get_app_config() -> dict:
    """앱 일반 설정 로딩 (편의 함수)"""
    return load_config("app")
