# Merlai Architecture Design

## ⚠️ Important Notice / 重要な注記

**AI-Assisted Development / AIアシスト開発:**
このアーキテクチャ設計書は、AIコーディングアシスタントの支援を受けて作成されています。
開発者は技術スタックに習熟しているわけではなく、AIの提案に基づいて設計を進めています。
実装前に十分な技術検証とレビューを推奨します。

This architecture document was created with the assistance of AI coding tools.
The developer is not proficient in the technical stacks and relies on AI suggestions for design decisions.
Thorough technical validation and review are recommended before implementation.

**Language Proficiency / 言語能力:**
開発者は英語が堪能ではないため、技術的な説明に不自然な点や誤りが含まれる可能性があります。
詳細な技術議論については、日本語でのコミュニケーションを推奨します。

The developer is not fluent in English, so there may be unnatural expressions or mistakes in technical explanations.
For detailed technical discussions, Japanese communication is recommended.

## システム概要
楽曲制作支援AIシステム - メインメロディを基に、AIが不足音を補完し、MIDIデータとして出力

## 技術スタック

### コア技術
- **AI/ML**: Python + PyTorch/TensorFlow
- **パフォーマンス**: Rust (音声処理、MIDI生成)
- **API**: FastAPI (Python)
- **型安全性**: mypy, pydantic, dataclasses

### インフラストラクチャ
- Docker（CPU/GPU両対応: Apple SiliconやGPU非搭載環境もサポート）
- Kubernetes
- NVIDIA Container Runtime（GPU利用時のみ）
- **ストレージ**: MinIO (S3互換)

## アーキテクチャ構成

