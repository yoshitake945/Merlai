"""
Core data types for music generation.
"""

from dataclasses import dataclass
from typing import List, Optional

from pydantic import BaseModel, field_validator


@dataclass
class Note:
    """Represents a musical note."""

    pitch: int  # MIDI pitch (0-127)
    velocity: int  # MIDI velocity (0-127)
    duration: float  # Duration in seconds
    start_time: float  # Start time in seconds
    channel: int = 0  # MIDI channel (0-15)

    def __post_init__(self) -> None:
        """Validate note parameters after initialization."""
        if not 0 <= self.pitch <= 127:
            raise ValueError(f"Pitch must be between 0 and 127, got {self.pitch}")
        if not 0 <= self.velocity <= 127:
            raise ValueError(f"Velocity must be between 0 and 127, got {self.velocity}")
        if self.duration <= 0:
            raise ValueError(f"Duration must be positive, got {self.duration}")
        if self.start_time < 0:
            raise ValueError(f"Start time must be non-negative, got {self.start_time}")
        if not 0 <= self.channel <= 15:
            raise ValueError(f"Channel must be between 0 and 15, got {self.channel}")

    def __str__(self) -> str:
        """Return a string representation of the note."""
        return (
            f"Note(pitch={self.pitch}, velocity={self.velocity}, duration={self.duration}, "  # noqa: E501
            f"start_time={self.start_time}, channel={self.channel})"
        )

    def __repr__(self) -> str:
        """Return a string representation of the note."""
        return self.__str__()  # noqa: E501


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
class Bass:
    """Represents a bass line."""

    notes: List[Note]
    style: str = "pop"
    key: str = "C"


@dataclass
class Drums:
    """Represents a drum pattern."""

    notes: List[Note]
    style: str = "pop"
    tempo: int = 120


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

    @field_validator("melody")
    @classmethod
    def melody_must_not_be_empty(cls, v: List[NoteData]) -> List[NoteData]:
        if not v:
            raise ValueError("melody must not be empty")
        return v


class GenerationResponse(BaseModel):
    """Response model for music generation."""

    harmony: Optional[List[Chord]] = None
    bass_line: Optional[List[Note]] = None
    drums: Optional[List[Note]] = None
    midi_data: Optional[str] = None  # Base64 encoded MIDI data
    duration: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
