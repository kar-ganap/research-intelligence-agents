# ArXiv Watcher Job Dockerfile
# Uses pre-built base image for faster builds

FROM gcr.io/research-intel-agents/base:latest

# Copy all source code (dependencies already installed in base)
COPY src/ ./src/

# Environment variables
ENV PYTHONUNBUFFERED=1

# Run ArXiv Watcher Job
CMD ["python", "-m", "src.jobs.arxiv_watcher.main"]
