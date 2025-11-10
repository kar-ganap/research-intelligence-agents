# Graph Updater Service Dockerfile
# Uses pre-built base image for faster builds

FROM gcr.io/research-intel-agents/base:latest

# Copy all source code (dependencies already installed in base)
COPY src/ ./src/

# Environment variables
ENV PORT=8083
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8083

# Run Graph Updater Service
CMD ["python", "-m", "src.services.graph_updater.main"]
