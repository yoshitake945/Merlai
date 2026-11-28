# Merlai MIDI FX開発

## 状態とスレッドの境界

MIDIの収集はAudio UnitのProcessorがレンダースレッド上で行い、Cocoa UIは`CaptureProgress`を定期取得して表示と完了フレーズの受け取りを行います。テキスト欄のフォーカスやIME変換は、Processorの収集だけでなくUIの進捗取得・完了処理も止めてはいけません。

入力元一覧の再構築など、テキスト入力に不要なUI更新は編集中だけ延期できます。取り込み状態、解析状態、完了フレーズの取得は常に継続します。UIポーリングから文字列、選択範囲、marked text、first responderを変更しません。

Generatorの状態は`Idle → Armed → Capturing → Ready`または`Failed`です。Audio Analyzerも同じ状態を使います。`Ready`を受け取ったUIはフレーズを一度だけ読み、Generatorでは原案として表示・共有し、Analyzerでは解析入力として公開します。

## ビルドと自動テスト

Apple Silicon Macで実行します。初回は固定コミットのAudioUnitSDKを`target/AudioUnitSDK`へ取得します。

```sh
scripts/build-midi-fx.sh
```

このスクリプトはRust編集ライブラリとModelBridgeをビルドし、MIDIファイル、Generator UI、Analyzer UIのテストを実行してから`dist/MerlaiFX.component`を署名します。UIテストでは通常入力、IME未確定入力、タブ移動、プレースホルダー、取り込み中の入力、ドラッグ書き出しを扱います。

## Logicへの配置と実機確認

```sh
mkdir -p ~/Library/Audio/Plug-Ins/Components
ditto dist/MerlaiFX.component ~/Library/Audio/Plug-Ins/Components/MerlaiFX.component
codesign --verify --strict ~/Library/Audio/Plug-Ins/Components/MerlaiFX.component
auval -v aumi MrFx Mrla
```

Logicが起動中にcomponentを置き換えても、ロード済みバイナリは更新されません。プロジェクトを保存してLogicを完全終了し、再起動してから確認します。

実機では2小節以上のサイクルを取り込みながら日本語IMEで指示を入力し、次を確認します。

- キャレットと未確定文字が安定し、プレースホルダーが二重描画されない。
- 進捗バーと音数が入力中も更新される。
- フォーカスを外さなくても取り込み完了になり、青い原案が表示される。
- 入力した指示が保持され、完了後に候補生成へ進める。
- Analyzerでは共有名の編集中もオンセット数が進み、完了後に入力元として公開される。

PRには対象トラック、サイクル範囲、入力中に使ったIME、取り込み完了、ピアノロール表示、`auval`の結果を記録します。制作中の曲や市販プリセットはコミットせず、再配布可能な自作MIDIだけを回帰テストに使います。
