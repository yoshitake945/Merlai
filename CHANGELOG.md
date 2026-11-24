# Changelog

## Unreleased

- Generatorの候補を適用前に試聴し、採用時だけUndo履歴へ追加できるようにしました。
- Codex/Claude CLIとローカルOpenAI互換モデルを検出・選択するModel Bridgeを追加しました。
- Codexのstrict JSON Schemaを修正し、使用中のMIDI入力元と音域を明示しました。
- モデル失敗時の暗黙な内蔵生成を廃止し、編集・伴奏生成の目的を分離しました。

- RustとSwiftによるLogic Pro向けMacアプリを追加。
- 旧Python版をアーカイブ。過去の変更履歴は [python-legacyのCHANGELOG](https://github.com/yoshitake945/Merlai/blob/python-legacy/CHANGELOG.md) に収録。
