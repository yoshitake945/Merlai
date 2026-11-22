# Merlai

Logic Proで作ったメロディーに、次の数小節を足すためのMacアプリです。短いMIDIフレーズを渡すと、リズムと音程を変えた続きが3案でき、好きな案をLogicのピアノロールで編集できます。ドラムMIDIや手元のAudio Unit音源も使えます。

## 起動する

Apple Silicon搭載Mac、macOS 14以降、Rust stable（Cargoを含む）、Swift 5.9以上のAppleツールチェーンを用意します。リポジトリのルートで次を実行します。

```sh
scripts/build-macos.sh
open dist/Merlai.app
```

最初は「メロディーMIDIを開く」で [サンプルの2小節](tests/native/melody.mid) を選び、「MIDIのみ」のまま「続きを3案生成」を押してください。候補の「Finderで表示」からMIDIファイルを開けます。[Logicへの取り込みと試聴の手順](macos/README.md)

## プロジェクトについて

現在の生成方式はRustによるルールベースです。AIモデルを使った生成は将来の拡張候補です。以前のPython版とモデル接続コードは [python-legacy タグ](https://github.com/yoshitake945/Merlai/tree/python-legacy) に保存しています。

- [設計とCLIの使い方](docs/native-engine.md)
- [開発・テスト・リリース](CONTRIBUTING.md)
- [変更履歴](CHANGELOG.md)
- [行動規範](CODE_OF_CONDUCT.md)・[ライセンス](LICENSE)・[クレジット](NOTICE)

設計の背景と旧版の原文は[設計判断の記録（ADR）](docs/adr/README.md)で参照できます。

Logicのトラックで既存の音色を使ってフレーズを推敲するには、[Merlai MIDI FXのビルドと操作](macos/MidiFX/README.md)を参照してください。
