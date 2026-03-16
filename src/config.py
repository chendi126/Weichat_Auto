"""配置管理模块"""
import os
import yaml
from pathlib import Path

_config = None

def get_config() -> dict:
    """获取配置"""
    global _config
    if _config is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config
