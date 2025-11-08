# API Gateway Service Dockerfile
# Uses pre-built base image for faster builds

FROM gcr.io/research-intel-agents/base:latest

# Copy all source code (dependencies already installed in base)
COPY src/ ./src/

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run API Gateway
CMD ["python", "-m", "src.services.api_gateway.main"]
