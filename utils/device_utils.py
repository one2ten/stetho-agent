"""MPS/CPU 디바이스 자동 감지 유틸리티"""
from __future__ import annotations

import logging
import os

import torch

logger = logging.getLogger(__name__)

# MPS 폴백 환경변수 설정
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"


def get_device() -> torch.device:
    """
    최적 디바이스 자동 감지.
    Apple Silicon: MPS 우선, 폴백: CPU.
    """
    if torch.backends.mps.is_available():
        logger.info("MPS 디바이스를 사용합니다.")
        return torch.device("mps")

    logger.info("CPU 디바이스를 사용합니다.")
    return torch.device("cpu")


def get_device_info() -> dict:
    """
    디바이스 정보 반환.
    - device: "mps" | "cpu"
    - mps_available: bool
    - mps_built: bool
    - pytorch_version: str
    """
    device = get_device()
    return {
        "device": device.type,
        "mps_available": torch.backends.mps.is_available(),
        "mps_built": torch.backends.mps.is_built(),
        "pytorch_version": torch.__version__,
    }
