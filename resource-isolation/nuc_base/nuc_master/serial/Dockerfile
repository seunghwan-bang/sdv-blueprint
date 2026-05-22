FROM python:3.11-slim

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir pyserial

CMD ["python3", "bridge.py"]
