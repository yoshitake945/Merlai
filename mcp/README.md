# Merlai MCP Server

MerlaiのためのModel Context Protocol (MCP)サーバー実装。

## 🎯 機能

### 1. MIDI操作
- MIDIファイルの読み込み・書き込み
- ノート情報の取得・編集
- トラック操作
- テンポ・キー情報の取得

### 2. Logic Pro連携
- Logic Proプロジェクトファイルの基本操作
- MIDIデータの送信
- リアルタイムノート入力
- プラグイン情報の取得

### 3. 作曲支援
- コード進行の提案
- メロディ補完
- ハーモニー生成
- リズムパターン提案

## 📦 提供するリソース

### Resources
- `midi://current` - 現在のMIDIファイル情報
- `midi://track/{track_id}` - 特定トラックの情報
- `composition://suggestions` - 作曲支援の提案

### Tools
- `read_midi` - MIDIファイルを読み込む
- `write_midi` - MIDIファイルを書き込む
- `suggest_chords` - コード進行を提案
- `complete_melody` - メロディを補完
- `generate_harmony` - ハーモニーを生成
- `send_to_daw` - DAWにMIDIを送信

## 🚀 使用方法

```bash
# MCPサーバーを起動
python -m mcp.server

# または、Merlai CLIから
merlai mcp start
```
