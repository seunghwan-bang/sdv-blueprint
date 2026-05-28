#!/usr/bin/env python3
"""
LED Normal Controller - Interval 기반 LED 제어

아키텍처:
- Main Thread: 상태 머신 관리, interval 계산, LED 토글
- Worker Thread: CPU 부하 시뮬레이션 (busy_work)
- Metrics Thread (daemon): Prometheus HTTP 서버 (:9102)

상태 머신:
- NORMAL: delay < 500ms, 정상 토글
- STRESS: delay >= 500ms, 느린 토글
- RECOVERY: STRESS → NORMAL 전이 시 timpani와 동기화
"""

import os
import sys
import time
import math
import signal
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import serial
except ImportError:
    print("pyserial not installed. Run: pip install pyserial")
    sys.exit(1)

# 설정
SERIAL_PORT = "/dev/arduino_led_normal"
BAUD_RATE = 115200
INTERVAL = 0.5  # 500ms
METRICS_PORT = 9102
SYNC_FILE = "/tmp/timpani_start"
LED_STATE_FILE = "/tmp/timpani_led_state"
DEFAULT_BUSY_ITERATIONS = 13_000_000

# 전역 상태
g_running = True
g_metrics = {
    "delay_ms": 0.0,
    "interval_ms": 500.0,
    "led_state": 0,
    "signal_count": 0,
}


def get_env_int(name: str, default: int) -> int:
    """환경 변수에서 정수 읽기"""
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def read_timpani_state() -> bool | None:
    """timpani LED 상태 파일 읽기 (동기화용)"""
    try:
        with open(LED_STATE_FILE, "r") as f:
            return f.read().strip() == "1"
    except (IOError, OSError):
        return None


class ComputationWorker:
    """별도 스레드에서 CPU 부하 작업 수행"""

    def __init__(self):
        self._completed = threading.Event()
        self._thread: threading.Thread | None = None
        self.computation_time = 0.0

    def start(self, iterations: int):
        """연산 시작"""
        self._completed.clear()
        self._thread = threading.Thread(target=self._run, args=(iterations,), daemon=True)
        self._thread.start()

    def _run(self, iterations: int):
        """busy_work 실행"""
        start = time.perf_counter()
        total = sum(i * i for i in range(iterations))
        _ = total  # 사용되지 않음 경고 방지
        self.computation_time = time.perf_counter() - start
        self._completed.set()

    def wait(self, timeout: float = None) -> bool:
        """완료 대기"""
        return self._completed.wait(timeout)

    @property
    def is_completed(self) -> bool:
        return self._completed.is_set()


class MetricsHandler(BaseHTTPRequestHandler):
    """Prometheus 메트릭 HTTP 핸들러"""

    def log_message(self, *args):
        pass  # 로그 비활성화

    def do_GET(self):
        body = (
            "# HELP led_delay_ms LED control delay in milliseconds\n"
            "# TYPE led_delay_ms gauge\n"
            f'led_delay_ms{{container="normal"}} {g_metrics["delay_ms"]:.2f}\n'
            "# HELP led_interval_ms LED toggle interval in milliseconds\n"
            "# TYPE led_interval_ms gauge\n"
            f'led_interval_ms{{container="normal"}} {g_metrics["interval_ms"]:.2f}\n'
            "# HELP led_state Current LED state (0=OFF, 1=ON)\n"
            "# TYPE led_state gauge\n"
            f'led_state{{container="normal"}} {g_metrics["led_state"]}\n'
            "# HELP led_signal_count Total LED toggle count\n"
            "# TYPE led_signal_count counter\n"
            f'led_signal_count{{container="normal"}} {g_metrics["signal_count"]}\n'
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body.encode())


