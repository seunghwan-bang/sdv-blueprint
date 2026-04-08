# Demo with NUC

x86_64 아키텍처의 CentOS Stream 사용하는 NUC 에서 진행

## 사전 준비

### Buzzer 구분

똑같이 생겼는데, buzzer 에 하얀 스티커 붙어있는 장치가 active buzzer, 스티커 없이 검정 장치만 있으면 passive buzzer 이다.

### Device 경로

장치 연결 할 때마다, `/dev/ttyACMx` 경로가 바뀔 수 있기 때문에 고정 필요

`99-arduino-buzzer.rules` 파일은 다음과 같이 구성되어 있음

```
# Active buzzer Arduino
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{serial}=="3CDC75F04E2C", SYMLINK+="arduino_active"

# Passive buzzer Arduino
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{serial}=="3CDC75F03F08", SYMLINK+="arduino_passive"
```

여기서 `2341` 은 Arduino 사의 vendor code 이고, 각 장치의 serial은 아래 command로 확인 가능하다. 

```
udevadm info -a -n /dev/ttyACM0 | grep '{serial}' -m 1
```

`ttyACM0` 은 Arduino device 붙을 때마다 숫자가 증가한다. `arduino-cli board list` command 로 어떤 경로에 붙었는지 알 수 있다.

최종적으로 다음 command를 실행하여 잘 생성되었는지 확인

```
sudo cp 99-arduino-buzzer.rules /etc/udev/rules.d/99-arduino-buzzer.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -al /dev/arduino_*
```

## Compile

컴파일은 `compile.sh` 을 실행하면 된다. compile 을 위해서는 `ino` 파일명과 폴더명이 동일해야 한다.

```sh
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi ardn_buzzer_active
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi ardn_buzzer_passive
```

컴파일이 잘 끝나면 다음과 같이 로그들이 나온다.
```
Sketch uses 52224 bytes (19%) of program storage space. Maximum is 262144 bytes.
Global variables use 6740 bytes (20%) of dynamic memory, leaving 26028 bytes for local variables. Maximum is 32768 bytes.
```

## Install

설치도 `install.sh` 을 실행하면 된다. 다만 주의사항이 있다.

```sh
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:renesas_uno:unor4wifi ardn_buzzer_active
arduino-cli upload -p /dev/ttyACM1 --fqbn arduino:renesas_uno:unor4wifi ardn_buzzer_passive
```

위 스크립트에서 보듯이 `/dev/arduino_*` 이 아니라 original 경로가 들어가야 설치가 된다.
그러므로 `ls -al /dev/arduino_*` 을 통해 폴더와 디바이스 경로를 정확히 맞춰줘야 한다.

```
# ls -al /dev/arduino_*
lrwxrwxrwx 1 root root 7 Mar 24 15:17 /dev/arduino_active -> ttyACM0
lrwxrwxrwx 1 root root 7 Mar 24 15:17 /dev/arduino_passive -> ttyACM1
```

이 경우는 active buzzer 가 `/dev/ttyACM0` 에 연결되었기 때문에 설치 스크립트의 첫번째에 `ACM0` 이 있어야 한다.

## Run

TBD
