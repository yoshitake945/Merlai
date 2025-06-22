"""
API routes for Merlai music generation service.
"""

import base64
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from ..core.music import MusicGenerator
from ..core.midi import MIDIGenerator, Track
from ..core.plugins import PluginManager
from ..core.types import Note, Chord, Harmony, GenerationRequest, GenerationResponse

router = APIRouter()


def get_music_generator() -> MusicGenerator:
    """Dependency to get music generator instance."""
    from .main import app

    return app.state.music_generator  # type: ignore


def get_midi_generator() -> MIDIGenerator:
    """Dependency to get MIDI generator instance."""
    from .main import app

    return app.state.midi_generator  # type: ignore


def get_plugin_manager() -> PluginManager:
    """Dependency to get plugin manager instance."""
    from .main import app

    return app.state.plugin_manager  # type: ignore


@router.post("/generate", response_model=GenerationResponse)
async def generate_music(
    request: GenerationRequest,
    music_generator: MusicGenerator = Depends(get_music_generator),
    midi_generator: MIDIGenerator = Depends(get_midi_generator),
) -> GenerationResponse:
    """Generate complementary music parts from a melody."""
    try:
        # Convert request to internal format
        melody_notes = []
        for note_data in request.melody:
            note = Note(
                pitch=note_data.pitch,
                velocity=note_data.velocity,
                duration=note_data.duration,
                start_time=note_data.start_time,
            )
            melody_notes.append(note)

        from ..core.types import Melody

        melody = Melody(notes=melody_notes, tempo=request.tempo, key=request.key)

        # Generate complementary parts
        harmony: Optional[Harmony] = None
        bass_line: Optional[List[Note]] = None
        drums: Optional[List[Note]] = None

        if request.generate_harmony:
            harmony = music_generator.generate_harmony(melody, request.style)

        if request.generate_bass and harmony is not None:
            bass_line = music_generator.generate_bass_line(melody, harmony)

        if request.generate_drums:
            drums = music_generator.generate_drums(melody, request.tempo)

        # Create MIDI file
        tracks: List[Track] = []

        # Add melody track
        tracks.append(Track(name="Melody", notes=melody.notes, channel=0, instrument=0))

        # Add generated tracks
        if harmony is not None:
            harmony_notes: List[Note] = []
            if harmony.chords:
                for chord in harmony.chords:
                    chord_notes = _chord_to_notes(chord)
                    harmony_notes.extend(chord_notes)
            tracks.append(
                Track(name="Harmony", notes=harmony_notes, channel=1, instrument=48)
            )

        if bass_line is not None:
            tracks.append(
                Track(
                    name="Bass", notes=bass_line, channel=2, instrument=32
                )
            )

        if drums is not None:
            tracks.append(
                Track(
                    name="Drums",
                    notes=drums,
                    channel=9,
                    instrument=0,
                )
            )

        # Generate MIDI data
        midi_data = midi_generator.merge_tracks(tracks)

        # Extract harmony chords for response
        harmony_chords = harmony.chords if harmony is not None else None

        return GenerationResponse(
            harmony=harmony_chords,
            bass_line=bass_line,
            drums=drums,
            midi_data=base64.b64encode(midi_data).decode('utf-8') if midi_data else None,
            duration=4.0,  # Calculate actual duration
            success=True,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/plugins")
async def list_plugins(
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> dict:
    """List available plugins."""
    try:
        plugins = plugin_manager.scan_plugins()
        return {
            "plugins": [
                {
                    "name": plugin.name,
                    "version": plugin.version,
                    "manufacturer": plugin.manufacturer,
                    "plugin_type": plugin.plugin_type,
                    "category": plugin.category,
                    "file_path": plugin.file_path,
                    "is_loaded": plugin.is_loaded,
                }
                for plugin in plugins
            ],
            "count": len(plugins),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list plugins: {str(e)}")


@router.get("/plugins/recommendations")
async def get_plugin_recommendations(
    style: str,
    instrument: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> dict:
    """Get plugin recommendations for a style and instrument."""
    try:
        recommendations = plugin_manager.get_plugin_recommendations(style, instrument)
        return {
            "style": style,
            "instrument": instrument,
            "recommendations": [
                {
                    "name": plugin.name,
                    "manufacturer": plugin.manufacturer,
                    "plugin_type": plugin.plugin_type,
                    "category": plugin.category,
                    "file_path": plugin.file_path,
                }
                for plugin in recommendations
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recommendations: {str(e)}"
        )


@router.post("/plugins/{plugin_name}/load")
async def load_plugin(
    plugin_name: str, plugin_manager: PluginManager = Depends(get_plugin_manager)
) -> dict:
    """Load a plugin."""
    try:
        success = plugin_manager.load_plugin(plugin_name)
        if success:
            return {"message": f"Plugin {plugin_name} loaded successfully"}
        else:
            raise HTTPException(
                status_code=404, detail=f"Plugin {plugin_name} not found"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load plugin: {str(e)}")


@router.get("/plugins/{plugin_name}/parameters")
async def get_plugin_parameters(
    plugin_name: str, plugin_manager: PluginManager = Depends(get_plugin_manager)
) -> dict:
    """Get parameters for a loaded plugin."""
    try:
        # プラグインが存在するかチェック
        plugin_info = plugin_manager.get_plugin_info(plugin_name)
        if not plugin_info:
            raise HTTPException(
                status_code=404, detail=f"Plugin '{plugin_name}' not found"
            )
        
        # プラグインがロードされているかチェック
        if not plugin_manager.is_plugin_loaded(plugin_name):
            raise HTTPException(
                status_code=400, detail=f"Plugin '{plugin_name}' is not loaded"
            )
        
        parameters = plugin_manager.get_plugin_parameters(plugin_name)
        return {"plugin_name": plugin_name, "parameters": parameters}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get parameters: {str(e)}"
        )


@router.get("/plugins/{plugin_name}/presets")
async def get_plugin_presets(
    plugin_name: str, plugin_manager: PluginManager = Depends(get_plugin_manager)
) -> dict:
    """Get presets for a plugin."""
    try:
        # プラグインが存在するかチェック
        plugin_info = plugin_manager.get_plugin_info(plugin_name)
        if not plugin_info:
            raise HTTPException(
                status_code=404, detail=f"Plugin '{plugin_name}' not found"
            )
        
        presets = plugin_manager.get_presets(plugin_name)
        return {"plugin_name": plugin_name, "presets": presets}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get presets: {str(e)}"
        )


@router.get("/plugins/{plugin_name}")
async def get_plugin_info(
    plugin_name: str, plugin_manager: PluginManager = Depends(get_plugin_manager)
) -> dict:
    """Get detailed information about a specific plugin."""
    try:
        plugin_info = plugin_manager.get_plugin_info(plugin_name)
        if not plugin_info:
            raise HTTPException(
                status_code=404, detail=f"Plugin '{plugin_name}' not found"
            )
        
        return {
            "name": plugin_info.name,
            "version": plugin_info.version,
            "manufacturer": plugin_info.manufacturer,
            "plugin_type": plugin_info.plugin_type,
            "category": plugin_info.category,
            "file_path": plugin_info.file_path,
            "is_loaded": plugin_info.is_loaded,
            "parameters": plugin_info.parameters,
            "presets": plugin_info.presets,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get plugin info: {str(e)}"
        )


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "merlai", "version": "0.1.0"}


def _chord_to_notes(chord: Chord) -> List[Note]:
    """Convert a chord to individual notes."""
    # Simple chord voicing - can be enhanced
    chord_notes = []
    root = chord.root

    # Major chord intervals: root, major third, perfect fifth
    intervals = [0, 4, 7]

    for interval in intervals:
        pitch = root + interval
        if pitch <= 127:  # MIDI pitch limit
            note = Note(
                pitch=pitch,
                velocity=60,
                duration=chord.duration,
                start_time=chord.start_time,
            )
            chord_notes.append(note)

    return chord_notes
