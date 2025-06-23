"""
API routes for Merlai music generation service.
"""

import base64
from typing import List, Optional
<<<<<<< HEAD

from fastapi import APIRouter, Depends, HTTPException

from ..core.ai_models import (
    ModelConfig,
    GenerationRequest as AIModelGenerationRequest,
    GenerationResponse as AIModelGenerationResponse,
)
from ..core.midi import MIDIGenerator, Track
from ..core.music import MusicGenerator
from ..core.plugins import PluginManager
from ..core.types import (
    Bass,
    Chord,
    Drums,
    Harmony,
    Melody,
    Note,
    GenerationRequest,
    GenerationResponse,
)
=======
from fastapi import APIRouter, Depends, HTTPException
from ..core.music import MusicGenerator
from ..core.midi import MIDIGenerator, Track
from ..core.plugins import PluginManager
from ..core.types import Note, Chord, Harmony, Melody, Bass, Drums, GenerationRequest as LegacyGenerationRequest, GenerationResponse as LegacyGenerationResponse
from ..core.ai_models import ModelConfig, ModelType, GenerationRequest, GenerationResponse
>>>>>>> origin/dev

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


<<<<<<< HEAD
@router.post("/generate", response_model=GenerationResponse)
async def generate_music(
    request: GenerationRequest,
    music_generator: MusicGenerator = Depends(get_music_generator),
    midi_generator: MIDIGenerator = Depends(get_midi_generator),
) -> GenerationResponse:
=======
@router.post("/generate", response_model=LegacyGenerationResponse)
async def generate_music(
    request: LegacyGenerationRequest,
    music_generator: MusicGenerator = Depends(get_music_generator),
    midi_generator: MIDIGenerator = Depends(get_midi_generator),
) -> LegacyGenerationResponse:
>>>>>>> origin/dev
    """Generate complementary music parts from a melody."""
    try:
        # Validate melody is not empty
        if not request.melody:
            raise HTTPException(
<<<<<<< HEAD
                status_code=422,
                detail="Melody cannot be empty. Please provide at least one note.",  # noqa: E501
            )

=======
                status_code=422, 
                detail="Melody cannot be empty. Please provide at least one note."
            )
        
>>>>>>> origin/dev
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

<<<<<<< HEAD
        melody = Melody(
            notes=melody_notes, tempo=request.tempo, key=request.key
        )
=======
        from ..core.types import Melody

        melody = Melody(notes=melody_notes, tempo=request.tempo, key=request.key)
>>>>>>> origin/dev

        # Generate complementary parts
        harmony: Optional[Harmony] = None
        bass_line: Optional[Bass] = None
        drums: Optional[Drums] = None

        if request.generate_harmony:
            harmony = music_generator.generate_harmony(melody, request.style)

        if request.generate_bass and harmony is not None:
            bass_line = music_generator.generate_bass_line(melody, harmony)

        if request.generate_drums:
            drums = music_generator.generate_drums(melody, request.tempo)

        # Create MIDI file
        tracks: List[Track] = []

        # Add melody track
<<<<<<< HEAD
        tracks.append(
            Track(name="Melody", notes=melody.notes, channel=0, instrument=0)
        )
=======
        tracks.append(Track(name="Melody", notes=melody.notes, channel=0, instrument=0))
>>>>>>> origin/dev

        # Add generated tracks
        if harmony is not None:
            harmony_notes: List[Note] = []
            if harmony.chords:
                for chord in harmony.chords:
                    chord_notes = _chord_to_notes(chord)
                    harmony_notes.extend(chord_notes)
            tracks.append(
<<<<<<< HEAD
                Track(
                    name="Harmony",
                    notes=harmony_notes,
                    channel=1,
                    instrument=48,
                )
=======
                Track(name="Harmony", notes=harmony_notes, channel=1, instrument=48)
>>>>>>> origin/dev
            )

        if bass_line is not None:
            # Convert Bass object to list of notes
            bass_notes = bass_line.notes
            tracks.append(
<<<<<<< HEAD
                Track(name="Bass", notes=bass_notes, channel=2, instrument=32)
=======
                Track(
                    name="Bass", notes=bass_notes, channel=2, instrument=32
                )
>>>>>>> origin/dev
            )

        if drums is not None:
            # Convert Drums object to list of notes
            drum_notes = drums.notes
            tracks.append(
                Track(
                    name="Drums",
                    notes=drum_notes,
                    channel=9,
                    instrument=0,
                )
            )

        # Generate MIDI data
        midi_data = midi_generator.merge_tracks(tracks)

        # Extract harmony chords for response
        harmony_chords = harmony.chords if harmony is not None else None

