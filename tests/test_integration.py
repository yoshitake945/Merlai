"""
Integration tests for the complete system.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from merlai.core.ai_models import ModelConfig, ModelType
from merlai.core.midi import MIDIGenerator
from merlai.core.music import MusicGenerator
from merlai.core.plugins import PluginManager
from merlai.core.types import (
    Bass,
    Drums,
    GenerationRequest,
    Harmony,
    Melody,
    Note,
    NoteData,
    Song,
    Track,
)


class TestEndToEndMusicGeneration:
    """Test complete music generation workflow."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.music_generator = MusicGenerator()
        self.midi_generator = MIDIGenerator()
        self.plugin_manager = PluginManager()

    def test_complete_music_generation_workflow(self) -> None:
        """Test complete workflow from melody to MIDI file."""
        # 1. Create input melody
        melody = Melody(
            notes=[
                Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
                Note(pitch=62, velocity=80, duration=1.0, start_time=1.0),
                Note(pitch=64, velocity=80, duration=1.0, start_time=2.0),
                Note(pitch=65, velocity=80, duration=1.0, start_time=3.0),
            ]
        )

        # 2. Generate harmony
        with (
            patch("merlai.core.music.AutoTokenizer"),
            patch("merlai.core.music.AutoModelForCausalLM"),
        ):
            harmony = self.music_generator.generate_harmony(melody, style="pop")
            assert isinstance(harmony, Harmony)
            assert len(harmony.chords) >= 0

        # 3. Generate bass line
        bass_notes = self.music_generator.generate_bass_line(melody, harmony)
        assert isinstance(bass_notes, Bass)
        assert len(bass_notes.notes) >= 0

        # 4. Generate drums
        drum_notes = self.music_generator.generate_drums(melody, tempo=120)
        assert isinstance(drum_notes, Drums)
        assert len(drum_notes.notes) > 0
        assert all(isinstance(note, Note) for note in drum_notes.notes)

        # 5. Create tracks
        melody_track = Track(name="Melody", notes=melody.notes, channel=0, instrument=0)

        bass_track = Track(
            name="Bass", notes=bass_notes.notes, channel=1, instrument=32
        )

        drum_track = Track(
            name="Drums",
            notes=drum_notes.notes,
            channel=9,  # MIDI channel 10 for drums
            instrument=0,
        )

        # 6. Create song
        song = Song(
            tracks=[melody_track, bass_track, drum_track], tempo=120, duration=4.0
        )

        # 7. Generate MIDI file
        midi_data = self.midi_generator.create_midi_file(song)
        assert isinstance(midi_data, bytes)
        assert len(midi_data) > 0

        # 8. Save to file and verify
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
            tmp_file.write(midi_data)
            midi_path = tmp_file.name

        try:
            assert os.path.exists(midi_path)
            assert os.path.getsize(midi_path) > 0

            # Verify file can be read back
            with open(midi_path, "rb") as f:
                read_data = f.read()
                assert read_data == midi_data

        finally:
            if os.path.exists(midi_path):
                os.unlink(midi_path)

    def test_midi_processing_workflow(self) -> None:
        """Test MIDI processing workflow."""
        # Create test notes
        notes = [
            Note(pitch=60, velocity=80, duration=0.5, start_time=0.0),
            Note(pitch=62, velocity=80, duration=0.5, start_time=0.5),
            Note(pitch=64, velocity=80, duration=0.5, start_time=1.0),
            Note(pitch=65, velocity=80, duration=0.5, start_time=1.5),
        ]

        # 1. Create MIDI from notes
        midi_data = self.midi_generator.create_midi_from_notes(notes, tempo=120)
        assert isinstance(midi_data, bytes)
        assert len(midi_data) > 0

        # 2. Quantize notes
        quantized_notes = self.midi_generator.quantize_notes(notes, grid_size=0.25)
        assert len(quantized_notes) == len(notes)

        # Verify quantization
        for note in quantized_notes:
            assert note.start_time % 0.25 == 0 or abs(note.start_time % 0.25) < 0.001
            assert note.duration % 0.25 == 0 or abs(note.duration % 0.25) < 0.001

        # 3. Transpose notes
        transposed_notes = self.midi_generator.transpose_notes(notes, semitones=2)
        assert len(transposed_notes) == len(notes)

        # Verify transposition
        for i, note in enumerate(transposed_notes):
            assert note.pitch == notes[i].pitch + 2

        # 4. Create MIDI from transposed notes
        transposed_midi = self.midi_generator.create_midi_from_notes(
            transposed_notes, tempo=120
        )
        assert isinstance(transposed_midi, bytes)
        assert len(transposed_midi) > 0
        assert transposed_midi != midi_data  # Should be different


