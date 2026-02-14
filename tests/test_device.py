"""디바이스 감지 테스트"""
from __future__ import annotations

import torch

from utils.device_utils import get_device, get_device_info


class TestGetDevice:
    """get_device 함수 테스트"""

    def test_디바이스_반환_타입(self):
        """torch.device 타입이 반환되는지 확인"""
        device = get_device()
        assert isinstance(device, torch.device)

    def test_디바이스_유효값(self):
        """반환된 디바이스가 mps 또는 cpu인지 확인"""
        device = get_device()
        assert device.type in ("mps", "cpu")

    def test_mps_가능_시_mps_반환(self):
        """MPS가 사용 가능한 환경에서 mps 디바이스 반환 확인"""
        device = get_device()
        if torch.backends.mps.is_available():
            assert device.type == "mps"
        else:
            assert device.type == "cpu"


class TestGetDeviceInfo:
    """get_device_info 함수 테스트"""

    def test_디바이스_정보_키(self):
        """반환된 딕셔너리에 필수 키가 포함되어 있는지 확인"""
        info = get_device_info()
        assert "device" in info
        assert "mps_available" in info
        assert "mps_built" in info
        assert "pytorch_version" in info

    def test_디바이스_정보_타입(self):
        """반환된 값들의 타입이 올바른지 확인"""
        info = get_device_info()
        assert isinstance(info["device"], str)
        assert isinstance(info["mps_available"], bool)
        assert isinstance(info["mps_built"], bool)
        assert isinstance(info["pytorch_version"], str)

    def test_pytorch_버전(self):
        """PyTorch 버전이 올바르게 반환되는지 확인"""
        info = get_device_info()
        assert info["pytorch_version"] == torch.__version__

    def test_mps_폴백_환경변수(self):
        """PYTORCH_ENABLE_MPS_FALLBACK 환경변수가 설정되었는지 확인"""
        import os
        # device_utils 임포트 시 자동으로 환경변수 설정됨
        assert os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK") == "1"
