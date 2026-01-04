FROM python:3.12-slim

LABEL maintainer="pentafive"
LABEL description="PSKReporter to Home Assistant MQTT Bridge"
LABEL version="2.0.1"

# No additional system packages needed (pure Python app)
# Unlike 8311-ha-bridge, we don't need SSH client

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY pskr-ha-bridge.py .
COPY config.py .

# Run the application
CMD ["python3", "-u", "pskr-ha-bridge.py"]
