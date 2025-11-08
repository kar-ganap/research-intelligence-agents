# ArXiv Watcher Job Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir arxiv

# Copy source code
COPY src/ ./src/

# Environment variables
ENV PYTHONUNBUFFERED=1

# Run ArXiv Watcher Job
CMD ["python", "-m", "src.jobs.arxiv_watcher.main"]
