# Multi-stage build for Merlai AI Music Assistant
FROM nvidia/cuda:11.8-devel-ubuntu22.04 as base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    python3.10-venv \
    git \
    curl \
    wget \
    build-essential \
    libsndfile1 \
    libasound2-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3.10 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY pyproject.toml /tmp/
RUN pip install -e /tmp/[gpu]

# Development stage
FROM base as development

# Install development dependencies
RUN pip install -e /tmp/[dev]

# Copy source code
COPY . /app
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 merlai && chown -R merlai:merlai /app
USER merlai

# Expose ports
EXPOSE 8000 8001

# Default command
CMD ["uvicorn", "merlai.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Copy source code
COPY . /app
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 merlai && chown -R merlai:merlai /app
USER merlai

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "merlai.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# GPU inference stage
FROM base as gpu-inference

# Install additional GPU-specific dependencies
RUN pip install torch[cu118] torchaudio[cu118] --index-url https://download.pytorch.org/whl/cu118

# Copy source code
COPY . /app
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 merlai && chown -R merlai:merlai /app
USER merlai

# Expose ports
EXPOSE 8000

# Default command for GPU inference
CMD ["python", "-m", "merlai.inference.server"] 