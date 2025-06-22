"""
MIDI generation and processing functionality.
"""

from typing import List
import io
from midiutil import MIDIFile
from .types import Note, Track, Song


class MIDIGenerator:
    """MIDI file generation and processing."""

    def __init__(self):
        """Initialize MIDI generator."""
        self.default_velocity = 64
        self.default_duration = 0.5

    def create_midi_file(self, song: Song) -> bytes:
        """Create MIDI file from song data."""
        if song.tempo <= 0:
            raise ValueError(f"tempo must be positive, got {song.tempo}")
        
        midi = MIDIFile(len(song.tracks), deinterleave=False)

        # Set tempo
        midi.addTempo(0, 0, song.tempo)

        # Add tracks
        for i, track in enumerate(song.tracks):
            self._add_track_to_midi(midi, track, i)

        # Write to bytes
        midi_bytes = io.BytesIO()
        midi.writeFile(midi_bytes)
        return midi_bytes.getvalue()

    def create_midi_from_notes(self, notes: List[Note], tempo: int = 120) -> bytes:
        """Create MIDI file from list of notes."""
        if tempo <= 0:
            raise ValueError(f"tempo must be positive, got {tempo}")
        
        midi = MIDIFile(1, deinterleave=False)
        midi.addTempo(0, 0, tempo)

        for note in notes:
            midi.addNote(
                track=0,
                channel=note.channel,
                pitch=note.pitch,
                time=note.start_time,
                duration=note.duration,
                volume=note.velocity,
            )

        midi_bytes = io.BytesIO()
        midi.writeFile(midi_bytes)
        return midi_bytes.getvalue()

    def parse_midi_file(self, midi_data: bytes) -> Song:
        """Parse MIDI file and convert to Song object."""
        # For now, return a simple song structure
        # This can be enhanced later with proper MIDI parsing
        return Song(
            tracks=[],
            tempo=120,
            duration=0.0,
        )

    def _add_track_to_midi(
        self, midi: MIDIFile, track: Track, track_index: int
    ) -> None:
        """Add a track to the MIDI file."""
        for note in track.notes:
            midi.addNote(
                track=track_index,
                channel=track.channel,
                pitch=note.pitch,
                time=note.start_time,
                duration=note.duration,
                volume=note.velocity,
            )

    def merge_tracks(self, tracks: List[Track]) -> bytes:
        """Merge multiple tracks into a single MIDI file."""
        midi = MIDIFile(len(tracks), deinterleave=False)
        midi.addTempo(0, 0, 120)  # Default tempo

        for i, track in enumerate(tracks):
            self._add_track_to_midi(midi, track, i)

        midi_bytes = io.BytesIO()
        midi.writeFile(midi_bytes)
        return midi_bytes.getvalue()

    def quantize_notes(self, notes: List[Note], grid_size: float = 0.25) -> List[Note]:
        """Quantize notes to a grid."""
        if grid_size <= 0:
            raise ValueError(f"grid_size must be positive, got {grid_size}")
        quantized_notes = []
        for note in notes:
            # Quantize start time
            quantized_start = round(note.start_time / grid_size) * grid_size
            quantized_duration = round(note.duration / grid_size) * grid_size

            quantized_note = Note(
                pitch=note.pitch,
                velocity=note.velocity,
                duration=quantized_duration,
                start_time=quantized_start,
                channel=note.channel,
            )
            quantized_notes.append(quantized_note)

        return quantized_notes

    def transpose_notes(self, notes: List[Note], semitones: int) -> List[Note]:
        """Transpose notes by a number of semitones."""
        transposed_notes = []
        for note in notes:
            new_pitch = max(0, min(127, note.pitch + semitones))
            transposed_note = Note(
                pitch=new_pitch,
                velocity=note.velocity,
                duration=note.duration,
                start_time=note.start_time,
                channel=note.channel,
            )
            transposed_notes.append(transposed_note)

        return transposed_notes
