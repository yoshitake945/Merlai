# Merlai開発ガイド

変更対象ごとに、次の文書を正本として使います。

| 対象 | 開発・検証手順 | 設計判断 |
|---|---|---|
| Rust生成エンジン | [ネイティブ生成エンジン](native-engine.md) | [0001](adr/0001-native-composer.md)、[0002](adr/0002-midi-takes.md) |
| macOSアプリと音源ホスト | [Mac版の操作と検証](../macos/README.md) | [0001](adr/0001-native-composer.md)、[0006](adr/0006-timbre-analysis-boundary.md) |
| Logic MIDI FX / Audio Analyzer | [MIDI FX開発](midi-fx-development.md) | [0003](adr/0003-track-midi-fx.md)〜[0006](adr/0006-timbre-analysis-boundary.md) |
| CI・配布 | [コントリビューション](../CONTRIBUTING.md) | [GitHub Actions](../.github/workflows/native.yml) |

共通の最小確認は `cargo fmt --check` と `cargo test --locked` です。macOS固有の変更はApple Silicon実機で対象のビルドスクリプトを実行し、署名と実際の画面・音声・MIDI出力を確認します。

開発支援用のCodex SKILLは `.agents/skills/` にあります。SKILLは判断と検証の入口だけを持ち、詳細手順は上記文書を参照します。

機能の導入順序とプロダクト上の責務は[プロダクトロードマップ](product-roadmap.md)を正本とします。
