# Demo with NUC

x86_64 아키텍처의 CentOS Stream 사용하는 NUC 2대에서 진행한다. 각 master node 와 guest node 가 있으며 pullpiri 가 설치된다.

## 전체 구조

2개의 NUC 가 각각 Pullpiri master node, guest node 가 된다.
Master node 에는 Arduino 3개, Guest node 에는 Arduino 2개를 USB-C 로 연결하여 serial 로 통신한다. [eclipse-sdv-e2e-demo-blueprint](https://github.com/chheis/eclipse-sdv-e2e-demo-blueprint) 에서는 Wi-Fi 를 통해 Raspberry Pi 와 Arduino 를 연결하였지만, 사내 무선 공유기 사용에 많은 제약사항이 있어 유선 serial 을 사용하였다.

### Master Node

아두이노 코드는 한번 install 하면 실행 절차 없이 serial만 연결되면 동작한다.

- Arduino Stick : 조이스틱으로 좌/우/버튼 을 인식한다.
- Arduino LED : LED strip 을 통해 좌, 우, 버튼 press 에 따라 빛을 낸다.
- Arduino Gear : 시계/반시계 방향 각속도를 인식하고, Pullpiri Scenario 를 Pullpiri api-server 에 전송하는 역할을 한다.

`docker-compose.yml` 로 나머지 container 를 구동한다. up/down 은 아래 커맨드를 사용한다.

```sh
docker compose up -d --build
docker compose down
```

여기서는 2개의 container 가 구동된다.

- Databroker : Eclipse Kuksa 의 VSS data 형식을 사용한다. 여기서는 gRPC 기반의 Pub-Sub 과 유사하게 사용한다. 컨테이너 이미지는 해당 프로젝트에서 제공하는 선빌드된 이미지를 사용한다.
- serial-kuksa-bridge : Serial 로 받은 조이스틱 정보를 VSS 로 변환하여 Kuksa client lib 을 통해 push 하는 역할을 한다. 그 외 3개의 아두이노 제어도 진행한다.

### Guest Node

아두이노 코드는 한번 install 하면 실행 절차 없이 serial만 연결되면 동작한다.

- Arduino Active Buzzer : Active speaker 로 high frequency 단일 소리가 난다. Kuksa Databroker 에서 받은 조이스틱 버튼 press 정보를 통해 소리를 낸다. 소리가 나는 위치를 명확히 보기 위해 LED strip 을 달아 소리가 날때 LED 도 같이 켜진다. 
- Arduino Passive Buzzer : Passive speaker 로 주파수 조절이 가능하나 low frequency 단일 소리를 내도록 설정하였다. 동작은 Active buzzer 와 같다. 소리가 나는 위치를 명확히 보기 위해 LED strip 을 달아 소리가 날때 LED 도 같이 켜진다. 

Guest node 에도 kuksa-serial 신호를 관장하는 python container 가 있으나, 별도의 docker compose 를 사용하지 않고, pullpiri 시나리오로 구동한다.

이를 위해 Guest Node 의 `nuc_base/nuc_guest/kuksa-serial-bridge` 폴더에서 컨테이너 이미지를 `localhost/kuksa-serial-bridge:latest` 이름으로 빌드해야 한다. 주의할 점은 `docker build` 가 아닌 `podman build` 를 해야 Pullpiri Nodeagent 에서 구동이 가능하다.
```sh
cd nuc_base/nuc_guest/kuksa-serial-bridge
podman build -t localhost/kuksa-serial-bridge:latest .
```

## 사전 준비

다음 과정은 master, guest 2대 모두에서 선행되어야 한다.

### Arduino CLI

```sh
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/usr/bin sh
```

(Optional) Bash completion

```sh
arduino-cli completion bash > arduino-cli.sh
sudo mv arduino-cli.sh /etc/bash_completion.d/
```

다음 명령어로 arduino uno platform 을 설치해야 컴파일이 가능하다.
```
arduino-cli core install arduino:renesas_uno
```

### Python
Python 3 설치 되어 있다고 가정.
`run.sh` 를 구동하여 serial.Serial 이 없다는 에러가 발생하면 `pip install pyserial` 로 패키지 설치.

> 주의 - `serial` 이 아니라 `pyserial` 을 설치해야 함

### Device group 권한 추가

```
sudo usermod -aG dialout $USER
```

## 다음 단계

각 node 별로 nuc_master 와 nuc_guest 의 `README.md` 를 참조하라.