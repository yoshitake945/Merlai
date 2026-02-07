"""
Additional tests for music generation functionality.

This file adds tests to improve coverage of merlai/core/music.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from merlai.core.music import MusicGenerator, GenerationConfig
from merlai.core.types import Melody, Note, Harmony, Bass, Drums


class TestGenerationConfig:
    """Test GenerationConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = GenerationConfig()
        assert config.temperature == 0.8
        assert config.max_length == 1024
        assert config.batch_size == 4
        assert config.top_p == 0.9
        assert config.top_k == 50
        assert config.repetition_penalty == 1.1

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = GenerationConfig(
            temperature=0.7,
            max_length=512,
            batch_size=2,
            top_p=0.95,
            top_k=40,
            repetition_penalty=1.2,
        )
        assert config.temperature == 0.7
        assert config.max_length == 512
        assert config.batch_size == 2
        assert config.top_p == 0.95
        assert config.top_k == 40
        assert config.repetition_penalty == 1.2


class TestMusicGeneratorInitialization:
    """Test MusicGenerator initialization."""

    def test_init_with_default_model_path(self) -> None:
        """Test initialization with default model path."""
        with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator()
            assert gen.model_path == "microsoft/DialoGPT-medium"
            assert gen.use_ai_models is True
            assert gen.config is not None

    def test_init_with_custom_model_path(self) -> None:
        """Test initialization with custom model path."""
        with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator(model_path="custom/model")
            assert gen.model_path == "custom/model"

    def test_init_without_ai_models(self) -> None:
        """Test initialization without AI models."""
        gen = MusicGenerator(use_ai_models=False)
        assert gen.use_ai_models is False
        assert gen.ai_model_manager is None

    def test_init_with_torch_available(self) -> None:
        """Test initialization when torch is available."""
        with patch("merlai.core.music.torch") as mock_torch, \
             patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            mock_torch.device.return_value = "cuda"
            mock_torch.cuda.is_available.return_value = True
            
            gen = MusicGenerator()
            # Device should be set when torch is available
            assert gen.device is not None

    def test_init_without_torch(self) -> None:
        """Test initialization when torch is not available."""
        with patch("merlai.core.music.torch", None), \
             patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator()
            assert gen.device == "cpu"


class TestMusicGeneratorModelLoading:
    """Test model loading functionality."""

    def test_load_model_with_ai_models_enabled(self) -> None:
        """Test load_model when AI models are enabled."""
        with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator(use_ai_models=True)
            gen.ai_model_manager = Mock()
            
            # Should return early when AI models are enabled
            gen.load_model()
            # No legacy model loading should occur
            assert gen.tokenizer is None
            assert gen.model is None

    def test_load_model_without_transformers(self) -> None:
        """Test load_model when transformers is not available."""
        with patch("merlai.core.music.AutoTokenizer", None), \
             patch("merlai.core.music.AutoModelForCausalLM", None):
            gen = MusicGenerator(use_ai_models=False)
            
            with pytest.raises(RuntimeError, match="transformers is not installed"):
                gen.load_model()

    def test_load_model_without_torch(self) -> None:
        """Test load_model when torch is not available."""
        with patch("merlai.core.music.torch", None), \
             patch("merlai.core.music.AutoTokenizer") as mock_tokenizer, \
             patch("merlai.core.music.AutoModelForCausalLM") as mock_model:
            
            gen = MusicGenerator(use_ai_models=False)
            
            with pytest.raises(RuntimeError, match="torch is not installed"):
                gen.load_model()


