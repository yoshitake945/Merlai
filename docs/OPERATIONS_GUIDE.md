# Merlai 運用ガイド

## 概要

Merlaiは複数のコンテナランタイムとKubernetesに対応し、可用性要件に応じた段階的な運用が可能な設計になっています。

## ⚠️ 重要な注記

**このドキュメントはAIによる提案が中心であり、実際の運用では以下の点について多くの議論と検討が必要です：**

- **可用性要件の詳細定義**: 99%〜99.9%の具体的な意味と測定方法
- **セキュリティ要件の検討**: 組織のセキュリティポリシーとの整合性
- **コスト最適化**: リソース使用量と運用コストのバランス
- **チームスキルレベル**: 運用チームの技術レベルに応じた複雑度の調整
- **監査・コンプライアンス**: 業界規制や組織のコンプライアンス要件
- **復旧計画**: データバックアップと復旧手順の詳細設計
- **パフォーマンス要件**: レスポンスタイムやスループットの具体的な目標値

**このドキュメントは参考資料として活用し、実際の導入前には関係者との十分な議論と検証を行ってください。**

## 🏗️ 可用性レベル別アーキテクチャ

### Level 1: 開発・テスト環境
```
┌─────────────────────────────────────────────────────────────┐
│                    開発・テスト環境                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Merlai    │  │   Redis     │  │  PostgreSQL │        │
│  │   API       │  │  (Cache)    │  │  (Metadata) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│           │              │                    │            │
│           ▼              ▼                    ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Docker    │  │   Volume    │  │   Network   │        │
│  │  Compose    │  │  (Local)    │  │  (Bridge)   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Level 2: ステージング環境
```
┌─────────────────────────────────────────────────────────────┐
│                    ステージング環境                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Merlai    │  │   Redis     │  │  PostgreSQL │        │
│  │   API       │  │  (Cache)    │  │  (Metadata) │        │
│  │ (Replica:2) │  │ (Cluster)   │  │ (Replica)   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│           │              │                    │            │
│           ▼              ▼                    ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Kubernetes  │  │  Persistent │  │   Load      │        │
│  │  (Single)   │  │   Volume    │  │  Balancer   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Level 3: 本番環境
```
┌─────────────────────────────────────────────────────────────┐
│                      本番環境                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Merlai    │  │   Redis     │  │  PostgreSQL │        │
│  │   API       │  │  (Cache)    │  │  (Metadata) │        │
│  │(Replica:3+) │  │ (Cluster)   │  │ (Replica)   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│           │              │                    │            │
│           ▼              ▼                    ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Kubernetes  │  │  Storage    │  │ Monitoring  │        │
│  │ (Multi-Node)│  │ (Distributed)│  │ & Logging   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 対応コンテナランタイム

### 1. Docker (推奨)
```bash
# 標準的な使用方法
docker build -f docker/Dockerfile.cpu -t merlai:latest .
docker run -p 8000:8000 merlai:latest

# 開発環境
docker-compose up -d
```

### 2. Podman (セキュリティ重視)
```bash
# rootless実行
podman build -f docker/Dockerfile.cpu -t merlai:latest .
podman run -p 8000:8000 merlai:latest

# Podman Compose
podman-compose up -d
```

### 3. containerd (軽量)
```bash
# 軽量ランタイム
ctr images pull merlai:latest
ctr run --rm -t merlai:latest merlai-instance
```

## 🔄 統合管理スクリプト

### 基本使用方法
```bash
# スクリプトを実行可能にする
chmod +x scripts/container-runtime.sh

# ヘルプを表示
./scripts/container-runtime.sh help

# サービスを起動
./scripts/container-runtime.sh up

# ログを表示
./scripts/container-runtime.sh logs

# サービスを停止
./scripts/container-runtime.sh down
```

### 環境変数
```bash
# コンテナランタイムを指定
export CONTAINER_RUNTIME=podman

# プロジェクト名を指定
export PROJECT_NAME=my-merlai

# カスタムcomposeファイルを指定
export COMPOSE_FILE=docker-compose.prod.yml
```

## 📊 可用性要件別設定

> **注意**: 以下の設定は一般的な例であり、実際の運用では組織の要件に応じて調整が必要です。可用性目標、リソース制限、スケーリング戦略は、ビジネス要件と技術的制約を考慮して決定してください。

### Level 1: 開発・テスト (99%可用性)

> **検討事項**: 開発チームの規模、テスト環境の重要性、データの機密性レベル
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  merlai-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### Level 2: ステージング (99.5%可用性)

> **検討事項**: ステージング環境の役割、本番環境との類似性、データの整合性要件
```yaml
# k8s/staging-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: merlai-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: merlai-api
  template:
    spec:
      containers:
      - name: merlai-api
        image: merlai:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Level 3: 本番 (99.9%可用性)

> **検討事項**: ビジネス継続性要件、コスト制約、運用チームのスキルレベル、監査要件
```yaml
# k8s/production-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: merlai-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: merlai-api
  template:
    spec:
      containers:
      - name: merlai-api
        image: merlai:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: merlai-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: merlai-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🔐 セキュリティ設定

> **注意**: セキュリティ設定は組織のセキュリティポリシーに従って決定してください。以下の設定は一般的な例であり、実際の運用ではセキュリティチームとの相談が必要です。

### 基本セキュリティ

> **検討事項**: 組織のセキュリティ基準、コンプライアンス要件、監査要件
```yaml
# 非rootユーザー実行
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

