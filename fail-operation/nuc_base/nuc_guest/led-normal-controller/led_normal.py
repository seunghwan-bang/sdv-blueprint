#!/usr/bin/env python3
"""
LED Normal Controller - Interval-based with computation check
500ms interval 고정, 연산이 interval 내에 완료되면 LED 신호 전송
연산이 interval을 넘어가면 다음 interval 스킵 (부하 상태 시각화)
CPU 12 pinned via os.sched_setaffinity()

Prometheus metrics exposed on port 9102
"""
import serial
import time
import sys
import signal
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = '/dev/arduino_led_normal'
BAUD = 115200
INTERVAL = 0.5  # 500ms 주기 (고정)
METRICS_PORT = 9102  # Prometheus metrics port

# 동기화 파일 (led_timpani가 생성)
SYNC_FILE = '/tmp/timpani_start'

# LED 상태 파일 (timpani가 기록, 부하 후 동기화용)
LED_STATE_FILE = '/tmp/timpani_led_state'

# 연산 반복 횟수 기본값 (환경변수 BUSY_ITERATIONS로 조정 가능)
# 정상: ~300ms, 부하: 500ms+ (interval 초과)
DEFAULT_BUSY_ITERATIONS = 13000000

# Prometheus metrics (thread-safe via GIL)
metrics = {
    'delay_ms': 0.0,
    'interval_ms': 500.0,
    'led_state': 0,
    'signal_count': 0
}


def get_busy_iterations():
    # 환경변수에서 반복 횟수 읽기 (기본값 13000000)
    env_val = os.environ.get('BUSY_ITERATIONS', str(DEFAULT_BUSY_ITERATIONS))
    try:
        iterations = int(env_val)
        print(f"[get_busy_iterations] BUSY_ITERATIONS env: {env_val}")
        return iterations
    except Exception as e:
        print(f"[get_busy_iterations] Invalid BUSY_ITERATIONS env: {env_val} ({e}), fallback to {DEFAULT_BUSY_ITERATIONS}")
        return DEFAULT_BUSY_ITERATIONS


def read_timpani_led_state():
    """
    timpani의 현재 LED 상태를 파일에서 읽음
    부하 후 동기화에 사용
    """
    try:
        if os.path.exists(LED_STATE_FILE):
            with open(LED_STATE_FILE, 'r') as f:
                state = f.read().strip()
                return state == '1'
    except Exception:
        pass
    return None  # 읽기 실패 시 None 반환


