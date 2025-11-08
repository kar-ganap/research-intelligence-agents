# Graph Service Dockerfile

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
ENV PORT=8082
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8082

# Run Graph Service
CMD ["python", "-m", "src.services.graph_service.main"]
