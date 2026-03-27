#!/bin/bash
# SPDX-FileCopyrightText: Copyright 2024 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

BODY=$(< ./yaml/buzzer-active-terminate.yaml)

curl -X POST 'http://192.168.1.2:47099/api/artifact' \
--header 'Content-Type: text/plain' \
--data "${BODY}"
