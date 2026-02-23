"""
Merlai 作曲支援デモ

このスクリプトは、Merlaiを使った実践的な作曲支援の例を示します。
"""

import json
import os
import sys
from pathlib import Path

# Merlaiのコアモジュールを直接インポート
sys.path.insert(0, str(Path(__file__).parent.parent))

from merlai.core.music import MusicGenerator
from merlai.core.midi import MIDIGenerator
from merlai.core.types import Note, Melody, Track, Song


def demo_1_simple_melody_to_song():
    """デモ1: シンプルなメロディから完全な曲を生成"""
    print("=" * 60)
    print("デモ1: メロディから完全な曲を生成")
    print("=" * 60)
    print()
    
    # 音楽ジェネレーターを初期化
    music_gen = MusicGenerator(use_ai_models=False)
    midi_gen = MIDIGenerator()
    
    # 簡単なメロディを作成（「きらきら星」の最初の部分）
    print("1. メロディを作成（きらきら星の最初の部分）...")
    melody_notes = [
        Note(pitch=60, velocity=80, duration=0.5, start_time=0.0),   # C
        Note(pitch=60, velocity=80, duration=0.5, start_time=0.5),   # C
        Note(pitch=67, velocity=80, duration=0.5, start_time=1.0),   # G
        Note(pitch=67, velocity=80, duration=0.5, start_time=1.5),   # G
        Note(pitch=69, velocity=80, duration=0.5, start_time=2.0),   # A
        Note(pitch=69, velocity=80, duration=0.5, start_time=2.5),   # A
        Note(pitch=67, velocity=90, duration=1.0, start_time=3.0),   # G
    ]
    
    melody = Melody(notes=melody_notes, tempo=120, key="C")
    print(f"   ✅ {len(melody.notes)}個のノートを作成")
    print()
    
    # ハーモニーを生成
    print("2. ハーモニー（コード進行）を生成...")
    harmony = music_gen.generate_harmony(melody, style="pop")
    print(f"   ✅ {len(harmony.chords)}個のコードを生成")
    for i, chord in enumerate(harmony.chords):
        print(f"      コード{i+1}: ルート音={chord.root}, タイプ={chord.chord_type}")
    print()
    
    # ベースラインを生成
    print("3. ベースラインを生成...")
    bass = music_gen.generate_bass_line(melody, harmony)
    print(f"   ✅ {len(bass.notes)}個のベースノートを生成")
    print()
    
    # ドラムパターンを生成
    print("4. ドラムパターンを生成...")
    drums = music_gen.generate_drums(melody, tempo=120)
    print(f"   ✅ {len(drums.notes)}個のドラムノートを生成")
    print()
    
    # すべてをMIDIファイルとして出力
    print("5. MIDIファイルを生成...")
    tracks = [
        Track(name="Melody", notes=melody.notes, channel=0, instrument=0),
        Track(name="Bass", notes=bass.notes, channel=1, instrument=32),
        Track(name="Drums", notes=drums.notes, channel=9, instrument=0),
    ]
    
    song = Song(tracks=tracks, tempo=120, duration=4.0)
    midi_data = midi_gen.create_midi_file(song)
    
    # ファイルに保存
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "twinkle_star_arrangement.mid"
    
    with open(output_path, "wb") as f:
        f.write(midi_data)
    
    print(f"   ✅ MIDIファイルを保存: {output_path}")
    print(f"   📊 ファイルサイズ: {len(midi_data)} bytes")
    print()


def demo_2_chord_progression_suggestion():
    """デモ2: コード進行の提案"""
    print("=" * 60)
    print("デモ2: メロディに合うコード進行を提案")
    print("=" * 60)
    print()
    
    music_gen = MusicGenerator(use_ai_models=False)
    
    # ユーザーが作ったメロディ
    print("1. ユーザーのメロディ...")
    user_melody = Melody(
        notes=[
            Note(pitch=64, velocity=80, duration=1.0, start_time=0.0),   # E
            Note(pitch=62, velocity=80, duration=1.0, start_time=1.0),   # D
            Note(pitch=60, velocity=80, duration=1.0, start_time=2.0),   # C
            Note(pitch=62, velocity=80, duration=1.0, start_time=3.0),   # D
        ],
        tempo=100,
        key="C"
    )
    print(f"   メロディ: {len(user_melody.notes)}ノート")
    print()
    
    # 複数のスタイルでコード進行を提案
    print("2. 異なるスタイルでコード進行を提案...")
    styles = ["pop", "jazz", "rock"]
    
    for style in styles:
        harmony = music_gen.generate_harmony(user_melody, style=style)
        print(f"\n   【{style.upper()}スタイル】")
        print(f"   提案されたコード進行:")
        
        for i, chord in enumerate(harmony.chords):
            chord_name = f"ルート音{chord.root} ({chord.chord_type})"
            print(f"      {i+1}. {chord_name} (開始: {chord.start_time}秒)")
    
    print()


