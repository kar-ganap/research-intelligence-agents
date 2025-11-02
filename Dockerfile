# Unified Dockerfile for all Cloud Run services and jobs
# Uses pre-built base image to speed up builds
# Build from project root

FROM gcr.io/research-intel-agents/base:latest

# Copy entire source code (dependencies already installed in base)
COPY src/ ./src/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port (will be overridden by Cloud Run)
EXPOSE 8080

# Default command (override with --command flag in Cloud Run deploy)
CMD ["python", "-m", "src.services.api_gateway.main"]
