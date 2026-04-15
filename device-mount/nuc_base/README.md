# Demo with NUC

This demo is conducted on two NUCs running CentOS Stream with x86_64 architecture. Each NUC serves as either a master node or a guest node, with Pullpiri installed on both.

## Overall Architecture

Two NUCs serve as the Pullpiri master node and guest node respectively.
The master node connects three Arduino devices via USB-C for serial communication, while the guest node connects two Arduinos. Although the [eclipse-sdv-e2e-demo-blueprint](https://github.com/chheis/eclipse-sdv-e2e-demo-blueprint) uses Wi-Fi to connect Raspberry Pi and Arduino, we opted for wired serial communication due to internal restrictions on wireless router usage.

### Master Node

Once the Arduino code is installed, it operates automatically whenever the serial connection is established, without requiring additional execution steps.

- Arduino Stick: Recognizes left/right/button inputs from a joystick.
- Arduino LED: Illuminates LED strips in response to left, right, and button press actions.
- Arduino Gear: Detects clockwise/counterclockwise angular velocity and sends Pullpiri Scenario data to the Pullpiri api-server.

The remaining containers are launched using Pullpiri scenario or `docker-compose.yml`. Use the following commands for up/down operations:

```sh
# for pullpiri
./scenario.sh 1 # launch
./scenario.sh 2 # terminate
```

```sh
# for docker-compose
docker compose up -d --build
docker compose down
```

Two containers are launched here:

- Databroker: Uses Eclipse Kuksa's VSS data format. It operates similarly to a gRPC-based Pub-Sub system. The container image is a pre-built image provided by the project.
- serial-kuksa-bridge: Converts joystick data received via serial into VSS format and pushes it through the Kuksa client library. It also controls the three Arduino devices.

### Guest Node

Once the Arduino code is installed, it operates automatically whenever the serial connection is established, without requiring additional execution steps.

- Arduino Active Buzzer: An active speaker that produces a single high-frequency sound. It makes sounds based on joystick button press information received from the Kuksa Databroker. An LED strip is attached to clearly indicate when the buzzer is active, illuminating alongside the sound.
- Arduino Passive Buzzer: A passive speaker capable of frequency adjustment, configured to produce a single low-frequency sound. It operates identically to the active buzzer. An LED strip is attached to clearly indicate when the buzzer is active, illuminating alongside the sound.

The guest node also includes a Python container that manages kuksa-serial signals, but it's launched via Pullpiri scenario instead of using a separate docker-compose.

For this purpose, you must build the container image with the name `localhost/kuksa-serial-bridge:latest` from the `nuc_base/nuc_guest/kuksa-serial-bridge` folder on the guest node. Note that you must use `podman build` instead of `docker build` for it to run with Pullpiri Nodeagent.
```sh
cd nuc_base/nuc_guest/kuksa-serial-bridge
podman build -t localhost/kuksa-serial-bridge:latest .
```

## Prerequisites

The following steps must be completed on both the master and guest nodes.

### Arduino CLI

```sh
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/usr/bin sh
```

(Optional) Bash completion

```sh
arduino-cli completion bash > arduino-cli.sh
sudo mv arduino-cli.sh /etc/bash_completion.d/
```

You must install the Arduino Uno platform with the following command to enable compilation:
```
arduino-cli core install arduino:renesas_uno
```

### Python
Assumes Python 3 is installed.
If you encounter an error indicating that serial.Serial is missing when running `run.sh`, install the package with `pip install pyserial`.

> Note - You must install `pyserial`, not `serial`

### Add Device Group Permission

```
sudo usermod -aG dialout $USER
```

## Next Steps

Refer to the `README.md` files in nuc_master and nuc_guest for each respective node.