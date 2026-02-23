"""
Additional tests to improve music.py coverage.

This file focuses on covering previously untested code paths.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from merlai.core.music import MusicGenerator
from merlai.core.types import Melody, Note, Harmony, Chord, Bass, Drums


class TestBasicHarmonyGeneration:
    """Test basic (non-AI) harmony generation."""

    def test_generate_basic_harmony_pop_style(self) -> None:
        """Test basic harmony generation for pop style."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[
                Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
                Note(pitch=64, velocity=80, duration=1.0, start_time=1.0),
                Note(pitch=67, velocity=80, duration=1.0, start_time=2.0),
            ],
            tempo=120,
            key="C"
        )
        
        harmony = gen._generate_basic_harmony(melody, "pop")
        
        assert isinstance(harmony, Harmony)
        assert harmony.style == "pop"
        assert len(harmony.chords) > 0
        assert all(isinstance(chord, Chord) for chord in harmony.chords)

    def test_generate_basic_harmony_jazz_style(self) -> None:
        """Test basic harmony generation for jazz style."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )
        
        harmony = gen._generate_basic_harmony(melody, "jazz")
        
        assert isinstance(harmony, Harmony)
        assert harmony.style == "jazz"

    def test_generate_basic_harmony_rock_style(self) -> None:
        """Test basic harmony generation for rock style."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )
        
        harmony = gen._generate_basic_harmony(melody, "rock")
        
        assert isinstance(harmony, Harmony)
        assert harmony.style == "rock"

    def test_generate_basic_harmony_classical_style(self) -> None:
        """Test basic harmony generation for classical style."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )
        
        harmony = gen._generate_basic_harmony(melody, "classical")
        
        assert isinstance(harmony, Harmony)
        assert harmony.style == "classical"

    def test_generate_basic_harmony_electronic_style(self) -> None:
        """Test basic harmony generation for electronic style."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )
        
        harmony = gen._generate_basic_harmony(melody, "electronic")
        
        assert isinstance(harmony, Harmony)
        assert harmony.style == "electronic"


class TestMelodyTokenization:
    """Test melody to token conversion."""

    def test_melody_to_tokens(self) -> None:
        """Test converting melody to tokens."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[
                Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
                Note(pitch=64, velocity=80, duration=0.5, start_time=1.0),
            ],
            tempo=120,
            key="C"
        )
        
        tokens = gen._melody_to_tokens(melody)
        
        assert isinstance(tokens, str)
        assert len(tokens) > 0
        # Should contain note information
        assert "60" in tokens or "NOTE" in tokens

    def test_melody_to_tokens_empty_melody(self) -> None:
        """Test converting empty melody to tokens."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(notes=[], tempo=120, key="C")
        
        tokens = gen._melody_to_tokens(melody)
        
        assert isinstance(tokens, str)


class TestTokenToHarmony:
    """Test token to harmony conversion."""

    def test_tokens_to_harmony_basic(self) -> None:
        """Test converting tokens to harmony."""
        gen = MusicGenerator(use_ai_models=False)
        
        # Simple token string
        tokens = "C_major D_minor E_major"
        
        harmony = gen._tokens_to_harmony(tokens, "pop")
        
        assert isinstance(harmony, Harmony)
        assert harmony.style == "pop"

    def test_tokens_to_harmony_empty_string(self) -> None:
        """Test converting empty token string."""
        gen = MusicGenerator(use_ai_models=False)
        
        tokens = ""
        
        harmony = gen._tokens_to_harmony(tokens, "pop")
        
        assert isinstance(harmony, Harmony)
        # Should return empty or basic harmony
        assert harmony.style == "pop"


