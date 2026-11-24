# 設計判断の記録

ADRには、ある時点での背景、採用した方法、理由と制約を残します。方針が変わったら、新しいADRから元の記録へリンクし、古い記録には後継を明記します。

| 記録 | 状態 |
| --- | --- |
| [0001　ローカル生成と音源ホストの分離](0001-native-composer.md) | 採用済み |
| [0002　MIDIファイルとテイクによる受け渡し](0002-midi-takes.md) | 今回の変更で採用 |
| [0003　Logicの音源トラックでフレーズを推敲する](0003-track-midi-fx.md) | 試作 |
| [0004　別トラックを文脈にしたMIDI生成](0004-cross-track-context-generation.md) | 提案 |
| [0005　Model BridgeでLogicとLLMを分離する](0005-model-bridge-and-data-boundary.md) | 採用 |
| [0006　音源の音色特徴は非破壊Analyzerで取得する](0006-timbre-analysis-boundary.md) | 提案 |

## 過去の設計資料

以下は旧版の原文です。当時の提案や検討事項も含みます。

- [Python版のアーキテクチャ](../history/python-architecture.md) · [原文のコミット](https://github.com/yoshitake945/Merlai/blob/d95210a481b729570263027c3f7ae7ab8037da04/ARCHITECTURE.md)
- [AIモデル管理の設計](../history/python-ai-model-management.md) · [旧版の文書一覧](https://github.com/yoshitake945/Merlai/tree/python-legacy/docs)
