#!/bin/bash
# エンドツーエンドテストを実行するスクリプト

set -e

echo "========================================="
echo "Merlai エンドツーエンドテスト"
echo "========================================="
echo ""

# PATH設定
export PATH="/home/ubuntu/.local/bin:$PATH"

# ワークスペースディレクトリに移動
cd /workspace

echo "1. 環境確認..."
python3 --version
echo ""

echo "2. ユニットテストとインテグレーションテストの実行..."
python3 -m pytest tests/ -v --disable-warnings --tb=short -k "not test_e2e" | tail -50
echo ""

echo "3. エンドツーエンドテストの実行..."
echo "   注: APIサーバーを起動してテストを実行します"
echo ""

python3 -m pytest tests/test_e2e_live.py -v -s --tb=short
echo ""

echo "========================================="
echo "✅ すべてのテストが完了しました"
echo "========================================="
