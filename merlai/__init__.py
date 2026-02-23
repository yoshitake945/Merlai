"""
Merlai - AI-powered music creation assistant

A system that helps fill in missing notes using AI.
You provide the main melody – Merlai complements the rest with MIDI-ready suggestions.
"""

__version__ = "0.1.0"
__author__ = "Merlai Team"
__email__ = "team@merlai.ai"

from .core.midi import MIDIGenerator
from .core.music import MusicGenerator
from .core.plugins import PluginManager
from .core.types import Bass, Chord, Drums, Harmony, Melody, Note, Song, Track

# Import API app (optional, only if FastAPI is available)
app = None
try:
    from .api.main import app as _app

    app = _app
except ImportError:
    # FastAPI not installed, app will be None
    pass

__all__ = [
    "MusicGenerator",
    "MIDIGenerator",
    "PluginManager",
    "Note",
    "Melody",
    "Chord",
    "Harmony",
    "Bass",
    "Drums",
    "Track",
    "Song",
    "app",
]
