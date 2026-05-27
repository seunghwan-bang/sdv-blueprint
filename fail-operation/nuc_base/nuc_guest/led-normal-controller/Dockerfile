FROM python:3.11-slim

WORKDIR /app
COPY led_normal.py /app/
RUN pip install --no-cache-dir pyserial

# Expose Prometheus metrics port
EXPOSE 9102

CMD ["python3", "-u", "led_normal.py"]