<<<<<<< HEAD
        return GenerationResponse(
            harmony=harmony_chords,
            bass_line=bass_line.notes if bass_line is not None else None,
            drums=drums.notes if drums is not None else None,
            midi_data=(
                base64.b64encode(midi_data).decode("utf-8") if midi_data else None  # noqa: E501
            ),
            duration=4.0,  # Calculate actual duration
            success=True,
        )  # noqa: E501
=======
        return LegacyGenerationResponse(
            harmony=harmony_chords,
            bass_line=bass_line.notes if bass_line is not None else None,
            drums=drums.notes if drums is not None else None,
            midi_data=base64.b64encode(midi_data).decode('utf-8') if midi_data else None,
            duration=4.0,  # Calculate actual duration
            success=True,
        )
>>>>>>> origin/dev

    except HTTPException:
        raise
    except Exception as e:
<<<<<<< HEAD
        raise HTTPException(
            status_code=500, detail=f"Generation failed: {str(e)}"
        )
=======
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
>>>>>>> origin/dev


# AI Model Management Endpoints

<<<<<<< HEAD

=======
>>>>>>> origin/dev
@router.post("/ai/models/register")
async def register_ai_model(
    config: ModelConfig,
    music_generator: MusicGenerator = Depends(get_music_generator),
) -> dict:
    """Register a new AI model."""
    try:
        success = music_generator.register_ai_model(config)
        if success:
            return {
                "message": f"AI model {config.name} registered successfully",
                "model_name": config.name,
<<<<<<< HEAD
                "model_type": config.type.value,
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to register AI model {config.name}",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to register AI model: {str(e)}"
=======
                "model_type": config.type.value
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to register AI model {config.name}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to register AI model: {str(e)}"
>>>>>>> origin/dev
        )


@router.post("/ai/models/{model_name}/set-default")
async def set_default_ai_model(
    model_name: str,
    music_generator: MusicGenerator = Depends(get_music_generator),
) -> dict:
    """Set the default AI model."""
    try:
        success = music_generator.set_default_ai_model(model_name)
        if success:
            return {
                "message": f"Default AI model set to {model_name}",
<<<<<<< HEAD
                "default_model": model_name,
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"AI model {model_name} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to set default AI model: {str(e)}"
=======
                "default_model": model_name
            }
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"AI model {model_name} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to set default AI model: {str(e)}"
>>>>>>> origin/dev
        )


@router.get("/ai/models")
async def list_ai_models(
    music_generator: MusicGenerator = Depends(get_music_generator),
) -> dict:
    """List available AI models."""
    try:
        models = music_generator.list_ai_models()
        return {
            "models": models,
            "count": len(models),
<<<<<<< HEAD
            "ai_models_enabled": music_generator.use_ai_models,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list AI models: {str(e)}"
=======
            "ai_models_enabled": music_generator.use_ai_models
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to list AI models: {str(e)}"
>>>>>>> origin/dev
        )


