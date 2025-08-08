FROM python:3.11-slim

# Faster Python, less disk churn
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set workdir
WORKDIR /app

# System deps (curl for healthcheck). Use --no-install-recommends to keep image small
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libffi-dev \
    libssl-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir gunicorn

# App code
COPY . .

# Ensure runtime dirs exist (even if bind-mounted later)
RUN mkdir -p /app/logs /app/uploads /app/data \
 && chmod 755 /app /app/logs /app/uploads /app/data

# Expose service port
EXPOSE 8080

# Container healthcheck (standalone-friendly)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -fsS http://localhost:8080/health || exit 1

# Start app (gunicorn.conf.py should bind 0.0.0.0:8080)
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
