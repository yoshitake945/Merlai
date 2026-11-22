# 生成エンジンと音源ホスト

SwiftUIアプリはMIDIのパスと生成設定をJSONでRustの子プロセスに渡します。Rustは3つの標準MIDIファイルを書き、元メロディーと候補のノート列を返します。生成はMacの音源から独立しているため、同じ入力とシードでCLIから再現できます。[Rust実装](../crates/composer/src/main.rs)

### MIDIの時間と音程

エンジンは先頭の完全な空小節を取り除き、小節内の休符を保持します。末尾の最大2小節をモチーフとして、候補ごとに音程の順序、打点、終止音を変えます。ドラムを渡した場合は拍の解像度を揃え、指定されたキックの近くの発音を間引きます。入力はPPQ形式のMIDI format 0または1で、テンポや拍子が途中で変わる場合は区間を分けて渡します。

### CLIで生成する

リポジトリのルートで実行します。出力先には新しいディレクトリ名を指定してください。

```sh
echo '{"version":1,"melody":"tests/native/melody.mid","drums":"tests/native/groove.mid","output":"take-01","bars":2,"seed":0,"kicks":[36],"tonic":6,"attack_ms":0,"release_ms":0}' | cargo run --locked -q -p merlai-compose
```

`bars` は生成する小節数、`tonic` はCを0とする主音です。上の例の6はF♯を表します。`drums` と `tonic` は省略できます。応答の `candidates[].file` がLogicに渡すファイルです。各ファイルは候補の先頭小節を原点とします。`continuation_at` は元メロディーに続けて試聴するときの開始tick、`ppq` は四分音符当たりのtick数、`tempo` は四分音符当たりのマイクロ秒です。

### 音色の計測と試聴

Swiftの音源ホストはAudio Unitを別プロセスでロードし、MIDIノート60・ベロシティ90の信号を10 ms単位で計測します。生成側は立ち上がりが75 ms以上なら近接する発音を間引き、余韻が300 ms以上なら発音長を短縮します。試聴では元メロディーと続きの音声を一度レンダリングして再利用します。SQLiteカタログと音源ごとの最後のプリセット状態は `~/Library/Application Support/Merlai/` に保存します。[音源ホスト](../macos/Sources/Host/main.swift)