@router.post("/ai/generate/harmony")
async def generate_harmony_ai(
<<<<<<< HEAD
    request: AIModelGenerationRequest,
    model_name: Optional[str] = None,
    music_generator: MusicGenerator = Depends(get_music_generator),
) -> AIModelGenerationResponse:
=======
    request: LegacyGenerationRequest,
    model_name: Optional[str] = None,
    music_generator: MusicGenerator = Depends(get_music_generator),
) -> LegacyGenerationResponse:
>>>>>>> origin/dev
    """Generate harmony using AI models."""
    try:
        response = music_generator.ai_model_manager.generate_harmony(
            model_name, request
        )
        return response
    except Exception as e:
        raise HTTPException(
<<<<<<< HEAD
            status_code=500, detail=f"AI harmony generation failed: {str(e)}"
=======
            status_code=500, 
            detail=f"AI harmony generation failed: {str(e)}"
>>>>>>> origin/dev
        )


@router.post("/ai/generate/bass")
async def generate_bass_ai(
<<<<<<< HEAD
    request: AIModelGenerationRequest,
    model_name: Optional[str] = None,
    music_generator: MusicGenerator = Depends(get_music_generator),
) -> AIModelGenerationResponse:
=======
    request: LegacyGenerationRequest,
    model_name: Optional[str] = None,
    music_generator: MusicGenerator = Depends(get_music_generator),
) -> LegacyGenerationResponse:
>>>>>>> origin/dev
    """Generate bass using AI models."""
    try:
        response = music_generator.ai_model_manager.generate_bass(
            model_name, request
        )
        return response
    except Exception as e:
        raise HTTPException(
<<<<<<< HEAD
            status_code=500, detail=f"AI bass generation failed: {str(e)}"
=======
            status_code=500, 
            detail=f"AI bass generation failed: {str(e)}"
>>>>>>> origin/dev
        )


@router.post("/ai/generate/drums")
async def generate_drums_ai(
<<<<<<< HEAD
    request: AIModelGenerationRequest,
    model_name: Optional[str] = None,
    music_generator: MusicGenerator = Depends(get_music_generator),
) -> AIModelGenerationResponse:
=======
    request: LegacyGenerationRequest,
    model_name: Optional[str] = None,
    music_generator: MusicGenerator = Depends(get_music_generator),
) -> LegacyGenerationResponse:
>>>>>>> origin/dev
    """Generate drums using AI models."""
    try:
        response = music_generator.ai_model_manager.generate_drums(
            model_name, request
        )
        return response
    except Exception as e:
        raise HTTPException(
<<<<<<< HEAD
            status_code=500, detail=f"AI drum generation failed: {str(e)}"
=======
            status_code=500, 
            detail=f"AI drum generation failed: {str(e)}"
>>>>>>> origin/dev
        )


@router.post("/ai/analyze")
async def analyze_music_ai(
    midi_data: bytes,
    model_name: Optional[str] = None,
    music_generator: MusicGenerator = Depends(get_music_generator),
<<<<<<< HEAD
) -> AIModelGenerationResponse:
=======
) -> LegacyGenerationResponse:
>>>>>>> origin/dev
    """Analyze music using AI models."""
    try:
        response = music_generator.ai_model_manager.analyze_music(
            model_name, midi_data
        )
        return response
    except Exception as e:
        raise HTTPException(
<<<<<<< HEAD
            status_code=500, detail=f"AI music analysis failed: {str(e)}"
=======
            status_code=500, 
            detail=f"AI music analysis failed: {str(e)}"
>>>>>>> origin/dev
        )


# Plugin Management Endpoints

<<<<<<< HEAD

=======
>>>>>>> origin/dev
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
<<<<<<< HEAD
        raise HTTPException(
            status_code=500, detail=f"Failed to list plugins: {str(e)}"
        )
=======
        raise HTTPException(status_code=500, detail=f"Failed to list plugins: {str(e)}")
>>>>>>> origin/dev


