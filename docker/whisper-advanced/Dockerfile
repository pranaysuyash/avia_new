# Multi-stage Dockerfile for Whisper Advanced Integration
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for Whisper Advanced
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    gcc \
    g++ \
    libasound2-dev \
    portaudio19-dev \
    libsndfile1-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 whisperuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-whisper-advanced.txt .
RUN pip install --no-cache-dir -r requirements-whisper-advanced.txt

# Download and cache Whisper models
FROM base as model-cache
RUN mkdir -p /app/models
WORKDIR /app/models

# Pre-download Whisper models to reduce startup time
RUN python -c "import whisper; whisper.load_model('tiny')" && \
    python -c "import whisper; whisper.load_model('base')" && \
    python -c "import whisper; whisper.load_model('small')" && \
    python -c "import whisper; whisper.load_model('medium')"

# Production stage
FROM base as production

# Copy pre-downloaded models
COPY --from=model-cache /root/.cache/whisper /home/whisperuser/.cache/whisper

# Copy application code
COPY whisper_advanced_processor.py .
COPY whisper_audio_preprocessor.py .
COPY whisper_advanced_exceptions.py .
COPY api/endpoints/whisper_advanced.py ./api/endpoints/
COPY config/ ./config/
COPY utils/ ./utils/

# Create necessary directories
RUN mkdir -p /app/uploads /app/temp /app/logs /app/models && \
    chown -R whisperuser:whisperuser /app

# Switch to non-root user
USER whisperuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/whisper-advanced/health || exit 1

# Expose port
EXPOSE 8000

# Set resource limits
ENV WHISPER_MODEL_CACHE_SIZE=2
ENV WHISPER_MAX_CONCURRENT_JOBS=3
ENV WHISPER_TEMP_DIR=/app/temp
ENV WHISPER_LOG_LEVEL=INFO

# Start command
CMD ["python", "-m", "uvicorn", "api.endpoints.whisper_advanced:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]