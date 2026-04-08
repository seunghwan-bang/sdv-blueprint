import serial
import sys
import threading
import queue
import json
import time
import os
from kuksa_client import KuksaClientThread
from kuksa_client.grpc import Datapoint

#PORT_ACTIVE = "/dev/arduino_active"
#PORT_PASSIVE = "/dev/arduino_passive"
PORT_BUZZER = "/dev/arduino_buzzer"
BAUD = 115200

def recv_to_databroker(client):
    try:
        #l = client.getValue("Vehicle.Body.Lights.DirectionIndicator.Left.IsSignaling")
        #r = client.getValue("Vehicle.Body.Lights.DirectionIndicator.Right.IsSignaling")
        b = client.getValue("Vehicle.Body.Lights.Brake.IsActive")

        if isinstance(b, str):
            b = json.loads(b)
        val = b.get('value') if isinstance(b, dict) else None

        if isinstance(val, str):
            val = json.loads(va)
        isBrake = val.get('value') if isinstance(val, dict) else None

        if isBrake == 'ACTIVE':
            return True
        elif isBrake == 'INACTIVE':
            return False
        else:
            return None
    except Exception as e:
        print(f"Databroker getValue error: {e}", file=sys.stderr)
        return None


def main(stop_event):
    master_ip = os.environ.get('MASTER_IP', '192.168.1.2')
    client = KuksaClientThread(config={'protocol': 'grpc', 'ip': master_ip, 'port': 55555, 'insecure': True})
    client.start()
    while not stop_event.is_set():
        try:
            with serial.Serial(PORT_BUZZER, BAUD, timeout=0) as s_bz:
                while not stop_event.is_set():
                    isBrake = recv_to_databroker(client)
                    print(f"isBrake: {isBrake}")
                    msg = b"1" if isBrake else b"0"
                    s_bz.write(msg)
                    s_bz.flush()
                    time.sleep(0.05)
        except (serial.SerialException, OSError) as e:
            print(f"Serial error: {e}. Reconnecting in 1 seconds...", file=sys.stderr)
            time.sleep(1)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 1 seconds...", file=sys.stderr)
            time.sleep(1)

if __name__ == "__main__":
    stop_event = threading.Event()
    try:
        main(stop_event)
    except KeyboardInterrupt:
        print("Stopped.")
        stop_event.set()
        sys.exit(0)
