"""
Plugin management system for sound plugins.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .types import Note, Song, Track


@dataclass
class PluginInfo:
    """Information about a sound plugin."""

    name: str
    version: str
    manufacturer: str
    plugin_type: str  # "VST", "AU", "VST3", etc.
    category: str  # "Synth", "Effect", "Drum Machine", etc.
    file_path: str
    parameters: List[str]
    presets: List[str]
    is_loaded: bool = False


class PluginParameter(BaseModel):
    """Parameter configuration for a plugin."""

    name: str
    value: float
    min_value: float
    max_value: float
    default_value: float
    unit: str = ""
    is_automated: bool = False


class PluginPreset(BaseModel):
    """Preset configuration for a plugin."""

    name: str
    parameters: Dict[str, float]
    category: str = "Default"


class PluginManager:
    """Manages external sound plugins and provides recommendations."""

    def __init__(self, plugin_directories: Optional[List[str]] = None):
        """Initialize plugin manager."""
        self.plugin_directories = plugin_directories or [
            "/Library/Audio/Plug-Ins/VST",
            "/Library/Audio/Plug-Ins/VST3",
            "/Library/Audio/Plug-Ins/Components",
            os.path.expanduser("~/Library/Audio/Plug-Ins/VST"),
            os.path.expanduser("~/Library/Audio/Plug-Ins/VST3"),
            os.path.expanduser("~/Library/Audio/Plug-Ins/Components"),
        ]
        self.plugins: Dict[str, PluginInfo] = {}
        self.loaded_plugins: Dict[str, Any] = {}

    def scan_plugins(self) -> List[PluginInfo]:
        """Scan for available plugins in configured directories."""
        found_plugins = []

        for directory in self.plugin_directories:
            if os.path.exists(directory):
                for file_path in Path(directory).rglob("*"):
                    if self._is_plugin_file(file_path):
                        plugin_info = self._extract_plugin_info(file_path)
                        if plugin_info:
                            self.plugins[plugin_info.name] = plugin_info
                            found_plugins.append(plugin_info)

        return found_plugins

    def get_plugin_recommendations(
        self, style: str, instrument_type: str
    ) -> List[PluginInfo]:
        """Get plugin recommendations based on style and instrument type."""
        recommendations = []

        # Simple recommendation logic - can be enhanced with ML
        style_keywords = {
            "pop": ["pop", "modern", "contemporary"],
            "rock": ["rock", "guitar", "distortion"],
            "jazz": ["jazz", "smooth", "acoustic"],
            "electronic": ["synth", "electronic", "digital"],
            "classical": ["orchestral", "classical", "acoustic"],
        }

        instrument_keywords = {
            "bass": ["bass", "low", "sub"],
            "lead": ["lead", "solo", "melody"],
            "drums": ["drum", "percussion", "rhythm"],
            "pad": ["pad", "ambient", "atmospheric"],
        }

        keywords = style_keywords.get(style, []) + instrument_keywords.get(
            instrument_type, []
        )

        for plugin in self.plugins.values():
            score = 0
            plugin_text = (
                f"{plugin.name} {plugin.category} {plugin.manufacturer}".lower()
            )

            for keyword in keywords:
                if keyword.lower() in plugin_text:
                    score += 1

            if score > 0:
                recommendations.append((plugin, score))

        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return [plugin for plugin, score in recommendations[:5]]

    def load_plugin(self, plugin_name: str) -> bool:
        """Load a plugin into memory."""
        if plugin_name not in self.plugins:
            return False

        plugin_info = self.plugins[plugin_name]

        try:
            # Plugin loading logic would go here
            plugin_info.is_loaded = True
            self.loaded_plugins[plugin_name] = plugin_info
            return True
        except Exception:
            # Return False if exception occurs
            return False

    def get_plugin_parameters(self, plugin_name: str) -> List[PluginParameter]:
        """Get parameters for a loaded plugin."""
        try:
            if plugin_name not in self.loaded_plugins:
                # プラグインが存在しない場合は空リストを返す（正常なエラー）
                return []

            # This would return actual plugin parameters
            # For now, return dummy parameters
            return [
                PluginParameter(
                    name="Volume",
                    value=0.5,
                    min_value=0.0,
                    max_value=1.0,
                    default_value=0.5,
                    unit="dB",
                ),
                PluginParameter(
                    name="Cutoff",
                    value=0.7,
                    min_value=0.0,
                    max_value=1.0,
                    default_value=0.5,
                    unit="Hz",
                ),
            ]
        except Exception:
            # Return empty list if exception occurs
            return []

    def set_plugin_parameter(
        self, plugin_name: str, parameter_name: str, value: float
    ) -> bool:
        """Set a parameter value for a loaded plugin."""
        try:
            if plugin_name not in self.loaded_plugins:
                # プラグインが存在しない場合はFalseを返す（正常なエラー）
                return False

            # Parameter setting logic would go here
            return True
        except Exception:
            # Return False if exception occurs
            return False

    def get_presets(self, plugin_name: str) -> List[PluginPreset]:
        """Get available presets for a plugin."""
        try:
            if plugin_name not in self.plugins:
                # プラグインが存在しない場合は空リストを返す（正常なエラー）
                return []

            # Preset loading logic would go here
            return [
                PluginPreset(
                    name="Default",
                    parameters={"Volume": 0.5, "Cutoff": 0.7},
                    category="Default",
                ),
                PluginPreset(
                    name="Bright",
                    parameters={"Volume": 0.6, "Cutoff": 0.9},
                    category="Bright",
                ),
            ]
        except Exception:
            # Return empty list if exception occurs
            return []

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get information about a specific plugin."""
        return self.plugins.get(plugin_name)

    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded."""
        return plugin_name in self.loaded_plugins

    def _is_plugin_file(self, file_path: Path) -> bool:
        """Check if a file is a plugin file."""
        plugin_extensions = {".vst", ".vst3", ".component", ".dll", ".so"}
        return file_path.suffix.lower() in plugin_extensions

    def _extract_plugin_info(self, file_path: Path) -> Optional[PluginInfo]:
        """Extract plugin information from a file."""
        try:
            # This would extract actual plugin metadata
            # For now, create dummy info
            return PluginInfo(
                name=file_path.stem,
                version="1.0.0",
                manufacturer="Unknown",
                plugin_type=file_path.suffix.upper().lstrip("."),
                category="Synth",
                file_path=str(file_path),
                parameters=["Volume", "Cutoff", "Resonance"],
                presets=["Default", "Bright", "Dark"],
            )
        except Exception:
            return None

    def export_plugin_config(self, file_path: str) -> bool:
        """Export plugin configuration to JSON."""
        try:
            config = {
                "plugins": {
                    name: {
                        "name": info.name,
                        "version": info.version,
                        "manufacturer": info.manufacturer,
                        "plugin_type": info.plugin_type,
                        "category": info.category,
                        "file_path": info.file_path,
                        "is_loaded": info.is_loaded,
                    }
                    for name, info in self.plugins.items()
                }
            }

            with open(file_path, "w") as f:
                json.dump(config, f, indent=2)

            return True
        except Exception as e:
            print(f"Failed to export plugin config: {e}")
            return False

    def import_plugin_config(self, file_path: str) -> bool:
        """Import plugin configuration from JSON."""
        try:
            with open(file_path, "r") as f:
                config = json.load(f)

            for name, info in config.get("plugins", {}).items():
                plugin_info = PluginInfo(
                    name=info["name"],
                    version=info["version"],
                    manufacturer=info["manufacturer"],
                    plugin_type=info["plugin_type"],
                    category=info["category"],
                    file_path=info["file_path"],
                    parameters=[],
                    presets=[],
                    is_loaded=info.get("is_loaded", False),
                )
                self.plugins[name] = plugin_info

            return True
        except Exception as e:
            print(f"Failed to import plugin config: {e}")
            return False

    def create_midi_file(self, song: Song) -> bytes:
        """Create MIDI file from song data using MIDIGenerator."""
        from .midi import MIDIGenerator

        generator = MIDIGenerator()
        return generator.create_midi_file(song)

    def create_midi_from_notes(self, notes: List[Note], tempo: int = 120) -> bytes:
        """Create MIDI file from notes using MIDIGenerator."""
        from .midi import MIDIGenerator

        generator = MIDIGenerator()
        return generator.create_midi_from_notes(notes, tempo)

    def merge_tracks(self, tracks: List[Track]) -> bytes:
        """Merge tracks into a MIDI file using MIDIGenerator."""
        from .midi import MIDIGenerator

        generator = MIDIGenerator()
        return generator.merge_tracks(tracks)
