#!/bin/bash
# Upload Arduino sketches using actual ttyACM devices

echo "Uploading ardn_stick to ttyACM2 (arduino_joystick)..."
arduino-cli upload -p /dev/ttyACM2 --fqbn arduino:renesas_uno:unor4wifi ardn_stick

echo "Uploading ardn_led to ttyACM1 (arduino_led)..."
arduino-cli upload -p /dev/ttyACM1 --fqbn arduino:renesas_uno:unor4wifi ardn_led

echo "Uploading ardn_gear to ttyACM0 (arduino_gear)..."
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:renesas_uno:unor4wifi ardn_gear

echo "Upload complete!"
