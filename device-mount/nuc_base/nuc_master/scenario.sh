#!/bin/bash
# SPDX-FileCopyrightText: Copyright 2024 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

# Function to display help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Send scenario to Pullpiri API server"
    echo ""
    echo "Options:"
    echo "  1    Launch scenario (master-scenario-launch.yaml)"
    echo "  2    Terminate scenario (master-scenario-terminate.yaml)"
    echo "  -h, --help    Display this help message"
    echo ""
    echo "Example:"
    echo "  $0 1    # Launch scenario"
    echo "  $0 2    # Terminate scenario"
}

# Check if parameter is provided
if [[ $# -eq 0 ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Select body based on parameter
case "$1" in
    1)
        BODY=$(< ./master-scenario-launch.yaml)
        echo "Sending launch scenario..."
        ;;
    2)
        BODY=$(< ./master-scenario-terminate.yaml)
        echo "Sending terminate scenario..."
        ;;
    *)
        echo "Error: Invalid option '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac

# Send request
curl -X POST 'http://192.168.1.2:47099/api/artifact' \
--header 'Content-Type: text/plain' \
--data "${BODY}"
