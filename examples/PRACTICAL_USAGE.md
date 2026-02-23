# Merlai 実践的な使い方ガイド

## 🎯 このガイドについて

Merlaiを実際の作曲作業で使用するための実践的なガイドです。

---

## 🚀 クイックスタート

### 最も簡単な使い方: デモスクリプト

```bash
cd /workspace
python3 examples/composition_assistant_demo.py
```

このデモでは以下を体験できます:
1. メロディから完全な楽曲を自動生成
2. 複数のスタイルでコード進行を提案
3. 部分的なメロディを自動補完
4. リアルタイム作曲支援のシミュレーション
5. Logic Pro用MIDIファイルの生成
6. API経由での作曲支援

生成されたMIDIファイルは `examples/output/` に保存されます。

---

## 💻 Pythonスクリプトでの使用

### 基本的な使い方

```python
from merlai.core.music import MusicGenerator
from merlai.core.midi import MIDIGenerator
from merlai.core.types import Note, Melody

# 初期化
music_gen = MusicGenerator(use_ai_models=False)
midi_gen = MIDIGenerator()

# メロディを作成
melody = Melody(
    notes=[
        Note(pitch=60, velocity=80, duration=1.0, start_time=0.0),  # C
        Note(pitch=64, velocity=80, duration=1.0, start_time=1.0),  # E
        Note(pitch=67, velocity=80, duration=1.0, start_time=2.0),  # G
    ],
    tempo=120,
    key="C"
)

# ハーモニーを生成
harmony = music_gen.generate_harmony(melody, style="pop")

# ベースを生成
bass = music_gen.generate_bass_line(melody, harmony)

# ドラムを生成
drums = music_gen.generate_drums(melody, tempo=120)

# MIDIファイルとして保存
from merlai.core.types import Track, Song

tracks = [
    Track(name="Melody", notes=melody.notes, channel=0, instrument=0),
    Track(name="Bass", notes=bass.notes, channel=1, instrument=32),
    Track(name="Drums", notes=drums.notes, channel=9, instrument=0),
]

song = Song(tracks=tracks, tempo=120, duration=3.0)
midi_data = midi_gen.create_midi_file(song)

with open("output.mid", "wb") as f:
    f.write(midi_data)

print(f"MIDIファイルを保存しました: output.mid")
```

---

## 🌐 API経由での使用

### APIサーバーの起動

```bash
cd /workspace
python3 -m merlai.api.main
```

または

```bash
merlai serve
```

サーバーは `http://localhost:8000` で起動します。

### 音楽生成のリクエスト

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "melody": [
      {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
      {"pitch": 64, "velocity": 80, "duration": 1.0, "start_time": 1.0},
      {"pitch": 67, "velocity": 80, "duration": 1.0, "start_time": 2.0}
    ],
    "style": "pop",
    "tempo": 120,
    "key": "C",
    "generate_harmony": true,
    "generate_bass": true,
    "generate_drums": true
  }'
```

レスポンスには、生成されたハーモニー、ベース、ドラム、そしてbase64エンコードされたMIDIデータが含まれます。

---

## 🎹 MCPサーバー経由での使用（Cursor / Claude Desktop）

### セットアップ

1. `mcp_config.json`をCursorの設定ディレクトリにコピー
2. Cursorを再起動
3. Merlai MCPサーバーが利用可能になります

### 使用例

Cursorで以下のように依頼するだけ：

```
「Cメジャースケールの簡単なメロディを作って、
ポップスタイルのコード進行を提案してください。
そしてLogic Pro用のMIDIファイルとして保存してください。」
```

MCPサーバーが自動的に：
1. メロディを生成
2. コード進行を提案
3. 完全なアレンジを作成
4. MIDIファイルとして保存

### 提供される機能

- ✅ **コード進行の提案** - メロディに合うコードを自動提案
- ✅ **メロディ補完** - 短いメロディを自動拡張
- ✅ **完全なアレンジ生成** - ハーモニー、ベース、ドラム
- ✅ **MIDIファイル操作** - 読み込み、書き込み、編集
- ✅ **DAW連携** - Logic Proへの自動送信

---

## 🎼 Logic Proでの使用

### 方法1: MIDIファイルのインポート

1. Merlaiで曲を生成（デモまたはAPI経由）
2. `examples/output/` にMIDIファイルが保存される
3. Logic Proで `File > Import` から読み込み
4. トラックが自動的に配置される

### 方法2: MCP経由でのダイレクト送信

```
Cursorで: 「このメロディをLogic Proに送ってください」
```

MCPサーバーが自動的にLogic Proを操作します（macOSのみ）。

---

## 🎨 実践的なユースケース

### ユースケース1: 鼻歌からデモ曲を作る

```python
# 1. 鼻歌をMIDIノートに変換（手動または音声認識）
melody_notes = [
    Note(pitch=60, velocity=80, duration=0.5, start_time=0.0),
    Note(pitch=62, velocity=80, duration=0.5, start_time=0.5),
    Note(pitch=64, velocity=80, duration=0.5, start_time=1.0),
]

