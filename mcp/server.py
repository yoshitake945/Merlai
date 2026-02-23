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

# Merlaiのコア機能をインポート
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from merlai.core.music import MusicGenerator
from merlai.core.midi import MIDIGenerator
from merlai.core.types import Note, Melody, Chord, Harmony

logger = logging.getLogger(__name__)

# グローバルな状態管理
current_midi_data: Optional[bytes] = None
current_melody: Optional[Melody] = None
music_generator = MusicGenerator(use_ai_models=False)
midi_generator = MIDIGenerator()


# MCPサーバーのインスタンス作成
mcp_server = Server("merlai-composition-assistant")


@mcp_server.list_resources()
async def list_resources() -> list[Resource]:
    """
    利用可能なリソースのリストを返す。
    
    Returns:
        - midi://current - 現在のMIDIファイル
        - composition://suggestions - 作曲支援の提案
    """
    resources = [
        Resource(
            uri="midi://current",
            name="Current MIDI File",
            description="現在作業中のMIDIファイルの情報",
            mimeType="application/json",
        ),
        Resource(
            uri="composition://suggestions",
            name="Composition Suggestions",
            description="現在のメロディに基づいた作曲支援の提案",
            mimeType="application/json",
        ),
        Resource(
            uri="composition://chord-progressions",
            name="Chord Progressions",
            description="人気のあるコード進行のライブラリ",
            mimeType="application/json",
        ),
    ]
    
    return resources


