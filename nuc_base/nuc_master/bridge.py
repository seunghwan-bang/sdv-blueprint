import serial, sys, threading, re

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

def main():
  with serial.Serial(PORT_STICK, BAUD, timeout=0) as s_in, \
       serial.Serial(PORT_LED, BAUD, timeout=0) as s_out:
    print(f"Bridge: {PORT_STICK} -> {PORT_LED}")
    last_x = 512
    last_btn = 1

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
        # print("No input in: ", line)
        # continue
      
      msg = f"{x},{btn}\n".encode()
      s_out.write(msg)
      s_out.flush()

      last_x, last_btn = x, btn           
      #print(f"btn={btn}")

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("Stopped.")
    sys.exit(0)
