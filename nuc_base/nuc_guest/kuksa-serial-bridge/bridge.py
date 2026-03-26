import serial
import sys
import threading
import queue
import json
import time
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

def main():
    client = KuksaClientThread(config={'protocol': 'grpc', 'ip': '192.168.1.2', 'port': 55555, 'insecure': True})
    #client = KuksaClientThread(config={'url': 'grpc://192.168.1.2:55555', 'insecure': True})
    client.start()

    #with serial.Serial(PORT_ACTIVE, BAUD, timeout=0) as s_ac, \
    #     serial.Serial(PORT_PASSIVE, BAUD, timeout=0) as s_pa:
    with serial.Serial(PORT_BUZZER, BAUD, timeout=0) as s_bz:
        while True:
            isBrake = recv_to_databroker(client)
            print(f"isBrake: {isBrake}")

            msg = b"1" if isBrake else b"0"
            #s_ac.write(msg)
            #s_pa.write(msg)
            #s_ac.flush()
            #s_pa.flush()
            s_bz.write(msg)
            s_bz.flush()

            time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped.")
        sys.exit(0)
