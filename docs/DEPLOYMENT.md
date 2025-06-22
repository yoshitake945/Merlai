# Deployment Guide

This guide covers deploying Merlai to production environments, including Docker, Kubernetes, and cloud platforms.

> **Note**: Throughout this guide, `yourdomain.com` and similar domain names are placeholders. Replace them with your actual domain name when deploying.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Platform Deployment](#cloud-platform-deployment)
- [Production Considerations](#production-considerations)
- [Monitoring and Logging](#monitoring-and-logging)
- [Scaling](#scaling)
- [Backup and Recovery](#backup-and-recovery)
- [Security](#security)

## Prerequisites

### System Requirements

- **CPU**: 4+ cores (8+ recommended for production)
- **Memory**: 8GB+ RAM (16GB+ recommended)
- **Storage**: 50GB+ available space
- **Network**: Stable internet connection for model downloads
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows

### Software Requirements

- **Docker**: 20.10+ or **Podman**: 3.0+
- **Kubernetes**: 1.24+ (for K8s deployment)
- **Python**: 3.9+ (for direct deployment)

### Network Requirements

- **Ports**: 8000 (API), 8001 (Health), 8002 (Metrics)
- **Firewall**: Configure to allow required ports
- **SSL/TLS**: Certificate for HTTPS (recommended)

## Environment Configuration

### Environment Variables

Create a `.env` file for your deployment:

```bash
# Application Configuration
MERLAI_ENV=production
MERLAI_LOG_LEVEL=INFO
MERLAI_HOST=0.0.0.0
MERLAI_PORT=8000

# AI Model Configuration
MERLAI_MODEL_PATH=/app/models
MERLAI_MODEL_SIZE=medium
MERLAI_BATCH_SIZE=4

# Performance Configuration
MERLAI_WORKERS=4
MERLAI_MAX_REQUESTS=1000
MERLAI_TIMEOUT=300

# Security Configuration
MERLAI_SECRET_KEY=your-secret-key-here
MERLAI_CORS_ORIGINS=https://yourdomain.com
MERLAI_RATE_LIMIT=100

# Plugin Configuration
MERLAI_PLUGIN_DIRECTORIES=/app/plugins,/usr/local/plugins
MERLAI_PLUGIN_CACHE_SIZE=1000
```

## Docker Deployment

### Production Dockerfile

```dockerfile
FROM python:3.11-slim as production

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN groupadd -r merlai && useradd -r -g merlai merlai

# Copy application code
COPY merlai/ ./merlai/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /app/models /app/plugins /app/logs /app/data && \
    chown -R merlai:merlai /app

USER merlai

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "merlai.api.main"]
```

### Docker Compose for Production

```yaml
version: '3.8'

services:
  merlai:
    build:
      context: .
      dockerfile: docker/Dockerfile.production
    image: merlai:production
    container_name: merlai-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - MERLAI_ENV=production
      - MERLAI_LOG_LEVEL=INFO
    volumes:
      - merlai-models:/app/models
      - merlai-plugins:/app/plugins
      - merlai-logs:/app/logs
      - merlai-data:/app/data
    networks:
      - merlai-network

  nginx:
    image: nginx:alpine
    container_name: merlai-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    networks:
      - merlai-network
    depends_on:
      - merlai

volumes:
  merlai-models:
  merlai-plugins:
  merlai-logs:
  merlai-data:

networks:
  merlai-network:
    driver: bridge
```

## Kubernetes Deployment

### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: merlai
  labels:
    name: merlai
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: merlai-config
  namespace: merlai
data:
  config.yaml: |
    app:
      name: merlai
      version: 1.0.0
      environment: production
    
    server:
      host: 0.0.0.0
      port: 8000
      workers: 4
      timeout: 300
    
    ai:
      model_path: /app/models
      model_size: medium
      batch_size: 4
      cache_size: 1000
    
    security:
      cors_origins:
        - https://yourdomain.com
      rate_limit: 100
    
    plugins:
      directories:
        - /app/plugins
        - /usr/local/plugins
      cache_size: 1000
      scan_interval: 3600
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: merlai-api
  namespace: merlai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: merlai-api
  template:
    metadata:
      labels:
        app: merlai-api
    spec:
      containers:
      - name: merlai
        image: merlai:production
        ports:
        - containerPort: 8000
        env:
        - name: MERLAI_ENV
          value: "production"
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: models
          mountPath: /app/models
        - name: plugins
          mountPath: /app/plugins
        - name: logs
          mountPath: /app/logs
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "1000m"
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
      volumes:
      - name: config
        configMap:
          name: merlai-config
      - name: models
        persistentVolumeClaim:
          claimName: merlai-models-pvc
      - name: plugins
        persistentVolumeClaim:
          claimName: merlai-plugins-pvc
      - name: logs
        persistentVolumeClaim:
          claimName: merlai-logs-pvc
      - name: data
        persistentVolumeClaim:
          claimName: merlai-data-pvc
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: merlai-service
  namespace: merlai
spec:
  selector:
    app: merlai-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

## Production Considerations

### Performance Optimization

1. **Resource Allocation**
   - Allocate sufficient CPU and memory
   - Use SSD storage for models and data
   - Configure proper network bandwidth

2. **Caching Strategy**
   - Implement Redis for session caching
   - Use CDN for static assets
   - Cache generated results

### Security Hardening

1. **Network Security**
   - Use HTTPS/TLS encryption
   - Implement proper firewall rules
   - Use VPN for internal communication

2. **Application Security**
   - Regular security updates
   - Input validation and sanitization
   - Rate limiting and DDoS protection

### Monitoring and Logging

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'merlai'
    static_configs:
      - targets: ['merlai-service:8000']
    metrics_path: '/metrics'
```

### Scaling

1. **Horizontal Scaling**
   - Use nginx or HAProxy for load balancing
   - Implement health checks
   - Configure auto-scaling

2. **Vertical Scaling**
   - Increase CPU and memory allocation
   - Use faster storage (NVMe SSDs)
   - Optimize application code

## Security

### SSL/TLS Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://merlai-service:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

**Note**: This deployment guide should be customized based on your specific requirements and infrastructure. Always test deployments in a staging environment before applying to production. 