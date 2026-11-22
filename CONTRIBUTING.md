# Merlaiの開発

機能ブランチからPRを作成し、変更内容と検証結果を記載してください。MIDIの回帰テストには再配布可能な自作素材を使用します。市販のプリセットや制作中の楽曲はローカルで検証します。

```sh
cargo fmt --check
cargo test --locked
```

Macアプリの変更はApple Siliconで `scripts/build-macos.sh` を実行し、アプリを起動して確認します。音源連携を変更した場合は音源名と試聴結果、Logic連携を変更した場合は配置した小節とピアノロールでの表示をPRに記録します。[Mac版の操作と検証](macos/README.md)

アーキテクチャや制作フローの判断を変更する場合は、[ADRの索引](docs/adr/README.md)から理由と後継の判断をたどれるようにしてください。