### 1. マイクロサービス構成
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Auth Service  │
│   (React/Vue)   │◄──►│   (Kong/Nginx)  │◄──►│   (JWT/OAuth)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  MIDI Generator │    │  AI Orchestrator│    │  Plugin Manager │
│   (Rust)        │◄──►│   (Python)      │◄──►│   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Model Service  │    │  Training       │    │  Data Pipeline  │
│   (GPU)         │    │  Service        │    │   (ETL)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. エッジコンピューティング構成
```
作曲家のローカル環境:
┌─────────────────────────────────────────────────────────────┐
│                    Local GPU Server                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   DAW       │  │  Merlai     │  │  Plugin     │        │
│  │  Integration│◄─┤  Local API  │◄─┤  Registry   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│           │              │                    │            │
│           ▼              ▼                    ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  MIDI       │  │  AI Model   │  │  Sound      │        │
│  │  Generator  │  │  (Fine-tuned│  │  Plugins    │        │
│  └─────────────┘  │  for user)  │  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## パフォーマンス最適化戦略

### 1. 言語選択の理由
- **Python**: AI/MLライブラリの豊富さ、開発速度
- **Rust**: 音声処理、MIDI生成の高速化
- **型安全性**: バグ削減、リファクタリング安全性

### 2. GPU活用
- **推論**: TensorRT最適化
- **バッチ処理**: 複数楽曲の並列処理
- **メモリ管理**: 効率的なGPUメモリ使用

### 3. キャッシュ戦略
- **Redis**: 生成結果のキャッシュ
- **CDN**: プラグイン配布
- **ローカルキャッシュ**: 頻繁使用パターンの保存

## 開発フェーズ

### Phase 1: 基盤構築
- [x] CPU専用Dockerfileとdocker-composeサービス（`merlai-cpu`）の実装
- [x] Apple Silicon/Mac環境での動作検証
- [ ] Docker環境構築
- [ ] Kubernetesクラスタ設定
- [ ] 基本的なMIDI生成API
- [ ] 型安全なPythonコードベース

### Phase 2: AI統合
- [ ] 音楽生成モデルの実装
- [ ] GPU最適化
- [ ] リアルタイム生成API
- [ ] プラグイン管理システム

### Phase 3: エッジ展開
- [ ] ローカルGPUサーバー構築
- [ ] オフライン対応
- [ ] 個人化モデル
- [ ] DAW統合

### Phase 4: ローカル作曲環境（新規追加）
- [ ] **ローカルGPU作曲処理**
  - [ ] ローカルGPU推論エンジン（TensorRT/PyTorch）
  - [ ] 低レイテンシーMIDI生成（<50ms）
  - [ ] リアルタイム伴奏生成
  - [ ] ローカルモデルキャッシュ
- [ ] **DAWプロジェクト連携**
  - [ ] Logic Pro X プロジェクトスキャン
  - [ ] Ableton Live プロジェクトスキャン
  - [ ] Cubase/Nuendo プロジェクトスキャン
  - [ ] MIDI/オーディオトラック解析
  - [ ] 既存楽曲パターン学習
- [ ] **プラグイン音源スキャン**
  - [ ] VST/AUプラグイン自動検出
  - [ ] 音色パラメータ解析
  - [ ] プリセット音色カタログ化
  - [ ] AI音色選択・提案
  - [ ] カスタム音色生成

## 実装ロードマップ

### Phase 4.1: ローカルGPU基盤（最優先）
1. **ローカルGPU推論エンジン**
   - PyTorch GPU最適化
   - TensorRT統合
   - 低レイテンシー推論パイプライン

2. **リアルタイム通信基盤**
   - WebSocket API実装
   - リアルタイムMIDIストリーミング
   - ローカルキャッシュシステム

### Phase 4.2: DAW連携（中優先）
1. **Logic Pro X連携**
   - .logicxファイル解析
   - MIDIトラック抽出
   - プロジェクト情報読み取り

2. **他DAW対応**
   - Ableton Live (.als)
   - Cubase (.cpr)
   - 共通インターフェース設計

### Phase 4.3: プラグイン音源スキャン（低優先）
1. **VST3スキャン**
   - プラグイン自動検出
   - 音色パラメータ解析
   - プリセット抽出

2. **Audio Unit対応**
   - macOS専用機能
   - Logic Pro X統合強化

## ローカル作曲環境の技術仕様

### 1. ローカルGPU作曲処理
```
技術スタック:
- PyTorch/TensorRT (GPU推論最適化)
- Rust (低レイテンシーMIDI処理)
- WebSocket (リアルタイム通信)
- SQLite (ローカルキャッシュ)

パフォーマンス目標:
- MIDI生成: <50ms
- リアルタイム伴奏: <20ms
- GPUメモリ使用: <4GB
```

### 2. DAWプロジェクト連携
```
対応DAW:
- Logic Pro X (.logicx)
- Ableton Live (.als)
- Cubase (.cpr)
- Pro Tools (.ptx)

解析機能:
- MIDIトラック抽出
- オーディオトラック分析
- プラグイン設定読み取り
- テンポ・キー情報取得
```

### 3. プラグイン音源スキャン
```
対応プラグイン形式:
- VST3 (.vst3)
- Audio Unit (.component)
- AAX (.aax)

