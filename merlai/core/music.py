"""
Music generation core functionality.
"""

from dataclasses import dataclass
from typing import List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .types import Chord, Harmony, Melody, Note, Bass, Drums
from .ai_models import AIModelManager, ModelConfig, ModelType, GenerationRequest


@dataclass
class GenerationConfig:
    """Configuration for music generation."""

    temperature: float = 0.8
    max_length: int = 1024
    batch_size: int = 4
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1


class MusicGenerator:
    """AI-powered music generation system."""

    def __init__(self, model_path: Optional[str] = None, use_ai_models: bool = True) -> None:
        """Initialize the music generator."""
        self.model_path = model_path or "microsoft/DialoGPT-medium"
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.config = GenerationConfig()
        
        # AI model integration
        self.use_ai_models = use_ai_models
        self.ai_model_manager = AIModelManager() if use_ai_models else None
        
        # Initialize default AI models if enabled
        if self.use_ai_models:
            self._initialize_default_models()

    def _initialize_default_models(self) -> None:
        """Initialize default AI models."""
        try:
            # Register a default HuggingFace model
            hf_config = ModelConfig(
                name="default-hf",
                type=ModelType.HUGGINGFACE,
                model_path=self.model_path
            )
            self.ai_model_manager.register_model(hf_config)
            self.ai_model_manager.set_default_model("default-hf")
        except Exception as e:
            # Fallback to legacy mode if AI models fail to initialize
            self.use_ai_models = False
            print(f"Warning: Failed to initialize AI models, falling back to legacy mode: {e}")

    def load_model(self) -> None:
        """Load the AI model for music generation."""
        if self.use_ai_models and self.ai_model_manager:
            # AI models are handled by AIModelManager
            return
        
        # Legacy model loading
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
            if self.model is not None:
                self.model.to(self.device)  # type: ignore
                self.model.eval()  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def generate_harmony(self, melody: Melody, style: str = "pop", model_name: Optional[str] = None) -> Harmony:
        """Generate harmony based on the main melody."""
        if self.use_ai_models and self.ai_model_manager:
            # Use AI model manager
            request = GenerationRequest(
                melody=melody,
                style=style,
                key=melody.key,
                tempo=melody.tempo,
                generation_type="harmony",
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                max_length=self.config.max_length
            )
            
            try:
                response = self.ai_model_manager.generate_harmony(model_name, request)
                
                if response.success and response.result:
                    return response.result
                else:
                    # Fallback to legacy method if AI model fails
                    print(f"Warning: AI model failed, using legacy method: {response.error_message}")
                    return self._generate_harmony_legacy(melody, style)
            except Exception as e:
                # Fallback to legacy method on any exception
                print(f"Warning: AI model exception, using legacy method: {e}")
                return self._generate_harmony_legacy(melody, style)
        
        # Legacy method
        return self._generate_harmony_legacy(melody, style)

    def _generate_harmony_legacy(self, melody: Melody, style: str) -> Harmony:
        """Legacy harmony generation method."""
        try:
            if self.model is None or self.tokenizer is None:
                self.load_model()
                if self.model is None or self.tokenizer is None:
                    # Fallback to basic harmony generation without AI
                    return self._generate_basic_harmony(melody, style)

            # Convert melody to token sequence
            melody_tokens = self._melody_to_tokens(melody)

            # Generate harmony tokens
            with torch.no_grad():
                if self.tokenizer is None or self.model is None:
                    return self._generate_basic_harmony(melody, style)
                    
                inputs = self.tokenizer.encode(melody_tokens, return_tensors="pt").to(  # type: ignore
                    self.device
                )

                outputs = self.model.generate(  # type: ignore
                    inputs,
                    max_length=self.config.max_length,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    top_k=self.config.top_k,
                    repetition_penalty=self.config.repetition_penalty,
                    pad_token_id=self.tokenizer.eos_token_id,  # type: ignore
                    do_sample=True,
                )

            # Decode and convert to harmony
            if self.tokenizer is None:
                return self._generate_basic_harmony(melody, style)
            harmony_tokens = self.tokenizer.decode(outputs[0], skip_special_tokens=True)  # type: ignore
            return self._tokens_to_harmony(harmony_tokens, style)
            
        except Exception as e:
            # Fallback to basic harmony generation on any error
            print(f"Warning: AI model failed, using basic harmony generation: {e}")
            return self._generate_basic_harmony(melody, style)

    def _generate_basic_harmony(self, melody: Melody, style: str) -> Harmony:
        """Generate basic harmony without AI models."""
        chords = []
        for i, note in enumerate(melody.notes):
            # Generate simple chord based on note
            root = note.pitch
            chord = Chord(
                root=root,
                chord_type="major",
                duration=note.duration,
                start_time=note.start_time,
            )
            chords.append(chord)
        
        return Harmony(
            chords=chords,
            style=style,
            key=melody.key
        )

    def generate_bass_line(self, melody: Melody, harmony: Harmony, model_name: Optional[str] = None) -> Bass:
        """Generate bass line based on melody and harmony."""
        if self.use_ai_models and self.ai_model_manager:
            # Use AI model manager
            request = GenerationRequest(
                melody=melody,
                style=harmony.style,
                key=harmony.key,
                tempo=melody.tempo,
                generation_type="bass",
                temperature=self.config.temperature,
                top_p=self.config.top_p
            )
            
            response = self.ai_model_manager.generate_bass(model_name, request)
            
            if response.success and response.result:
                return response.result
            else:
                # Fallback to legacy method if AI model fails
                print(f"Warning: AI model failed, using legacy method: {response.error_message}")
                return self._generate_bass_line_legacy(melody, harmony)
        
        # Legacy method
        return self._generate_bass_line_legacy(melody, harmony)

    def _generate_bass_line_legacy(self, melody: Melody, harmony: Harmony) -> Bass:
        """Legacy bass line generation method."""
        # Implementation for bass line generation
        bass_notes = []
        for chord in harmony.chords:
            # Generate bass note based on chord root
            root_note = chord.root
            bass_note = Note(
                pitch=root_note - 12,  # One octave lower
                velocity=64,
                duration=chord.duration,
                start_time=chord.start_time,
            )
            bass_notes.append(bass_note)

        return Bass(notes=bass_notes)

    def generate_drums(self, melody: Melody, tempo: int = 120, model_name: Optional[str] = None) -> Drums:
        """Generate drum pattern based on melody and tempo."""
        if self.use_ai_models and self.ai_model_manager:
            # Use AI model manager
            request = GenerationRequest(
                melody=melody,
                style="pop",  # Default style for drums
                key=melody.key,
                tempo=tempo,
                generation_type="drums",
                temperature=self.config.temperature,
                top_p=self.config.top_p
            )
            
            response = self.ai_model_manager.generate_drums(model_name, request)
            
            if response.success and response.result:
                return response.result
            else:
                # Fallback to legacy method if AI model fails
                print(f"Warning: AI model failed, using legacy method: {response.error_message}")
                return self._generate_drums_legacy(melody, tempo)
        
        # Legacy method
        return self._generate_drums_legacy(melody, tempo)

    def _generate_drums_legacy(self, melody: Melody, tempo: int) -> Drums:
        """Legacy drum pattern generation method."""
        # Implementation for drum pattern generation
        drum_notes = []
        beats_per_bar = 4
        beat_duration = 60.0 / tempo

        for bar in range(len(melody.notes) // 4):
            # Kick drum on beats 1 and 3
            kick_1 = Note(
                pitch=36,
                velocity=80,
                duration=0.25,
                start_time=bar * beats_per_bar * beat_duration,
            )
            kick_3 = Note(
                pitch=36,
                velocity=80,
                duration=0.25,
                start_time=(bar * beats_per_bar + 2) * beat_duration,
            )

            # Snare on beats 2 and 4
            snare_2 = Note(
                pitch=38,
                velocity=70,
                duration=0.25,
                start_time=(bar * beats_per_bar + 1) * beat_duration,
            )
            snare_4 = Note(
                pitch=38,
                velocity=70,
                duration=0.25,
                start_time=(bar * beats_per_bar + 3) * beat_duration,
            )

            # Hi-hat on every beat
            for beat in range(4):
                hihat = Note(
                    pitch=42,
                    velocity=50,
                    duration=0.125,
                    start_time=(bar * beats_per_bar + beat) * beat_duration,
                )
                drum_notes.append(hihat)

            drum_notes.extend([kick_1, kick_3, snare_2, snare_4])

        return Drums(notes=drum_notes)

    def register_ai_model(self, config: ModelConfig) -> bool:
        """Register a new AI model."""
        if not self.use_ai_models or not self.ai_model_manager:
            return False
        
        return self.ai_model_manager.register_model(config)

    def set_default_ai_model(self, model_name: str) -> bool:
        """Set the default AI model."""
        if not self.use_ai_models or not self.ai_model_manager:
            return False
        
        return self.ai_model_manager.set_default_model(model_name)

    def list_ai_models(self) -> List[str]:
        """List available AI models."""
        if not self.use_ai_models or not self.ai_model_manager:
            return []
        
        return self.ai_model_manager.list_models()

    def _melody_to_tokens(self, melody: Melody) -> str:
        """Convert melody to token sequence for the model."""
        tokens = []
        for note in melody.notes:
            tokens.append(f"NOTE_{note.pitch}_{note.duration}_{note.velocity}")
        return " ".join(tokens)

    def _tokens_to_harmony(self, tokens: str, style: str) -> Harmony:
        """Convert model output tokens to harmony."""
        # Parse tokens and create harmony
        chords = []
        token_list = tokens.split()

        for i in range(0, len(token_list), 3):
            if i + 2 < len(token_list):
                try:
                    root = int(token_list[i].split("_")[1])
                    duration = float(token_list[i + 1].split("_")[1])
                    start_time = float(token_list[i + 2].split("_")[1])

                    chord = Chord(
                        root=root,
                        chord_type="major",  # Default, could be enhanced
                        duration=duration,
                        start_time=start_time,
                    )
                    chords.append(chord)
                except (ValueError, IndexError):
                    continue

        return Harmony(chords=chords, style=style)
