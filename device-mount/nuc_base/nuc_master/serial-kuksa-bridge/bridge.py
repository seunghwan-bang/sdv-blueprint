import serial
import sys
import re
import threading
import queue
import json
import requests
import time
import os

from kuksa_client import KuksaClientThread
from kuksa_client.grpc import Datapoint

PORT_STICK = "/dev/arduino_joystick"
PORT_LED = "/dev/arduino_led"
PORT_GEAR = "/dev/arduino_gear"
BAUD = 115200

def parse_x_btn(line: str):
    parts = [p.strip() for p in line.split(',')]
    if len(parts) == 4 and parts[1].isdigit() and parts[3] in ("0", "1"):
        x = int(parts[1])
        btn = int(parts[3])
        if 0 <= x <= 1023:
            return x, btn

    nums = [int(m.group()) for m in re.finditer(r'[-+]?\d+', line)]
    xs = [n for n in nums if 0 <= n <= 1023]
    btns = [n for n in nums if n in (0,1)]
    x = xs[-1] if xs else None
    btn = btns[-1] if btns else None
    return x, btn

def extract_btn(line: str):
    last = None
    for ch in line:
        if ch in ("0", "1"):
            last = int(ch)
    return last

def send_to_databroker(client, left, right, brake):
    try:
        client.setValue("Vehicle.Body.Lights.DirectionIndicator.Left.IsSignaling", json.dumps(left))
        client.setValue("Vehicle.Body.Lights.DirectionIndicator.Right.IsSignaling", json.dumps(right))
        client.setValue("Vehicle.Body.Lights.Brake.IsActive", json.dumps(brake))
    except Exception as e:
        print(f"Databroker setValue error: {e}", file=sys.stderr)

def databroker_worker(client, q, stop_event):
    while not stop_event.is_set():
        try:
            left, right, brake = q.get(timeout=0.5)
        except queue.Empty:
            continue
        try:
            send_to_databroker(client, left, right, brake)
        except Exception as e:
            print(f"Databroker send error: {e}", file=sys.stderr)
        q.task_done()

def handle_pullpiri_yaml(stop_event):
    prev_yaml_state = -1
    while not stop_event.is_set():
        try:
            with serial.Serial(PORT_GEAR, BAUD, timeout=1) as s_in:
                while not stop_event.is_set():
                    raw = s_in.readline()
                    if not raw:
                        continue
                    try:
                        line = raw.decode(errors="replace").strip()
                    except Exception as e:
                        print(f"Decode error: {e}", file=sys.stderr)
                        continue
                    if not line:
                        continue

                    if line.isdigit():
                        if line == "0":
                            if prev_yaml_state == 0:
                                continue
                            prev_yaml_state = 0
                            print("LOW FREQ")
                            send_yaml_artifact('/yaml/buzzer-active-terminate.yaml')
                            time.sleep(1)
                            send_yaml_artifact('/yaml/buzzer-passive-launch.yaml')
                        elif line == "1":
                            if prev_yaml_state == 1:
                                continue
                            prev_yaml_state = 1
                            print("HIGH FREQ")
                            send_yaml_artifact('/yaml/buzzer-passive-terminate.yaml')
                            time.sleep(1)
                            send_yaml_artifact('/yaml/buzzer-active-launch.yaml')
                    else:
                        print(f"Message: {line}")
                    time.sleep(0.05)
        except (serial.SerialException, OSError) as e:
            print(f"Gear serial error: {e}. Retrying in 1 second...", file=sys.stderr)
            time.sleep(1)
        except Exception as e:
            print(f"Gear thread error: {e}. Retrying in 1 second...", file=sys.stderr)
            time.sleep(1)

def send_yaml_artifact(yaml_path: str):
    master_ip = os.environ.get('MASTER_IP', '192.168.1.2')
    url = f'http://{master_ip}:47099/api/artifact'
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            body = f.read()
        headers = {'Content-Type': 'text/plain'}
        response = requests.post(url, headers=headers, data=body)
        print(f"[POST] {url} status={response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"send_yaml_artifact error: {e}", file=sys.stderr)


def main(q, stop_event):
    while not stop_event.is_set():
        try:
            with serial.Serial(PORT_STICK, BAUD, timeout=0) as s_in, \
                 serial.Serial(PORT_LED, BAUD, timeout=0) as s_out:
                print(f"Bridge: {PORT_STICK} -> {PORT_LED}")
                last_x = 512
                last_btn = 1
                while not stop_event.is_set():
                    raw = s_in.readline()
                    if not raw:
                        continue
                    line = raw.decode(errors="replace").strip()
                    if not line:
                        continue

                    x, btn = parse_x_btn(line)
                    if x is None:
                        x = last_x
                    if btn is None:
                        btn = last_btn

                    left = (x < 300)
                    right = (x > 723)
                    brake = "ACTIVE" if btn == 0 else "INACTIVE"
                    q.put((left, right, brake))

                    msg = f"{x},{btn}\n".encode()
                    s_out.write(msg)
                    s_out.flush()

                    last_x, last_btn = x, btn
                    #print(f"x={x} btn={btn}")
        except (serial.SerialException, OSError) as e:
            print(f"Main serial error: {e}. Reconnecting in 1 second...", file=sys.stderr)
            time.sleep(1)
        except Exception as e:
            print(f"Main loop error: {e}. Retrying in 1 second...", file=sys.stderr)
            time.sleep(1)

if __name__ == "__main__":
    stop_event = threading.Event()
    client = KuksaClientThread(config={'protocol': 'grpc', 'ip': 'databroker', 'port': 55555, 'insecure': True})
    client.start()
    q = queue.Queue()
    t_db = threading.Thread(target=databroker_worker, args=(client, q, stop_event), daemon=True)
    t_db.start()
    t_gear = threading.Thread(target=handle_pullpiri_yaml, args=(stop_event,), daemon=True)
    t_gear.start()
    try:
        main(q, stop_event)
    except KeyboardInterrupt:
        print("Stopped.")
        stop_event.set()
        t_db.join(timeout=1)
        t_gear.join(timeout=1)
        sys.exit(0)
