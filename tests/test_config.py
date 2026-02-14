"""Config 파일 로딩 테스트"""
from __future__ import annotations

import pytest

from utils.config_loader import (
    load_config,
    get_llm_config,
    get_ast_config,
    get_vitals_reference,
    get_app_config,
)


class TestLoadConfig:
    """load_config 함수 테스트"""

    def test_llm_설정_로딩(self):
        """llm.yaml 로딩 확인"""
        config = load_config("llm")
        assert "ollama" in config
        assert config["ollama"]["model"] == "qwen3:8b"
        assert "base_url" in config["ollama"]

    def test_ast_model_설정_로딩(self):
        """ast_model.yaml 로딩 확인"""
        config = load_config("ast_model")
        assert "model" in config
        assert "MIT/ast-finetuned-audioset" in config["model"]["name"]
        assert "audio" in config
        assert config["audio"]["sample_rate"] == 16000

    def test_vitals_reference_설정_로딩(self):
        """vitals_reference.yaml 로딩 확인"""
        config = load_config("vitals_reference")
        assert "heart_rate" in config
        assert config["heart_rate"]["default"] == 75
        assert "blood_pressure" in config
        assert "body_temperature" in config

    def test_app_설정_로딩(self):
        """app.yaml 로딩 확인"""
        config = load_config("app")
        assert config["app"]["name"] == "StethoAgent"
        assert "disclaimer" in config
        assert "symptoms" in config

    def test_존재하지_않는_설정_파일(self):
        """존재하지 않는 설정 파일 로딩 시 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent")


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    def test_get_llm_config(self):
        """get_llm_config 편의 함수 확인"""
        config = get_llm_config()
        assert "ollama" in config

    def test_get_ast_config(self):
        """get_ast_config 편의 함수 확인"""
        config = get_ast_config()
        assert "model" in config

    def test_get_vitals_reference(self):
        """get_vitals_reference 편의 함수 확인"""
        config = get_vitals_reference()
        assert "heart_rate" in config

    def test_get_app_config(self):
        """get_app_config 편의 함수 확인"""
        config = get_app_config()
        assert "app" in config


class TestConfigValues:
    """설정 값 상세 검증 테스트"""

    def test_llm_타임아웃_설정(self):
        """LLM 타임아웃 값이 합리적인지 확인"""
        config = get_llm_config()
        timeout = config["ollama"]["timeout"]
        assert 30 <= timeout <= 300

    def test_오디오_샘플레이트(self):
        """오디오 샘플레이트가 16000Hz인지 확인"""
        config = get_ast_config()
        assert config["audio"]["sample_rate"] == 16000

    def test_심박수_정상범위(self):
        """심박수 정상 범위가 올바른지 확인"""
        config = get_vitals_reference()
        hr = config["heart_rate"]
        assert hr["normal"]["min"] == 60
        assert hr["normal"]["max"] == 100

    def test_면책조항_포함(self):
        """앱 설정에 면책 조항이 포함되어 있는지 확인"""
        config = get_app_config()
        assert "의료 진단이 아닙니다" in config["disclaimer"]
