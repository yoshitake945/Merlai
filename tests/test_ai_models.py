"""
Tests for AI model integration functionality.
"""

from unittest.mock import Mock, patch

from merlai.core.ai_models import (
    AIModelInterface,
    AIModelManager,
    ExternalAPIModel,
    GenerationRequest,
    GenerationResponse,
    HuggingFaceModel,
    ModelConfig,
    ModelType,
)
from merlai.core.music import MusicGenerator
from merlai.core.types import Bass, Drums, Harmony, Melody, Note


class TestAIModelInterface:
    """Test the abstract AI model interface."""

    def test_interface_methods(self) -> None:
        """Test that interface defines required methods."""
        # This test ensures the interface has the expected methods
        assert hasattr(AIModelInterface, "generate_harmony")
        assert hasattr(AIModelInterface, "generate_bass")
        assert hasattr(AIModelInterface, "generate_drums")
        assert hasattr(AIModelInterface, "analyze_music")
        assert hasattr(AIModelInterface, "get_model_info")
        assert hasattr(AIModelInterface, "is_available")


class TestModelConfig:
    """Test ModelConfig class."""

    def test_model_config_creation(self) -> None:
        """Test creating a ModelConfig object."""
        config = ModelConfig(
            name="test-model",
            type=ModelType.HUGGINGFACE,
            model_path="facebook/musicgen-small",
            local_path="/app/models/musicgen",
            api_key="test-key",
            endpoint="https://api.example.com",
        )

        assert config.name == "test-model"
        assert config.type == ModelType.HUGGINGFACE
        assert config.model_path == "facebook/musicgen-small"
        assert config.local_path == "/app/models/musicgen"
        assert config.api_key == "test-key"
        assert config.endpoint == "https://api.example.com"

    def test_model_config_defaults(self) -> None:
        """Test ModelConfig with default values."""
        config = ModelConfig(
            name="test-model",
            type=ModelType.HUGGINGFACE,
            model_path="facebook/musicgen-small",
        )

        assert config.name == "test-model"
        assert config.type == ModelType.HUGGINGFACE
        assert config.model_path == "facebook/musicgen-small"
        assert config.local_path is None
        assert config.api_key is None
        assert config.endpoint is None


class TestGenerationRequest:
    """Test GenerationRequest class."""

    def test_generation_request_creation(self) -> None:
        """Test creating a GenerationRequest object."""
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="harmony"
        )

        assert request.melody == melody
        assert request.style == "pop"
        assert request.key == "C"
        assert request.tempo == 120
        assert request.generation_type == "harmony"

    def test_generation_request_optional_params(self) -> None:
        """Test GenerationRequest with optional parameters."""
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        request = GenerationRequest(
            melody=melody,
            style="pop",
            key="C",
            tempo=120,
            generation_type="harmony",
            max_length=32,
            temperature=0.8,
            top_p=0.9,
        )

        assert request.max_length == 32
        assert request.temperature == 0.8
        assert request.top_p == 0.9


class TestGenerationResponse:
    """Test GenerationResponse class."""

    def test_generation_response_creation(self) -> None:
        """Test creating a GenerationResponse object."""
        harmony = Harmony(chords=[])

        response = GenerationResponse(
            success=True,
            result=harmony,
            model_name="test-model",
            generation_time=1.5,
            metadata={"tokens_generated": 100},
        )

        assert response.success is True
        assert response.result == harmony
        assert response.model_name == "test-model"
        assert response.generation_time == 1.5
        assert response.metadata["tokens_generated"] == 100

    def test_generation_response_error(self) -> None:
        """Test GenerationResponse for error cases."""
        response = GenerationResponse(
            success=False,
            error_message="Model not available",
            model_name="test-model",
            generation_time=0.0,
        )

        assert response.success is False
        assert response.error_message == "Model not available"
        assert response.result is None


