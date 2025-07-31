# Audio/Video Transcription App - Production Docker Configuration
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies with security updates
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    ca-certificates \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with security considerations
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories with proper permissions
RUN mkdir -p temp logs \
    && chown -R appuser:appuser /app \
    && chmod 755 /app \
    && chmod 755 temp logs

# Set production environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
ENV STREAMLIT_SERVER_MAX_UPLOAD_SIZE=100
ENV STREAMLIT_SERVER_MAX_MESSAGE_SIZE=200
ENV STREAMLIT_LOGGER_LEVEL=INFO
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Security settings
ENV STREAMLIT_SERVER_COOKIE_SECRET=""
ENV STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=false

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8501

# Enhanced health check with custom endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/health || exit 1

# Run the application with production settings
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=true", \
     "--logger.level=info"]