# LogicでMerlai MIDI FXを使う

Apple Silicon Macのリポジトリのルートで実行します。ビルドにはCargo、Git、C++23対応のAppleツールチェーンが必要です。初回はAppleのAudioUnitSDKを固定コミットで取得します。

```sh
scripts/build-midi-fx.sh
mkdir -p ~/Library/Audio/Plug-Ins/Components
ditto dist/MerlaiFX.component ~/Library/Audio/Plug-Ins/Components/MerlaiFX.component
auval -v aumi MrFx Mrla
```

1. Logicを起動し、音源の入ったソフトウェア音源トラックの「MIDI FX」で「Audio Units」内のMerlaiを選びます。初回インストール中にLogicが開いていた場合はプロジェクトを保存して起動し直します。
2. 曲中のフレーズを含む2小節をサイクル指定します。Merlai画面の「フレーズを取り込む」を押し、サイクル先頭から一周して再び先頭を通るまで再生します。取り込み完了時に原案の音数が表示されます。
3. 例として「後半だけ音数を半分に。最後の音は残して」を入力し、「変更内容を確認」で音数を見ます。「適用して比較」で次の周回から修正案を鳴らします。「原案」「修正案」の切り替えもループ先頭で反映されます。
4. 再編集には「もう少し減らして」、直前の状態に戻るには「一手戻す」を使います。自由な文章への対応は限定的です。「休符を増やして」も発音の間引きとして扱います。
5. 採用時は送信元でMerlai直後を「MIDIをこのトラックに録音」の位置に指定し、別のソフトウェア音源トラックの内部MIDI入力で送信元を選択します。受け側を録音可能にして対象区間を録音し、ピアノロールで確認します。両トラックが発音するときは試聴用の出力を調整します。[Logicの内部MIDIルーティング](https://support.apple.com/guide/logicpro/lgcp1efa7c4d/mac)

取り込み上限は2048音です。再取り込みで履歴が消えるため、残す案は先に録音してください。MIDIのチャンネルメッセージを対象とし、SysEx・MIDI 2.0・プリセットの自動識別は対象外です。
