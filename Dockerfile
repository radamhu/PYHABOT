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

# Install only runtime dependencies
RUN apt-get update && apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security
RUN groupadd -r pyhabot && useradd -r -g pyhabot pyhabot

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

# Copy entrypoint script and set permissions
COPY --chown=pyhabot:pyhabot entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER pyhabot

# Set entrypoint to handle secrets before running the main command
ENTRYPOINT ["/entrypoint.sh"]

# Use the new CLI command
CMD ["pyhabot", "run"]