def get_cpu_affinity():
    # 환경변수에서 CPU 번호 읽기 (기본값 12)
    env_val = os.environ.get('CPU_AFFINITY', '12')
    try:
        cpu_set = {int(env_val)}
        print(f"[get_cpu_affinity] CPU_AFFINITY env: {env_val} → set: {cpu_set}")
        return cpu_set
    except Exception as e:
        print(f"[get_cpu_affinity] Invalid CPU_AFFINITY env: {env_val} ({e}), fallback to {{12}}")
        return {12}


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint"""
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP request logging
    
    def do_GET(self):
        if self.path == '/metrics' or self.path == '/':
            body = (
                '# HELP led_delay_ms LED control delay in milliseconds\n'
                '# TYPE led_delay_ms gauge\n'
                f'led_delay_ms{{container="normal"}} {metrics["delay_ms"]:.2f}\n'
                '# HELP led_interval_ms LED toggle interval in milliseconds\n'
                '# TYPE led_interval_ms gauge\n'
                f'led_interval_ms{{container="normal"}} {metrics["interval_ms"]:.2f}\n'
                '# HELP led_state Current LED state (0=OFF, 1=ON)\n'
                '# TYPE led_state gauge\n'
                f'led_state{{container="normal"}} {metrics["led_state"]}\n'
                '# HELP led_signal_count Total LED toggle count\n'
                '# TYPE led_signal_count counter\n'
                f'led_signal_count{{container="normal"}} {metrics["signal_count"]}\n'
            )
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body.encode())
        else:
            self.send_response(404)
            self.end_headers()


def start_metrics_server():
    """Start Prometheus metrics HTTP server in background thread"""
    try:
        server = HTTPServer(('0.0.0.0', METRICS_PORT), MetricsHandler)
        print(f"[Metrics] Prometheus metrics server started on port {METRICS_PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"[Metrics] Failed to start metrics server: {e}", file=sys.stderr)


running = True

def signal_handler(sig, frame):
    global running
    running = False
    print("Shutdown signal received...")


class ComputationWorker:
    """
    별도 스레드에서 연산을 수행하고, 완료 여부를 추적
    """
    def __init__(self):
        self.is_running = False
        self.is_completed = False
        self.thread = None
        self.result = None
        self.computation_time = 0
    
    def compute(self, iterations):
        """CPU 집약적 연산 수행"""
        total = 0
        for i in range(iterations):
            total += i * i
        return total
    
    def start(self, iterations):
        """연산 시작 (새 스레드에서)"""
        if self.is_running:
            return False  # 이미 실행 중
        
        self.is_running = True
        self.is_completed = False
        self.thread = threading.Thread(target=self._run, args=(iterations,))
        self.thread.start()
        return True
    
    def _run(self, iterations):
        """스레드에서 실행되는 연산"""
        start_time = time.perf_counter()
        self.result = self.compute(iterations)
        self.computation_time = time.perf_counter() - start_time
        self.is_completed = True
        self.is_running = False
    
    def check_completed(self):
        """연산이 완료되었는지 확인"""
        return self.is_completed
    
    def reset(self):
        """상태 리셋"""
        self.is_completed = False
        self.result = None


def main():
    cpu_affinity = get_cpu_affinity()
    busy_iterations = get_busy_iterations()
    
    os.sched_setaffinity(0, cpu_affinity)
    print(f"CPU affinity set to: {cpu_affinity}")
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start Prometheus metrics server in background thread
    metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
    metrics_thread.start()
    
    print(f"=== LED Normal Controller (interval-based) ===")
    print(f"Serial port: {PORT}")
    print(f"Fixed interval: {INTERVAL*1000:.0f}ms")
    print(f"Busy iterations: {busy_iterations}")
    print(f"Metrics port: {METRICS_PORT}")
    print(f"!! 부하 시 연산이 interval 초과하면 LED 스킵 !!")
    print(f"Waiting for sync file ({SYNC_FILE})...")
    
    # 동기화 파일 대기 (led_timpani와 동시 시작)
    while running and not os.path.exists(SYNC_FILE):
        time.sleep(0.01)  # 더 빠른 감지를 위해 10ms로 줄임
    
    if not running:
        print("Shutdown before sync file detected")
        return
    
    print(f"Sync file detected! Starting LED control...")
    
    worker = ComputationWorker()
    signal_count = 0
    skip_count = 0
    led_state = False
    was_skipping = False  # 이전 interval이 스킵이었는지 추적
    
    while running:
        try:
            with serial.Serial(PORT, BAUD, timeout=1) as ser:
                print(f"Connected to {PORT}")
                # sync file 감지 직후 첫 LED 토글 (timpani와 동시 시작)
                signal_count += 1
                led_state = not led_state
                ser.write(b'1' if led_state else b'0')
                ser.flush()
                print(f"[Normal {signal_count}] LED {'ON' if led_state else 'OFF'} (start)")
                # 첫 interval 시작 시간 기록
                last_signal_time = time.perf_counter()
                next_interval_time = last_signal_time + INTERVAL
                # 첫 연산 시작
                computation_start_time = time.perf_counter()
                worker.start(busy_iterations)
                computation_logged = False  # 이번 interval에서 연산 완료 로그를 찍었는지
                while running:
                    current_time = time.perf_counter()
                    
                    # 연산 완료 시 즉시 metrics 업데이트 (LED toggle은 interval 끝에)
                    # Grafana delay: 정상(연산<500ms)이면 interval-500, 부하(연산>=500ms)이면 연산시간
                    if worker.check_completed() and not computation_logged:
                        comp_time_ms = worker.computation_time * 1000
                        # 정상인 경우 일단 0으로 설정 (interval 끝에 최종 계산)
                        if comp_time_ms < 500:
                            metrics['delay_ms'] = 0  # 나중에 interval 끝에서 계산
                        else:
                            metrics['delay_ms'] = comp_time_ms  # 연산 시간 자체가 delay
                        computation_logged = True
                    
                    # interval 끝 시점 도달 여부 확인
                    if current_time >= next_interval_time:
                        # interval 끝 시점에 연산 완료 여부 확인
                        if worker.check_completed():
                            # 스킵에서 복귀 시 timpani와 동기화 (토글 없이 바로 동기화)
                            if was_skipping:
                                timpani_state = read_timpani_led_state()
                                if timpani_state is not None:
                                    # timpani 상태와 동일하게 바로 설정 (토글 없이)
                                    led_state = timpani_state
                                    ser.write(b'1' if led_state else b'0')
                                    ser.flush()
                                    signal_count += 1
                                    computation_duration = worker.computation_time * 1000
                                    actual_interval = current_time - last_signal_time
                                    actual_interval_ms = actual_interval * 1000
                                    # Grafana delay
                                    if computation_duration < 500:
                                        delay_for_grafana = actual_interval_ms - 500
                                        if delay_for_grafana < 0:
                                            delay_for_grafana = 0
                                        metrics['delay_ms'] = delay_for_grafana
                                    else:
                                        metrics['delay_ms'] = computation_duration
                                    metrics['interval_ms'] = actual_interval_ms
                                    metrics['led_state'] = 1 if led_state else 0
                                    metrics['signal_count'] = signal_count
                                    print(f"[Normal {signal_count}] SYNC LED {'ON' if led_state else 'OFF'} (interval: {actual_interval_ms:.1f}ms, delay: {computation_duration:.1f}ms)")
                                    last_signal_time = current_time
                                was_skipping = False
                                # 새 연산 시작
                                worker.reset()
                                computation_start_time = time.perf_counter()
                                worker.start(busy_iterations)
                                computation_logged = False
                            else:
                                # 정상: 연산 완료 → LED 토글
                                signal_count += 1
                                led_state = not led_state
                                ser.write(b'1' if led_state else b'0')
                                ser.flush()
                                # 실제 연산에 걸린 시간 (worker 내부에서 측정)
                                computation_duration = worker.computation_time * 1000  # ms
                                # interval 측정 (이전 신호로부터 경과 시간)
                                actual_interval = current_time - last_signal_time
                                # Update Prometheus metrics
                                # Grafana delay: 정상(연산<500ms)이면 interval-500, 부하(연산>=500ms)이면 연산시간
                                actual_interval_ms = actual_interval * 1000
                                if computation_duration < 500:
                                    delay_for_grafana = actual_interval_ms - 500
                                    if delay_for_grafana < 0:
                                        delay_for_grafana = 0
                                    metrics['delay_ms'] = delay_for_grafana
                                else:
                                    metrics['delay_ms'] = computation_duration
                                metrics['interval_ms'] = actual_interval_ms
                                metrics['led_state'] = 1 if led_state else 0
                                metrics['signal_count'] = signal_count
                                print(f"[Normal {signal_count}] LED {'ON' if led_state else 'OFF'} (interval: {actual_interval*1000:.1f}ms, delay: {computation_duration:.1f}ms)")
                                last_signal_time = current_time
                                # 상태 리셋 후 새 연산 시작
                                worker.reset()
                                computation_start_time = time.perf_counter()
                                worker.start(busy_iterations)
                                computation_logged = False
                        else:
                            # 연산 미완료 → 이번 interval SKIP (LED toggle 안 함)
                            skip_count += 1
                            was_skipping = True
                            # 실제 연산에 걸린 시간 (아직 진행 중이므로 현재까지의 시간)
                            elapsed_time = (current_time - computation_start_time) * 1000  # ms
                            print(f"[Normal] !! SKIP interval (연산 진행중: {elapsed_time:.1f}ms > 500ms)")
                            # metrics 업데이트: 연산 시간을 delay로 (부하 상황)
                            metrics['delay_ms'] = elapsed_time
                        
                        next_interval_time += INTERVAL
                    else:
                        # interval 끝까지 짧게 sleep
                        time.sleep(0.001)  # 1ms
                ser.write(b'0')
                ser.flush()
                print("Sent OFF signal before exit")
                
        except serial.SerialException as e:
            print(f"Serial error: {e}. Reconnecting in 1s...", file=sys.stderr)
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}. Retrying in 1s...", file=sys.stderr)
            time.sleep(1)
    
    print(f"LED Normal Controller terminated. Signals: {signal_count}, Skips: {skip_count}")

if __name__ == "__main__":
    main()
