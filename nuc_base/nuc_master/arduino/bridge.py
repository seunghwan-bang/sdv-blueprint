import serial
import sys
import time

PORT = "/dev/ttyACM0"
BAUD = 115200

def main():
    with serial.Serial(PORT, BAUD, timeout=0.1) as s_in:
        while True:
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
            # 버튼 메시지와 숫자(회전값) 구분 출력
            if line.isdigit():
                if line == "0":
                    print("LOW FREQ")
                elif line == "1":
                    print("HIGH FREQ")
            else:
                print(f"Message: {line}")
            time.sleep(0.05)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped.")
        sys.exit(0)