@mcp_server.read_resource()
async def read_resource(uri: str) -> str:
    """
    リソースの内容を読み込む。
    
    Args:
        uri: リソースのURI
        
    Returns:
        リソースの内容（JSON文字列）
    """
    if uri == "midi://current":
        if current_midi_data is None:
            return json.dumps({
                "status": "no_file",
                "message": "MIDIファイルが読み込まれていません",
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
                "message": "メロディが設定されていません",
                "suggestions": []
            })
        
        # コード進行を提案
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
        # 人気のコード進行ライブラリ
        progressions = {
            "pop": [
                {"name": "I-V-vi-IV", "chords": ["C", "G", "Am", "F"], "description": "最も人気のあるポップス進行"},
                {"name": "I-vi-IV-V", "chords": ["C", "Am", "F", "G"], "description": "50年代ドゥーワップ"},
                {"name": "vi-IV-I-V", "chords": ["Am", "F", "C", "G"], "description": "感情的なポップス"},
            ],
            "jazz": [
                {"name": "ii-V-I", "chords": ["Dm7", "G7", "Cmaj7"], "description": "ジャズの基本"},
                {"name": "I-VI-ii-V", "chords": ["Cmaj7", "A7", "Dm7", "G7"], "description": "ジャズスタンダード"},
            ],
            "rock": [
                {"name": "I-IV-V", "chords": ["C", "F", "G"], "description": "ロックの基本"},
                {"name": "I-bVII-IV", "chords": ["C", "Bb", "F"], "description": "モダンロック"},
            ],
        }
        
        return json.dumps(progressions)
    
    return json.dumps({"error": f"Unknown resource: {uri}"})


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """
    利用可能なツールのリストを返す。
    """
    tools = [
        Tool(
            name="read_midi_file",
            description="MIDIファイルを読み込んで解析します",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "読み込むMIDIファイルのパス",
                    }
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="write_midi_file",
            description="MIDIファイルを生成して保存します",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "保存先のMIDIファイルパス",
                    },
                    "melody": {
                        "type": "array",
                        "description": "メロディノートの配列",
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
            description="現在のメロディに合うコード進行を提案します",
            inputSchema={
                "type": "object",
                "properties": {
                    "melody": {
                        "type": "array",
                        "description": "メロディノートの配列",
                    },
                    "style": {
                        "type": "string",
                        "description": "音楽スタイル（pop, rock, jazz, classical, electronic）",
                        "enum": ["pop", "rock", "jazz", "classical", "electronic"],
                    },
                    "key": {
                        "type": "string",
                        "description": "キー（C, D, E, F, G, A, B）",
                    },
                },
                "required": ["melody", "style"],
            },
        ),
        Tool(
            name="complete_melody",
            description="部分的なメロディを補完します",
            inputSchema={
                "type": "object",
                "properties": {
                    "partial_melody": {
                        "type": "array",
                        "description": "部分的なメロディノート",
                    },
                    "target_length": {
                        "type": "number",
                        "description": "目標の長さ（秒）",
                    },
                    "style": {
                        "type": "string",
                        "description": "音楽スタイル",
                    },
                },
                "required": ["partial_melody"],
            },
        ),
        Tool(
            name="generate_full_arrangement",
            description="メロディから完全なアレンジ（ハーモニー、ベース、ドラム）を生成します",
            inputSchema={
                "type": "object",
                "properties": {
                    "melody": {
                        "type": "array",
                        "description": "メロディノート",
                    },
                    "style": {
                        "type": "string",
                        "description": "音楽スタイル",
                    },
                    "tempo": {
                        "type": "integer",
                        "description": "テンポ（BPM）",
                    },
                    "key": {
                        "type": "string",
                        "description": "キー",
                    },
                },
                "required": ["melody", "style", "tempo", "key"],
            },
        ),
        Tool(
            name="analyze_midi",
            description="MIDIファイルを分析して、キー、コード進行、テンポなどを検出します",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "分析するMIDIファイルのパス",
                    }
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="send_to_logic_pro",
            description="生成したMIDIをLogic Proに送信します（AppleScript経由）",
            inputSchema={
                "type": "object",
                "properties": {
                    "midi_file_path": {
                        "type": "string",
                        "description": "Logic Proに送信するMIDIファイルのパス",
                    },
                    "track_name": {
                        "type": "string",
                        "description": "トラック名（オプション）",
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
    ツールを実行する。
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
                        "error": f"ファイルが見つかりません: {file_path}",
                        "success": False
                    })
                )]
            
            with open(file_path, "rb") as f:
                current_midi_data = f.read()
            
            # 簡易的なMIDI情報の抽出
            result = {
                "success": True,
                "file_path": file_path,
                "size": len(current_midi_data),
                "message": f"MIDIファイルを読み込みました: {file_path}",
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        elif name == "write_midi_file":
            file_path = arguments["file_path"]
            melody_data = arguments["melody"]
            
            # メロディノートを作成
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
                "message": f"MIDIファイルを保存しました: {file_path}",
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
                "message": f"{len(chord_progression)}個のコードを提案しました",
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
            
            # 現在のメロディの長さ
            current_length = max(n.start_time + n.duration for n in notes)
            
            # 補完が必要な長さ
            remaining_length = target_length - current_length
            
            if remaining_length > 0:
                # 簡易的な補完: 最後のノートパターンを繰り返す
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
                "message": f"{len(new_notes)}個のノートを追加してメロディを補完しました",
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
                "message": f"完全なアレンジを生成しました（ハーモニー: {len(harmony.chords)}コード、ベース: {len(bass.notes)}ノート、ドラム: {len(drums.notes)}ノート）",
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        elif name == "analyze_midi":
            file_path = arguments["file_path"]
            
            if not os.path.exists(file_path):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"ファイルが見つかりません: {file_path}",
                        "success": False
                    })
                )]
            
            # MIDIファイルを読み込んで分析
            with open(file_path, "rb") as f:
                midi_data = f.read()
            
            # 簡易的な分析結果
            result = {
                "success": True,
                "file_path": file_path,
                "size": len(midi_data),
                "analysis": {
                    "estimated_key": "C",
                    "estimated_tempo": 120,
                    "estimated_style": "pop",
                    "note": "詳細な分析機能は今後実装予定",
                },
                "message": "MIDIファイルを分析しました",
            }
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        elif name == "send_to_logic_pro":
            midi_file_path = arguments["midi_file_path"]
            track_name = arguments.get("track_name", "Merlai Track")
            
            if not os.path.exists(midi_file_path):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"MIDIファイルが見つかりません: {midi_file_path}",
                        "success": False
                    })
                )]
            
            # Logic Proに送信（AppleScriptを使用）
            # 注: これは macOS でのみ動作します
            applescript = f'''
tell application "Logic Pro"
    activate
    -- MIDIファイルをインポート
    -- 注: 実際の実装では、より詳細な制御が必要
    set trackName to "{track_name}"
    set midiFile to "{midi_file_path}"
end tell
'''
            
            result = {
                "success": True,
                "midi_file": midi_file_path,
                "track_name": track_name,
                "platform": "macOS required",
                "message": f"Logic Proへの送信準備完了: {track_name}",
                "note": "実際の送信にはmacOS環境とLogic Proが必要です",
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
    """MCPサーバーを起動する。"""
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
