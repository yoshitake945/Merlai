# Merlai MCP サーバー使用例

## 🎯 概要

Merlai MCPサーバーを使用すると、CursorやClaude DesktopなどのAIアシスタントから、
直接Merlaiの作曲支援機能を利用できます。

## 🚀 セットアップ

### 1. MCP設定ファイルの配置

Cursorの場合、`~/.cursor/mcp_config.json`に以下を追加：

```json
{
  "mcpServers": {
    "merlai": {
      "command": "python3",
      "args": ["-m", "mcp.server"],
      "cwd": "/workspace",
      "env": {
        "PYTHONPATH": "/workspace",
        "PATH": "/home/ubuntu/.local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

### 2. MCPサーバーの起動

```bash
cd /workspace
python3 -m mcp.server
```

## 📚 利用可能なツール

### 1. `read_midi_file` - MIDIファイルを読み込む

```json
{
  "file_path": "/path/to/your/song.mid"
}
```

**用途**: 既存のMIDIファイルを分析・編集する

### 2. `write_midi_file` - MIDIファイルを作成

```json
{
  "file_path": "/path/to/output.mid",
  "melody": [
    {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0},
    {"pitch": 64, "velocity": 80, "duration": 1.0, "start_time": 1.0}
  ]
}
```

**用途**: メロディからMIDIファイルを生成

### 3. `suggest_chord_progression` - コード進行を提案

```json
{
  "melody": [
    {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0}
  ],
  "style": "pop",
  "key": "C"
}
```

**用途**: メロディに合うコード進行を自動提案

### 4. `complete_melody` - メロディを補完

```json
{
  "partial_melody": [
    {"pitch": 60, "velocity": 80, "duration": 0.5, "start_time": 0.0}
  ],
  "target_length": 8.0,
  "style": "pop"
}
```

**用途**: 短いメロディを自動的に拡張

### 5. `generate_full_arrangement` - 完全なアレンジを生成

```json
{
  "melody": [
    {"pitch": 60, "velocity": 80, "duration": 1.0, "start_time": 0.0}
  ],
  "style": "pop",
  "tempo": 120,
  "key": "C"
}
```

**用途**: メロディからハーモニー・ベース・ドラムを自動生成

### 6. `analyze_midi` - MIDIファイルを分析

```json
{
  "file_path": "/path/to/song.mid"
}
```

**用途**: キー、テンポ、コード進行を自動検出

### 7. `send_to_logic_pro` - Logic Proに送信

```json
{
  "midi_file_path": "/path/to/output.mid",
  "track_name": "Merlai Generated Track"
}
```

**用途**: 生成したMIDIをLogic Proに直接送信（macOSのみ）

## 🎵 実用的な使用例

### 例1: メロディからフル楽曲を生成

**Cursorで以下のように依頼**:
```
「C-D-E-Fのメロディから、ポップスタイルの完全な楽曲を作ってください」
```

**MCPサーバーの実行**:
1. メロディノートを作成
2. `suggest_chord_progression`でコード進行を提案
3. `generate_full_arrangement`で完全なアレンジを生成
4. `write_midi_file`でMIDIファイルを保存

### 例2: 既存の曲を分析してアレンジ

**Cursorで以下のように依頼**:
```
「song.midを読み込んで、ジャズスタイルに再アレンジしてください」
```

**MCPサーバーの実行**:
1. `read_midi_file`で既存ファイルを読み込み
2. `analyze_midi`でキーとテンポを検出
3. `suggest_chord_progression`でジャズコードを提案
4. `generate_full_arrangement`でアレンジ
5. `write_midi_file`で保存

### 例3: Logic Proでの作曲支援

**Cursorで以下のように依頼**:
```
「きらきら星のメロディを作って、Logic Proに送ってください」
```

**MCPサーバーの実行**:
1. メロディを作成
2. `generate_full_arrangement`で完全なアレンジ
3. `write_midi_file`で一時ファイルに保存
4. `send_to_logic_pro`でLogic Proに送信

## 💡 実用的なワークフロー

### ワークフロー1: アイデアから楽曲へ

```
1. あなた: 「C-E-G-Cのメロディを作って」
   → Merlai: メロディノートを作成

2. あなた: 「このメロディに合うコード進行を提案して」
   → Merlai: suggest_chord_progression で提案

3. あなた: 「ベースとドラムを追加して」
   → Merlai: generate_full_arrangement で完全なアレンジ

4. あなた: 「Logic Proに送って」
   → Merlai: send_to_logic_pro で送信
```

### ワークフロー2: 既存曲の編集

```
1. あなた: 「mysong.midのコード進行を分析して」
   → Merlai: analyze_midi で分析

2. あなた: 「もっとジャジーなコードに変えて」
   → Merlai: suggest_chord_progression でジャズコード提案

3. あなた: 「新しいアレンジで保存して」
   → Merlai: write_midi_file で保存
```

## 🔧 トラブルシューティング

### MCPサーバーが起動しない

```bash
# 依存関係を確認
pip install mcp

# PYTHONPATHを確認
export PYTHONPATH=/workspace
python3 -m mcp.server
```

### Logic Proに送信できない

- macOS環境が必要です
- Logic Proがインストールされている必要があります
- AppleScriptの実行権限が必要です

## 📖 参考情報

- Merlai API ドキュメント: `/workspace/docs/API.md`
- MCPサーバーコード: `/workspace/mcp/server.py`
- デモスクリプト: `/workspace/examples/composition_assistant_demo.py`

## 🎉 次のステップ

1. Cursor/Claude Desktopでこのサーバーを設定
2. 自然言語で作曲支援を依頼
3. 生成されたMIDIをDAWで編集
4. さらにMerlaiで改善を重ねる

**Merlaiを使って、創造的な音楽制作を楽しんでください！** 🎵
