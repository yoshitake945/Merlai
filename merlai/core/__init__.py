"""
Core functionality for Merlai music generation.
"""

from .midi import MIDIGenerator
from .music import MusicGenerator
from .plugins import PluginManager

__all__ = ["MusicGenerator", "MIDIGenerator", "PluginManager"]
