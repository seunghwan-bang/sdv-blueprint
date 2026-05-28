#!/bin/bash
# Install LED Arduino sketches to devices
# NOTE: Check actual ttyACMx paths with: ls -al /dev/arduino_*
#       Then match the correct ACM number below

# Example output of ls -al /dev/arduino_*:
#   /dev/arduino_led_timpani -> ttyACM0
#   /dev/arduino_led_normal -> ttyACM1

arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:renesas_uno:unor4wifi ardn_led_timpani
arduino-cli upload -p /dev/ttyACM1 --fqbn arduino:renesas_uno:unor4wifi ardn_led_normal
