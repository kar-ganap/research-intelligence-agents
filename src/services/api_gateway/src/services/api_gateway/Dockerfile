# API Gateway Service Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install requirements directly
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    flask>=3.0.0 \
    flask-cors>=4.0.0 \
    requests>=2.31.0 \
    google-cloud-firestore>=2.14.0 \
    google-generativeai>=0.3.0 \
    google-adk>=0.1.0

# Copy service code
COPY . /app/

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run API Gateway
CMD ["python", "main.py"]
