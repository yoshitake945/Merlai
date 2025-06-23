"""
AI model integration for Merlai.

This module provides a unified interface for different AI models,
including Hugging Face models, external APIs, and custom implementations.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, cast

import requests

from .types import Bass, Chord, Drums, Harmony, Melody, Note

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Types of AI models supported by Merlai."""

    HUGGINGFACE = "huggingface"
    EXTERNAL_API = "external_api"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class ModelConfig:
    """Configuration for an AI model."""

    name: str
    type: ModelType
    model_path: Optional[str] = None
    local_path: Optional[str] = None
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationRequest:
    """Request for music generation."""

    melody: Melody
    style: str
    key: str
    tempo: int
    generation_type: str  # "harmony", "bass", "drums", "analysis"
    max_length: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResponse:
    """Response from music generation."""

    success: bool
    result: Optional[Union[Harmony, Bass, Drums, Dict[str, Any]]] = None
    error_message: Optional[str] = None
    model_name: Optional[str] = None
    generation_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIModelInterface(ABC):
    """Abstract interface for AI models."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.model_name = config.name

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model is available for use."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        pass

    @abstractmethod
    def generate_harmony(self, request: GenerationRequest) -> GenerationResponse:
        """Generate harmony from melody."""
        pass

    @abstractmethod
    def generate_bass(self, request: GenerationRequest) -> GenerationResponse:
        """Generate bass line from melody and harmony."""
        pass

    @abstractmethod
    def generate_drums(self, request: GenerationRequest) -> GenerationResponse:
        """Generate drum patterns from melody and style."""
        pass

    @abstractmethod
    def analyze_music(self, midi_data: bytes) -> GenerationResponse:
        """Analyze music and extract features."""
        pass

    def unload_model(self) -> None:
        pass


class HuggingFaceModel(AIModelInterface):
    """Hugging Face model implementation."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.tokenizer: Any = None
        self.model: Any = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the Hugging Face model."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            model_path = self.config.local_path or self.config.model_path
            if not model_path:
                raise ValueError("Model path not specified")

            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForCausalLM.from_pretrained(model_path)

            if self.model is not None:
                self.model.eval()

            logger.info(f"Loaded HuggingFace model: {self.config.name}")
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model: {e}")
            self.tokenizer = None
            self.model = None

    def is_available(self) -> bool:
        """Check if the model is available."""
        return self.tokenizer is not None and self.model is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "name": self.config.name,
            "type": self.config.type.value,
            "model_path": self.config.model_path,
            "available": self.is_available(),
            "parameters": self.config.parameters,
        }

    def _safe_generate(
        self, func: Any, *args: Any, **kwargs: Any
    ) -> GenerationResponse:
        """
        Common safe generation wrapper. Returns GenerationResponse(success=False) on exceptions.
        Args:
            func: Actual generation function
            *args, **kwargs: Arguments for the generation function
        Returns:
            GenerationResponse: Generation result or error information
        """
        start_time = time.time()
        if not self.is_available():
            return GenerationResponse(
                success=False,
                error_message="Model not available",
                model_name=self.model_name,
                generation_time=time.time() - start_time,
                metadata={"method": "placeholder"},
            )
        try:
            result = func(*args, **kwargs)
            return GenerationResponse(
                success=True,
                result=result,
                model_name=self.model_name,
                generation_time=time.time() - start_time,
                metadata={"method": "placeholder"},
            )
        except Exception as e:
            logger.error(f"Error in {getattr(func, '__name__', str(func))}: {e}")
            return GenerationResponse(
                success=False,
                error_message=str(e),
                model_name=self.model_name,
                generation_time=time.time() - start_time,
                metadata={"method": "placeholder"},
            )

    def generate_harmony(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate harmony using Hugging Face model.
        Args:
            request (GenerationRequest): Generation request
        Returns:
            GenerationResponse: Generation result
        """

        def _generate() -> Any:
            # Temporary implementation (should be replaced with actual model inference)
            chords = [
                Chord(
                    root=note.pitch,
                    chord_type="major",
                    duration=note.duration,
                    start_time=note.start_time,
                )
                for note in request.melody.notes
            ]
            return Harmony(chords=chords, style=request.style, key=request.key)

        return self._safe_generate(_generate)

    def generate_bass(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate bass line using Hugging Face model.
        Args:
            request (GenerationRequest): Generation request
        Returns:
            GenerationResponse: Generation result
        """

        def _generate() -> Any:
            # Temporary implementation (should be replaced with actual model inference)
            bass_notes = [
                Note(
                    pitch=request.melody.notes[0].pitch - 12,
                    velocity=80,
                    duration=1.0,
                    start_time=0.0,
                )
            ]
            return Bass(notes=bass_notes)

        return self._safe_generate(_generate)

    def generate_drums(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate drum patterns using Hugging Face model.
        Args:
            request (GenerationRequest): Generation request
        Returns:
            GenerationResponse: Generation result
        """

        def _generate() -> Any:
            # Temporary implementation (should be replaced with actual model inference)
            drum_notes = [
                Note(pitch=36, velocity=100, duration=0.5, start_time=0.0),
                Note(pitch=38, velocity=80, duration=0.5, start_time=0.5),
            ]
            return Drums(notes=drum_notes)

        return self._safe_generate(_generate)

    def analyze_music(self, midi_data: bytes) -> GenerationResponse:
        """
        Analyze music using Hugging Face model.
        Args:
            midi_data (bytes): MIDI data
        Returns:
            GenerationResponse: Analysis result
        """

        def _generate() -> Any:
            # Temporary implementation (should be replaced with actual model inference)
            return {
                "key": "C",
                "tempo": 120,
                "style": "pop",
                "complexity": "medium",
            }

        return self._safe_generate(_generate)

    def unload_model(self) -> None:
        pass


class ExternalAPIModel(AIModelInterface):
    """External API model implementation."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.session = requests.Session()
        if self.config.api_key:
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                }
            )

    def is_available(self) -> bool:
        """Check if the API is available."""
        if not self.config.endpoint:
            return False
        try:
            response = self.session.get(self.config.endpoint + "/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "name": self.config.name,
            "type": self.config.type.value,
            "endpoint": self.config.endpoint,
            "available": self.is_available(),
            "parameters": self.config.parameters,
        }

    def _safe_generate(
        self, func: Any, *args: Any, **kwargs: Any
    ) -> GenerationResponse:
        """
        Common safe generation wrapper. Returns GenerationResponse(success=False) on exceptions.
        Args:
            func: Actual generation function
            *args, **kwargs: Arguments for the generation function
        Returns:
            GenerationResponse: Generation result or error information
        """
        start_time = time.time()
        if not self.config.endpoint:
            msg = "API endpoint not configured"
            return self._error_response(msg)
        try:
            result = func(*args, **kwargs)
            return GenerationResponse(
                success=True,
                result=result,
                model_name=self.model_name,
                generation_time=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"Error in {getattr(func, '__name__', str(func))}: {e}")
            return GenerationResponse(
                success=False,
                error_message=str(e),
                model_name=self.model_name,
                generation_time=time.time() - start_time,
            )

    def generate_harmony(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate harmony using external API.
        Args:
            request (GenerationRequest): Generation request
        Returns:
            GenerationResponse: Generation result
        """

        def _generate() -> Any:
            # API call example (mockable for testing exceptions)
            if not self.config.endpoint:
                raise Exception("API endpoint not configured")
            # Actual API call (GET here, but can be changed to POST etc.)
            response = self.session.get(self.config.endpoint + "/harmony", timeout=5)
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code}")
            # Temporary return value (should be generated from response.json() etc.)
            chords = [
                Chord(
                    root=note.pitch,
                    chord_type="major",
                    duration=note.duration,
                    start_time=note.start_time,
                )
                for note in request.melody.notes
            ]
            return Harmony(chords=chords, style=request.style, key=request.key)

        return self._safe_generate(_generate)

    def generate_bass(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate bass using external API.
        Args:
            request (GenerationRequest): Generation request
        Returns:
            GenerationResponse: Generation result
        """

        def _generate() -> Any:
            bass_notes = [
                Note(
                    pitch=request.melody.notes[0].pitch - 12,
                    velocity=80,
                    duration=1.0,
                    start_time=0.0,
                )
            ]
            return Bass(notes=bass_notes)

        return self._safe_generate(_generate)

    def generate_drums(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate drums using external API.
        Args:
            request (GenerationRequest): Generation request
        Returns:
            GenerationResponse: Generation result
        """

        def _generate() -> Any:
            drum_notes = [
                Note(pitch=36, velocity=100, duration=0.5, start_time=0.0),
                Note(pitch=38, velocity=80, duration=0.5, start_time=0.5),
            ]
            return Drums(notes=drum_notes)

        return self._safe_generate(_generate)

    def analyze_music(self, midi_data: bytes) -> GenerationResponse:
        """
        Analyze music using external API.
        Args:
            midi_data (bytes): MIDI data
        Returns:
            GenerationResponse: Analysis result
        """

        def _generate() -> Any:
            return {
                "key": "C",
                "tempo": 120,
                "style": "pop",
                "complexity": "medium",
            }

        return self._safe_generate(_generate)

    def unload_model(self) -> None:
        pass

    @staticmethod
    def _error_response(msg: str) -> GenerationResponse:
        return GenerationResponse(success=False, error_message=msg)


class AIModelManager:
    """Manager for AI models."""

    def __init__(self) -> None:
        self.models: Dict[str, AIModelInterface] = {}
        self.default_model: Optional[str] = None

    def register_model(self, config: ModelConfig) -> bool:
        """
        Register a new AI model.
        Args:
            config (ModelConfig): Model configuration
        Returns:
            bool: Registration success if True
        """
        try:
            if config.name in self.models:
                logger.warning(f"Model {config.name} already registered")
                return False

            model: AIModelInterface
            if config.type == ModelType.HUGGINGFACE:
                model = HuggingFaceModel(config)
            elif config.type == ModelType.EXTERNAL_API:
                model = ExternalAPIModel(config)
            else:
                logger.error(f"Unsupported model type: {config.type}")
                return False

            self.models[config.name] = model
            logger.info(f"Registered model: {config.name} ({config.type})")
            return True

        except Exception as e:
            logger.error(f"Failed to register model {config.name}: {e}")
            return False

    def remove_model(self, name: str) -> bool:
        """
        Remove a registered model by name.
        Args:
            name (str): Model name
        Returns:
            bool: Removal success if True
        """
        if name in self.models:
            del self.models[name]
            if self.default_model == name:
                self.default_model = None
            logger.info(f"Removed model: {name}")
            return True
        return False

    def get_model(self, name: str) -> Optional[AIModelInterface]:
        """
        Get a registered model by name.
        Args:
            name (str): Model name
        Returns:
            Optional[AIModelInterface]: Model instance or None
        """
        return self.models.get(name)

    def list_models(self) -> List[str]:
        """
        List all registered model names.
        Returns:
            List[str]: Model name list
        """
        return list(self.models.keys())

    def set_default_model(self, name: str) -> bool:
        """
        Set the default model.
        Args:
            name (str): Model name
        Returns:
            bool: Setting success if True
        """
        if name in self.models:
            self.default_model = name
            logger.info(f"Set default model: {name}")
            return True
        logger.warning(f"Cannot set default model: {name} not found")
        return False

    def _safe_call(
        self,
        method_name: str,
        model_name: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> GenerationResponse:
        """
        Common safe model call wrapper.
        Args:
            method_name (str): Method to call
            model_name (Optional[str]): Model name
            *args, **kwargs: Arguments for the method
        Returns:
            GenerationResponse: Generation result or error information
        """
        name = model_name or self.default_model
        if not name:
            return GenerationResponse(
                success=False,
                error_message="No model specified and no default model set",
                model_name="",
                generation_time=0.0,
            )

        model = self.get_model(name)
        if not model:
            return GenerationResponse(
                success=False,
                error_message=f"Model not found: {name}",
                model_name=name,
                generation_time=0.0,
            )

        try:
            method = getattr(model, method_name)
            return cast(GenerationResponse, method(*args, **kwargs))
        except Exception as e:
            logger.error(f"Error calling {method_name} on model {name}: {e}")
            return GenerationResponse(
                success=False,
                error_message=str(e),
                model_name=name,
                generation_time=0.0,
            )

    def generate_harmony(
        self,
        model_name: Optional[str] = None,
        request: Optional[GenerationRequest] = None,
    ) -> GenerationResponse:
        """
        Generate harmony using specified or default model.
        Args:
            model_name (Optional[str]): Model name
            request (Optional[GenerationRequest]): Generation request
        Returns:
            GenerationResponse: Generation result
        """
        if request is None:
            return GenerationResponse(
                success=False,
                error_message="No generation request provided",
                model_name=model_name or "",
                generation_time=0.0,
            )
        return self._safe_call("generate_harmony", model_name, request)

    def generate_bass(
        self,
        model_name: Optional[str] = None,
        request: Optional[GenerationRequest] = None,
    ) -> GenerationResponse:
        """
        Generate bass using specified or default model.
        Args:
            model_name (Optional[str]): Model name
            request (Optional[GenerationRequest]): Generation request
        Returns:
            GenerationResponse: Generation result
        """
        if request is None:
            return GenerationResponse(
                success=False,
                error_message="No generation request provided",
                model_name=model_name or "",
                generation_time=0.0,
            )
        return self._safe_call("generate_bass", model_name, request)

    def generate_drums(
        self,
        model_name: Optional[str] = None,
        request: Optional[GenerationRequest] = None,
    ) -> GenerationResponse:
        """
        Generate drums using specified or default model.
        Args:
            model_name (Optional[str]): Model name
            request (Optional[GenerationRequest]): Generation request
        Returns:
            GenerationResponse: Generation result
        """
        if request is None:
            return GenerationResponse(
                success=False,
                error_message="No generation request provided",
                model_name=model_name or "",
                generation_time=0.0,
            )
        return self._safe_call("generate_drums", model_name, request)

    def analyze_music(
        self, model_name: Optional[str] = None, midi_data: Optional[bytes] = None
    ) -> GenerationResponse:
        """
        Analyze music using specified or default model.
        Args:
            model_name (Optional[str]): Model name
            midi_data (Optional[bytes]): MIDI data
        Returns:
            GenerationResponse: Analysis result
        """
        if midi_data is None:
            return GenerationResponse(
                success=False,
                error_message="No MIDI data provided",
                model_name=model_name or "",
                generation_time=0.0,
            )
        return self._safe_call("analyze_music", model_name, midi_data)

    @staticmethod
    def _error_response(msg: str) -> GenerationResponse:
        return GenerationResponse(success=False, error_message=msg)

    def get_model_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a registered model.
        Args:
            name (str): Model name
        Returns:
            Optional[Dict[str, Any]]: Model information or None
        """
        model = self.get_model(name)
        if not model:
            return None

        return {
            "name": name,
            "type": model.config.type.value,
            "available": model.is_available(),
            "config": {
                "model_path": model.config.model_path,
                "local_path": model.config.local_path,
                "endpoint": model.config.endpoint,
            },
        }
