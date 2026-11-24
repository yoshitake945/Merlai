# 0005　Model BridgeでLogicとLLMを分離する

- 状態: 採用
- 関連: [#68](https://github.com/yoshitake945/Merlai/issues/68)

## 背景

GeneratorからCodexやClaudeのCLI、Ollama、LM Studioなどを選び、取り込んだMIDIをモデルへ渡したい。一方、Audio Unitのレンダースレッドでプロセス起動、HTTP、JSON処理を行うと、Logicの発音を止める危険がある。クラウドへ送るデータとローカルだけで処理するデータも、画面上で区別する必要がある。

## 決定

モデル検出と呼び出しは、Audio Unitに同梱する別プロセス `ModelBridge` が担当する。GeneratorのCocoa UIはワーカーキューからBridgeを一回の要求ごとに起動し、標準入出力のJSONで通信する。Audio UnitのProcessorとレンダースレッドはBridgeを参照しない。

BridgeはCodex CLI、Claude CLI、Ollama、LM Studio、およびユーザーが指定したローカルOpenAI互換URLを同じプロバイダー一覧へ正規化する。CLIの認証は各CLIの既存ログインへ委譲し、認証情報をMerlaiへ保存しない。モデルが利用できない場合は、既存の決定的なルール生成へフォールバックする。

送るデータは、指示、生成目的、フレーズ範囲、拍子、入力元表示名、MIDIノートに限定する。音声、Logicプロジェクト、プラグイン状態は送らない。CodexとClaudeはクラウドとして扱い、要求のたびに確認を表示する。localhostの互換APIはローカルとして表示し、確認ダイアログなしで実行できる。

## 結果

- モデル処理が遅延・停止してもリアルタイム音声処理をブロックしない。
- 未導入の提供元も利用不可として一覧に残り、導入後に再検出できる。
- Bridgeの入力はモデル非依存で、応答は既存のノート候補へ正規化される。
- Logicのホストコールバックから得たテンポと拍子を送る。まだ再生されておらずテンポが未取得の場合はテンポを省略する。
- 常駐localhostサーバーではなく一回限りのstdioプロセスを採用し、待受ポートと認証面を増やさない。