def start_metrics_server():
    """Prometheus 메트릭 서버 시작"""
    try:
        server = HTTPServer(("0.0.0.0", METRICS_PORT), MetricsHandler)
        print(f"[Metrics] Server listening on port {METRICS_PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"[Metrics] Error: {e}", file=sys.stderr)


def shutdown_handler(sig, frame):
    """종료 시그널 핸들러"""
    global g_running
    g_running = False
    print("\nShutdown signal received")


def main():
    global g_running

    # 환경 변수
    cpu_affinity = get_env_int("CPU_AFFINITY", 12)
    busy_iterations = get_env_int("BUSY_ITERATIONS", DEFAULT_BUSY_ITERATIONS)

    # CPU affinity 설정
    try:
        os.sched_setaffinity(0, {cpu_affinity})
        print(f"CPU affinity set to: {cpu_affinity}")
    except (OSError, AttributeError) as e:
        print(f"Warning: Could not set CPU affinity: {e}")

    # 시그널 핸들러
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # 메트릭 서버 시작 (daemon)
    threading.Thread(target=start_metrics_server, daemon=True).start()

    print("=== LED Normal Controller ===")
    print(f"Serial: {SERIAL_PORT}, Interval: {INTERVAL*1000:.0f}ms, Iterations: {busy_iterations}")

    # 동기화 파일 대기
    print(f"Waiting for sync file: {SYNC_FILE}")
    while g_running and not os.path.exists(SYNC_FILE):
        time.sleep(0.01)

    if not g_running:
        return

    print("Sync file detected, starting...")

    # Serial 연결
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Serial connected: {SERIAL_PORT}")
    except serial.SerialException as e:
        print(f"Warning: Serial unavailable ({e}), dry-run mode")
        ser = None

    # 상태 초기화
    state = "NORMAL"  # NORMAL, STRESS, RECOVERY
    led_state = False
    signal_count = 0
    worker = ComputationWorker()

    # 첫 토글 (timpani와 동시 시작)
    signal_count += 1
    led_state = True
    if ser:
        ser.write(b"1")
        ser.flush()
    g_metrics["led_state"] = 1
    g_metrics["signal_count"] = signal_count
    print(f"[Normal {signal_count}] LED ON (start)")

    last_signal_time = time.perf_counter()

    # Main Loop
    while g_running:
        # 1. 연산 시작
        worker.start(busy_iterations)

        # 2. 연산 완료 대기
        while g_running and not worker.is_completed:
            time.sleep(0.001)

        if not g_running:
            break

        computation_ms = worker.computation_time * 1000

        # 3. 다음 interval 끝 시점 계산 (500ms 단위 정렬)
        elapsed = time.perf_counter() - last_signal_time
        intervals_to_wait = math.ceil(elapsed / INTERVAL)
        next_interval_end = last_signal_time + (intervals_to_wait * INTERVAL)

        # 4. interval 끝까지 대기
        sleep_time = next_interval_end - time.perf_counter()
        if sleep_time > 0:
            time.sleep(sleep_time)

        current_time = time.perf_counter()
        actual_interval_ms = (current_time - last_signal_time) * 1000

        # 5. 상태 전이 및 LED 제어
        if state == "STRESS" and computation_ms < 500:
            # RECOVERY: timpani와 동기화
            timpani_state = read_timpani_state()
            if timpani_state is not None:
                led_state = timpani_state  # 동기화 (토글 아님)
            else:
                led_state = not led_state  # fallback

            state = "NORMAL"
            log_prefix = "SYNC "
        elif computation_ms >= 500:
            # STRESS: 느린 토글
            state = "STRESS"
            led_state = not led_state
            log_prefix = "STRESS "
        else:
            # NORMAL: 정상 토글
            state = "NORMAL"
            led_state = not led_state
            log_prefix = ""

        # 6. LED 전송
        signal_count += 1
        if ser:
            ser.write(b"1" if led_state else b"0")
            ser.flush()

        # 7. Delay 계산
        if computation_ms < 500:
            delay_ms = max(0, actual_interval_ms - 500)
        else:
            delay_ms = computation_ms

        # 8. 메트릭 업데이트
        g_metrics["delay_ms"] = delay_ms
        g_metrics["interval_ms"] = actual_interval_ms
        g_metrics["led_state"] = 1 if led_state else 0
        g_metrics["signal_count"] = signal_count

        # 9. 로그
        print(f"[Normal {signal_count}] {log_prefix}LED {'ON' if led_state else 'OFF'} "
              f"(interval: {actual_interval_ms:.1f}ms, delay: {delay_ms:.1f}ms)")

        last_signal_time = current_time

    # 정리
    if ser:
        ser.close()
    print("Shutdown complete")


if __name__ == "__main__":
    main()
