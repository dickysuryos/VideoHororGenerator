FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8005

WORKDIR /app

# Install system dependencies if any are needed in the future
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app/

# Create a non-privileged user and set ownership
RUN useradd -u 10001 -m -d /app -s /bin/bash appuser && \
    mkdir -p /app/uploads /app/output && \
    touch /app/history.json && \
    chown -R appuser:appuser /app

USER appuser

# Expose BFF port
EXPOSE 8005

# Start the application
CMD ["python3", "app.py"]
