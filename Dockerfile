FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Run unit tests during container build for quality assurance
RUN pytest tests/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose default standard IO entrypoint
ENTRYPOINT ["python", "server.py"]
