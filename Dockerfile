FROM python:3.13-slim

WORKDIR /app

# System deps — curl needed for healthcheck on Railway
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps first (layer-cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Railway injects $PORT — default to 8000 locally
ENV PORT=8000

EXPOSE $PORT

# Health check (Railway also has its own but belt-and-suspenders)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

# Entry point — run.py reads APP_PORT from env
CMD ["python", "run.py", "server"]
