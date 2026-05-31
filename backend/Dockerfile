FROM python:3.12-slim

WORKDIR /app

# Install system deps for PyMuPDF (libmupdf bundled in wheel, but needs libgomp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Sessions directory — override with SESSIONS_DIR env var pointing to a Railway volume
ENV PORT=8080
ENV SESSIONS_DIR=/data/sessions
ENV DATA_CACHE_DIR=/data/data_cache

# Create default persistent dirs (Railway volumes can be mounted here)
RUN mkdir -p /data/sessions /data/data_cache

EXPOSE 8080

CMD ["python", "api.py"]
