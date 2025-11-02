# Orchestrator Service Dockerfile
# Uses pre-built base image for faster builds

FROM gcr.io/research-intel-agents/base:latest

# Copy all source code (dependencies already installed in base)
COPY src/ ./src/

# Environment variables
ENV PORT=8081
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8081

# Run Orchestrator Service
CMD ["python", "-m", "src.services.orchestrator.main"]
