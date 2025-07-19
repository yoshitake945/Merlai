# mypy: disable-error-code=no-untyped-def
import os
import tempfile
from typing import Optional

import yaml

from merlai.core.ai_models import (
    AIModelInterface,
    AIModelManager,
    GenerationResponse,
    ModelConfig,
    ModelType,
)

# Use ModelType.DUMMY if available, else fallback to HUGGINGFACE for compatibility
DUMMY_TYPE = getattr(ModelType, "DUMMY", ModelType.HUGGINGFACE)


# DummyModel for test isolation
class DummyModel(AIModelInterface):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)

    def is_available(self) -> bool:
        return True

    def get_model_info(self) -> dict:
        return {"name": self.config.name, "type": self.config.type.value}

    def generate_harmony(self, request: object) -> GenerationResponse:
        return GenerationResponse(
            success=True, result=None, model_name=self.model_name, generation_time=0.0
        )

    def generate_bass(self, request: object) -> GenerationResponse:
        return GenerationResponse(
            success=True, result=None, model_name=self.model_name, generation_time=0.0
        )

    def generate_drums(self, request: object) -> GenerationResponse:
        return GenerationResponse(
            success=True, result=None, model_name=self.model_name, generation_time=0.0
        )

    def analyze_music(self, midi_data: object) -> GenerationResponse:
        return GenerationResponse(
            success=True, result=None, model_name=self.model_name, generation_time=0.0
        )

    def unload_model(self) -> None:
        pass


# Patch AIModelManager for tests to always use DummyModel
class TestAIModelManager(AIModelManager):
    def register_model(self, config: Optional[ModelConfig]) -> bool:
        if config is None or config.name in self.models:
            return False
        model = DummyModel(config)
        self.models[config.name] = model
        return True

    def load_from_config(self, config_path: str) -> bool:
        raise NotImplementedError(
            "load_from_config is not implemented in TestAIModelManager for tests."
        )


def make_temp_config(content: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".yaml")
    with os.fdopen(fd, "w") as f:
        yaml.dump(content, f)
    return path


def dummy_config(name: str = "dummy", type=DUMMY_TYPE) -> ModelConfig:
    """Create a ModelConfig for DummyModel (test isolation)."""
    return ModelConfig(name=name, type=type, model_path="/tmp/model")


def test_register_and_list_models() -> None:
    mgr = TestAIModelManager()
    cfg1 = dummy_config("m1", DUMMY_TYPE)
    cfg2 = dummy_config("m2", DUMMY_TYPE)
    assert mgr.register_model(cfg1) is True
    assert mgr.register_model(cfg2) is True
    assert set(mgr.list_models()) == {"m1", "m2"}


def test_duplicate_registration() -> None:
    mgr = TestAIModelManager()
    cfg = dummy_config("dup", DUMMY_TYPE)
    assert mgr.register_model(cfg) is True
    assert mgr.register_model(cfg) is False  # Duplicate


def test_get_and_remove_model() -> None:
    mgr = TestAIModelManager()
    cfg = dummy_config("to_remove", DUMMY_TYPE)
    mgr.register_model(cfg)
    assert mgr.get_model("to_remove") is not None
    assert mgr.remove_model("to_remove") is True
    assert mgr.get_model("to_remove") is None


def test_set_and_get_default_model() -> None:
    mgr = TestAIModelManager()
    cfg1 = dummy_config("d1", DUMMY_TYPE)
    cfg2 = dummy_config("d2", DUMMY_TYPE)
    mgr.register_model(cfg1)
    mgr.register_model(cfg2)
    assert mgr.set_default_model("d2") is True
    assert mgr.default_model == "d2"
    assert mgr.set_default_model("notfound") is False


def test_load_from_config() -> None:
    config_data: dict = {
        "ai_models": {
            "default": "test-model",
            "available": [
                {"name": "test-model", "type": DUMMY_TYPE.value},
                {"name": "api-model", "type": DUMMY_TYPE.value},
            ],
        }
    }
    path = make_temp_config(config_data)
    os.remove(path)
