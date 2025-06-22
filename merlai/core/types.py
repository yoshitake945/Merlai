"""
Core data types for music generation.
"""

from typing import List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel


@dataclass
class Note:
    """Represents a musical note."""

    pitch: int  # MIDI pitch (0-127)
    velocity: int  # MIDI velocity (0-127)
    duration: float  # Duration in seconds
    start_time: float  # Start time in seconds
    channel: int = 0  # MIDI channel (0-15)


@dataclass
class Chord:
    """Represents a musical chord."""

    root: int  # Root note pitch
    chord_type: str  # "major", "minor", "dim", "aug", etc.
    duration: float  # Duration in seconds
    start_time: float  # Start time in seconds
    voicing: Optional[List[int]] = None  # Optional chord voicing


@dataclass
class Melody:
    """Represents a melodic line."""

    notes: List[Note]
    tempo: int = 120
    key: str = "C"
    time_signature: str = "4/4"


@dataclass
class Harmony:
    """Represents harmonic progression."""

    chords: List[Chord]
    style: str = "pop"
    key: str = "C"


@dataclass
class Track:
    """Represents a MIDI track."""

    name: str
    notes: List[Note]
    channel: int = 0
    instrument: int = 0  # MIDI program number


@dataclass
class Song:
    """Represents a complete song."""

    tracks: List[Track]
    tempo: int = 120
    time_signature: str = "4/4"
    key: str = "C"
    duration: float = 0.0


class NoteData(BaseModel):
    """Note data for API requests."""

    pitch: int
    velocity: int
    duration: float
    start_time: float


class GenerationRequest(BaseModel):
    """Request model for music generation."""

    melody: List[NoteData]
    style: str = "pop"
    tempo: int = 120
    key: str = "C"
    generate_harmony: bool = True
    generate_bass: bool = True
    generate_drums: bool = True


class GenerationResponse(BaseModel):
    """Response model for music generation."""

    harmony: Optional[List[Chord]] = None
    bass_line: Optional[List[Note]] = None
    drums: Optional[List[Note]] = None
    midi_data: Optional[str] = None  # Base64 encoded MIDI data
    duration: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
