# Daanaa Phase 1 Production Dockerfile
# V6 Percentile System + Privacy Guardrails

FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only runtime requirements (data/ is volume-mounted, scripts/ are local pipeline only)
COPY daanaa_api.py .
COPY frontend/dist/ ./frontend/dist/

# Create logs directory
RUN mkdir -p /app/logs

# Environment
ENV DB_PATH=/app/data/merit_registry.db
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Run
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "daanaa_api:app"]
