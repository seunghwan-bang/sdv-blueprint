#!/bin/bash
# Compile LED Arduino sketches for Guest NUC

arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi ardn_led_timpani
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi ardn_led_normal