melody = Melody(notes=melody_notes, tempo=100, key="C")

# 2. Merlaiで完全なデモを生成
music_gen = MusicGenerator(use_ai_models=False)
harmony = music_gen.generate_harmony(melody, style="pop")
bass = music_gen.generate_bass_line(melody, harmony)
drums = music_gen.generate_drums(melody, tempo=100)

# 3. MIDIファイルとして保存
# 4. Logic Proで開いて細かい調整
```

### ユースケース2: コード進行の実験

```python
# 複数のスタイルでコード進行を試す
styles = ["pop", "jazz", "rock", "electronic", "classical"]

for style in styles:
    harmony = music_gen.generate_harmony(melody, style=style)
    print(f"{style}: {len(harmony.chords)}コード")
    
    # 気に入ったスタイルを選んで保存
```

### ユースケース3: ループ素材の生成

```python
# 4小節のループを生成
loop_melody = Melody(
    notes=[
        Note(pitch=60, velocity=80, duration=0.25, start_time=i*0.25)
        for i in range(16)  # 16ノート = 4小節（4/4拍子）
    ],
    tempo=128,
    key="C"
)

# ベースとドラムを追加
bass = music_gen.generate_bass_line(loop_melody, harmony)
drums = music_gen.generate_drums(loop_melody, tempo=128)

# ループ素材として保存
# DAWのループライブラリに追加して使用
```

---

## 🔧 高度な使い方

### カスタマイズされた生成

```python
# GenerationConfigをカスタマイズ
music_gen.config.temperature = 0.9  # より創造的に
music_gen.config.top_p = 0.95      # より多様性を

# スタイルとキーを細かく指定
harmony = music_gen.generate_harmony(
    melody,
    style="jazz",
    key="Dm"  # マイナーキー
)
```

### 複数トラックの管理

```python
# 各楽器に異なる音色を設定
tracks = [
    Track(name="Lead", notes=melody.notes, channel=0, instrument=81),      # Lead Synth
    Track(name="Pad", notes=harmony_notes, channel=1, instrument=89),       # Pad
    Track(name="Bass", notes=bass.notes, channel=2, instrument=38),         # Synth Bass
    Track(name="Drums", notes=drums.notes, channel=9, instrument=0),        # Standard Kit
]
```

---

## 📊 パフォーマンス

### 生成速度
- ハーモニー生成: ~10-20ms
- ベース生成: ~5-10ms
- ドラム生成: ~5-10ms
- MIDIファイル作成: ~5ms

### 推奨環境
- **開発**: Python 3.9+, 2GB RAM
- **本番**: Python 3.11+, 4GB RAM, GPUオプション

---

## 🎓 学習リソース

### 基本から学ぶ
1. `examples/composition_assistant_demo.py` - 実行してみる
2. デモのソースコードを読む
3. 自分のメロディで試してみる

### API を学ぶ
1. `/docs/API.md` - API仕様を確認
2. `http://localhost:8000/docs` - Swagger UI
3. `curl`でAPIを試す

### MCP を学ぶ
1. `mcp/README.md` - MCP機能の概要
2. `examples/mcp_usage_example.md` - 使用例（本ドキュメント）
3. Cursorで実際に使ってみる

---

## 🆘 よくある質問

### Q: AIモデルは必須ですか？
A: いいえ。現在は基本的なルールベースの生成で動作します。AIモデルを追加すると、より高度な生成が可能になります。

### Q: どのDAWに対応していますか？
A: MIDIファイルを出力するので、すべての主要DAW（Logic Pro, Ableton, FL Studio, Cubase等）で使用できます。

### Q: 商用利用は可能ですか？
A: Apache 2.0ライセンスで、商用利用可能です。

### Q: 生成された音楽の著作権は？
A: ユーザーに帰属します。Merlaiは作曲支援ツールであり、最終的な創作物はユーザーのものです。

---

## 💡 Tips

1. **メロディは短くてOK**: 2-4ノートでも十分なアレンジが生成できます
2. **スタイルを実験**: 同じメロディでも、スタイルを変えると全く違う雰囲気に
3. **テンポを変更**: 生成後にDAWでテンポを調整しても問題ありません
4. **レイヤーを重ねる**: 複数回生成して、好きな部分を組み合わせる

---

**Merlaiで、創造的な音楽制作を加速させましょう！** 🎵

質問や提案がある場合は、GitHubのIssuesまたはDiscussionsをご利用ください。