class TestPublicBassAndDrumGeneration:
    """Test public bass and drum generation methods (which use basic methods internally)."""

    def test_generate_bass_line_uses_basic_generation(self) -> None:
        """Test that bass line generation works (uses basic generation internally)."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )
        harmony = Harmony(
            chords=[Chord(root=60, chord_type="major", duration=1.0, start_time=0.0)],
            style="pop",
            key="C"
        )
        
        bass = gen.generate_bass_line(melody, harmony)
        
        assert isinstance(bass, Bass)
        assert len(bass.notes) > 0
        assert all(isinstance(note, Note) for note in bass.notes)

    def test_generate_bass_line_with_multiple_chords(self) -> None:
        """Test bass line with multiple chords."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[
                Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
                Note(pitch=64, velocity=80, duration=1.0, start_time=1.0),
            ],
            tempo=120,
            key="C"
        )
        harmony = Harmony(
            chords=[
                Chord(root=60, chord_type="major", duration=1.0, start_time=0.0),
                Chord(root=65, chord_type="minor", duration=1.0, start_time=1.0),
            ],
            style="pop",
            key="C"
        )
        
        bass = gen.generate_bass_line(melody, harmony)
        
        assert isinstance(bass, Bass)
        assert len(bass.notes) >= 2

    def test_generate_drums_uses_basic_generation(self) -> None:
        """Test that drum generation works (uses basic generation internally)."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )
        
        drums = gen.generate_drums(melody, tempo=120)
        
        assert isinstance(drums, Drums)
        assert all(isinstance(note, Note) for note in drums.notes)

    def test_generate_drums_fast_tempo(self) -> None:
        """Test drum generation with fast tempo."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[
                Note(pitch=60, velocity=80, duration=0.5, start_time=0.0),
                Note(pitch=62, velocity=80, duration=0.5, start_time=0.5),
            ],
            tempo=180,
            key="C"
        )
        
        drums = gen.generate_drums(melody, tempo=180)
        
        assert isinstance(drums, Drums)

    def test_generate_drums_slow_tempo(self) -> None:
        """Test drum generation with slow tempo."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=2.0, start_time=0.0)],
            tempo=60,
            key="C"
        )
        
        drums = gen.generate_drums(melody, tempo=60)
        
        assert isinstance(drums, Drums)


class TestHarmonyGenerationFallback:
    """Test harmony generation with AI fallback."""

    def test_generate_harmony_with_model_none(self) -> None:
        """Test harmony generation when model is None."""
        gen = MusicGenerator(use_ai_models=False)
        gen.model = None
        gen.tokenizer = None
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )
        
        # Should fall back to basic generation
        harmony = gen.generate_harmony(melody, style="pop")
        
        assert isinstance(harmony, Harmony)
        assert harmony.style == "pop"

    def test_generate_harmony_exception_handling(self) -> None:
        """Test harmony generation exception handling."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )
        
        # Mock to raise exception
        with patch.object(gen, '_generate_basic_harmony', side_effect=Exception("Test error")):
            # Should handle exception and try fallback
            with pytest.raises(Exception):
                gen.generate_harmony(melody, style="pop")


class TestBassLineGenerationMethods:
    """Test various bass line generation code paths."""

    def test_generate_bass_line_fallback_to_basic(self) -> None:
        """Test bass line generation falling back to basic method."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )
        harmony = Harmony(
            chords=[Chord(root=60, chord_type="major", duration=1.0, start_time=0.0)],
            style="pop",
            key="C"
        )
        
        bass = gen.generate_bass_line(melody, harmony)
        
        assert isinstance(bass, Bass)
        assert len(bass.notes) > 0


class TestDrumGenerationMethods:
    """Test various drum generation code paths."""

    def test_generate_drums_fallback_to_basic(self) -> None:
        """Test drum generation falling back to basic method."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[
                Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
                Note(pitch=62, velocity=80, duration=1.0, start_time=1.0),
            ],
            tempo=120,
            key="C"
        )
        
        drums = gen.generate_drums(melody, tempo=120)
        
        assert isinstance(drums, Drums)


class TestEdgeCasesInGeneration:
    """Test edge cases in music generation."""

    def test_harmony_with_different_keys(self) -> None:
        """Test harmony generation with different keys."""
        gen = MusicGenerator(use_ai_models=False)
        
        for key in ["C", "D", "E", "F", "G", "A", "B"]:
            melody = Melody(
                notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
                tempo=120,
                key=key
            )
            
            harmony = gen._generate_basic_harmony(melody, "pop")
            
            assert isinstance(harmony, Harmony)
            assert harmony.key == key

    def test_bassline_with_empty_chords(self) -> None:
        """Test bassline generation with no chords."""
        gen = MusicGenerator(use_ai_models=False)
        
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
            tempo=120,
            key="C"
        )
        harmony = Harmony(chords=[], style="pop", key="C")
        
        bass = gen.generate_bass_line(melody, harmony)
        
        assert isinstance(bass, Bass)
        # Should handle empty chords gracefully

    def test_drums_with_very_long_melody(self) -> None:
        """Test drum generation with very long melody."""
        gen = MusicGenerator(use_ai_models=False)
        
        # Create 50-note melody
        notes = [
            Note(pitch=60 + (i % 12), velocity=80, duration=0.5, start_time=i * 0.5)
            for i in range(50)
        ]
        melody = Melody(notes=notes, tempo=120, key="C")
        
        drums = gen.generate_drums(melody, tempo=120)
        
        assert isinstance(drums, Drums)
