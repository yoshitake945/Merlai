# Troubleshooting Guide

This guide helps you resolve common issues with Merlai. If you don't find your issue here, please create a GitHub issue with detailed information.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Runtime Issues](#runtime-issues)
- [API Issues](#api-issues)
- [Plugin Issues](#plugin-issues)
- [Performance Issues](#performance-issues)
- [Docker Issues](#docker-issues)
- [Development Issues](#development-issues)
- [Getting Help](#getting-help)

## Installation Issues

### Python Version Issues

**Problem**: `Python 3.9+ is required`

**Solution**:
```bash
# Check your Python version
python --version

# If using pyenv
pyenv install 3.11.6
pyenv global 3.11.6

# If using conda
conda create -n merlai python=3.11
conda activate merlai
```

### Virtual Environment Issues

**Problem**: `venv module not found`

**Solution**:
```bash
# Install venv (Ubuntu/Debian)
sudo apt-get install python3-venv

# Install venv (macOS)
brew install python3

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### Dependency Installation Issues

**Problem**: `pip install fails`

**Solution**:
```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -v -r requirements.txt

# If specific package fails
pip install --no-cache-dir package-name
```

## Runtime Issues

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'merlai'`

**Solution**:
```bash
# Install in development mode
pip install -e .

# Or activate virtual environment
source venv/bin/activate
```

### Permission Issues

**Problem**: `Permission denied` errors

**Solution**:
```bash
# Fix file permissions
chmod +x scripts/*.sh

# Fix directory permissions
chmod 755 merlai/

# If using Docker
sudo usermod -aG docker $USER
```

### Memory Issues

**Problem**: `MemoryError` or `OutOfMemoryError`

**Solution**:
```bash
# Reduce batch size
export MERLAI_BATCH_SIZE=1

# Use CPU-only mode
export MERLAI_USE_GPU=false

# Increase swap space (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## API Issues

### Server Won't Start

**Problem**: `Address already in use`

**Solution**:
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
merlai serve --port 8001
```

### API Timeout Issues

**Problem**: `Request timeout`

**Solution**:
```bash
# Increase timeout
merlai serve --timeout 300

# Check server logs
tail -f logs/merlai.log
```

### CORS Issues

**Problem**: `CORS error` in browser

**Solution**:
```bash
# Enable CORS
merlai serve --cors

# Or configure specific origins
merlai serve --cors-origins "http://localhost:3000,https://yourdomain.com"
```

## Plugin Issues

### Plugin Not Found

**Problem**: `Plugin not found` error

**Solution**:
```bash
# Scan for plugins
merlai scan-plugins

# Check plugin directories
merlai scan-plugins --list-directories

# Add custom plugin directory
merlai scan-plugins --directory /path/to/plugins
```

### Plugin Loading Issues

**Problem**: `Failed to load plugin`

**Solution**:
```bash
# Check plugin compatibility
merlai scan-plugins --verbose

# Verify plugin file permissions
ls -la /path/to/plugin.vst

# Check plugin dependencies
ldd /path/to/plugin.vst
```

### Plugin Recommendations Not Working

**Problem**: No plugin recommendations

**Solution**:
```bash
# Force plugin scan
merlai scan-plugins --force

# Check recommendation logic
merlai recommend-plugins --style pop --instrument lead --verbose
```

## Performance Issues

### Slow Music Generation

**Problem**: Generation takes too long

**Solution**:
```bash
# Enable GPU acceleration
export MERLAI_USE_GPU=true

# Reduce model complexity
export MERLAI_MODEL_SIZE=small

# Use caching
export MERLAI_ENABLE_CACHE=true
```

### High Memory Usage

**Problem**: Excessive memory consumption

**Solution**:
```bash
# Limit memory usage
export MERLAI_MAX_MEMORY=4GB

# Use streaming generation
export MERLAI_STREAMING=true

# Enable garbage collection
export MERLAI_GC_FREQUENCY=100
```

### Slow API Response

**Problem**: API responses are slow

**Solution**:
```bash
# Enable async processing
export MERLAI_ASYNC=true

# Use connection pooling
export MERLAI_POOL_SIZE=10

# Enable response compression
export MERLAI_COMPRESS=true
```

## Docker Issues

### Container Won't Start

**Problem**: `Docker container exits immediately`

**Solution**:
```bash
# Check container logs
docker logs merlai-container

# Run with interactive mode
docker run -it merlai:latest /bin/bash

# Check resource limits
docker run --memory=4g --cpus=2 merlai:latest
```

### Port Binding Issues

**Problem**: `Port already in use`

**Solution**:
```bash
# Use different port
docker run -p 8001:8000 merlai:latest

# Check port usage
netstat -tulpn | grep :8000

# Kill conflicting process
sudo fuser -k 8000/tcp
```

### Volume Mount Issues

**Problem**: `Permission denied` on mounted volumes

**Solution**:
```bash
# Fix volume permissions
docker run -v /host/path:/container/path:rw merlai:latest

# Use named volumes
docker volume create merlai-data
docker run -v merlai-data:/app/data merlai:latest
```

## Development Issues

### Test Failures

**Problem**: `pytest fails`

**Solution**:
```bash
# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/test_api.py::TestAPIEndpoints::test_health_check

# Run with coverage
pytest --cov=merlai --cov-report=html
```

### Type Checking Issues

**Problem**: `mypy errors`

**Solution**:
```bash
# Run mypy with verbose output
mypy --verbose merlai/

# Ignore specific errors
mypy --ignore-missing-imports merlai/

# Generate stub files
mypy --stubgen merlai/
```

### Linting Issues

**Problem**: `flake8/black errors`

**Solution**:
```bash
# Auto-format code
black merlai/
isort merlai/

# Fix specific issues
flake8 --max-line-length=88 merlai/
```

### Debug Mode

**Problem**: Need to debug issues

**Solution**:
```bash
# Enable debug logging
export MERLAI_LOG_LEVEL=DEBUG

# Run with debugger
python -m pdb -m merlai.api.main

# Use debug Docker image
docker run merlai:debug
```

## Log Analysis

### Understanding Logs

**Log Levels**:
- `DEBUG`: Detailed information for debugging
- `INFO`: General information about program execution
- `WARNING`: Warning messages for potentially problematic situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical errors that may prevent the program from running

**Common Log Patterns**:
```bash
# Filter by log level
grep "ERROR" logs/merlai.log

# Filter by time
grep "2024-01-15" logs/merlai.log

# Filter by component
grep "music_generator" logs/merlai.log
```

### Performance Monitoring

**Key Metrics**:
- Response time
- Memory usage
- CPU usage
- GPU utilization (if applicable)

**Monitoring Commands**:
```bash
# Monitor system resources
htop
nvidia-smi  # GPU monitoring

# Monitor application
ps aux | grep merlai
lsof -p <pid>
```

## Getting Help

### Before Asking for Help

1. **Check this guide** for common solutions
2. **Search existing issues** on GitHub
3. **Check the logs** for error messages
4. **Try the latest version** of Merlai
5. **Reproduce the issue** in a minimal environment

### When Creating an Issue

Please include:

1. **Environment details**:
   - OS and version
   - Python version
   - Merlai version
   - Docker version (if applicable)

2. **Steps to reproduce**:
   - Exact commands run
   - Input data used
   - Expected vs actual behavior

3. **Error messages**:
   - Full error traceback
   - Log files
   - Screenshots (if applicable)

4. **Additional context**:
   - What you were trying to do
   - Any recent changes
   - Workarounds you've tried

### Contact Information

- **GitHub Issues**: [Create an issue](https://github.com/yoshitake945/merlai/issues)
- **Project Maintainer**: [@yoshitake945](https://github.com/yoshitake945)

---

**Note**: This troubleshooting guide is continuously updated. If you find a solution that's not documented here, please contribute it by creating a pull request. 