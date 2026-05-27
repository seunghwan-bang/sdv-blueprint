# Fail Operation Demo with Arduino

x86_64 아키텍처의 CentOS Stream 사용하는 NUC (Master)에서 진행

## 사전 준비

### Device 경로 고정

장치 연결 할 때마다, `/dev/ttyACMx` 경로가 바뀔 수 있기 때문에 고정 필요

`99-arduino.rules` 파일은 다음과 같이 구성되어 있음

```
# Joystick Arduino
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{serial}=="48CA435E506C", SYMLINK+="arduino_joystick"

# LED Arduino
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{serial}=="F0F5BD507E9C", SYMLINK+="arduino_led"

# Gear Arduino
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{serial}=="D885ACA7070C", SYMLINK+="arduino_gear"
```

여기서 `2341`은 Arduino 사의 vendor code이고, 각 장치의 serial은 아래 command로 확인 가능하다.

```bash
udevadm info -a -n /dev/ttyACM0 | grep '{serial}' -m 1
```

`ttyACM0`은 Arduino device 붙을 때마다 숫자가 증가한다. `arduino-cli board list` command로 어떤 경로에 붙었는지 알 수 있다.

최종적으로 다음 command를 실행하여 잘 생성되었는지 확인

```bash
sudo cp 99-arduino.rules /etc/udev/rules.d/99-arduino.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -al /dev/arduino_*
```

**예상 결과:**
```
lrwxrwxrwx. 1 root root 7 May 26 04:44 /dev/arduino_gear -> ttyACM0
lrwxrwxrwx. 1 root root 7 May 26 04:44 /dev/arduino_joystick -> ttyACM2
lrwxrwxrwx. 1 root root 7 May 26 04:44 /dev/arduino_led -> ttyACM1
```

## Arduino 구성

이 프로젝트는 3개의 Arduino UNO R4 WiFi 보드를 사용:

- **ardn_stick**: Joystick 버튼 입력 (버튼 press/release 감지)
- **ardn_led**: NeoPixel LED 제어 (GREEN/RED/OFF 명령 수신)
- **ardn_gear**: 로터리 엔코더 입력 + NeoPixel LED (CW/CCW 감지, 색상 표시)

## Compile

LED 사용을 위해 다음 library 설치가 필요하다.

```bash
arduino-cli lib install "Adafruit NeoPixel"
```

컴파일은 `compile.sh`를 실행하면 된다. compile을 위해서는 `ino` 파일명과 폴더명이 동일해야 한다.

```bash
./compile.sh
```

**내부 동작:**
```bash
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi ardn_stick
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi ardn_led
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi ardn_gear
```

컴파일이 잘 끝나면 다음과 같이 로그들이 나온다.

```
Sketch uses 52224 bytes (19%) of program storage space. Maximum is 262144 bytes.
Global variables use 6740 bytes (20%) of dynamic memory, leaving 26028 bytes for local variables. Maximum is 32768 bytes.
```

## Install

설치도 `install.sh`를 실행하면 된다. 다만 주의사항이 있다.

```bash
./install.sh
```

**내부 동작:**
```bash
arduino-cli upload -p /dev/ttyACM2 --fqbn arduino:renesas_uno:unor4wifi ardn_stick
arduino-cli upload -p /dev/ttyACM1 --fqbn arduino:renesas_uno:unor4wifi ardn_led
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:renesas_uno:unor4wifi ardn_gear
```

위 스크립트에서 보듯이 `/dev/arduino_*`이 아니라 original 경로가 들어가야 설치가 된다.
그러므로 `ls -al /dev/arduino_*`을 통해 폴더와 디바이스 경로를 정확히 맞춰줘야 한다.

## Arduino 프로그램 설명

### ardn_stick (Joystick)
- **핀 구성**: Pin 8 (Joystick SW)
- **기능**: 버튼 press/release 감지
- **출력**: 시리얼로 "1" (press) 또는 "0" (release) 전송
- **용도**: bridge.py에서 수신하여 DataBroker 전송 + LED 제어

### ardn_led (LED Controller)
- **핀 구성**: Pin 6 (NeoPixel data)
- **기능**: 시리얼 명령 수신하여 LED 색상 변경
- **명령어**:
  - `GREEN\n`: 초록색 표시
  - `RED\n`: 빨간색 표시
  - `OFF\n`: LED 끄기

### ardn_gear (Rotary Encoder + LED)
- **핀 구성**:
  - Pin 5, 6: Rotary encoder A/B
  - Pin 7: 엔코더 버튼
  - Pin 8: NeoPixel data
- **기능**: 
  - 회전 방향 감지 (CW/CCW)
  - 시리얼로 "CW" 또는 "CCW" 전송
  - bridge.py로부터 색상 명령 수신 (PURPLE/GREEN/RED)
- **상태 머신**: 
  - 초기 state=0: CW만 허용 → LAUNCH
  - state=1: CCW만 허용 → STOP
  - 잘못된 방향 입력 시 빨간색 LED 표시

## 디버깅

각 Arduino의 시리얼 출력을 직접 확인하려면:

```bash
# Joystick 모니터링
arduino-cli monitor -p /dev/ttyACM2 -c baudrate=115200

# LED 모니터링
arduino-cli monitor -p /dev/ttyACM1 -c baudrate=115200

# Gear 모니터링
arduino-cli monitor -p /dev/ttyACM0 -c baudrate=115200
```
