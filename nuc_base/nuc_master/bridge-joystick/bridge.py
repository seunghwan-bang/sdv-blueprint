import serial, sys, re
from kuksa_client import KuksaClientThread as KuksaClient
from kuksa_client.grpc import Datapoint
import threading
import queue
import json

PORT_STICK = "/dev/arduino_joystick"
PORT_LED = "/dev/arduino_led"
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

def databroker_worker(client, q):
    while True:
        left, right, brake = q.get()
        try:
            send_to_databroker(client, left, right, brake)
        except Exception as e:
            print(f"Databroker send error: {e}", file=sys.stderr)
        q.task_done()

def main():
    with serial.Serial(PORT_STICK, BAUD, timeout=0) as s_in, \
         serial.Serial(PORT_LED, BAUD, timeout=0) as s_out:
        print(f"Bridge: {PORT_STICK} -> {PORT_LED}")
        last_x = 512
        last_btn = 1

        client = KuksaClient(config={'protocol': 'grpc', 'ip': 'databroker', 'port': 55555, 'insecure': True})
        #client = KuksaClient(config={'url': 'grpc://databroker:55555', 'insecure': True})
        client.start()

        q = queue.Queue()
        t = threading.Thread(target=databroker_worker, args=(client, q), daemon=True)
        t.start()

        while True:
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

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped.")
        sys.exit(0)
