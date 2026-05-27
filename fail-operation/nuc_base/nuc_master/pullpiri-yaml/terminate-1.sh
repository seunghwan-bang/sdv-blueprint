#!/bin/bash
# Terminate container workload 1

MASTER_IP=${MASTER_IP:-"192.168.1.2"}
URL="http://${MASTER_IP}:47099/api/artifact"
YAML_FILE="/yaml/container-stop-1.yaml"

curl -X POST \
  -H "Content-Type: text/plain" \
  --data-binary "@${YAML_FILE}" \
  "${URL}"

echo "Sent container-stop-1.yaml to Pullpiri"
