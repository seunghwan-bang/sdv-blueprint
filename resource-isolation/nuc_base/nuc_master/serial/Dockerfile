FROM python:3.11-slim

WORKDIR /app

# Copy all files from build context
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir \
    pyserial \
    kuksa-client \
    requests

# Run the bridge
CMD ["python", "bridge.py"]