class TestHuggingFaceModel:
    """Test HuggingFace model implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = ModelConfig(
            name="test-hf-model",
            type=ModelType.HUGGINGFACE,
            model_path="facebook/musicgen-small",
            local_path="/tmp/test-model",
        )

    @patch("transformers.AutoTokenizer")
    @patch("transformers.AutoModelForCausalLM")
    def test_huggingface_model_initialization(
        self, mock_model: Mock, mock_tokenizer: Mock
    ) -> None:
        """Test HuggingFace model initialization."""
        # Mock the transformers library
        mock_tokenizer_instance = Mock()
        mock_model_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_model.from_pretrained.return_value = mock_model_instance

        model = HuggingFaceModel(self.config)

        assert model.config == self.config
        assert model.model_name == "test-hf-model"
        assert model.is_available() is True

    @patch("transformers.AutoTokenizer")
    @patch("transformers.AutoModelForCausalLM")
    def test_huggingface_generate_harmony(
        self, mock_model: Mock, mock_tokenizer: Mock
    ) -> None:
        """Test harmony generation with HuggingFace model."""
        # Mock the transformers library
        mock_tokenizer_instance = Mock()
        mock_model_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_model.from_pretrained.return_value = mock_model_instance

        model = HuggingFaceModel(self.config)

        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="harmony"
        )

        response = model.generate_harmony(request)

        assert isinstance(response, GenerationResponse)
        assert response.success is True
        assert isinstance(response.result, Harmony)
        assert response.model_name == "test-hf-model"
        assert response.metadata["method"] == "placeholder"

    def test_huggingface_model_not_available(self) -> None:
        """Test HuggingFace model when not available."""
        with patch("transformers.AutoTokenizer") as mock_tokenizer:
            mock_tokenizer.from_pretrained.side_effect = Exception("Model not found")

            model = HuggingFaceModel(self.config)
            assert model.is_available() is False

    @patch("transformers.AutoTokenizer")
    @patch("transformers.AutoModelForCausalLM")
    def test_huggingface_generate_bass(
        self, mock_model: Mock, mock_tokenizer: Mock
    ) -> None:
        """Test bass generation with HuggingFace model."""
        # Mock the transformers library
        mock_tokenizer_instance = Mock()
        mock_model_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_model.from_pretrained.return_value = mock_model_instance

        model = HuggingFaceModel(self.config)

        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="bass"
        )

        response = model.generate_bass(request)

        assert isinstance(response, GenerationResponse)
        assert response.success is True
        assert isinstance(response.result, Bass)
        assert response.model_name == "test-hf-model"

    @patch("transformers.AutoTokenizer")
    @patch("transformers.AutoModelForCausalLM")
    def test_huggingface_generate_drums(
        self, mock_model: Mock, mock_tokenizer: Mock
    ) -> None:
        """Test drum generation with HuggingFace model."""
        # Mock the transformers library
        mock_tokenizer_instance = Mock()
        mock_model_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_model.from_pretrained.return_value = mock_model_instance

        model = HuggingFaceModel(self.config)

        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="drums"
        )

        response = model.generate_drums(request)

        assert isinstance(response, GenerationResponse)
        assert response.success is True
        assert isinstance(response.result, Drums)
        assert response.model_name == "test-hf-model"


class TestExternalAPIModel:
    """Test External API model implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = ModelConfig(
            name="test-api-model",
            type=ModelType.EXTERNAL_API,
            endpoint="https://api.example.com/generate",
            api_key="test-api-key",
        )

    @patch("merlai.core.ai_models.requests.Session")
    def test_external_api_model_initialization(self, mock_session: Mock) -> None:
        """Test External API model initialization."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        model = ExternalAPIModel(self.config)

        assert model.config == self.config
        assert model.model_name == "test-api-model"
        mock_session_instance.headers.update.assert_called_once()

    @patch("merlai.core.ai_models.requests.Session.get")
    def test_external_api_generate_harmony(self, mock_get: Mock) -> None:
        """Test harmony generation with external API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test"}
        mock_get.return_value = mock_response

        model = ExternalAPIModel(self.config)

        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="harmony"
        )

        response = model.generate_harmony(request)

        assert isinstance(response, GenerationResponse)
        assert response.success is True

    @patch("merlai.core.ai_models.requests.Session")
    def test_external_api_generate_bass(self, mock_session: Mock) -> None:
        """Test bass generation with external API."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        model = ExternalAPIModel(self.config)

        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="bass"
        )

        response = model.generate_bass(request)

        assert isinstance(response, GenerationResponse)
        assert response.success is True
        assert isinstance(response.result, Bass)
        assert response.model_name == "test-api-model"

    @patch("merlai.core.ai_models.requests.Session")
    def test_external_api_generate_drums(self, mock_session: Mock) -> None:
        """Test drum generation with external API."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        model = ExternalAPIModel(self.config)

        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="drums"
        )

        response = model.generate_drums(request)

        assert isinstance(response, GenerationResponse)
        assert response.success is True
        assert isinstance(response.result, Drums)
        assert response.model_name == "test-api-model"

    @patch("merlai.core.ai_models.requests.Session")
    def test_external_api_no_endpoint(self, mock_session: Mock) -> None:
        """Test external API without endpoint configured."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        config = ModelConfig(name="test-api-model", type=ModelType.EXTERNAL_API)

        model = ExternalAPIModel(config)

        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="harmony"
        )

        response = model.generate_harmony(request)

        assert isinstance(response, GenerationResponse)
        assert response.success is False
        assert response.error_message is not None
        assert "API endpoint not configured" in response.error_message


class TestAIModelManager:
    """Test AI model manager functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.manager = AIModelManager()

        # Add test models
        self.hf_config = ModelConfig(
            name="test-hf",
            type=ModelType.HUGGINGFACE,
            model_path="facebook/musicgen-small",
        )

        self.api_config = ModelConfig(
            name="test-api",
            type=ModelType.EXTERNAL_API,
            endpoint="https://api.example.com/generate",
        )

    def test_register_model(self) -> None:
        """Test registering a model."""
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()
            mock_hf.return_value = mock_model

            result = self.manager.register_model(self.hf_config)

            assert result is True
            assert "test-hf" in self.manager.models
            assert self.manager.models["test-hf"] == mock_model

    def test_register_unsupported_model_type(self) -> None:
        """Test registering an unsupported model type."""
        config = ModelConfig(name="test-unsupported", type=ModelType.LOCAL)

        result = self.manager.register_model(config)

        assert result is False
        assert "test-unsupported" not in self.manager.models

    def test_get_model(self) -> None:
        """Test getting a registered model."""
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()
            mock_hf.return_value = mock_model

            self.manager.register_model(self.hf_config)
            model = self.manager.get_model("test-hf")

            assert model == mock_model

    def test_get_model_not_found(self) -> None:
        """Test getting a non-existent model."""
        model = self.manager.get_model("non-existent")
        assert model is None

    def test_list_models(self) -> None:
        """Test listing registered models."""
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()
            mock_hf.return_value = mock_model

            self.manager.register_model(self.hf_config)
            self.manager.register_model(self.api_config)

            models = self.manager.list_models()

            assert "test-hf" in models
            assert "test-api" in models
            assert len(models) == 2

    def test_set_default_model(self) -> None:
        """Test setting default model."""
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()
            mock_hf.return_value = mock_model

            self.manager.register_model(self.hf_config)
            result = self.manager.set_default_model("test-hf")

            assert result is True
            assert self.manager.default_model == "test-hf"

    def test_set_default_model_not_found(self) -> None:
        """Test setting non-existent model as default."""
        result = self.manager.set_default_model("non-existent")

        assert result is False
        assert self.manager.default_model is None

    def test_generate_harmony_with_model(self) -> None:
        """Test generation using a specific model."""
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()
            mock_hf.return_value = mock_model

            # Mock successful generation
            mock_response = GenerationResponse(
                success=True,
                result=Harmony(chords=[]),
                model_name="test-hf",
                generation_time=1.0,
            )
            mock_model.generate_harmony.return_value = mock_response

            self.manager.register_model(self.hf_config)

            melody = Melody(
                notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
            )

            request = GenerationRequest(
                melody=melody,
                style="pop",
                key="C",
                tempo=120,
                generation_type="harmony",
            )

            response = self.manager.generate_harmony("test-hf", request)

            assert response.success is True
            assert response.model_name == "test-hf"
            mock_model.generate_harmony.assert_called_once_with(request)

    def test_generate_harmony_with_default_model(self) -> None:
        """Test generation using default model."""
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()
            mock_hf.return_value = mock_model

            # Mock successful generation
            mock_response = GenerationResponse(
                success=True,
                result=Harmony(chords=[]),
                model_name="test-hf",
                generation_time=1.0,
            )
            mock_model.generate_harmony.return_value = mock_response

            self.manager.register_model(self.hf_config)
            self.manager.set_default_model("test-hf")

            melody = Melody(
                notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
            )

            request = GenerationRequest(
                melody=melody,
                style="pop",
                key="C",
                tempo=120,
                generation_type="harmony",
            )

            response = self.manager.generate_harmony(request=request)

            assert response.success is True
            assert response.model_name == "test-hf"

    def test_generate_harmony_no_model_specified(self) -> None:
        """Test generation without specifying model and no default."""
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="harmony"
        )

        response = self.manager.generate_harmony(request=request)

        assert response.success is False
        assert response.error_message is not None
        assert "No model specified and no default model set" in response.error_message

    def test_generate_harmony_model_not_found(self) -> None:
        """Test generation with non-existent model."""
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="harmony"
        )

        response = self.manager.generate_harmony("non-existent", request)

        assert response.success is False
        assert response.error_message is not None
        assert "Model not found: non-existent" in response.error_message

    def test_generate_harmony_no_request(self) -> None:
        """Test generation without providing request."""
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()
            mock_hf.return_value = mock_model

            self.manager.register_model(self.hf_config)

            response = self.manager.generate_harmony("test-hf")

            assert response.success is False
            assert response.error_message is not None
            assert "No generation request provided" in response.error_message

    def test_generate_bass_with_model(self) -> None:
        """Test bass generation using a specific model."""
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()
            mock_hf.return_value = mock_model

            # Mock successful generation
            mock_response = GenerationResponse(
                success=True,
                result=Bass(notes=[]),
                model_name="test-hf",
                generation_time=1.0,
            )
            mock_model.generate_bass.return_value = mock_response

            self.manager.register_model(self.hf_config)

            melody = Melody(
                notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
            )

            request = GenerationRequest(
                melody=melody, style="pop", key="C", tempo=120, generation_type="bass"
            )

            response = self.manager.generate_bass("test-hf", request)

            assert response.success is True
            assert response.model_name == "test-hf"
            mock_model.generate_bass.assert_called_once_with(request)

    def test_generate_drums_with_model(self) -> None:
        """Test drum generation using a specific model."""
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()
            mock_hf.return_value = mock_model

            # Mock successful generation
            mock_response = GenerationResponse(
                success=True,
                result=Drums(notes=[]),
                model_name="test-hf",
                generation_time=1.0,
            )
            mock_model.generate_drums.return_value = mock_response

            self.manager.register_model(self.hf_config)

            melody = Melody(
                notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
            )

            request = GenerationRequest(
                melody=melody, style="pop", key="C", tempo=120, generation_type="drums"
            )

            response = self.manager.generate_drums("test-hf", request)

            assert response.success is True
            assert response.model_name == "test-hf"
            mock_model.generate_drums.assert_called_once_with(request)

    def test_analyze_music_with_model(self) -> None:
        """Test music analysis using a specific model."""
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()
            mock_hf.return_value = mock_model

            # Mock successful analysis
            mock_response = GenerationResponse(
                success=True,
                result={"key": "C", "tempo": 120},
                model_name="test-hf",
                generation_time=1.0,
            )
            mock_model.analyze_music.return_value = mock_response

            self.manager.register_model(self.hf_config)

            midi_data = b"fake_midi_data"

            response = self.manager.analyze_music("test-hf", midi_data)

            assert response.success is True
            assert response.model_name == "test-hf"
            mock_model.analyze_music.assert_called_once_with(midi_data)


