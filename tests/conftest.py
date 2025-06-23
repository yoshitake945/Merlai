"""
Pytest configuration and fixtures.
"""

import os
import tempfile
from typing import Generator
from unittest.mock import Mock, patch

import pytest

from merlai.core.midi import MIDIGenerator
from merlai.core.music import MusicGenerator
from merlai.core.plugins import PluginManager
from merlai.core.types import (
    Chord,
    GenerationRequest,
    Harmony,
    Melody,
    Note,
    Song,
    Track,
)


@pytest.fixture
def sample_notes() -> list[Note]:
    """Provide sample notes for testing."""
    return [
        Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
        Note(pitch=62, velocity=80, duration=1.0, start_time=1.0),
        Note(pitch=64, velocity=80, duration=1.0, start_time=2.0),
        Note(pitch=65, velocity=80, duration=1.0, start_time=3.0),
    ]


@pytest.fixture
def sample_melody(sample_notes: list[Note]) -> Melody:
    """Provide sample melody for testing."""
    return Melody(notes=sample_notes, tempo=120, key="C")


@pytest.fixture
def sample_chords() -> list[Chord]:
    """Provide sample chords for testing."""
    return [
        Chord(root=60, chord_type="major", duration=1.0, start_time=0.0),
        Chord(root=62, chord_type="minor", duration=1.0, start_time=1.0),
        Chord(root=64, chord_type="major", duration=1.0, start_time=2.0),
    ]


@pytest.fixture
def sample_harmony(sample_chords: list[Chord]) -> Harmony:
    """Provide sample harmony for testing."""
    return Harmony(chords=sample_chords, style="pop", key="C")


@pytest.fixture
def sample_tracks(sample_notes: list[Note]) -> list[Track]:
    """Provide sample tracks for testing."""
    return [
        Track(name="Melody", notes=sample_notes, channel=0, instrument=0),
        Track(name="Bass", notes=sample_notes, channel=1, instrument=32),
        Track(name="Drums", notes=sample_notes, channel=9, instrument=0),
    ]


@pytest.fixture
def sample_song(sample_tracks: list[Track]) -> Song:
    """Provide sample song for testing."""
    return Song(tracks=sample_tracks, tempo=120, duration=4.0)


@pytest.fixture
def music_generator() -> MusicGenerator:
    """Provide music generator instance for testing."""
    return MusicGenerator()


@pytest.fixture
def midi_generator() -> MIDIGenerator:
    """Provide MIDI generator instance for testing."""
    return MIDIGenerator()


@pytest.fixture
def plugin_manager() -> PluginManager:
    """Provide plugin manager instance for testing."""
    return PluginManager()


@pytest.fixture
def temp_midi_file() -> Generator[str, None, None]:
    """Provide temporary MIDI file path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp_file:
        yield tmp_file.name
        # Cleanup
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)


@pytest.fixture
def temp_json_file() -> Generator[str, None, None]:
    """Provide temporary JSON file path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
        yield tmp_file.name
        # Cleanup
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)


@pytest.fixture
def mock_transformer_model() -> Generator[dict[str, Mock], None, None]:
    """Mock transformer model for testing."""
    with (
        patch("merlai.core.music.AutoTokenizer") as mock_tokenizer,
        patch("merlai.core.music.AutoModelForCausalLM") as mock_model,
    ):

        # Mock tokenizer
        mock_tokenizer_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_tokenizer_instance.encode.return_value = Mock()
        mock_tokenizer_instance.decode.return_value = "NOTE_60_1.0_80 NOTE_64_1.0_80"
        mock_tokenizer_instance.eos_token_id = 50256

        # Mock model
        mock_model_instance = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_model_instance.generate.return_value = Mock()
        mock_model_instance.to.return_value = None
        mock_model_instance.eval.return_value = None

        yield {
            "tokenizer": mock_tokenizer,
            "model": mock_model,
            "tokenizer_instance": mock_tokenizer_instance,
            "model_instance": mock_model_instance,
        }


@pytest.fixture
def sample_generation_request() -> Generator[GenerationRequest, None, None]:
    """Provide sample generation request for testing."""
    from merlai.core.types import GenerationRequest, NoteData

    yield GenerationRequest(
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


@pytest.fixture
def sample_plugin_data() -> Generator[dict[str, str], None, None]:
    """Provide sample plugin data for testing."""
    yield {
        "id": "test_plugin_1",
        "name": "Test Plugin 1",
        "type": "VST3",
        "path": "/path/to/plugin.vst3",
        "manufacturer": "Test Company",
        "version": "1.0.0",
        "category": "Synthesizer",
    }


@pytest.fixture
def sample_plugins(
    sample_plugin_data: dict[str, str],
) -> Generator[list[dict[str, str]], None, None]:
    """Provide sample plugins list for testing."""
    yield [
        sample_plugin_data,
        {
            "id": "test_plugin_2",
            "name": "Test Plugin 2",
            "type": "AU",
            "path": "/path/to/plugin.component",
            "manufacturer": "Test Company",
            "version": "2.0.0",
            "category": "Effect",
        },
    ]


# Pytest configuration
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")
    config.addinivalue_line("markers", "cli: marks tests as CLI tests")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Modify test collection."""
    # Mark tests based on file name
    for item in items:
        if "test_core" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        elif "test_cli" in item.nodeid:
            item.add_marker(pytest.mark.cli)
        elif "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)


# Test data generators
def generate_test_notes(
    count: int = 10, start_pitch: int = 60, duration: float = 1.0
) -> list[Note]:
    """Generate test notes."""
    notes = []
    for i in range(count):
        notes.append(
            Note(
                pitch=start_pitch + (i % 12),
                velocity=80,
                duration=duration,
                start_time=i * duration,
            )
        )
    return notes


def generate_test_melody(count: int = 10, tempo: int = 120, key: str = "C") -> Melody:
    """Generate test melody."""
    notes = generate_test_notes(count)
    return Melody(notes=notes, tempo=tempo, key=key)


def generate_test_chords(count: int = 5) -> list[Chord]:
    """Generate test chords."""
    chord_types = ["major", "minor", "dim", "aug"]
    chords = []
    for i in range(count):
        chords.append(
            Chord(
                root=60 + (i * 2),
                chord_type=chord_types[i % len(chord_types)],
                duration=1.0,
                start_time=i * 1.0,
            )
        )
    return chords


def generate_test_harmony(
    count: int = 5, style: str = "pop", key: str = "C"
) -> Harmony:
    """Generate test harmony."""
    chords = generate_test_chords(count)
    return Harmony(chords=chords, style=style, key=key)
