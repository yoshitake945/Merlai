# 0006　音源の音色特徴は非破壊Analyzerで取得する

- 状態: 提案
- 関連: [#73](https://github.com/yoshitake945/Merlai/issues/73)

## 背景

挿入中のAudio Unit音源に合う音域、密度、長さのMIDIを生成したい。プラグイン内部をeBPFなどで傍受する方法は、macOSの保護境界、Audio Unitホストの安定性、プラグイン互換性を損なう。

## 提案

音源内部へ介入せず、Merlai Audio Analyzerの非破壊タップ、Audio Unitが公開するパラメータとプリセット情報、必要に応じた短いオフライン試聴レンダーを組み合わせる。ローカルでattack、release、brightness、bandwidth、dynamics、reverb相当の特徴量へ変換し、MIDI生成には特徴量だけを渡す。

音声スレッドでは固定サイズ処理だけを行い、割当、ロック、ファイルI/O、モデル呼び出しを行わない。生音声をクラウドLLMへ送らないことを既定とする。

## 今回の扱い

本ADRは将来方針だけを記録する。音色特徴の実装はGeneratorの入力・編集UX改善には含めない。
