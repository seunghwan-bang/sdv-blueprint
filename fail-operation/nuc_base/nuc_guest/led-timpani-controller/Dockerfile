# Build stage
FROM gcc:12 AS builder
WORKDIR /build
COPY led_timpani.c Makefile ./
RUN make

# Runtime stage
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends tini && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /build/led_timpani ./

EXPOSE 9101
ENTRYPOINT ["/usr/bin/tini", "-s", "--"]
CMD ["./led_timpani"]
