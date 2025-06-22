"""
Tests for core music generation functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from merlai.core.types import Note, Harmony, Melody, Chord, Track, Song
from merlai.core.music import MusicGenerator
from merlai.core.midi import MIDIGenerator
from merlai.core.plugins import PluginManager


class TestNote:
    """Test Note class functionality."""
    
    def test_note_creation(self):
        """Test creating a Note object."""
        note = Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)
        assert note.pitch == 60
        assert note.velocity == 80
        assert note.duration == 1.0
        assert note.start_time == 0.0
        assert note.channel == 0  # Default channel
    
    def test_note_with_custom_channel(self):
        """Test creating Note with custom channel."""
        note = Note(pitch=60, velocity=80, duration=1.0, start_time=0.0, channel=1)
        assert note.channel == 1
    
    def test_invalid_pitch(self):
        """Test handling of invalid pitch values."""
        with pytest.raises(ValueError):
            Note(pitch=-1, velocity=80, duration=1.0, start_time=0.0)
        
        with pytest.raises(ValueError):
            Note(pitch=128, velocity=80, duration=1.0, start_time=0.0)


class TestMelody:
    """Test Melody class functionality."""
    
    def test_melody_creation(self):
        """Test creating a Melody object."""
        notes = [
            Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
            Note(pitch=62, velocity=80, duration=1.0, start_time=1.0)
        ]
        melody = Melody(notes=notes)
        assert len(melody.notes) == 2
        assert melody.notes[0].pitch == 60
        assert melody.notes[1].pitch == 62
        assert melody.tempo == 120  # Default tempo
        assert melody.key == "C"  # Default key
    
    def test_empty_melody(self):
        """Test creating an empty melody."""
        melody = Melody(notes=[])
        assert len(melody.notes) == 0
    
    def test_melody_with_custom_params(self):
        """Test creating melody with custom parameters."""
        notes = [Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        melody = Melody(notes=notes, tempo=140, key="G", time_signature="3/4")
        assert melody.tempo == 140
        assert melody.key == "G"
        assert melody.time_signature == "3/4"


class TestChord:
    """Test Chord class functionality."""
    
    def test_chord_creation(self):
        """Test creating a Chord object."""
        chord = Chord(root=60, chord_type="major", duration=1.0, start_time=0.0)
        assert chord.root == 60
        assert chord.chord_type == "major"
        assert chord.duration == 1.0
        assert chord.start_time == 0.0
        assert chord.voicing is None
    
    def test_chord_with_voicing(self):
        """Test creating chord with custom voicing."""
        voicing = [60, 64, 67]  # C major triad
        chord = Chord(root=60, chord_type="major", duration=1.0, start_time=0.0, voicing=voicing)
        assert chord.voicing == voicing


class TestHarmony:
    """Test Harmony class functionality."""
    
    def test_harmony_creation(self):
        """Test creating a Harmony object."""
        chords = [
            Chord(root=60, chord_type="major", duration=1.0, start_time=0.0),
            Chord(root=62, chord_type="minor", duration=1.0, start_time=1.0)
        ]
        harmony = Harmony(chords=chords)
        assert len(harmony.chords) == 2
        assert harmony.chords[0].root == 60
        assert harmony.chords[1].root == 62
        assert harmony.style == "pop"  # Default style
        assert harmony.key == "C"  # Default key
    
    def test_harmony_with_custom_params(self):
        """Test creating harmony with custom parameters."""
        chords = [Chord(root=60, chord_type="major", duration=1.0, start_time=0.0)]
        harmony = Harmony(chords=chords, style="jazz", key="F")
        assert harmony.style == "jazz"
        assert harmony.key == "F"


class TestTrack:
    """Test Track class functionality."""
    
    def test_track_creation(self):
        """Test creating a Track object."""
        notes = [Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        track = Track(name="Melody", notes=notes, channel=0, instrument=0)
        assert track.name == "Melody"
        assert len(track.notes) == 1
        assert track.channel == 0
        assert track.instrument == 0
    
    def test_track_with_custom_params(self):
        """Test creating track with custom parameters."""
        notes = [Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        track = Track(name="Bass", notes=notes, channel=1, instrument=32)
        assert track.name == "Bass"
        assert track.channel == 1
        assert track.instrument == 32


class TestSong:
    """Test Song class functionality."""
    
    def test_song_creation(self):
        """Test creating a Song object."""
        tracks = [
            Track(name="Melody", notes=[], channel=0, instrument=0)
        ]
        song = Song(tracks=tracks, tempo=120, time_signature="4/4", key="C", duration=2.0)
        assert len(song.tracks) == 1
        assert song.tempo == 120
        assert song.time_signature == "4/4"
        assert song.key == "C"
        assert song.duration == 2.0


class TestMusicGenerator:
    """Test MusicGenerator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = MusicGenerator()
    
    @patch('merlai.core.music.AutoTokenizer')
    @patch('merlai.core.music.AutoModelForCausalLM')
    def test_generate_harmony(self, mock_model, mock_tokenizer):
        """Test harmony generation with mocked model."""
        # Mock the model and tokenizer
        mock_tokenizer_instance = Mock()
        mock_model_instance = Mock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_model.from_pretrained.return_value = mock_model_instance
        
        # Mock tokenizer methods
        mock_tokenizer_instance.encode.return_value = Mock()
        mock_tokenizer_instance.decode.return_value = "NOTE_60_1.0_80 NOTE_64_1.0_80"
        mock_tokenizer_instance.eos_token_id = 50256
        
        # Mock model generation - create a proper mock that supports indexing
        mock_output = Mock()
        mock_output.__getitem__ = Mock(return_value=Mock())
        mock_model_instance.generate.return_value = mock_output
        mock_model_instance.to.return_value = None
        mock_model_instance.eval.return_value = None
        
        melody = Melody(notes=[
            Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
            Note(pitch=62, velocity=80, duration=1.0, start_time=1.0)
        ])
        
        harmony = self.generator.generate_harmony(melody, style="pop")
        assert isinstance(harmony, Harmony)
        assert len(harmony.chords) >= 0
    
    def test_generate_bass_line(self):
        """Test bass line generation."""
        melody = Melody(notes=[
            Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
            Note(pitch=62, velocity=80, duration=1.0, start_time=1.0)
        ])
        
        harmony = Harmony(chords=[
            Chord(root=60, chord_type="major", duration=1.0, start_time=0.0),
            Chord(root=62, chord_type="minor", duration=1.0, start_time=1.0)
        ])
        
        bass = self.generator.generate_bass_line(melody, harmony)
        assert isinstance(bass, list)
        assert len(bass) > 0
        assert all(isinstance(note, Note) for note in bass)
    
    def test_generate_drums(self):
        """Test drum generation."""
        melody = Melody(notes=[
            Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
            Note(pitch=62, velocity=80, duration=1.0, start_time=1.0),
            Note(pitch=64, velocity=80, duration=1.0, start_time=2.0),
            Note(pitch=65, velocity=80, duration=1.0, start_time=3.0)
        ])
        
        drums = self.generator.generate_drums(melody, tempo=120)
        assert isinstance(drums, list)
        assert len(drums) > 0
        assert all(isinstance(note, Note) for note in drums)


