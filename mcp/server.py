"""
MCP Server implementation for Merlai.

Provides tools and resources for:
- MIDI file manipulation
- DAW integration (Logic Pro, Ableton, etc.)
- Real-time composition assistance
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import Merlai core functionality
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from merlai.core.music import MusicGenerator
from merlai.core.midi import MIDIGenerator
from merlai.core.types import Note, Melody, Chord, Harmony

logger = logging.getLogger(__name__)

# Global state management
current_midi_data: Optional[bytes] = None
current_melody: Optional[Melody] = None
music_generator = MusicGenerator(use_ai_models=False)
midi_generator = MIDIGenerator()


# Create MCP server instance
mcp_server = Server("merlai-composition-assistant")


@mcp_server.list_resources()
async def list_resources() -> list[Resource]:
    """
    List available resources.
    
    Returns:
        - midi://current - Current MIDI file
        - composition://suggestions - Composition suggestions
    """
    resources = [
        Resource(
            uri="midi://current",
            name="Current MIDI File",
            description="Information about the current MIDI file being worked on",
            mimeType="application/json",
        ),
        Resource(
            uri="composition://suggestions",
            name="Composition Suggestions",
            description="Composition assistance suggestions based on current melody",
            mimeType="application/json",
        ),
        Resource(
            uri="composition://chord-progressions",
            name="Chord Progressions",
            description="Library of popular chord progressions",
            mimeType="application/json",
        ),
    ]
    
    return resources


@mcp_server.read_resource()
async def read_resource(uri: str) -> str:
    """
    Read resource content.
    
    Args:
        uri: Resource URI
        
    Returns:
        Resource content (JSON string)
    """
    if uri == "midi://current":
        if current_midi_data is None:
            return json.dumps({
                "status": "no_file",
                "message": "No MIDI file loaded",
                "data": None
            })
        
        return json.dumps({
            "status": "ok",
            "size": len(current_midi_data),
            "format": "MIDI",
            "melody_notes": len(current_melody.notes) if current_melody else 0,
        })
    
    elif uri == "composition://suggestions":
        if current_melody is None:
            return json.dumps({
                "status": "no_melody",
                "message": "No melody set",
                "suggestions": []
            })
        
        # Suggest chord progression
        harmony = music_generator.generate_harmony(current_melody, style="pop")
        
        suggestions = {
            "status": "ok",
            "chord_progression": [
                {
                    "root": chord.root,
                    "type": chord.chord_type,
                    "start_time": chord.start_time,
                    "duration": chord.duration,
                }
                for chord in harmony.chords
            ],
            "suggested_key": harmony.key,
            "style": harmony.style,
        }
        
        return json.dumps(suggestions)
    
    elif uri == "composition://chord-progressions":
        # Popular chord progression library
        progressions = {
            "pop": [
                {"name": "I-V-vi-IV", "chords": ["C", "G", "Am", "F"], "description": "Most popular pop progression"},
                {"name": "I-vi-IV-V", "chords": ["C", "Am", "F", "G"], "description": "50s doo-wop"},
                {"name": "vi-IV-I-V", "chords": ["Am", "F", "C", "G"], "description": "Emotional pop"},
            ],
            "jazz": [
                {"name": "ii-V-I", "chords": ["Dm7", "G7", "Cmaj7"], "description": "Jazz basics"},
                {"name": "I-VI-ii-V", "chords": ["Cmaj7", "A7", "Dm7", "G7"], "description": "Jazz standard"},
            ],
            "rock": [
                {"name": "I-IV-V", "chords": ["C", "F", "G"], "description": "Rock basics"},
                {"name": "I-bVII-IV", "chords": ["C", "Bb", "F"], "description": "Modern rock"},
            ],
        }
        
        return json.dumps(progressions)
    
    return json.dumps({"error": f"Unknown resource: {uri}"})


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available tools.
    """
    tools = [
        Tool(
            name="read_midi_file",
            description="Read and parse a MIDI file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the MIDI file to read",
                    }
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="write_midi_file",
            description="Generate and save a MIDI file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Destination path for the MIDI file",
                    },
                    "melody": {
                        "type": "array",
                        "description": "Array of melody notes",
                        "items": {
                            "type": "object",
                            "properties": {
                                "pitch": {"type": "integer"},
                                "velocity": {"type": "integer"},
                                "duration": {"type": "number"},
                                "start_time": {"type": "number"},
                            },
                        },
                    },
                },
                "required": ["file_path", "melody"],
            },
        ),
        Tool(
            name="suggest_chord_progression",
            description="Suggest chord progression matching the current melody",
            inputSchema={
                "type": "object",
                "properties": {
                    "melody": {
                        "type": "array",
                        "description": "Melody notesの配列",
                    },
                    "style": {
                        "type": "string",
                        "description": "Music style (pop, rock, jazz, classical, electronic)",
                        "enum": ["pop", "rock", "jazz", "classical", "electronic"],
                    },
                    "key": {
                        "type": "string",
                        "description": "Key (C, D, E, F, G, A, B)",
                    },
                },
                "required": ["melody", "style"],
            },
        ),
        Tool(
            name="complete_melody",
            description="Complete a partial melody",
            inputSchema={
                "type": "object",
                "properties": {
                    "partial_melody": {
                        "type": "array",
                        "description": "Partial melody notes",
                    },
                    "target_length": {
                        "type": "number",
                        "description": "Target length (seconds)",
                    },
                    "style": {
                        "type": "string",
                        "description": "Music style",
                    },
                },
                "required": ["partial_melody"],
            },
        ),
        Tool(
            name="generate_full_arrangement",
            description="Generate full arrangement (harmony, bass, drums) from melody",
            inputSchema={
                "type": "object",
                "properties": {
                    "melody": {
                        "type": "array",
                        "description": "Melody notes",
                    },
                    "style": {
                        "type": "string",
                        "description": "Music style",
                    },
                    "tempo": {
                        "type": "integer",
                        "description": "Tempo (BPM)",
                    },
                    "key": {
                        "type": "string",
                        "description": "Key",
                    },
                },
                "required": ["melody", "style", "tempo", "key"],
            },
        ),
        Tool(
            name="analyze_midi",
            description="MIDIファイルを分析して、Key、コード進行、テンポなどを検出します",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to MIDI file to analyze",
                    }
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="send_to_logic_pro",
            description="Send generated MIDI to Logic Pro (via AppleScript)",
            inputSchema={
                "type": "object",
                "properties": {
                    "midi_file_path": {
                        "type": "string",
                        "description": "Path to MIDI file to send to Logic Pro",
                    },
                    "track_name": {
                        "type": "string",
                        "description": "Track name (optional)",
                    },
                },
                "required": ["midi_file_path"],
            },
        ),
    ]
    
    return tools