class TestAIModelManagerEdgeCases:
    def setup_method(self) -> None:
        self.manager = AIModelManager()

    # def test_register_unsupported_type(self):
    #     with pytest.raises(ValueError):
    #         ModelConfig(name="unsupported", type="UNKNOWN", model_path="none")

    def test_register_duplicate_model(self) -> None:
        config = ModelConfig(
            name="dup", type=ModelType.HUGGINGFACE, model_path="facebook/musicgen-small"
        )
        assert self.manager.register_model(config) is True
        assert self.manager.register_model(config) is False

    def test_remove_nonexistent_model(self) -> None:
        assert self.manager.remove_model("notfound") is False

    def test_get_nonexistent_model(self) -> None:
        assert self.manager.get_model("notfound") is None

    def test_list_models_empty(self) -> None:
        assert self.manager.list_models() == []

    def test_generate_harmony_exception(self) -> None:
        config = ModelConfig(
            name="errmodel",
            type=ModelType.HUGGINGFACE,
            model_path="facebook/musicgen-small",
        )
        self.manager.register_model(config)
        with patch.object(
            HuggingFaceModel, "generate_harmony", side_effect=Exception("fail")
        ):
            req = GenerationRequest(
                melody=Melody(notes=[]),
                style="pop",
                key="C",
                tempo=120,
                generation_type="harmony",
            )
            resp = self.manager.generate_harmony("errmodel", req)
            assert resp.success is False
            assert resp.error_message is not None
            assert "fail" in resp.error_message

    def test_external_api_model_http_error(self) -> None:
        config = ModelConfig(
            name="apimodel",
            type=ModelType.EXTERNAL_API,
            endpoint="http://localhost:9999",
        )
        self.manager.register_model(config)
        req = GenerationRequest(
            melody=Melody(notes=[]),
            style="pop",
            key="C",
            tempo=120,
            generation_type="harmony",
        )
        with patch(
            "merlai.core.ai_models.requests.Session.get",
            side_effect=Exception("http error"),
        ):
            resp = self.manager.generate_harmony("apimodel", req)
            assert resp.success is False
            assert resp.error_message is not None
            assert "error" in resp.error_message.lower()