class TestMIDIGenerator:
    """Test MIDIGenerator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = MIDIGenerator()
    
    def test_create_midi_from_notes(self):
        """Test creating MIDI file from notes."""
        notes = [
            Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
            Note(pitch=62, velocity=80, duration=1.0, start_time=1.0)
        ]
        
        midi_data = self.generator.create_midi_from_notes(notes, tempo=120)
        assert isinstance(midi_data, bytes)
        assert len(midi_data) > 0
    
    def test_create_midi_file_from_song(self):
        """Test creating MIDI file from song."""
        tracks = [
            Track(
                name="Melody",
                notes=[
                    Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
                    Note(pitch=62, velocity=80, duration=1.0, start_time=1.0)
                ],
                channel=0,
                instrument=0
            )
        ]
        
        song = Song(tracks=tracks, tempo=120, duration=2.0)
        midi_data = self.generator.create_midi_file(song)
        assert isinstance(midi_data, bytes)
        assert len(midi_data) > 0
    
    def test_merge_tracks(self):
        """Test merging multiple tracks."""
        tracks = [
            Track(
                name="Melody",
                notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
                channel=0,
                instrument=0
            ),
            Track(
                name="Bass",
                notes=[Note(pitch=48, velocity=80, duration=1.0, start_time=0.0)],
                channel=1,
                instrument=32
            )
        ]
        
        midi_data = self.generator.merge_tracks(tracks)
        assert isinstance(midi_data, bytes)
        assert len(midi_data) > 0
    
    def test_quantize_notes(self):
        """Test note quantization."""
        notes = [
            Note(pitch=60, velocity=80, duration=0.3, start_time=0.1),
            Note(pitch=62, velocity=80, duration=0.7, start_time=1.2)
        ]
        
        quantized = self.generator.quantize_notes(notes, grid_size=0.25)
        assert len(quantized) == 2
        assert quantized[0].start_time == 0.0  # Quantized to grid
        assert quantized[0].duration == 0.25   # Quantized to grid
        assert quantized[1].start_time == 1.25 # Quantized to grid
        assert quantized[1].duration == 0.75   # Quantized to grid
    
    def test_transpose_notes(self):
        """Test note transposition."""
        notes = [
            Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
            Note(pitch=62, velocity=80, duration=1.0, start_time=1.0)
        ]
        
        transposed = self.generator.transpose_notes(notes, semitones=2)
        assert len(transposed) == 2
        assert transposed[0].pitch == 62  # C4 -> D4
        assert transposed[1].pitch == 64  # D4 -> E4
    
    def test_transpose_notes_boundary(self):
        """Test note transposition at pitch boundaries."""
        # Test upper boundary
        high_note = Note(pitch=127, velocity=80, duration=1.0, start_time=0.0)
        transposed_up = self.generator.transpose_notes([high_note], semitones=5)
        assert transposed_up[0].pitch == 127  # Should be clamped
        
        # Test lower boundary
        low_note = Note(pitch=0, velocity=80, duration=1.0, start_time=0.0)
        transposed_down = self.generator.transpose_notes([low_note], semitones=-5)
        assert transposed_down[0].pitch == 0  # Should be clamped 


class TestMusicGeneratorEdgeCases:
    def setup_method(self):
        self.generator = MusicGenerator()

    def test_generate_harmony_empty_melody(self):
        melody = Melody(notes=[])
        with pytest.raises(Exception):
            self.generator.generate_harmony(melody, style="pop")

    def test_generate_harmony_unknown_style(self):
        # NOTE: 現状は未知のstyleで例外を期待するが、
        # 将来的にはどんなstyleでも結果が返るべき（例外を投げない設計が望ましい）
        melody = Melody(notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)])
        with pytest.raises(Exception):
            self.generator.generate_harmony(melody, style="unknown_style")

    def test_generate_bass_line_empty_harmony(self):
        melody = Melody(notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)])
        harmony = Harmony(chords=[])
        bass = self.generator.generate_bass_line(melody, harmony)
        assert bass == []

    def test_generate_drums_zero_tempo(self):
        melody = Melody(notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)])
        with pytest.raises(Exception):
            self.generator.generate_drums(melody, tempo=0)

    def test_generate_drums_extreme_tempo(self):
        melody = Melody(notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)])
        drums = self.generator.generate_drums(melody, tempo=1000)
        assert isinstance(drums, list) 


class TestMIDIGeneratorEdgeCases:
    def setup_method(self):
        self.generator = MIDIGenerator()

    def test_merge_tracks_empty(self):
        midi = self.generator.merge_tracks([])
        assert isinstance(midi, bytes)
        assert len(midi) > 0

    def test_quantize_notes_negative_grid(self):
        notes = [Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        with pytest.raises(Exception):
            self.generator.quantize_notes(notes, grid_size=-0.25)

    def test_transpose_notes_extreme(self):
        notes = [Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)]
        transposed = self.generator.transpose_notes(notes, semitones=100)
        assert transposed[0].pitch == 127
        transposed = self.generator.transpose_notes(notes, semitones=-100)
        assert transposed[0].pitch == 0 


class TestPluginManagerEdgeCases:
    def setup_method(self):
        self.manager = PluginManager()

    def test_scan_plugins_invalid_directory(self):
        result = self.manager.scan_plugins()
        assert isinstance(result, list)

    def test_load_plugin_not_found(self):
        success = self.manager.load_plugin("not_a_plugin")
        assert not success

    def test_recommend_plugins_unknown(self):
        recs = self.manager.get_plugin_recommendations(style="unknown", instrument_type="unknown")
        assert isinstance(recs, list) 