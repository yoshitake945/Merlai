"""
Core functionality for Merlai music generation.
"""

from .music import MusicGenerator
from .midi import MIDIGenerator
from .plugins import PluginManager

__all__ = ["MusicGenerator", "MIDIGenerator", "PluginManager"] 