# Orchestrator Service Dockerfile

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
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Environment variables
ENV PORT=8081
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8081

# Run Orchestrator
CMD ["python", "-m", "src.services.orchestrator.main"]