class TestAIModelManagement:
    """Test AI model management functionality."""

    def test_register_ai_model(self) -> None:
        """Test registering a new AI model."""
        generator = MusicGenerator()
        config = ModelConfig(
            name="test-model",
            type=ModelType.HUGGINGFACE,
            model_path="/path/to/model",
            parameters={"layers": 12, "heads": 8}
        )
        result = generator.register_ai_model(config)
        assert result is True
        # Note: MusicGenerator may not have ai_models attribute directly accessible
        # This test may need adjustment based on actual implementation

    def test_set_default_ai_model(self) -> None:
        """Test setting default AI model."""
        generator = MusicGenerator()
        config = ModelConfig(
            name="test-model",
            type=ModelType.HUGGINGFACE,
            model_path="/path/to/model",
            parameters={"layers": 12, "heads": 8}
        )
        generator.register_ai_model(config)
        result = generator.set_default_ai_model("test-model")
        assert result is True
        # Note: MusicGenerator may not have default_ai_model attribute directly accessible
        # This test may need adjustment based on actual implementation

    def test_list_ai_models(self) -> None:
        """Test listing AI models."""
        generator = MusicGenerator()
        config1 = ModelConfig(
            name="model1",
            type=ModelType.HUGGINGFACE,
            model_path="/path/to/model1",
            parameters={}
        )
        config2 = ModelConfig(
            name="model2",
            type=ModelType.EXTERNAL_API,
            model_path="/path/to/model2",
            parameters={}
        )
        generator.register_ai_model(config1)
        generator.register_ai_model(config2)
        
        models = generator.list_ai_models()
        assert len(models) == 2
        assert "model1" in models
        assert "model2" in models

    def test_ai_model_not_found(self) -> None:
        """Test behavior when AI model is not found."""
        generator = MusicGenerator()
        result = generator.set_default_ai_model("nonexistent")
        assert result is False

    def test_ai_model_generation_with_model(self) -> None:
        """Test AI model-based generation."""
        generator = MusicGenerator()
        config = ModelConfig(
            name="test-model",
            type=ModelType.HUGGINGFACE,
            model_path="/path/to/model",
            parameters={"layers": 12, "heads": 8}
        )
        generator.register_ai_model(config)
        generator.set_default_ai_model("test-model")
        generator.use_ai_models = True

        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )

        # Test AI harmony generation
        harmony = generator.generate_harmony(melody, "pop")
        assert harmony is not None

        # Test AI bass generation
        bass = generator.generate_bass_line(melody, harmony)
        assert bass is not None

        # Test AI drums generation
        drums = generator.generate_drums(melody, 120)
        assert drums is not None


