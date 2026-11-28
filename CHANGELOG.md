# Changelog

## Unreleased

- MIDI FXの右側を制作チャット履歴へ拡張し、指示とモデル説明を次の再生成へ引き継げるようにしました。
- Logicプラグインへキー／スケール付きの「続きを生成」を追加し、Context v2の基盤を導入しました。
- 手動MIDI編集を読み取り専用の候補差分へ置き換え、詳細編集をLogicへ集約しました。

- Generatorの候補を適用前に試聴し、採用時だけUndo履歴へ追加できるようにしました。
- Codex/Claude CLIとローカルOpenAI互換モデルを検出・選択するModel Bridgeを追加しました。
- Codexのstrict JSON Schemaを修正し、使用中のMIDI入力元と音域を明示しました。
- モデル失敗時の暗黙な内蔵生成を廃止し、編集・伴奏生成の目的を分離しました。
- 指示欄を複数行入力へ変更し、LLM生成の段階・経過時間・説明・次の提案を表示しました。
- 広いMIDI編集タブで修正案の移動、音程変更、伸縮、削除、Undoを可能にしました。

- RustとSwiftによるLogic Pro向けMacアプリを追加。
- 旧Python版をアーカイブ。過去の変更履歴は [python-legacyのCHANGELOG](https://github.com/yoshitake945/Merlai/blob/python-legacy/CHANGELOG.md) に収録。
