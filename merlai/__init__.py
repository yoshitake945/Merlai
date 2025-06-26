"""
Merlai - AI-powered music creation assistant

A system that helps fill in missing notes using AI.
You provide the main melody – Merlai complements the rest with MIDI-ready suggestions.
"""

__version__ = "0.1.0"
__author__ = "Merlai Team"
__email__ = "team@merlai.ai"

from .api.main import app
from .core.midi import MIDIGenerator
from .core.music import MusicGenerator
from .core.plugins import PluginManager

__all__ = [
    "MusicGenerator",
    "MIDIGenerator",
    "PluginManager",
    "app",
]