# 読み取り専用ルートファイルシステム
securityContext:
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

### ネットワークポリシー

> **検討事項**: ネットワークセグメンテーション戦略、アクセス制御要件、監視要件
```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: merlai-network-policy
spec:
  podSelector:
    matchLabels:
      app: merlai-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    ports:
    - protocol: TCP
      port: 5432
```

## 📈 監視とログ

### 基本監視
```yaml
# ヘルスチェックエンドポイント
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### ログ設定
```yaml
# 構造化ログ
apiVersion: v1
kind: ConfigMap
metadata:
  name: merlai-logging
data:
  log-config.yaml: |
    version: 1
    formatters:
      json:
        format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    handlers:
      console:
        class: logging.StreamHandler
        formatter: json
    root:
      level: INFO
      handlers: [console]
```

## 🔧 トラブルシューティング

### よくある問題

#### 1. コンテナが起動しない
```bash
# ログを確認
./scripts/container-runtime.sh logs

# コンテナの詳細情報を確認
docker inspect <container_id>

# リソース使用量を確認
docker stats
```

#### 2. メモリ不足
```bash
# メモリ使用量を確認
kubectl top pods -n merlai

# リソース制限を調整
kubectl patch deployment merlai-api -p '{"spec":{"template":{"spec":{"containers":[{"name":"merlai-api","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
```

#### 3. ネットワーク問題
```bash
# ネットワーク接続を確認
kubectl exec -it <pod-name> -- curl -v http://service-name:port

# ネットワークポリシーを確認
kubectl get networkpolicy -n merlai
```

## 🏆 運用プラクティス

> **注意**: 運用プラクティスは組織の文化、チーム構成、技術レベルに応じて調整してください。以下のプラクティスは一般的な例であり、実際の導入には十分な検討と段階的な導入が必要です。

### 1. デプロイメント戦略

> **検討事項**: リリース頻度、ダウンタイム許容度、ロールバック戦略、テスト戦略
- **Blue-Green**: ゼロダウンタイムデプロイ
- **Rolling Update**: 段階的更新
- **Canary**: リスク軽減デプロイ

### 2. バックアップ戦略

> **検討事項**: データの重要度、復旧時間目標（RTO）、復旧ポイント目標（RPO）、コスト制約
```bash
# データベースバックアップ
kubectl exec -it <postgres-pod> -- pg_dump -U merlai merlai > backup.sql

# 設定バックアップ
kubectl get configmap -n merlai -o yaml > config-backup.yaml
```

### 3. スケーリング戦略

> **検討事項**: トラフィックパターン、コスト効率、パフォーマンス要件、リソース制約
```bash
# 手動スケーリング
kubectl scale deployment merlai-api --replicas=5

# 自動スケーリング
kubectl autoscale deployment merlai-api --min=2 --max=10 --cpu-percent=80
```

### 4. 監視戦略

> **検討事項**: 監視ツールの選定、アラート閾値の設定、エスカレーション手順、ダッシュボード設計
- **アプリケーションメトリクス**: レスポンスタイム、エラー率
- **インフラメトリクス**: CPU、メモリ、ディスク使用量
- **ビジネスメトリクス**: ユーザー数、リクエスト数

## 📚 参考資料

- [Kubernetes公式ドキュメント](https://kubernetes.io/docs/)
- [Docker公式ドキュメント](https://docs.docker.com/)
- [Podman公式ドキュメント](https://podman.io/getting-started/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

## 🚀 次のステップ

このドキュメントを参考に、以下の手順で実際の運用設計を進めることを推奨します：

### 1. 要件定義フェーズ
- [ ] ビジネス要件の明確化（可用性、パフォーマンス、セキュリティ）
- [ ] 技術要件の定義（インフラ、ツール、スキル）
- [ ] 制約条件の整理（コスト、リソース、時間）

### 2. 設計フェーズ
- [ ] アーキテクチャ設計の詳細化
- [ ] セキュリティ設計の策定
- [ ] 監視・ログ設計の策定
- [ ] 災害復旧計画の策定

### 3. 実装フェーズ
- [ ] 段階的な実装計画の策定
- [ ] プロトタイプの作成と検証
- [ ] 本格実装とテスト

### 4. 運用フェーズ
- [ ] 運用手順書の作成
- [ ] チーム研修の実施
- [ ] 継続的な改善と最適化

## ⚠️ 最終的な注意事項

**このドキュメントはAIによる提案であり、実際の運用では以下が重要です：**

1. **関係者との十分な議論**: 技術チーム、ビジネスチーム、セキュリティチームとの協働
2. **段階的な導入**: 一度に全てを導入せず、段階的に複雑度を上げる
3. **継続的な改善**: 運用開始後も定期的な見直しと改善
4. **リスク管理**: 各段階でのリスク評価と対策の実施
5. **コスト管理**: 運用コストの継続的な監視と最適化

**このドキュメントを参考資料として活用し、組織の実情に応じた適切な運用設計を行ってください。** 