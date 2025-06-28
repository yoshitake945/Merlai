# Deployment Guide

## Docker Deployment

### Available Images

Merlai provides two Docker image variants:

1. **Lightweight Version** (~450MB)
   - Tag: `ghcr.io/your-org/merlai:latest`
   - Minimal dependencies for basic music generation
   - Suitable for development, testing, and production
   - 85% size reduction from original

2. **GPU Version** (~3.1GB)
   - Tag: `ghcr.io/your-org/merlai:latest-gpu`
   - Full AI model support with GPU acceleration
   - Requires NVIDIA Docker runtime
   - For advanced AI-powered music generation

### Quick Deployment

```bash
# Lightweight version (recommended)
docker run -d \
  --name merlai \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  ghcr.io/your-org/merlai:latest

# GPU version
docker run -d \
  --name merlai-gpu \
  --gpus all \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  ghcr.io/your-org/merlai:latest-gpu
```

### Production Deployment

For production environments, we recommend using the lightweight version unless you specifically need GPU acceleration:

```yaml
# docker-compose.yml
version: '3.8'
services:
  merlai:
    image: ghcr.io/your-org/merlai:latest
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - ENVIRONMENT=production
    restart: unless-stopped
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: merlai
spec:
  replicas: 2
  selector:
    matchLabels:
      app: merlai
  template:
    metadata:
      labels:
        app: merlai
    spec:
      containers:
      - name: merlai
        image: ghcr.io/your-org/merlai:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: merlai-data
```

**Note**: The optimized CPU version (~2GB) is temporarily unavailable due to CI/CD constraints. The lightweight version provides excellent performance for most production use cases. 