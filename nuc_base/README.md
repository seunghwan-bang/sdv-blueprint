# Demo with NUC

x86_64 아키텍처의 CentOS Stream 사용하는 NUC 2대에서 진행한다. 각 master node 와 guest node 가 있으며 pullpiri 가 설치된다.

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