@mcp_server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """
    Execute tool.
    """
    global current_midi_data, current_melody
    
    try:
        if name == "read_midi_file":
            file_path = arguments["file_path"]
            
            # MIDIファイルを読み込む
            if not os.path.exists(file_path):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"File not found: {file_path}",
                        "success": False
                    })
                )]
            
            with open(file_path, "rb") as f:
                current_midi_data = f.read()
            
            # Extract basic MIDI information
            result = {
                "success": True,
                "file_path": file_path,
                "size": len(current_midi_data),
                "message": f"MIDI file loaded: {file_path}",
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        elif name == "write_midi_file":
            file_path = arguments["file_path"]
            melody_data = arguments["melody"]
            
            # Melody notesを作成
            notes = [
                Note(
                    pitch=note["pitch"],
                    velocity=note.get("velocity", 80),
                    duration=note["duration"],
                    start_time=note["start_time"]
                )
                for note in melody_data
            ]
            
            current_melody = Melody(notes=notes, tempo=120, key="C")
            
            # MIDIファイルを生成
            midi_data = midi_generator.create_midi_from_notes(notes, tempo=120)
            current_midi_data = midi_data
            
            # ファイルに保存
            with open(file_path, "wb") as f:
                f.write(midi_data)
            
            result = {
                "success": True,
                "file_path": file_path,
                "notes_count": len(notes),
                "size": len(midi_data),
                "message": f"MIDI file saved: {file_path}",
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        elif name == "suggest_chord_progression":
            melody_data = arguments["melody"]
            style = arguments.get("style", "pop")
            key = arguments.get("key", "C")
            
            # メロディを作成
            notes = [
                Note(
                    pitch=note["pitch"],
                    velocity=note.get("velocity", 80),
                    duration=note["duration"],
                    start_time=note["start_time"]
                )
                for note in melody_data
            ]
            
            melody = Melody(notes=notes, tempo=120, key=key)
            current_melody = melody
            
            # ハーモニーを生成
            harmony = music_generator.generate_harmony(melody, style=style)
            
            # コード進行を返す
            chord_progression = [
                {
                    "root_note": chord.root,
                    "chord_type": chord.chord_type,
                    "start_time": chord.start_time,
                    "duration": chord.duration,
                    "voicing": chord.voicing if chord.voicing else [],
                }
                for chord in harmony.chords
            ]
            
            result = {
                "success": True,
                "style": style,
                "key": key,
                "chord_progression": chord_progression,
                "suggestion_count": len(chord_progression),
                "message": f"{len(chord_progression)} chord suggestions generated",
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        elif name == "complete_melody":
            partial_melody_data = arguments["partial_melody"]
            target_length = arguments.get("target_length", 8.0)
            style = arguments.get("style", "pop")
            
            # 部分的なメロディを作成
            notes = [
                Note(
                    pitch=note["pitch"],
                    velocity=note.get("velocity", 80),
                    duration=note["duration"],
                    start_time=note["start_time"]
                )
                for note in partial_melody_data
            ]
            
            melody = Melody(notes=notes, tempo=120, key="C")
            
            # Current melody length
            current_length = max(n.start_time + n.duration for n in notes)
            
            # Length needed for completion
            remaining_length = target_length - current_length
            
            if remaining_length > 0:
                # Simple completion: repeat the last note pattern
                last_notes = notes[-min(4, len(notes)):]
                pattern_length = max(n.start_time + n.duration for n in last_notes) - min(n.start_time for n in last_notes)
                
                new_notes = []
                offset = current_length
                
                while offset < target_length:
                    for note in last_notes:
                        new_note = Note(
                            pitch=note.pitch,
                            velocity=note.velocity,
                            duration=note.duration,
                            start_time=offset + (note.start_time - last_notes[0].start_time)
                        )
                        new_notes.append(new_note)
                    offset += pattern_length
            else:
                new_notes = []
            
            result = {
                "success": True,
                "original_notes": len(notes),
                "added_notes": len(new_notes),
                "total_notes": len(notes) + len(new_notes),
                "original_length": current_length,
                "final_length": target_length,
                "completed_melody": [
                    {
                        "pitch": n.pitch,
                        "velocity": n.velocity,
                        "duration": n.duration,
                        "start_time": n.start_time,
                    }
                    for n in notes + new_notes
                ],
                "message": f"{len(new_notes)} notes added to complete melody",
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        elif name == "generate_full_arrangement":
            melody_data = arguments["melody"]
            style = arguments["style"]
            tempo = arguments["tempo"]
            key = arguments["key"]
            
            # メロディを作成
            notes = [
                Note(
                    pitch=note["pitch"],
                    velocity=note.get("velocity", 80),
                    duration=note["duration"],
                    start_time=note["start_time"]
                )
                for note in melody_data
            ]
            
            melody = Melody(notes=notes, tempo=tempo, key=key)
            current_melody = melody
            
            # 完全なアレンジを生成
            harmony = music_generator.generate_harmony(melody, style=style)
            bass = music_generator.generate_bass_line(melody, harmony)
            drums = music_generator.generate_drums(melody, tempo=tempo)
            
            result = {
                "success": True,
                "arrangement": {
                    "melody": {
                        "notes_count": len(melody.notes),
                        "notes": [{"pitch": n.pitch, "velocity": n.velocity, "duration": n.duration, "start_time": n.start_time} for n in melody.notes]
                    },
                    "harmony": {
                        "chords_count": len(harmony.chords),
                        "chords": [
                            {
                                "root": c.root,
                                "type": c.chord_type,
                                "start_time": c.start_time,
                                "duration": c.duration,
                            }
                            for c in harmony.chords
                        ],
                    },
                    "bass": {
                        "notes_count": len(bass.notes),
                        "notes": [{"pitch": n.pitch, "velocity": n.velocity, "duration": n.duration, "start_time": n.start_time} for n in bass.notes]
                    },
                    "drums": {
                        "notes_count": len(drums.notes),
                        "notes": [{"pitch": n.pitch, "velocity": n.velocity, "duration": n.duration, "start_time": n.start_time} for n in drums.notes]
                    },
                },
                "style": style,
                "tempo": tempo,
                "key": key,
                "message": f"Full arrangement generated (Harmony: {len(harmony.chords)} chords, Bass: {len(bass.notes)} notes, Drums: {len(drums.notes)} notes)",
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        elif name == "analyze_midi":
            file_path = arguments["file_path"]
            
            if not os.path.exists(file_path):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"File not found: {file_path}",
                        "success": False
                    })
                )]
            
            # MIDIファイルを読み込んで分析
            with open(file_path, "rb") as f:
                midi_data = f.read()
            
            # Basic analysis results
            result = {
                "success": True,
                "file_path": file_path,
                "size": len(midi_data),
                "analysis": {
                    "estimated_key": "C",
                    "estimated_tempo": 120,
                    "estimated_style": "pop",
                    "note": "Detailed analysis features coming soon",
                },
                "message": "MIDI file analyzed",
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        elif name == "send_to_logic_pro":
            midi_file_path = arguments["midi_file_path"]
            track_name = arguments.get("track_name", "Merlai Track")
            
            if not os.path.exists(midi_file_path):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"MIDIFile not found: {midi_file_path}",
                        "success": False
                    })
                )]
            
            # Logic Proに送信（AppleScriptを使用）
            # 注: これは macOS でのみ動作します
            applescript = f'''
tell application "Logic Pro"
    activate
    -- Import MIDI file
    -- Note: Actual implementation requires more detailed control
    set trackName to "{track_name}"
    set midiFile to "{midi_file_path}"
end tell
'''
            
            result = {
                "success": True,
                "midi_file": midi_file_path,
                "track_name": track_name,
                "platform": "macOS required",
                "message": f"Ready to send to Logic Pro: {track_name}",
                "note": "Actual sending requires macOS and Logic Pro",
                "applescript": applescript,
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}",
                    "success": False
                })
            )]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "success": False,
                "tool": name,
            })
        )]


async def main():
    """Start MCP server."""
    logger.info("Starting Merlai MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
