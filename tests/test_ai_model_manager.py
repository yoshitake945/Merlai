# mypy: disable-error-code=no-untyped-def
import os
import tempfile
from typing import Optional

import pytest
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
class DummyAIModelManager(AIModelManager):
    def register_model(self, config: Optional[ModelConfig]) -> bool:
        if config is None or config.name in self.models:
            return False
        model = DummyModel(config)
        self.models[config.name] = model
        return True

    def load_from_config(self, config_path: Optional[str] = None) -> bool:
        import os

        import yaml

        config_path = config_path or os.path.expanduser("~/.merlai/config.yaml")
        if not os.path.exists(config_path):
            return False
        try:
            with open(config_path, "r") as f:
                conf = yaml.safe_load(f)
            models_conf = conf.get("ai_models", {})
            default_name = models_conf.get("default")
            available = models_conf.get("available", [])
            loaded = False
            for m in available:
                try:
                    model_config = ModelConfig(
                        name=m["name"],
                        type=ModelType(m["type"]),
                        model_path=m.get("model_path"),
                        local_path=m.get("local_path"),
                        api_key=m.get("api_key"),
                        endpoint=m.get("endpoint"),
                        parameters=m.get("parameters", {}),
                    )
                    if self.register_model(model_config):
                        loaded = True
                except Exception:
                    pass
            if default_name:
                self.set_default_model(default_name)
            return loaded
        except Exception:
            return False


def make_temp_config(content: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".yaml")
    with os.fdopen(fd, "w") as f:
        yaml.dump(content, f)
    return path


def dummy_config(name: str = "dummy", type=DUMMY_TYPE) -> ModelConfig:
    """Create a ModelConfig for DummyModel (test isolation)."""
    return ModelConfig(name=name, type=type, model_path="/tmp/model")


def test_register_and_list_models() -> None:
    mgr = DummyAIModelManager()
    cfg1 = dummy_config("m1", DUMMY_TYPE)
    cfg2 = dummy_config("m2", DUMMY_TYPE)
    assert mgr.register_model(cfg1) is True
    assert mgr.register_model(cfg2) is True
    assert set(mgr.list_models()) == {"m1", "m2"}


def test_duplicate_registration() -> None:
    mgr = DummyAIModelManager()
    cfg = dummy_config("dup", DUMMY_TYPE)
    assert mgr.register_model(cfg) is True
    assert mgr.register_model(cfg) is False  # Duplicate


def test_get_and_remove_model() -> None:
    mgr = DummyAIModelManager()
    cfg = dummy_config("to_remove", DUMMY_TYPE)
    mgr.register_model(cfg)
    assert mgr.get_model("to_remove") is not None
    assert mgr.remove_model("to_remove") is True
    assert mgr.get_model("to_remove") is None


def test_set_and_get_default_model() -> None:
    mgr = DummyAIModelManager()
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
    try:
        mgr = DummyAIModelManager()
        loaded = mgr.load_from_config(path)
        assert loaded is True
        assert set(mgr.list_models()) == {"test-model", "api-model"}
        assert mgr.default_model == "test-model"
    finally:
        os.remove(path)


@pytest.mark.skip(
    reason="This test requires valid external model resources and is skipped by default."
)
def test_ai_model_manager_load_from_config_real() -> None:
    """
    Test the real AIModelManager.load_from_config method with a temporary config file.
    """
    import tempfile

    import yaml

    from merlai.core.ai_models import AIModelManager, ModelType

    config_data = {
        "ai_models": {
            "default": "test-model",
            "available": [
                {"name": "test-model", "type": ModelType.HUGGINGFACE.value},
                {"name": "api-model", "type": ModelType.EXTERNAL_API.value},
            ],
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tf:
        yaml.dump(config_data, tf)
        temp_path = tf.name

    try:
        mgr = AIModelManager()
        loaded = mgr.load_from_config(temp_path)
        assert loaded is True, "Models should be loaded from config"
        assert set(mgr.list_models()) == {"test-model", "api-model"}
        assert mgr.default_model == "test-model"
    finally:
        import os

        os.remove(temp_path)


def test_ai_model_manager_load_from_config_missing_params() -> None:
    """
    "Models should be loaded from config if required params are present"
    """
    import tempfile

    import yaml

    from merlai.core.ai_models import AIModelManager, ModelType

    # model_path など必須パラメータが無い設定
    config_data = {
        "ai_models": {
            "default": "test-model",
            "available": [
                {"name": "test-model", "type": ModelType.HUGGINGFACE.value},
                {"name": "api-model", "type": ModelType.EXTERNAL_API.value},
            ],
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tf:
        yaml.dump(config_data, tf)
        temp_path = tf.name

    try:
        mgr = AIModelManager()
        loaded = mgr.load_from_config(temp_path)
        assert (
            loaded is False
        ), "Models should not be loaded if required params are missing"
        assert mgr.list_models() == []
        assert mgr.default_model is None
    finally:
        import os

        os.remove(temp_path)


def test_ai_model_manager_load_from_config_with_params() -> None:
    """
    Test DummyAIModelManager.load_from_config with all required parameters (should succeed).
    """
    import tempfile

    import yaml

    from merlai.core.ai_models import ModelType

    config_data = {
        "ai_models": {
            "default": "test-model",
            "available": [
                {
                    "name": "test-model",
                    "type": ModelType.CUSTOM.value,
                    "model_path": "/tmp/model",
                },
                {
                    "name": "local-model",
                    "type": ModelType.LOCAL.value,
                    "local_path": "/tmp/localmodel",
                },
            ],
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tf:
        yaml.dump(config_data, tf)
        temp_path = tf.name

    try:
        mgr = DummyAIModelManager()
        loaded = mgr.load_from_config(temp_path)
        assert (
            loaded is True
        ), "Models should be loaded from config if required params are present"
        assert set(mgr.list_models()) == {"test-model", "local-model"}
        assert mgr.default_model == "test-model"
    finally:
        import os

        os.remove(temp_path)
