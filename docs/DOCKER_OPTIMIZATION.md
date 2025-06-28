# Docker Optimization Guide

## Current Status

Due to CI/CD pipeline constraints, Merlai currently provides two Docker image variants:

1. **Lightweight Version** (~450MB) - **Currently Available**
   - Minimal dependencies for basic music generation
   - 85% size reduction from original
   - Suitable for most use cases

2. **Optimized CPU Version** (~2GB) - **Temporarily Unavailable**
   - Full AI model support without GPU
   - 35% size reduction from original
   - Currently disabled due to CI/CD build issues

## Lightweight Version Details

### Size Breakdown
- Base Alpine image: ~5MB
- Python runtime: ~40MB
- Core dependencies: ~150MB
- Application code: ~10MB
- Total: ~450MB

### Optimizations Applied
1. **Alpine Linux base** - Minimal OS footprint
2. **Multi-stage build** - Separate build and runtime stages
3. **Dependency optimization** - Only essential packages
4. **Layer caching** - Efficient Docker layer reuse
5. **.dockerignore** - Exclude unnecessary files

### Build Process
```bash
# Build lightweight image
docker build -f docker/Dockerfile.lightweight -t merlai:lightweight .

# Size comparison
docker images | grep merlai
```

## Future Optimizations

When CI/CD constraints are resolved, we plan to reintroduce the optimized CPU version with:

### Multi-Stage Build Strategy
```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as production
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
```

### Dependency Optimization
- Separate dev/test dependencies
- Use `--no-deps` for specific packages
- Remove unnecessary build tools
- Optimize Python package installation

### Layer Optimization
- Combine RUN commands
- Use .dockerignore effectively
- Minimize COPY operations
- Cache pip dependencies

## Performance Comparison

| Version | Size | Build Time | Memory Usage | Use Case |
|---------|------|------------|--------------|----------|
| Original | ~3.1GB | 15min | 2GB+ | Development |
| Lightweight | ~450MB | 5min | 512MB | Production |
| Optimized CPU | ~2GB | 10min | 1GB | AI Features |
| GPU | ~3.1GB | 20min | 4GB+ | AI + GPU |

## Recommendations

### For Development
- Use lightweight version for faster iteration
- Mount source code as volume for live reloading

### For Production
- Use lightweight version unless AI features are required
- Consider GPU version for advanced AI music generation

### For CI/CD
- Use lightweight version for faster builds
- Implement proper caching strategies
- Consider multi-architecture builds

## Troubleshooting

### Build Issues
```bash
# Clean build cache
docker builder prune

# Build with no cache
docker build --no-cache -f docker/Dockerfile.lightweight .

# Check image layers
docker history merlai:lightweight
```

### Size Issues
```bash
# Analyze image size
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Export and analyze layers
docker save merlai:lightweight | tar -tv
```

## Migration Path

When the optimized CPU version becomes available again:

1. **Gradual Migration**
   - Test optimized version in staging
   - Compare performance metrics
   - Update deployment configurations

2. **Rollback Strategy**
   - Keep lightweight version as fallback
   - Monitor resource usage
   - Maintain both versions temporarily

3. **Documentation Updates**
   - Update deployment guides
   - Revise size comparisons
   - Update CI/CD pipelines

---

**Note**: The lightweight version provides excellent performance for most use cases and is recommended for production deployments unless specific AI features are required. 