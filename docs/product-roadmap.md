# Merlaiプロダクトロードマップ

MerlaiはLogic内でMIDIを直接仕上げるエディタではなく、制作文脈を集め、AIと会話し、候補を比較・試聴・確定するコパイロットを目指します。

## 制作ループ

1. **Context** — メロディー、コード、ベース、ドラム、キー、音色特徴を取得する。
2. **Conversation** — 分析、生成、説明、修正、比較を反復する。
3. **Commit** — 読み取り専用差分と試聴で確認し、確定MIDIをLogicへ渡す。

## M4 Context

[Issue #85](https://github.com/yoshitake945/Merlai/issues/85)で、役割付き複数Context、キー／スケール、フレーズ継続を導入します。LogicのChordトラックはAUv2から暗黙に読まず、コード用MIDIトラックを明示的な入力元として扱います。手動MIDI編集は[#90](https://github.com/yoshitake945/Merlai/issues/90)で読み取り専用候補差分へ置き換えます。

## M5 Conversation

[#86](https://github.com/yoshitake945/Merlai/issues/86)で右側パネルを会話スレッドへ拡張し、Context分析、和声説明、候補生成、再修正、比較をツールとして提供します。AIは候補準備まで行えますが、確定、Logicへの出力、クラウド送信はユーザー確認を維持します。

[#87](https://github.com/yoshitake945/Merlai/issues/87)でOpenTelemetry GenAI Semantic Conventionsに合わせ、モデル、provider、conversation、input/output/cache/reasoning tokens、duration、statusを正規化します。会話本文、MIDI、プロンプト本文は既定でTelemetryへ含めません。

## M6 Sound

[#88](https://github.com/yoshitake945/Merlai/issues/88)と[#73](https://github.com/yoshitake945/Merlai/issues/73)で、ユーザー指定Audio Unitのプリセットをローカル計測・索引します。決定的ランキングで候補を絞り、上位3〜5件の名前、用途タグ、数値特徴だけをAIへ渡します。最終適用はLogicの音源UIで行います。

## M7 Arrangement

[#89](https://github.com/yoshitake945/Merlai/issues/89)で複数MIDIの構造要約を先に実装し、その後Stereo Out／Bus用の非破壊Mix Analyzerを追加します。Mix Analyzerは密度、帯域、明るさなどの補助文脈に限定し、採譜や完全なコード推定には使いません。生音声は保存・クラウド送信しません。
