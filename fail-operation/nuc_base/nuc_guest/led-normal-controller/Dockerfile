FROM python:3.11-slim

WORKDIR /app
COPY led_normal.py ./
RUN pip install --no-cache-dir pyserial

EXPOSE 9102
CMD ["python3", "-u", "led_normal.py"]