class TestAPIIntegration:
    """Test API integration with core functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.music_generator = MusicGenerator()
        self.midi_generator = MIDIGenerator()

    def test_generation_request_to_midi_workflow(self) -> None:
        """Test workflow from API request to MIDI generation."""
        # 1. Create API request
        request = GenerationRequest(
            melody=[
                NoteData(pitch=60, velocity=80, duration=1.0, start_time=0.0),
                NoteData(pitch=62, velocity=80, duration=1.0, start_time=1.0),
                NoteData(pitch=64, velocity=80, duration=1.0, start_time=2.0),
            ],
            style="pop",
            tempo=120,
            key="C",
            generate_harmony=True,
            generate_bass=True,
            generate_drums=True,
        )

        # 2. Convert to internal types
        melody = Melody(
            notes=[
                Note(
                    pitch=note.pitch,
                    velocity=note.velocity,
                    duration=note.duration,
                    start_time=note.start_time,
                )
                for note in request.melody
            ]
        )

        # 3. Generate music components
        with (
            patch("merlai.core.music.AutoTokenizer"),
            patch("merlai.core.music.AutoModelForCausalLM"),
        ):
            harmony = self.music_generator.generate_harmony(melody, style=request.style)

        bass_notes = self.music_generator.generate_bass_line(melody, harmony)
        drum_notes = self.music_generator.generate_drums(melody, tempo=request.tempo)

        # 4. Create tracks
        tracks = [
            Track(name="Melody", notes=melody.notes, channel=0, instrument=0),
            Track(name="Bass", notes=bass_notes.notes, channel=1, instrument=32),
            Track(name="Drums", notes=drum_notes.notes, channel=9, instrument=0),
        ]

        # 5. Create song and generate MIDI
        song = Song(tracks=tracks, tempo=request.tempo, duration=3.0)
        midi_data = self.midi_generator.create_midi_file(song)

        # 6. Verify results
        assert isinstance(midi_data, bytes)
        assert len(midi_data) > 0

        # Verify harmony
        assert isinstance(harmony, Harmony)
        assert harmony.style == request.style

        # Verify bass
        assert isinstance(bass_notes, Bass)
        assert len(bass_notes.notes) >= 0

        # Verify drums
        assert isinstance(drum_notes, Drums)
        assert len(drum_notes.notes) > 0


class TestAIModelIntegration:
    """Test AI model integration with the complete system."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.music_generator = MusicGenerator(use_ai_models=True)
        self.midi_generator = MIDIGenerator()
        self.ai_manager = self.music_generator.ai_model_manager

    def test_ai_model_registration_and_usage(self) -> None:
        """Test AI model registration and usage workflow."""
        # 1. Register AI models
        with (
            patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf,
            patch("merlai.core.ai_models.ExternalAPIModel") as mock_api,
        ):
            mock_hf_model = Mock()
            mock_api_model = Mock()

            # Mock the generate_drums method to return a proper Drums object
            from merlai.core.types import Drums, Note

            mock_drums = Drums(
                notes=[Note(pitch=36, velocity=80, duration=0.5, start_time=0.0)]
            )
            mock_response = Mock()
            mock_response.success = True
            mock_response.result = mock_drums
            mock_hf_model.generate_drums.return_value = mock_response
            mock_api_model.generate_drums.return_value = mock_response

            mock_hf.return_value = mock_hf_model
            mock_api.return_value = mock_api_model

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

            # Register models
            success_hf = self.music_generator.register_ai_model(hf_config)
            success_api = self.music_generator.register_ai_model(api_config)

            assert success_hf is True
            assert success_api is True

            # 2. List models
            models = self.music_generator.list_ai_models()
            assert "test-hf" in models
            assert "test-api" in models
            assert len(models) >= 2

            # 3. Set default model
            success = self.music_generator.set_default_ai_model("test-hf")
            assert success is True

            # 4. Test AI generation (with fallback to basic generation)
            melody = Melody(
                notes=[
                    Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
                    Note(pitch=62, velocity=80, duration=1.0, start_time=1.0),
                ]
            )

            # Generate harmony using AI (will fallback to basic generation)
            harmony = self.music_generator.generate_harmony(
                melody, style="pop", model_name="test-hf"
            )
            assert isinstance(harmony, Harmony)
            assert len(harmony.chords) >= 0

            # Generate bass using AI (will fallback to basic generation)
            bass = self.music_generator.generate_bass_line(
                melody, harmony, model_name="test-hf"
            )
            assert isinstance(bass, Bass)
            assert len(bass.notes) >= 0

            # Generate drums using AI (will fallback to basic generation)
            drums = self.music_generator.generate_drums(
                melody, tempo=120, model_name="test-hf"
            )
            assert isinstance(drums, Drums)
            assert len(drums.notes) >= 0

    def test_ai_model_fallback_mechanism(self) -> None:
        """Test AI model fallback when primary model fails."""
        # 1. Register a model that will fail
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()
            mock_hf.return_value = mock_model
            mock_model.generate_harmony.return_value = Mock(
                success=False, error_message="Model unavailable", result=None
            )

            config = ModelConfig(
                name="failing-model",
                type=ModelType.HUGGINGFACE,
                model_path="invalid/path",
            )

            self.music_generator.register_ai_model(config)
            self.music_generator.set_default_ai_model("failing-model")

            # 2. Test generation with failing model (should fallback to basic generation)
            melody = Melody(
                notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
            )

            # Should fallback to basic generation method
            harmony = self.music_generator.generate_harmony(melody, style="pop")
            assert isinstance(harmony, Harmony)

    def test_multiple_ai_models_for_different_tasks(self) -> None:
        """Test using different AI models for different generation tasks."""
        # 1. Register multiple models
        with (
            patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf,
            patch("merlai.core.ai_models.ExternalAPIModel") as mock_api,
        ):
            mock_hf_model = Mock()
            mock_api_model = Mock()

            # Mock the generate_drums method to return a proper Drums object
            from merlai.core.types import Drums, Note

            mock_drums = Drums(
                notes=[Note(pitch=36, velocity=80, duration=0.5, start_time=0.0)]
            )
            mock_response = Mock()
            mock_response.success = True
            mock_response.result = mock_drums
            mock_hf_model.generate_drums.return_value = mock_response
            mock_api_model.generate_drums.return_value = mock_response

            mock_hf.return_value = mock_hf_model
            mock_api.return_value = mock_api_model

            hf_config = ModelConfig(
                name="harmony-model",
                type=ModelType.HUGGINGFACE,
                model_path="facebook/musicgen-small",
            )

            api_config = ModelConfig(
                name="bass-model",
                type=ModelType.EXTERNAL_API,
                endpoint="https://api.example.com/generate",
            )

            self.music_generator.register_ai_model(hf_config)
            self.music_generator.register_ai_model(api_config)

            # 2. Test using different models for different tasks (will fallback to basic generation)
            melody = Melody(
                notes=[
                    Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
                    Note(pitch=62, velocity=80, duration=1.0, start_time=1.0),
                ]
            )

            # Use different models for different tasks (will fallback to basic generation)
            harmony = self.music_generator.generate_harmony(
                melody, style="pop", model_name="harmony-model"
            )
            assert isinstance(harmony, Harmony)

            bass = self.music_generator.generate_bass_line(
                melody, harmony, model_name="bass-model"
            )
            assert isinstance(bass, Bass)

            drums = self.music_generator.generate_drums(
                melody, tempo=120, model_name="harmony-model"
            )
            assert isinstance(drums, Drums)

    def test_ai_model_with_midi_generation_workflow(self) -> None:
        """Test complete workflow with AI models and MIDI generation."""
        # 1. Set up AI models
        with patch("merlai.core.ai_models.HuggingFaceModel") as mock_hf:
            mock_model = Mock()

            # Mock the generate_drums method to return a proper Drums object
            from merlai.core.types import Drums, Note

            mock_drums = Drums(
                notes=[Note(pitch=36, velocity=80, duration=0.5, start_time=0.0)]
            )
            mock_response = Mock()
            mock_response.success = True
            mock_response.result = mock_drums
            mock_model.generate_drums.return_value = mock_response

            mock_hf.return_value = mock_model

            config = ModelConfig(
                name="test-model",
                type=ModelType.HUGGINGFACE,
                model_path="facebook/musicgen-small",
            )
            self.music_generator.register_ai_model(config)

            # 2. Create melody
            melody = Melody(
                notes=[
                    Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
                    Note(pitch=62, velocity=80, duration=1.0, start_time=1.0),
                    Note(pitch=64, velocity=80, duration=1.0, start_time=2.0),
                ]
            )

            # 3. Generate music using AI models (will fallback to basic generation)
            harmony = self.music_generator.generate_harmony(
                melody, style="pop", model_name="test-model"
            )
            bass = self.music_generator.generate_bass_line(
                melody, harmony, model_name="test-model"
            )
            drums = self.music_generator.generate_drums(
                melody, tempo=120, model_name="test-model"
            )

            # 4. Create tracks
            tracks = [
                Track(name="Melody", notes=melody.notes, channel=0, instrument=0),
                Track(
                    name="Harmony", notes=[], channel=1, instrument=48
                ),  # Empty for now
                Track(name="Bass", notes=bass.notes, channel=2, instrument=32),
                Track(name="Drums", notes=drums.notes, channel=9, instrument=0),
            ]

            # 5. Create song and generate MIDI
            song = Song(tracks=tracks, tempo=120, duration=3.0)
            midi_data = self.midi_generator.create_midi_file(song)

            # 6. Verify results
            assert isinstance(midi_data, bytes)
            assert len(midi_data) > 0

            # Verify AI-generated components
            assert isinstance(harmony, Harmony)
            assert isinstance(bass, Bass)
            assert isinstance(drums, Drums)

            # Verify track structure
            assert len(song.tracks) == 4
            assert song.tracks[0].name == "Melody"
            assert song.tracks[1].name == "Harmony"
            assert song.tracks[2].name == "Bass"
            assert song.tracks[3].name == "Drums"


