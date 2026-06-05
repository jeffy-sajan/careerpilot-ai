# ────────────────────────────────────────────
# Stage 1 — Builder
# Install dependencies with build tools available.
# ────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder

# Prevent Python from writing .pyc files and enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed to compile some Python packages
# (e.g. asyncpg requires libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into /app/wheels
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt && \
    pip install --no-cache-dir --no-index --find-links=/app/wheels -r requirements.txt

# ────────────────────────────────────────────
# Stage 2 — Production Image
# Lean image — only runtime dependencies.
# ────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime system dependency for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels from builder and install
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy application source
COPY . .

EXPOSE 8000

# prestart.sh runs Alembic migrations before starting uvicorn
COPY prestart.sh /prestart.sh
RUN chmod +x /prestart.sh

CMD ["/prestart.sh"]
