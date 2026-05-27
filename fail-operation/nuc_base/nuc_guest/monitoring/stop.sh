#!/bin/bash
# Stop Monitoring Stack

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if docker/podman is available
if command -v docker &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="podman-compose"
else
    echo "Error: docker or podman-compose not found"
    exit 1
fi

cd "$SCRIPT_DIR"

echo "Stopping Prometheus and Grafana..."
$COMPOSE_CMD down

echo "Monitoring stack stopped."
