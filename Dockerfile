# Multi-stage build for optimized layer caching and smaller final image

# Stage 1: Builder stage with all dependencies
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y git build-essential && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip and install Poetry
RUN pip install --upgrade pip && \
    pip install poetry

# Configure Poetry for production
RUN poetry config virtualenvs.create false && \
    poetry config cache-dir /tmp/poetry_cache

# Copy dependency files first (optimized layer caching)
COPY pyproject.toml poetry.lock* ./

# Install dependencies with cache optimization
RUN poetry install --only=main --no-root && \
    rm -rf /tmp/poetry_cache

# Stage 2: Runtime stage with minimal dependencies
FROM python:3.12-slim as runtime

# Install only runtime dependencies (including curl for health checks)
RUN apt-get update && apt-get install -y git curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security
# Use host user ID if provided, otherwise use default 999
ARG USER_ID=999
ARG GROUP_ID=999
RUN groupadd -r -g ${GROUP_ID} pyhabot && \
    useradd -r -u ${USER_ID} -g pyhabot pyhabot

# Set working directory
WORKDIR /app
ENV PERSISTENT_DATA_PATH=/data

# Create persistent data directory with proper permissions
RUN mkdir -p /data && chown pyhabot:pyhabot /data

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=pyhabot:pyhabot . .

# Install the application
RUN pip install -e . && \
    rm -rf /root/.cache/pip

# Copy entrypoint scripts and set permissions
COPY --chown=pyhabot:pyhabot entrypoint.sh /entrypoint.sh
COPY --chown=pyhabot:pyhabot start_both.sh /start_both.sh
RUN chmod +x /entrypoint.sh /start_both.sh

# Expose port for Railway (Railway will set PORT env var)
EXPOSE 8000

# Switch to non-root user
USER pyhabot

# Set entrypoint to handle secrets before running the main command
ENTRYPOINT ["/entrypoint.sh"]

# Run both CLI and API with proper process management
CMD ["/start_both.sh"]