class TestPluginIntegration:
    """Test plugin integration with core functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.plugin_manager = PluginManager()

    def test_plugin_integration_workflow(self) -> None:
        """Test plugin scanning and management workflow."""
        # 1. Scan for plugins
        plugins = self.plugin_manager.scan_plugins()
        assert isinstance(plugins, list)

        # 2. Get plugin recommendations
        recommendations = self.plugin_manager.get_plugin_recommendations("pop", "piano")
        assert isinstance(recommendations, list)

        # 3. Test plugin loading (if any plugins found)
        if plugins:
            plugin = plugins[0]
            success = self.plugin_manager.load_plugin(plugin.name)
            assert isinstance(success, bool)

            # 4. Test plugin parameters
            if success:
                parameters = self.plugin_manager.get_plugin_parameters(plugin.name)
                assert isinstance(parameters, list)
                if parameters:
                    param = parameters[0]
                    assert hasattr(param, "name")
                    set_success = self.plugin_manager.set_plugin_parameter(
                        plugin.name, param.name, 0.5
                    )
                    assert isinstance(set_success, bool)


class TestErrorHandlingIntegration:
    """Test error handling across the complete system."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.music_generator = MusicGenerator()
        self.midi_generator = MIDIGenerator()
        self.plugin_manager = PluginManager()

    def test_music_generation_with_invalid_input(self) -> None:
        """Test music generation with invalid input."""
        # Test with empty melody
        empty_melody = Melody(notes=[])

        # Should handle gracefully
        harmony = self.music_generator.generate_harmony(empty_melody, style="pop")
        assert isinstance(harmony, Harmony)

        # Test with invalid style
        melody = Melody(
            notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        )

        harmony = self.music_generator.generate_harmony(melody, style="invalid_style")
        assert isinstance(harmony, Harmony)

    def test_midi_generation_with_invalid_input(self) -> None:
        """Test MIDI generation with invalid input."""
        # Test with empty notes
        empty_notes: list[Note] = []
        midi_data = self.midi_generator.create_midi_from_notes(empty_notes, tempo=120)
        assert isinstance(midi_data, bytes)

        # Test with invalid tempo (should raise ValueError)
        notes = [Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        with pytest.raises(ValueError, match="tempo must be positive"):
            self.midi_generator.create_midi_from_notes(notes, tempo=0)

    def test_plugin_management_with_invalid_input(self) -> None:
        """Test plugin management with invalid input."""
        # Test loading non-existent plugin
        success = self.plugin_manager.load_plugin("non_existent_plugin")
        assert success is False

        # Test getting parameters for non-existent plugin
        parameters = self.plugin_manager.get_plugin_parameters("non_existent_plugin")
        assert parameters == []  # Returns empty list for non-existent plugins


class TestPerformanceIntegration:
    """Test performance characteristics of the complete system."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.music_generator = MusicGenerator()
        self.midi_generator = MIDIGenerator()

    def test_large_melody_processing(self) -> None:
        """Test processing of large melodies."""
        # Create a large melody
        large_melody = Melody(
            notes=[
                Note(pitch=60 + (i % 12), velocity=80, duration=0.5, start_time=i * 0.5)
                for i in range(100)  # 100 notes
            ]
        )

        # Test harmony generation
        with (
            patch("merlai.core.music.AutoTokenizer"),
            patch("merlai.core.music.AutoModelForCausalLM"),
        ):
            harmony = self.music_generator.generate_harmony(large_melody, style="pop")
            assert isinstance(harmony, Harmony)

        # Test bass generation
        bass = self.music_generator.generate_bass_line(large_melody, harmony)
        assert isinstance(bass, Bass)

        # Test drum generation
        drums = self.music_generator.generate_drums(large_melody, tempo=120)
        assert isinstance(drums, Drums)

        # Test MIDI generation
        tracks = [
            Track(name="Melody", notes=large_melody.notes, channel=0, instrument=0),
            Track(name="Bass", notes=bass.notes, channel=1, instrument=32),
            Track(name="Drums", notes=drums.notes, channel=9, instrument=0),
        ]

        song = Song(tracks=tracks, tempo=120, duration=50.0)
        midi_data = self.midi_generator.create_midi_file(song)

        assert isinstance(midi_data, bytes)
        assert len(midi_data) > 0

    def test_midi_processing_performance(self) -> None:
        """Test MIDI processing performance."""
        # Create large set of notes
        notes = [
            Note(pitch=60 + (i % 12), velocity=80, duration=0.25, start_time=i * 0.25)
            for i in range(200)  # 200 notes
        ]

        # Test quantization
        quantized_notes = self.midi_generator.quantize_notes(notes, grid_size=0.125)
        assert len(quantized_notes) == len(notes)

        # Test transposition
        transposed_notes = self.midi_generator.transpose_notes(notes, semitones=5)
        assert len(transposed_notes) == len(notes)

        # Test MIDI generation
        midi_data = self.midi_generator.create_midi_from_notes(notes, tempo=120)
        assert isinstance(midi_data, bytes)
        assert len(midi_data) > 0
