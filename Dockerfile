FROM python:3.11-slim

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    bluez \
    libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy the rest of the application
COPY . .

# Create directory for config
RUN mkdir -p /root/.omramin

# Make the script executable
RUN chmod +x omramin.py

ENTRYPOINT ["./omramin.py"] 