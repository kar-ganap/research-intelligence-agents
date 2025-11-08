# Uses pre-built base image for faster builds

FROM gcr.io/research-intel-agents/base:latest

# Copy all source code (dependencies already installed in base)
COPY src/ ./src/

# Environment variables
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.workers.alert_worker.main"]