スキャン機能:
- 自動プラグイン検出
- 音色パラメータ解析
- プリセット音色抽出
- メタデータ生成
```

## 期待されるイノベーション

### 1. リアルタイム作曲支援
- 演奏中のリアルタイム伴奏生成
- 即座のフィードバック

### 2. 個人化AI
- 作曲家のスタイル学習
- カスタムモデルの自動生成

### 3. 分散処理
- 複数GPUの効率的活用
- クラウド・エッジの連携

### 4. プラグインエコシステム
- 自動プラグイン提案
- 音色の自動選択

## 期待される効果

### 作曲家への価値
- **低レイテンシー**: リアルタイム作曲支援
- **既存資産活用**: DAWプロジェクトの継続利用
- **音色最適化**: 所有プラグインの自動活用
- **オフライン作業**: クラウド不要の作曲環境

### 技術的メリット
- **GPU効率化**: ローカルGPUの最大活用
- **データ統合**: DAW・プラグイン・AIの連携
- **パフォーマンス**: エッジコンピューティングの恩恵 

## Phase 4対応の改善アーキテクチャ

### 1. リアルタイム処理基盤
```
┌─────────────────────────────────────────────────────────────┐
│                    Real-time Processing Layer               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ WebSocket   │  │ MIDI Stream │  │ Audio       │        │
│  │ Gateway     │◄─┤ Processor   │◄─┤ Processor   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│           │              │                    │            │
│           ▼              ▼                    ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Real-time   │  │ Low-latency │  │ GPU         │        │
│  │ AI Engine   │  │ MIDI Gen    │  │ Optimizer   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 2. DAW統合アーキテクチャ
```
┌─────────────────────────────────────────────────────────────┐
│                    DAW Integration Layer                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Logic Pro   │  │ Ableton     │  │ Cubase      │        │
│  │ Scanner     │  │ Scanner     │  │ Scanner     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│           │              │                    │            │
│           ▼              ▼                    ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Project     │  │ Pattern     │  │ Style       │        │
│  │ Analyzer    │  │ Learner     │  │ Extractor   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 3. プラグイン音源AI統合
```
┌─────────────────────────────────────────────────────────────┐
│                    Plugin AI Integration                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ VST3        │  │ Audio Unit  │  │ AAX         │        │
│  │ Scanner     │  │ Scanner     │  │ Scanner     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│           │              │                    │            │
│           ▼              ▼                    ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Sound       │  │ AI Sound    │  │ Custom      │        │
│  │ Analyzer    │  │ Selector    │  │ Generator   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 新たなバリュー提案

### 1. **AI音色生成・最適化**
- **既存プラグイン音色のAI分析**: 所有プラグインの音色特性を学習
- **カスタム音色生成**: AIが作曲に最適な音色を自動生成
- **音色マッチング**: 楽曲スタイルに最適な音色を自動選択

### 2. **楽曲スタイル学習・継承**
- **既存楽曲パターン学習**: DAWプロジェクトから作曲パターンを抽出
- **スタイル継承**: 過去の楽曲スタイルを新しい楽曲に適用
- **楽曲進化**: 既存楽曲を基にバリエーションを自動生成

### 3. **リアルタイム作曲支援**
- **演奏中の伴奏生成**: リアルタイムで伴奏を生成・調整
- **即座のフィードバック**: 演奏と同時にAIが提案
- **インタラクティブ作曲**: 人間とAIの協調作曲

### 4. **分散AI処理**
- **エッジ・クラウド連携**: ローカルGPU + クラウドAIの最適化
- **マルチGPU活用**: 複数GPUの効率的な分散処理
- **オフライン対応**: インターネット不要の作曲環境

## 技術的改善点

### 1. **リアルタイム処理基盤**
```python
# 新規追加が必要なモジュール
- merlai/core/realtime.py      # リアルタイム処理エンジン
- merlai/core/websocket.py     # WebSocket通信
- merlai/core/streaming.py     # MIDIストリーミング
- merlai/core/gpu_optimizer.py # GPU最適化
```

### 2. **DAW統合モジュール**
```python
# 新規追加が必要なモジュール
- merlai/core/daw/             # DAW統合ディレクトリ
  - logic_scanner.py           # Logic Pro Xスキャン
  - ableton_scanner.py         # Ableton Liveスキャン
  - project_analyzer.py        # プロジェクト解析
  - pattern_learner.py         # パターン学習
```

### 3. **プラグインAI統合**
```python
# 新規追加が必要なモジュール
- merlai/core/plugins/         # プラグイン拡張ディレクトリ
  - sound_analyzer.py          # 音色解析
  - ai_selector.py             # AI音色選択
  - custom_generator.py        # カスタム音色生成
``` 