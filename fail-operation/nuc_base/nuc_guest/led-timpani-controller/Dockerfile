# Build stage
FROM gcc:12 AS builder

WORKDIR /build
COPY led_timpani.c Makefile ./
RUN make

# Runtime stage
FROM debian:bookworm-slim

# Install tini - a minimal init for containers
# tini handles PID 1 responsibilities and properly forwards signals
RUN apt-get update && apt-get install -y --no-install-recommends tini && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /build/led_timpani /app/

# Default serial port (can be overridden with -e SERIAL_PORT=...)
ENV SERIAL_PORT=/dev/arduino_led_timpani

# Expose Prometheus metrics port
EXPOSE 9101

# Use tini as init process with -s flag to forward signals to child
# -s: Forward all signals to the child process (not just standard ones)
ENTRYPOINT ["/usr/bin/tini", "-s", "--"]
CMD ["./led_timpani"]
