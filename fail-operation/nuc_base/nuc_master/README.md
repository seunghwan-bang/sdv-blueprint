# Fail Operation Demo - NUC Master

This folder contains the NUC Master setup for the fail-operation demonstration.

## 사전 준비

### Required Docker Images

다음 Docker 이미지들을 사전에 빌드해야 함:

- `failop-serial-bridge:latest` - Arduino와 KUKSA/Pullpiri를 연결하는 브리지
- `quay.io/eclipse-kuksa/kuksa-databroker:0.6.0` - KUKSA databroker (공식 이미지)

### Docker Image 빌드

```bash
# Serial bridge 이미지 빌드
cd /home/lge/work/sdv-blueprint/fail-operation/nuc_base/nuc_master
docker compose build failop-serial-bridge
```

**확인:**
```bash
docker images | grep failop-serial-bridge
# failop-serial-bridge   latest   ...
```

KUKSA databroker는 docker-compose.yml에서 자동으로 pull됩니다.

## Arduino 설정

[arduino](./arduino/README.md) 참조

**요약:**
1. udev rules 설정으로 디바이스 경로 고정
2. Arduino 펌웨어 컴파일 및 업로드
3. 3개 보드: Joystick, LED, Gear

## Hardware Setup

- **3 Arduino UNO R4 WiFi boards:**
  - `ardn_stick` - Joystick with button (input)
  - `ardn_led` - NeoPixel LED strip (output)
  - `ardn_gear` - Rotary encoder with LED ring (input)

## Architecture

### Data Flow

1. **Joystick Button → LED + KUKSA**
   - `ardn_stick` detects button press/release
   - Sends signal to `bridge.py`
   - `bridge.py` forwards to:
     - Local `ardn_led` Arduino (GREEN on press, OFF on release)
     - KUKSA databroker (for Guest to receive)

2. **Rotary Encoder → Pullpiri**
   - `ardn_gear` detects rotation (CW/CCW)
   - `bridge.py` manages state-based filtering:
     - state=0 or -1: Only CW allowed → LAUNCH
     - state=1: Only CCW allowed → STOP
     - Invalid direction → RED LED
   - Sends YAML artifact to Pullpiri via HTTP API (`192.168.0.3:47099/api/artifact`)

## Components

### Arduino Programs

- `ardn_stick/ardn_stick.ino` - Joystick button detection
- `ardn_led/ardn_led.ino` - LED controller (GREEN/RED/OFF)
- `ardn_gear/ardn_gear.ino` - Rotary encoder with state machine

### Python Bridge

- `serial/bridge.py` - Main bridge connecting Arduino ↔ KUKSA ↔ Pullpiri
  - Main Thread: Joystick → DataBroker + LED Control
  - Thread-DB: DataBroker worker (queue consumer)
  - Thread-Gear: Gear → YAML artifacts (CW/CCW)

### Pullpiri YAML

- `pullpiri-yaml/yaml/container-launch.yaml` - Launch containers
- `pullpiri-yaml/yaml/container-stop.yaml` - Stop containers

## 실행

### 1. Docker Compose 시작

```bash
cd /home/lge/work/sdv-blueprint/fail-operation/nuc_base/nuc_master
docker compose up -d
```

**확인:**
```bash
docker compose ps
# NAME                   IMAGE                                          STATUS
# failop-databroker      quay.io/eclipse-kuksa/kuksa-databroker:0.6.0   Up
# failop-serial-bridge   failop-serial-bridge:latest                    Up
```

### 2. 로그 확인

```bash
# 실시간 로그
docker logs -f failop-serial-bridge

# 최근 로그
docker logs --tail 50 failop-serial-bridge
```

**정상 시작 로그:**
```
============================================================
Fail-Operation Serial Bridge
============================================================
Thread Architecture:
  [Main Thread]   Joystick (ttyACM2) → DataBroker + LED Control
  [Thread-DB]     DataBroker worker (queue consumer)
  [Thread-Gear]   Gear (ttyACM0) → YAML artifacts (CW/CCW)
============================================================
✓ Ready to send signals
[Thread-Gear] Monitor started: /dev/arduino_gear
[Main-Joystick] Monitor started: /dev/arduino_joystick
[Main-LED] Monitor started: /dev/arduino_led
```

### 3. 동작 테스트

**Joystick 테스트:**
- 버튼 누름 → LED 초록색 + DataBroker 전송
- 버튼 뗌 → LED 꺼짐 + DataBroker 전송

**예상 로그:**
```
[Joystick] PRESSED → DataBroker + LED GREEN
✓ Sent to databroker: ButtonPressed=True
[Joystick] RELEASED → DataBroker + LED OFF
✓ Sent to databroker: ButtonPressed=False
```

**Gear (Rotary Encoder) 테스트:**
- 첫 동작: 시계방향(CW) → LAUNCH YAML 전송, 보라색 LED
- 다음: 반시계방향(CCW) → STOP YAML 전송, 초록색 LED
- 잘못된 방향 → 무시, 빨간색 LED

**예상 로그:**
```
Gear signal: CW
[Gear] State=0 + CW → LAUNCH (state becomes 1)
[POST] http://192.168.0.3:47099/api/artifact yaml=container-launch.yaml status=200

Gear signal: CCW
[Gear] State=1 + CCW → STOP (state becomes -1)
[POST] http://192.168.0.3:47099/api/artifact yaml=container-stop.yaml status=200
```

## 중지

```bash
docker compose down
```

## 문제 해결

### Arduino가 인식되지 않을 때

```bash
# 디바이스 확인
ls -la /dev/arduino_*
arduino-cli board list

# udev rules 재적용
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Docker 컨테이너가 Arduino에 접근 못할 때

```bash
# 컨테이너 내부에서 디바이스 확인
docker exec failop-serial-bridge ls -la /dev/arduino_*

# 권한 확인 (rw 필요)
ls -la /dev/arduino_*
```

### Pullpiri 연결 실패

```bash
# Pullpiri 서버 확인
curl -I http://192.168.0.3:47099/api/artifact

# 네트워크 확인
ping 192.168.0.3
```

```bash
cd arduino/
./compile.sh
./install.sh
```

## Running the Bridge

```bash
cd serial/
python bridge.py
```

Or use Docker Compose (see parent folder).
