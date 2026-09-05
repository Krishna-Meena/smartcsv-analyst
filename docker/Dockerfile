# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY src/ src/
COPY sample_data/ sample_data/
COPY .streamlit/ .streamlit/

# Runtime stage  
FROM python:3.12-slim AS runtime

# Create non-root user
RUN groupadd -r smartcsv && useradd -r -g smartcsv -d /app -s /sbin/nologin smartcsv

WORKDIR /app

# Copy virtual environment and app from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src src/
COPY --from=builder /app/sample_data sample_data/
COPY --from=builder /app/.streamlit .streamlit/
COPY --from=builder /app/pyproject.toml pyproject.toml

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Switch to non-root user
USER smartcsv

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Run Streamlit
CMD ["streamlit", "run", "src/smartcsv/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