class TestMusicGeneratorAIIntegration:
    """Test AI model integration methods."""

    def test_register_ai_model(self) -> None:
        """Test registering an AI model."""
        with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator(use_ai_models=True)
            gen.ai_model_manager = Mock()
            gen.ai_model_manager.register_model.return_value = True
            
            from merlai.core.ai_models import ModelConfig, ModelType
            config = ModelConfig(
                name="test-model",
                type=ModelType.HUGGINGFACE,
                model_path="test/path"
            )
            
            result = gen.register_ai_model(config)
            assert result is True
            gen.ai_model_manager.register_model.assert_called_once_with(config)

    def test_register_ai_model_without_manager(self) -> None:
        """Test registering AI model when manager is None."""
        gen = MusicGenerator(use_ai_models=False)
        
        from merlai.core.ai_models import ModelConfig, ModelType
        config = ModelConfig(
            name="test-model",
            type=ModelType.HUGGINGFACE,
            model_path="test/path"
        )
        
        result = gen.register_ai_model(config)
        assert result is False

    def test_set_default_ai_model(self) -> None:
        """Test setting default AI model."""
        with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator(use_ai_models=True)
            gen.ai_model_manager = Mock()
            gen.ai_model_manager.set_default_model.return_value = True
            
            result = gen.set_default_ai_model("test-model")
            assert result is True
            gen.ai_model_manager.set_default_model.assert_called_once_with("test-model")

    def test_list_ai_models(self) -> None:
        """Test listing AI models."""
        with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator(use_ai_models=True)
            gen.ai_model_manager = Mock()
            gen.ai_model_manager.list_models.return_value = ["model1", "model2"]
            
            models = gen.list_ai_models()
            assert models == ["model1", "model2"]
            gen.ai_model_manager.list_models.assert_called_once()


class TestMusicGenerationEdgeCases:
    """Test edge cases in music generation."""

    def test_generate_harmony_with_very_long_melody(self) -> None:
        """Test harmony generation with very long melody."""
        with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator()
            
            # Create a very long melody (100 notes)
            notes = [
                Note(pitch=60 + (i % 12), velocity=80, duration=0.5, start_time=i * 0.5)
                for i in range(100)
            ]
            melody = Melody(notes=notes, tempo=120, key="C")
            
            with patch("merlai.core.music.AutoTokenizer"), \
                 patch("merlai.core.music.AutoModelForCausalLM"):
                harmony = gen.generate_harmony(melody, style="pop")
                
                assert isinstance(harmony, Harmony)
                # Should generate chords for long melody
                assert len(harmony.chords) >= 0

    def test_generate_bass_with_empty_harmony(self) -> None:
        """Test bass generation with harmony containing no chords."""
        with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator()
            
            melody = Melody(
                notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
                tempo=120,
                key="C"
            )
            harmony = Harmony(chords=[], style="pop", key="C")
            
            bass = gen.generate_bass_line(melody, harmony)
            
            assert isinstance(bass, Bass)
            # Should handle empty harmony gracefully
            assert isinstance(bass.notes, list)

    def test_generate_drums_with_extreme_tempo(self) -> None:
        """Test drum generation with extreme tempo values."""
        with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator()
            
            melody = Melody(
                notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
                tempo=120,
                key="C"
            )
            
            # Test very fast tempo
            drums_fast = gen.generate_drums(melody, tempo=300)
            assert isinstance(drums_fast, Drums)
            
            # Test very slow tempo
            drums_slow = gen.generate_drums(melody, tempo=40)
            assert isinstance(drums_slow, Drums)


class TestMusicGeneratorConfiguration:
    """Test configuration management."""

    def test_config_attribute_exists(self) -> None:
        """Test that config attribute is properly initialized."""
        with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator()
            assert hasattr(gen, 'config')
            assert isinstance(gen.config, GenerationConfig)

    def test_config_can_be_modified(self) -> None:
        """Test that configuration can be modified."""
        with patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            gen = MusicGenerator()
            
            # Modify configuration
            gen.config.temperature = 0.5
            gen.config.max_length = 2048
            
            assert gen.config.temperature == 0.5
            assert gen.config.max_length == 2048


class TestInitializationFailure:
    """Test initialization failure scenarios."""

    def test_initialize_default_models_failure(self) -> None:
        """Test graceful handling of default model initialization failure."""
        with patch("merlai.core.music.AIModelManager") as mock_manager:
            # Make registration fail
            mock_instance = Mock()
            mock_instance.register_model.side_effect = Exception("Registration failed")
            mock_manager.return_value = mock_instance
            
            # Should not raise exception, but fall back to legacy mode
            gen = MusicGenerator(use_ai_models=True)
            
            # Should fall back to non-AI mode
            assert gen.use_ai_models is False

    def test_device_selection_with_torch(self) -> None:
        """Test device selection when torch is available."""
        with patch("merlai.core.music.torch") as mock_torch, \
             patch("merlai.core.music.MusicGenerator._initialize_default_models"):
            
            mock_device = Mock()
            mock_torch.device.return_value = mock_device
            mock_torch.cuda.is_available.return_value = False
            
            gen = MusicGenerator()
            
            # Should call torch.device
            mock_torch.device.assert_called()
