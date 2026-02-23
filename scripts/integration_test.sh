#!/bin/bash
# 統合動作確認スクリプト
# このスクリプトは、Merlaiの主要機能を実際に動作させて確認します

set -e

echo "========================================="
echo "🎵 Merlai 統合動作確認"
echo "========================================="
echo ""

# PATH設定
export PATH="/home/ubuntu/.local/bin:$PATH"

# カラー出力設定
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# テスト用の一時ディレクトリ
TEST_DIR=$(mktemp -d)
echo "📁 テスト用ディレクトリ: $TEST_DIR"
echo ""

# クリーンアップ関数
cleanup() {
    echo ""
    echo "🧹 クリーンアップ中..."
    rm -rf "$TEST_DIR"
    echo "✅ クリーンアップ完了"
}
trap cleanup EXIT

# テスト結果を記録
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# テスト実行関数
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${BLUE}テスト $TOTAL_TESTS: $test_name${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ 成功${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo ""
        return 0
    else
        echo -e "${YELLOW}⚠️  失敗 (継続)${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo ""
        return 1
    fi
}

echo "========================================="
echo "1. 環境確認"
echo "========================================="
echo ""

run_test "Python バージョン確認" "python3 --version"
run_test "Merlai パッケージインストール確認" "python3 -c 'import merlai; print(\"Merlai version:\", merlai.__version__)'"

echo "========================================="
echo "2. コア機能テスト"
echo "========================================="
echo ""

# テスト: Note作成
run_test "Note オブジェクト作成" "python3 -c '
from merlai.core.types import Note
note = Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)
print(f\"Note created: pitch={note.pitch}, duration={note.duration}\")
'"

# テスト: Melody作成
run_test "Melody オブジェクト作成" "python3 -c '
from merlai.core.types import Note, Melody
notes = [
    Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
    Note(pitch=62, velocity=80, duration=1.0, start_time=1.0),
]
melody = Melody(notes=notes, tempo=120, key=\"C\")
print(f\"Melody created: {len(melody.notes)} notes, tempo={melody.tempo}\")
'"

# テスト: MIDI生成
run_test "MIDI ファイル生成" "python3 -c '
from merlai.core.types import Note
from merlai.core.midi import MIDIGenerator
notes = [
    Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
    Note(pitch=64, velocity=80, duration=1.0, start_time=1.0),
    Note(pitch=67, velocity=80, duration=1.0, start_time=2.0),
]
midi_gen = MIDIGenerator()
midi_data = midi_gen.create_midi_from_notes(notes, tempo=120)
with open(\"$TEST_DIR/test.mid\", \"wb\") as f:
    f.write(midi_data)
import os
print(f\"MIDI file created: {os.path.getsize(\"$TEST_DIR/test.mid\")} bytes\")
'"

# テスト: 音楽生成
run_test "音楽生成 (ハーモニー・ベース・ドラム)" "python3 -c '
from unittest.mock import patch
from merlai.core.types import Note, Melody
from merlai.core.music import MusicGenerator

with patch(\"merlai.core.music.MusicGenerator._initialize_default_models\"):
    music_gen = MusicGenerator()
    
    melody = Melody(
        notes=[
            Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
            Note(pitch=62, velocity=80, duration=1.0, start_time=1.0),
        ],
        tempo=120,
        key=\"C\"
    )
    
    # ハーモニー生成
    with patch(\"merlai.core.music.AutoTokenizer\"), patch(\"merlai.core.music.AutoModelForCausalLM\"):
        harmony = music_gen.generate_harmony(melody, style=\"pop\")
        print(f\"Harmony generated: {len(harmony.chords)} chords\")
    
    # ベース生成
    bass = music_gen.generate_bass_line(melody, harmony)
    print(f\"Bass generated: {len(bass.notes)} notes\")
    
    # ドラム生成
    drums = music_gen.generate_drums(melody, tempo=120)
    print(f\"Drums generated: {len(drums.notes)} notes\")
'"

echo "========================================="
echo "3. API機能テスト (モック)"
echo "========================================="
echo ""

# テスト: GenerationRequest作成
run_test "GenerationRequest オブジェクト作成" "python3 -c '
from merlai.core.types import GenerationRequest, NoteData

request = GenerationRequest(
    melody=[
        NoteData(pitch=60, velocity=80, duration=1.0, start_time=0.0),
    ],
    style=\"pop\",
    tempo=120,
    key=\"C\",
)
print(f\"Request created: {len(request.melody)} notes, style={request.style}\")
'"

echo "========================================="
echo "4. プラグイン機能テスト"
echo "========================================="
echo ""

run_test "PluginManager 初期化" "python3 -c '
from merlai.core.plugins import PluginManager
plugin_mgr = PluginManager()
plugins = plugin_mgr.scan_plugins()
print(f\"Plugin manager initialized: {len(plugins)} plugins found\")
'"

run_test "プラグイン推奨取得" "python3 -c '
from merlai.core.plugins import PluginManager
plugin_mgr = PluginManager()
recommendations = plugin_mgr.get_plugin_recommendations(\"pop\", \"piano\")
print(f\"Recommendations: {len(recommendations)} plugins\")
'"

echo "========================================="
echo "5. MIDI処理機能テスト"
echo "========================================="
echo ""

run_test "ノートのクオンタイズ" "python3 -c '
from merlai.core.types import Note
from merlai.core.midi import MIDIGenerator

notes = [
    Note(pitch=60, velocity=80, duration=0.33, start_time=0.11),
    Note(pitch=62, velocity=80, duration=0.48, start_time=0.99),
]
midi_gen = MIDIGenerator()
quantized = midi_gen.quantize_notes(notes, grid_size=0.25)
print(f\"Quantized: {len(quantized)} notes\")
for i, note in enumerate(quantized):
    print(f\"  Note {i+1}: start={note.start_time}, duration={note.duration}\")
'"

run_test "ノートの移調" "python3 -c '
from merlai.core.types import Note
from merlai.core.midi import MIDIGenerator

notes = [
    Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
    Note(pitch=64, velocity=80, duration=1.0, start_time=1.0),
]
midi_gen = MIDIGenerator()
transposed = midi_gen.transpose_notes(notes, semitones=5)
print(f\"Transposed: original pitches [60, 64] -> [{transposed[0].pitch}, {transposed[1].pitch}]\")
'"

run_test "複数トラックのマージ" "python3 -c '
from merlai.core.types import Note, Track
from merlai.core.midi import MIDIGenerator

track1 = Track(
    name=\"Melody\",
    notes=[Note(pitch=60, velocity=80, duration=1.0, start_time=0.0)],
    channel=0,
    instrument=0
)
track2 = Track(
    name=\"Bass\",
    notes=[Note(pitch=48, velocity=80, duration=1.0, start_time=0.0)],
    channel=1,
    instrument=32
)

midi_gen = MIDIGenerator()
merged = midi_gen.merge_tracks([track1, track2])
print(f\"Merged MIDI data: {len(merged)} bytes\")
'"

echo "========================================="
echo "6. 完全なワークフローテスト"
echo "========================================="
echo ""

run_test "エンドツーエンド: メロディ→生成→MIDI出力" "python3 -c '
from unittest.mock import patch
from merlai.core.types import Note, Melody, Track, Song
from merlai.core.music import MusicGenerator
from merlai.core.midi import MIDIGenerator
import os

# 1. メロディ作成
melody = Melody(
    notes=[
        Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),
        Note(pitch=62, velocity=80, duration=1.0, start_time=1.0),
        Note(pitch=64, velocity=80, duration=1.0, start_time=2.0),
        Note(pitch=65, velocity=80, duration=1.0, start_time=3.0),
    ],
    tempo=120,
    key=\"C\"
)
print(f\"1. Melody created: {len(melody.notes)} notes\")

# 2. 音楽生成
with patch(\"merlai.core.music.MusicGenerator._initialize_default_models\"):
    music_gen = MusicGenerator()
    
    with patch(\"merlai.core.music.AutoTokenizer\"), patch(\"merlai.core.music.AutoModelForCausalLM\"):
        harmony = music_gen.generate_harmony(melody, style=\"pop\")
    bass = music_gen.generate_bass_line(melody, harmony)
    drums = music_gen.generate_drums(melody, tempo=120)
    
    print(f\"2. Music generated: harmony={len(harmony.chords)}, bass={len(bass.notes)}, drums={len(drums.notes)}\")

# 3. トラック作成
tracks = [
    Track(name=\"Melody\", notes=melody.notes, channel=0, instrument=0),
    Track(name=\"Bass\", notes=bass.notes, channel=1, instrument=32),
    Track(name=\"Drums\", notes=drums.notes, channel=9, instrument=0),
]
print(f\"3. Tracks created: {len(tracks)} tracks\")

# 4. 曲作成
song = Song(tracks=tracks, tempo=120, duration=4.0)
print(f\"4. Song created: {len(song.tracks)} tracks, tempo={song.tempo}, duration={song.duration}s\")

# 5. MIDI生成
midi_gen = MIDIGenerator()
midi_data = midi_gen.create_midi_file(song)
print(f\"5. MIDI data generated: {len(midi_data)} bytes\")

# 6. ファイル保存
output_path = \"$TEST_DIR/complete_song.mid\"
with open(output_path, \"wb\") as f:
    f.write(midi_data)
file_size = os.path.getsize(output_path)
print(f\"6. MIDI file saved: {output_path} ({file_size} bytes)\")
'"

echo ""
echo "========================================="
echo "📊 テスト結果サマリー"
echo "========================================="
echo ""
echo "総テスト数:   $TOTAL_TESTS"
echo -e "${GREEN}成功:        $PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${YELLOW}失敗:        $FAILED_TESTS${NC}"
else
    echo "失敗:        $FAILED_TESTS"
fi
echo ""

SUCCESS_RATE=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
echo "成功率:      ${SUCCESS_RATE}%"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ すべてのテストが成功しました！${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  一部のテストが失敗しました${NC}"
    exit 1
fi
