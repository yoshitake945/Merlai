# Optimized multi-stage build for Merlai AI Music Assistant
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy requirements and source code first for better caching
COPY pyproject.toml ./
COPY README.md ./
COPY merlai/ ./merlai/

# Create non-root user before pip install
RUN useradd --create-home --shell /bin/bash merlai

# Install dependencies in user space for merlai user
USER merlai
ENV PATH="/home/merlai/.local/bin:$PATH"
WORKDIR /app
RUN pip install --user --no-cache-dir -e .[cpu,ai]

# Production stage
FROM python:3.11-slim AS production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash merlai && \
    chown -R merlai:merlai /app

# Copy Python packages and app from builder
COPY --from=builder /home/merlai/.local /home/merlai/.local
COPY --from=builder /app /app

USER merlai
ENV PATH="/home/merlai/.local/bin:$PATH"

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["merlai", "serve", "--host", "0.0.0.0", "--port", "8000"]

# Development stage (optional)
FROM production AS development

USER root

# Install development dependencies
RUN pip install --user --no-cache-dir -e .[dev]

USER merlai

EXPOSE 8000 8001

CMD ["merlai", "serve", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# GPU inference stage
FROM python:3.11-slim AS gpu-inference

# Install additional GPU-specific dependencies
RUN pip install torch[cu118] torchaudio[cu118] --index-url https://download.pytorch.org/whl/cu118

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash merlai && \
    chown -R merlai:merlai /app

USER merlai

EXPOSE 8000

CMD ["python", "-m", "merlai.inference.server"] 