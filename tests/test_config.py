import os
import tempfile

import yaml  # type: ignore

from merlai.config import Config


def make_temp_config(content: dict) -> str:
    """Create a temporary YAML config file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".yaml")
    with os.fdopen(fd, "w") as f:
        yaml.dump(content, f)
    return path


def test_load_and_get_section() -> None:
    config_data = {
        "ai_models": {
            "default": "test-model",
            "available": [
                {"name": "test-model", "type": "huggingface", "model_path": "foo"}
            ],
        },
        "plugins": {"enabled": True},
    }
    path = make_temp_config(config_data)
    config = Config(config_path=path)
    assert config.get("ai_models")["default"] == "test-model"
    assert config.get("plugins")["enabled"] is True
    os.remove(path)


def test_get_default_value() -> None:
    config = Config(config_path="/tmp/nonexistent.yaml")
    assert config.get("notfound", 123) == 123


def test_reload() -> None:
    config_data1 = {"foo": 1}
    config_data2 = {"foo": 2}
    path = make_temp_config(config_data1)
    config = Config(config_path=path)
    assert config.get("foo") == 1
    # Overwrite file
    with open(path, "w") as f:
        yaml.dump(config_data2, f)
    config.reload()
    assert config.get("foo") == 2
    os.remove(path)