@router.get("/plugins/recommendations")
async def get_plugin_recommendations(
    style: str,
    instrument: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> dict:
    """Get plugin recommendations for a style and instrument."""
    try:
<<<<<<< HEAD
        recommendations = plugin_manager.get_plugin_recommendations(
            style, instrument
        )
=======
        recommendations = plugin_manager.get_plugin_recommendations(style, instrument)
>>>>>>> origin/dev
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
<<<<<<< HEAD
    plugin_name: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
=======
    plugin_name: str, plugin_manager: PluginManager = Depends(get_plugin_manager)
>>>>>>> origin/dev
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
<<<<<<< HEAD
        raise HTTPException(
            status_code=500, detail=f"Failed to load plugin: {str(e)}"
        )
=======
        raise HTTPException(status_code=500, detail=f"Failed to load plugin: {str(e)}")
>>>>>>> origin/dev


@router.get("/plugins/{plugin_name}/parameters")
async def get_plugin_parameters(
<<<<<<< HEAD
    plugin_name: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
=======
    plugin_name: str, plugin_manager: PluginManager = Depends(get_plugin_manager)
>>>>>>> origin/dev
) -> dict:
    """Get plugin parameters."""
    try:
        # Check if plugin exists first
        plugin_info = plugin_manager.get_plugin_info(plugin_name)
        if plugin_info is None:
            raise HTTPException(
                status_code=404, detail=f"Plugin {plugin_name} not found"
            )
<<<<<<< HEAD

=======
        
>>>>>>> origin/dev
        parameters = plugin_manager.get_plugin_parameters(plugin_name)
        if parameters is not None:
            return {
                "plugin_name": plugin_name,
                "parameters": parameters,
            }
        else:
            raise HTTPException(
                status_code=400, detail=f"Plugin {plugin_name} is not loaded"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
<<<<<<< HEAD
            status_code=500,
            detail=f"Failed to get plugin parameters: {str(e)}",  # noqa: E501
=======
            status_code=500, detail=f"Failed to get plugin parameters: {str(e)}"
>>>>>>> origin/dev
        )


@router.post("/plugins/{plugin_name}/parameters/{parameter_name}")
async def set_plugin_parameter(
    plugin_name: str,
    parameter_name: str,
    value: float,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> dict:
    """Set a plugin parameter."""
    try:
<<<<<<< HEAD
        success = plugin_manager.set_plugin_parameter(
            plugin_name, parameter_name, value
        )
        if success:
            return {
                "message": f"Parameter {parameter_name} set to {value} for plugin {plugin_name}"  # noqa: E501
=======
        success = plugin_manager.set_plugin_parameter(plugin_name, parameter_name, value)
        if success:
            return {
                "message": f"Parameter {parameter_name} set to {value} for plugin {plugin_name}"
>>>>>>> origin/dev
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"Plugin {plugin_name} not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to set plugin parameter: {str(e)}"
        )


@router.get("/plugins/{plugin_name}/presets")
async def get_plugin_presets(
<<<<<<< HEAD
    plugin_name: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
=======
    plugin_name: str, plugin_manager: PluginManager = Depends(get_plugin_manager)
>>>>>>> origin/dev
) -> dict:
    """Get plugin presets."""
    try:
        # Check if plugin exists first
        plugin_info = plugin_manager.get_plugin_info(plugin_name)
        if plugin_info is None:
            raise HTTPException(
                status_code=404, detail=f"Plugin {plugin_name} not found"
            )
<<<<<<< HEAD

=======
        
>>>>>>> origin/dev
        presets = plugin_manager.get_plugin_presets(plugin_name)
        if presets is not None:
            return {
                "plugin_name": plugin_name,
                "presets": presets,
            }
        else:
            raise HTTPException(
                status_code=400, detail=f"Plugin {plugin_name} is not loaded"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get plugin presets: {str(e)}"
        )


@router.get("/plugins/{plugin_name}")
async def get_plugin_info(
<<<<<<< HEAD
    plugin_name: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
=======
    plugin_name: str, plugin_manager: PluginManager = Depends(get_plugin_manager)
>>>>>>> origin/dev
) -> dict:
    """Get detailed plugin information."""
    try:
        plugin_info = plugin_manager.get_plugin_info(plugin_name)
        if plugin_info is not None:
            return {
                "name": plugin_info.name,
                "version": plugin_info.version,
                "manufacturer": plugin_info.manufacturer,
                "plugin_type": plugin_info.plugin_type,
                "category": plugin_info.category,
                "file_path": plugin_info.file_path,
                "is_loaded": plugin_info.is_loaded,
<<<<<<< HEAD
                "description": getattr(plugin_info, "description", ""),
=======
                "description": getattr(plugin_info, 'description', ''),
>>>>>>> origin/dev
                "parameters": plugin_info.parameters,
                "presets": plugin_info.presets,
            }
        else:
            raise HTTPException(
                status_code=404, detail=f"Plugin {plugin_name} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get plugin info: {str(e)}"
        )


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "Merlai Music Generation API"}


@router.get("/config")
async def get_config() -> dict:
    """Get current configuration."""
    return {
        "temperature": 0.8,
        "max_length": 1024,
        "batch_size": 4,
        "top_p": 0.9,
        "top_k": 50,
<<<<<<< HEAD
        "repetition_penalty": 1.1,
=======
        "repetition_penalty": 1.1
>>>>>>> origin/dev
    }


@router.post("/config")
async def update_config(config_update: dict) -> dict:
    """Update configuration."""
    try:
        # Validate config update
<<<<<<< HEAD
        valid_keys = {
            "temperature",
            "max_length",
            "batch_size",
            "top_p",
            "top_k",
            "repetition_penalty",
        }
        invalid_keys = set(config_update.keys()) - valid_keys

        if invalid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration keys: {list(invalid_keys)}",
            )

        # Validate types
        for key, value in config_update.items():
            if key in [
                "temperature",
                "top_p",
                "repetition_penalty",
            ] and not isinstance(value, (int, float)):
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid type for {key}: expected number, got {type(value).__name__}",  # noqa: E501
                )
            elif key in [
                "max_length",
                "batch_size",
                "top_k",
            ] and not isinstance(value, int):
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid type for {key}: expected integer, got {type(value).__name__}",  # noqa: E501
                )

        return {
            "message": "Configuration updated successfully",
            "updated_config": config_update,
        }