def demo_3_melody_completion():
    """デモ3: メロディの補完"""
    print("=" * 60)
    print("デモ3: 部分的なメロディを補完")
    print("=" * 60)
    print()
    
    midi_gen = MIDIGenerator()
    
    # 部分的なメロディ（最初の2小節だけ）
    print("1. 部分的なメロディ（2小節）...")
    partial_melody = [
        Note(pitch=60, velocity=80, duration=0.5, start_time=0.0),
        Note(pitch=62, velocity=80, duration=0.5, start_time=0.5),
        Note(pitch=64, velocity=80, duration=0.5, start_time=1.0),
        Note(pitch=65, velocity=80, duration=0.5, start_time=1.5),
    ]
    print(f"   元のメロディ: {len(partial_melody)}ノート")
    print()
    
    # パターンを繰り返して補完
    print("2. メロディを補完（8小節に拡張）...")
    completed_melody = []
    completed_melody.extend(partial_melody)
    
    # パターンを繰り返す
    for i in range(3):  # 3回繰り返して4倍の長さに
        offset = (i + 1) * 2.0
        for note in partial_melody:
            new_note = Note(
                pitch=note.pitch + (i % 2) * 2,  # 少しピッチを変える
                velocity=note.velocity,
                duration=note.duration,
                start_time=note.start_time + offset
            )
            completed_melody.append(new_note)
    
    print(f"   ✅ 補完完了: {len(completed_melody)}ノート")
    print()
    
    # MIDIファイルとして保存
    print("3. MIDIファイルとして保存...")
    midi_data = midi_gen.create_midi_from_notes(completed_melody, tempo=120)
    
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "completed_melody.mid"
    
    with open(output_path, "wb") as f:
        f.write(midi_data)
    
    print(f"   ✅ 保存完了: {output_path}")
    print()


def demo_4_real_time_suggestion():
    """デモ4: リアルタイムの作曲支援シミュレーション"""
    print("=" * 60)
    print("デモ4: リアルタイム作曲支援シミュレーション")
    print("=" * 60)
    print()
    
    music_gen = MusicGenerator(use_ai_models=False)
    midi_gen = MIDIGenerator()
    
    print("シナリオ: ユーザーが1小節ずつメロディを入力していく")
    print()
    
    # 小節ごとにメロディを追加
    all_notes = []
    
    measures = [
        [
            Note(pitch=60, velocity=80, duration=0.5, start_time=0.0),
            Note(pitch=62, velocity=80, duration=0.5, start_time=0.5),
        ],
        [
            Note(pitch=64, velocity=80, duration=0.5, start_time=2.0),
            Note(pitch=65, velocity=80, duration=0.5, start_time=2.5),
        ],
        [
            Note(pitch=67, velocity=80, duration=1.0, start_time=4.0),
        ],
    ]
    
    for i, measure_notes in enumerate(measures):
        print(f"【小節 {i+1}】")
        all_notes.extend(measure_notes)
        
        # 現在のメロディでハーモニーを提案
        current_melody = Melody(notes=all_notes, tempo=120, key="C")
        harmony = music_gen.generate_harmony(current_melody, style="pop")
        
        print(f"   入力: {len(measure_notes)}ノート追加")
        print(f"   提案コード: ", end="")
        
        # 最新のコードを表示
        if harmony.chords:
            latest_chord = harmony.chords[-1]
            print(f"ルート音{latest_chord.root} ({latest_chord.chord_type})")
        else:
            print("なし")
        
        print()
    
    print(f"✅ 完成: {len(all_notes)}ノートのメロディ")
    print(f"   推奨コード進行: {len(harmony.chords)}コード")
    print()


def demo_5_export_for_logic_pro():
    """デモ5: Logic Pro用にエクスポート"""
    print("=" * 60)
    print("デモ5: Logic Pro用のMIDIファイルを作成")
    print("=" * 60)
    print()
    
    music_gen = MusicGenerator(use_ai_models=False)
    midi_gen = MIDIGenerator()
    
    # シンプルなコード進行
    print("1. コード進行ベースの曲を生成...")
    
    # C - Am - F - G のコード進行
    chord_progression = [
        Note(pitch=60, velocity=80, duration=2.0, start_time=0.0),   # C
        Note(pitch=69, velocity=80, duration=2.0, start_time=2.0),   # A
        Note(pitch=65, velocity=80, duration=2.0, start_time=4.0),   # F
        Note(pitch=67, velocity=80, duration=2.0, start_time=6.0),   # G
    ]
    
    melody = Melody(notes=chord_progression, tempo=90, key="C")
    
    # ハーモニー、ベース、ドラムを生成
    harmony = music_gen.generate_harmony(melody, style="pop")
    bass = music_gen.generate_bass_line(melody, harmony)
    drums = music_gen.generate_drums(melody, tempo=90)
    
    print(f"   ✅ ハーモニー: {len(harmony.chords)}コード")
    print(f"   ✅ ベース: {len(bass.notes)}ノート")
    print(f"   ✅ ドラム: {len(drums.notes)}ノート")
    print()
    
    # 複数トラックのMIDIファイルを作成
    print("2. Logic Pro互換のMIDIファイルを作成...")
    
    tracks = [
        Track(name="Lead Melody", notes=melody.notes, channel=0, instrument=0),
        Track(name="Bass", notes=bass.notes, channel=1, instrument=32),
        Track(name="Drums", notes=drums.notes, channel=9, instrument=0),
    ]
    
    song = Song(tracks=tracks, tempo=90, duration=8.0)
    midi_data = midi_gen.create_midi_file(song)
    
    # 保存
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "for_logic_pro.mid"
    
    with open(output_path, "wb") as f:
        f.write(midi_data)
    
    print(f"   ✅ 保存完了: {output_path}")
    print(f"   📊 トラック数: {len(tracks)}")
    print(f"   📊 ファイルサイズ: {len(midi_data)} bytes")
    print()
    
    print("3. Logic Proでの使用方法:")
    print("   1. Logic Proを起動")
    print(f"   2. File > Import > {output_path}")
    print("   3. トラックが自動的にインポートされます")
    print()


