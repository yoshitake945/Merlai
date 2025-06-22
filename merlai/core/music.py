"""
Music generation core functionality.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM
import numpy as np
from pydantic import BaseModel

from .types import Note, Chord, Melody, Harmony


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
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the music generator."""
        self.model_path = model_path or "microsoft/DialoGPT-medium"
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.config = GenerationConfig()
        
    def load_model(self) -> None:
        """Load the AI model for music generation."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    
    def generate_harmony(self, melody: Melody, style: str = "pop") -> Harmony:
        """Generate harmony based on the main melody."""
        if self.model is None:
            self.load_model()
            
        # Convert melody to token sequence
        melody_tokens = self._melody_to_tokens(melody)
        
        # Generate harmony tokens
        with torch.no_grad():
            inputs = self.tokenizer.encode(melody_tokens, return_tensors="pt").to(self.device)
            
            outputs = self.model.generate(
                inputs,
                max_length=self.config.max_length,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                repetition_penalty=self.config.repetition_penalty,
                pad_token_id=self.tokenizer.eos_token_id,
                do_sample=True
            )
            
        # Decode and convert to harmony
        harmony_tokens = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return self._tokens_to_harmony(harmony_tokens, style)
    
    def generate_bass_line(self, melody: Melody, harmony: Harmony) -> List[Note]:
        """Generate bass line based on melody and harmony."""
        # Implementation for bass line generation
        bass_notes = []
        for chord in harmony.chords:
            # Generate bass note based on chord root
            root_note = chord.root
            bass_note = Note(
                pitch=root_note - 12,  # One octave lower
                velocity=64,
                duration=chord.duration,
                start_time=chord.start_time
            )
            bass_notes.append(bass_note)
        
        return bass_notes
    
    def generate_drums(self, melody: Melody, tempo: int = 120) -> List[Note]:
        """Generate drum pattern based on melody and tempo."""
        # Implementation for drum pattern generation
        drum_notes = []
        beats_per_bar = 4
        beat_duration = 60.0 / tempo
        
        for bar in range(len(melody.notes) // 4):
            # Kick drum on beats 1 and 3
            kick_1 = Note(pitch=36, velocity=80, duration=0.25, start_time=bar * beats_per_bar * beat_duration)
            kick_3 = Note(pitch=36, velocity=80, duration=0.25, start_time=(bar * beats_per_bar + 2) * beat_duration)
            
            # Snare on beats 2 and 4
            snare_2 = Note(pitch=38, velocity=70, duration=0.25, start_time=(bar * beats_per_bar + 1) * beat_duration)
            snare_4 = Note(pitch=38, velocity=70, duration=0.25, start_time=(bar * beats_per_bar + 3) * beat_duration)
            
            # Hi-hat on every beat
            for beat in range(4):
                hihat = Note(pitch=42, velocity=50, duration=0.125, start_time=(bar * beats_per_bar + beat) * beat_duration)
                drum_notes.append(hihat)
            
            drum_notes.extend([kick_1, kick_3, snare_2, snare_4])
        
        return drum_notes
    
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
                        start_time=start_time
                    )
                    chords.append(chord)
                except (ValueError, IndexError):
                    continue
        
        return Harmony(chords=chords, style=style) 