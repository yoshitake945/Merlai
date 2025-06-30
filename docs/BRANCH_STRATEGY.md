# ブランチ戦略とトラブルシューティング

## 📋 ブランチ戦略

### ブランチ構成
```
feature → dev → main
```

### ブランチの役割

- **main**: 本番環境用の安定ブランチ
- **dev**: 開発・統合用のブランチ
- **feature**: 機能開発用のブランチ

### ワークフロー

1. **機能開発**: `feature/機能名`ブランチを作成
2. **dev統合**: featureブランチからdevへPR
3. **本番リリース**: devブランチからmainへPR
4. **自動同期**: mainマージ後、devブランチが自動同期

## 🔄 自動同期ワークフロー

### 概要
mainブランチにマージされた後、自動でdevブランチがmainに同期されます。

### 動作
- **トリガー**: mainブランチへのプッシュ
- **動作**: devブランチをmainに強制同期
- **ワークフロー**: `.github/workflows/sync-dev.yml`

## ⚠️ トラブルシューティング

### 問題: devブランチが分岐している

#### 症状
```bash
$ git status
Your branch and 'origin/dev' have diverged,
and have 1 and 1 different commits each, respectively.
```

#### 原因
- mainにマージされた後、自動同期によりリモートのdevが更新された
- ローカルのdevブランチが古い状態のまま

#### 解決方法

##### 1. 強制リセット（推奨）
```bash
git reset --hard origin/dev
```
- **メリット**: 確実に同期、高速
- **注意**: ローカルの変更は失われる

##### 2. リベース
```bash
git pull --rebase origin dev
```
- **メリット**: 履歴を整理
- **注意**: コンフリクトが発生する可能性

##### 3. ブランチ再作成
```bash
git fetch origin
git checkout -B dev origin/dev
```
- **メリット**: 確実に最新状態
- **注意**: ローカルブランチが完全に再作成される

### 問題: 通常のpullができない

#### 症状
```bash
$ git pull origin dev
fatal: Need to specify how to reconcile divergent branches.
```

#### 解決方法
上記の「強制リセット」を使用してください。

## 🛠️ 日常的な操作

### devブランチの更新
```bash
# 通常の更新（分岐していない場合）
git pull origin dev

# 分岐している場合
git reset --hard origin/dev
```

### 新しい機能開発
```bash
# 新しいfeatureブランチを作成
git checkout -b feature/新機能名

# 開発・コミット
git add .
git commit -m "feat: 新機能の実装"

# devブランチにPR作成
gh pr create --base dev --head feature/新機能名
```

### mainへのリリース
```bash
# devからmainへのPR作成
gh pr create --base main --head dev
```

## 📊 ブランチ状態の確認

### 現在の状態確認
```bash
# ブランチの状態
git status

# 履歴の可視化
git log --oneline --graph --all -10

# リモートブランチの確認
git branch -r
```

### 分岐の確認
```bash
# ローカルとリモートの差分
git log --oneline --graph --all -5
```

## 🔧 設定とカスタマイズ

### Git設定
```bash
# プル時のデフォルト動作設定
git config pull.rebase false  # merge
git config pull.rebase true   # rebase
git config pull.ff only       # fast-forward only
```

### エイリアス設定（オプション）
```bash
# .gitconfigに追加
[alias]
    sync-dev = reset --hard origin/dev
    graph = log --oneline --graph --all -10
```

## 📝 ベストプラクティス

1. **定期的な同期**: 作業前にdevブランチを最新化
2. **早期発見**: `git status`で分岐を早期発見
3. **自動同期を活用**: mainマージ後の自動同期を待つ
4. **バックアップ**: 重要な変更は事前にコミット

## 🆘 緊急時の対処

### 重要な変更がある場合
```bash
# 現在の変更を一時保存
git stash

# devブランチを同期
git reset --hard origin/dev

# 変更を復元
git stash pop
```

### コンフリクトが発生した場合
```bash
# リベースを中止
git rebase --abort

# 強制リセットで解決
git reset --hard origin/dev
```

---

## 📞 サポート

問題が解決しない場合は、以下を確認してください：

1. 現在のブランチ状態: `git status`
2. 履歴の確認: `git log --oneline --graph --all -5`
3. リモートの状態: `git fetch origin`