=======
        valid_keys = {"temperature", "max_length", "batch_size", "top_p", "top_k", "repetition_penalty"}
        invalid_keys = set(config_update.keys()) - valid_keys
        
        if invalid_keys:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid configuration keys: {list(invalid_keys)}"
            )
        
        # Validate types
        for key, value in config_update.items():
            if key in ["temperature", "top_p", "repetition_penalty"] and not isinstance(value, (int, float)):
                raise HTTPException(
                    status_code=422, 
                    detail=f"Invalid type for {key}: expected number, got {type(value).__name__}"
                )
            elif key in ["max_length", "batch_size", "top_k"] and not isinstance(value, int):
                raise HTTPException(
                    status_code=422, 
                    detail=f"Invalid type for {key}: expected integer, got {type(value).__name__}"
                )
        
        return {
            "message": "Configuration updated successfully",
            "updated_config": config_update
        }
        
>>>>>>> origin/dev
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
<<<<<<< HEAD
            status_code=500, detail=f"Failed to update configuration: {str(e)}"
=======
            status_code=500, 
            detail=f"Failed to update configuration: {str(e)}"
>>>>>>> origin/dev
        )


def _chord_to_notes(chord: Chord) -> List[Note]:
    """Convert a chord to individual notes."""
    notes = []
    if chord.voicing:
        for pitch in chord.voicing:
            note = Note(
                pitch=pitch,
                velocity=80,
                duration=chord.duration,
                start_time=chord.start_time,
            )
            notes.append(note)
    else:
        # Default voicing for major chord
        root = chord.root
        third = root + 4 if chord.chord_type == "major" else root + 3
        fifth = root + 7
        for pitch in [root, third, fifth]:
            note = Note(
                pitch=pitch,
                velocity=80,
                duration=chord.duration,
                start_time=chord.start_time,
            )
            notes.append(note)
    return notes