def demo_6_api_based_composition():
    """デモ6: API経由での作曲支援"""
    print("=" * 60)
    print("デモ6: API経由での作曲支援（シミュレーション）")
    print("=" * 60)
    print()
    
    print("シナリオ: ユーザーがAPIを通じて作曲支援を受ける")
    print()
    
    # APIリクエストのシミュレーション
    print("1. ユーザーからのリクエスト:")
    request_data = {
        "melody": [
            {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
            {"pitch": 64, "velocity": 80, "duration": 1.0, "start_time": 1.0},
            {"pitch": 67, "velocity": 80, "duration": 1.0, "start_time": 2.0},
        ],
        "style": "pop",
        "tempo": 120,
        "key": "C",
        "generate_harmony": True,
        "generate_bass": True,
        "generate_drums": True,
    }
    
    print(f"   メロディノート: {len(request_data['melody'])}個")
    print(f"   スタイル: {request_data['style']}")
    print(f"   テンポ: {request_data['tempo']} BPM")
    print()
    
    # 作曲支援の実行
    print("2. Merlaiが作曲支援を実行...")
    
    music_gen = MusicGenerator(use_ai_models=False)
    
    # メロディを変換
    melody_notes = [
        Note(**{k: v for k, v in note.items()})
        for note in request_data["melody"]
    ]
    melody = Melody(notes=melody_notes, tempo=request_data["tempo"], key=request_data["key"])
    
    # 生成
    harmony = music_gen.generate_harmony(melody, style=request_data["style"])
    bass = music_gen.generate_bass_line(melody, harmony)
    drums = music_gen.generate_drums(melody, tempo=request_data["tempo"])
    
    print(f"   ✅ ハーモニー生成完了: {len(harmony.chords)}コード")
    print(f"   ✅ ベース生成完了: {len(bass.notes)}ノート")
    print(f"   ✅ ドラム生成完了: {len(drums.notes)}ノート")
    print()
    
    # レスポンスを作成
    print("3. APIレスポンス（JSON）:")
    response_data = {
        "success": True,
        "harmony": [
            {
                "root": c.root,
                "type": c.chord_type,
                "start_time": c.start_time,
                "duration": c.duration,
            }
            for c in harmony.chords
        ],
        "bass_line": [
            {"pitch": n.pitch, "velocity": n.velocity, "duration": n.duration, "start_time": n.start_time}
            for n in bass.notes
        ],
        "drums": [
            {"pitch": n.pitch, "velocity": n.velocity, "duration": n.duration, "start_time": n.start_time}
            for n in drums.notes
        ],
    }
    
    print(json.dumps(response_data, indent=2, ensure_ascii=False))
    print()


def main():
    """すべてのデモを実行"""
    print()
    print("🎵" * 30)
    print("   Merlai 作曲支援デモ")
    print("🎵" * 30)
    print()
    
    try:
        demo_1_simple_melody_to_song()
        input("Enterキーを押して次のデモへ... ")
        print()
        
        demo_2_chord_progression_suggestion()
        input("Enterキーを押して次のデモへ... ")
        print()
        
        demo_3_melody_completion()
        input("Enterキーを押して次のデモへ... ")
        print()
        
        demo_4_real_time_suggestion()
        input("Enterキーを押して次のデモへ... ")
        print()
        
        demo_5_export_for_logic_pro()
        input("Enterキーを押して次のデモへ... ")
        print()
        
        demo_6_api_based_composition()
        
    except KeyboardInterrupt:
        print("\n\n👋 デモを終了します")
        return
    
    print("=" * 60)
    print("✅ すべてのデモが完了しました！")
    print()
    print("生成されたファイルは examples/output/ に保存されています")
    print("=" * 60)


if __name__ == "__main__":
    main()
