# Merlaiの開発

変更対象ごとの正本と検証経路は[開発ガイド](docs/development.md)から確認してください。

機能ブランチからPRを作成し、変更内容と検証結果を記載してください。MIDIの回帰テストには再配布可能な自作素材を使用します。市販のプリセットや制作中の楽曲はローカルで検証します。

```sh
cargo fmt --check
cargo test --locked
```

Macアプリの変更はApple Siliconで `scripts/build-macos.sh` を実行し、アプリを起動して確認します。音源連携を変更した場合は音源名と試聴結果、Logic連携を変更した場合は配置した小節とピアノロールでの表示をPRに記録します。[Mac版の操作と検証](macos/README.md) / [MIDI FX開発](docs/midi-fx-development.md)

## CIと配布

PRではGitHub ActionsがRustの書式・テストを検査し、macOSでアプリをビルドして署名を検証します。Macジョブの成果物はアプリを含むZIPです。配布時は実機で確認したコミットに `macos-v` で始まるバージョンタグを付けます。タグのビルドが成功するとZIP付きのドラフトReleaseが作成されるため、対応環境と検証結果を確認して公開します。[ワークフロー](.github/workflows/native.yml)

アーキテクチャや制作フローの判断を変更する場合は、[ADRの索引](docs/adr/README.md)から理由と後継の判断をたどれるようにしてください。
