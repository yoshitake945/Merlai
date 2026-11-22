# Merlai

Logic Proで作ったメロディーMIDIの続きを生成する、Apple Silicon向けのローカル作曲アシスタントです。Rustがリズムと音程を変形して3案を生成し、SwiftアプリがAudio Unitでの試聴とMIDIの書き出しを担当します。現在の生成方式はルールベースです。AIモデルによる候補生成は将来の拡張候補です。

## Macで使う

macOS 14以降、Rust stableとSwift 5.9以上を用意し、リポジトリのルートで実行します。

```sh
scripts/build-macos.sh
open dist/Merlai.app
```

最初は同梱の `tests/native/melody.mid` で試せます。[音色の選択、試聴、Logicへの取り込み](macos/README.md)

## 開発

Rustエンジンは `crates/composer`、Macアプリと音源ホストは `macos` にあります。[開発とテスト](CONTRIBUTING.md)

旧Python版とモデル接続コードは [python-legacy タグ](https://github.com/yoshitake945/Merlai/tree/python-legacy) から参照できます。

設計の背景と旧版の原文は[設計判断の記録（ADR）](docs/adr/README.md)で参照できます。