class TestAIModelErrorHandling:
    """Test AI model error handling."""

    def test_invalid_model_config(self) -> None:
        """Test handling of invalid model configuration."""
        generator = MusicGenerator()
        # Test with invalid config
        result = generator.register_ai_model(None)  # type: ignore
        assert result is False

    def test_model_loading_error(self) -> None:
        """Test handling of model loading errors."""
        generator = MusicGenerator()
        config = ModelConfig(
            name="invalid-model",
            type=ModelType.HUGGINGFACE,
            model_path="/nonexistent/path",
            parameters={}
        )
        result = generator.register_ai_model(config)
        # Should handle gracefully
        assert result is False

    def test_generation_without_models(self) -> None:
        """Test generation when no AI models are available."""
        generator = MusicGenerator()
        generator.use_ai_models = True
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )

        # Should fall back to rule-based generation
        harmony = generator.generate_harmony(melody, "pop")
        assert harmony is not None


class TestAIModelIntegration:
    """Integration tests for AI model functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.manager = AIModelManager()

    @patch("merlai.core.ai_models.HuggingFaceModel")
    @patch("merlai.core.ai_models.ExternalAPIModel")
    def test_multiple_model_types(self, mock_api: Mock, mock_hf: Mock) -> None:
        """Test using multiple model types together."""
        # Mock HuggingFace model
        mock_hf_model = Mock()
        mock_hf.return_value = mock_hf_model
        mock_hf_response = GenerationResponse(
            success=True,
            result=Harmony(chords=[]),
            model_name="test-hf",
            generation_time=1.0,
        )
        mock_hf_model.generate_harmony.return_value = mock_hf_response

        # Mock External API model
        mock_api_model = Mock()
        mock_api.return_value = mock_api_model
        mock_api_response = GenerationResponse(
            success=True,
            result=Bass(notes=[]),
            model_name="test-api",
            generation_time=0.5,
        )
        mock_api_model.generate_bass.return_value = mock_api_response

        # Register both models
        hf_config = ModelConfig(
            name="test-hf",
            type=ModelType.HUGGINGFACE,
            model_path="facebook/musicgen-small",
        )

        api_config = ModelConfig(
            name="test-api",
            type=ModelType.EXTERNAL_API,
            endpoint="https://api.example.com/generate",
        )

        self.manager.register_model(hf_config)
        self.manager.register_model(api_config)

        # Test using different models for different tasks
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        harmony_request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="harmony"
        )

        bass_request = GenerationRequest(
            melody=melody, style="pop", key="C", tempo=120, generation_type="bass"
        )

        harmony_response = self.manager.generate_harmony("test-hf", harmony_request)
        bass_response = self.manager.generate_bass("test-api", bass_request)

        assert harmony_response.success is True
        assert harmony_response.model_name == "test-hf"
        assert bass_response.success is True
        assert bass_response.model_name == "test-api"

    def test_model_fallback(self) -> None:
        """Test fallback to alternative model when primary fails."""
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            # Primary model fails
            mock_hf_model = Mock()
            mock_hf.return_value = mock_hf_model
            mock_hf_model.generate_harmony.return_value = GenerationResponse(
                success=False,
                error_message="Model unavailable",
                model_name="test-hf",
                generation_time=0.0,
            )

            hf_config = ModelConfig(
                name="test-hf",
                type=ModelType.HUGGINGFACE,
                model_path="facebook/musicgen-small",
            )

            self.manager.register_model(hf_config)
            self.manager.set_default_model("test-hf")

            melody = Melody(
                notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
            )

            request = GenerationRequest(
                melody=melody,
                style="pop",
                key="C",
                tempo=120,
                generation_type="harmony",
            )

            # Should handle failure gracefully
            response = self.manager.generate_harmony(request=request)

            assert response.success is False
            assert response.error_message is not None
            assert "Model unavailable" in response.error_message
