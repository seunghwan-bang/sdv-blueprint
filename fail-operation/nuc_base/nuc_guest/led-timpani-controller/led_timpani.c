/*
 * LED TIMPANI Controller - Signal-based periodic control
 * 
 * Architecture:
 * - Worker thread: Continuously runs busy_work (simulates CPU load)
 * - Main thread: Waits for TIMPANI signal and toggles LED
 * - Metrics thread: Exposes Prometheus metrics on HTTP port 9101
 * 
 * This demonstrates TIMPANI's advantage:
 * - Even with continuous CPU work, LED toggle timing is precise
 * - TIMPANI signal preempts the busy work for immediate response
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
#include <stdbool.h>
#include <errno.h>
#include <time.h>
#include <sys/prctl.h>
#include <pthread.h>
#include <sched.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

/* TIMPANI-N uses __SIGRTMIN+2 for time-triggered scheduling */
#define SIGNO_TT (__SIGRTMIN + 2)

#define DEFAULT_SERIAL_PORT "/dev/arduino_led_timpani"
#define BAUD_RATE B115200
#define EXPECTED_INTERVAL_MS 500.0  /* 예상 주기 (ms) */
#define DEFAULT_BUSY_ITERATIONS 13000000  /* 기본 반복 횟수 (환경변수로 조정 가능) */
#define SYNC_FILE "/tmp/timpani_start"  /* 동기화 파일 */
#define LED_STATE_FILE "/tmp/timpani_led_state"  /* LED 상태 파일 (normal 동기화용) */
#define METRICS_PORT 9101  /* Prometheus metrics port */

volatile bool shutdown_requested = false;
volatile bool sync_file_created = false;
int serial_fd = -1;
unsigned long signal_count = 0;
bool led_state = false;
int busy_iterations = DEFAULT_BUSY_ITERATIONS;  /* 환경변수로 조정 가능 */

/* Prometheus metrics - thread-safe with volatile */
volatile double metrics_delay_ms = 0.0;
volatile double metrics_interval_ms = 500.0;
volatile int metrics_led_state = 0;
volatile unsigned long metrics_signal_count = 0;

static int get_busy_iterations(void) {
    const char *env_val = getenv("BUSY_ITERATIONS");
    if (env_val != NULL) {
        int val = atoi(env_val);
        if (val > 0) {
            printf("[get_busy_iterations] BUSY_ITERATIONS env: %s\n", env_val);
            return val;
        }
    }
    printf("[get_busy_iterations] Using default: %d\n", DEFAULT_BUSY_ITERATIONS);
    return DEFAULT_BUSY_ITERATIONS;
}

static void shutdown_handler(int signo) {
    shutdown_requested = true;
    printf("\nShutdown signal received: %d\n", signo);
}

/* Empty handler for SIGRTMIN+2 - prevents default termination behavior for PID 1 */
static void tt_signal_handler(int signo) {
    (void)signo;
}

/**
 * busy_wait_iterations - CPU 부하 시뮬레이션
 */
static unsigned long long busy_wait_iterations(int iterations) {
    unsigned long long total = 0;
    for (int i = 0; i < iterations; i++) {
        total += (unsigned long long)i * i;
    }
    return total;
}

/**
 * worker_thread - 별도 스레드에서 busy_work 계속 실행
 * - CPU 부하를 계속 발생시킴 (led_normal과 동일한 조건)
 * - TIMPANI 신호와 독립적으로 실행
 */
static void *worker_thread(void *arg) {
    (void)arg;
    
    /* 동기화 파일이 생성될 때까지 대기 (TIMPANI-N이 affinity 설정 완료 후) */
    while (!shutdown_requested && !sync_file_created) {
        usleep(10000);  /* 10ms */
    }
    
    /* TIMPANI-N이 main thread에 설정한 CPU affinity를 worker에도 적용 */
    cpu_set_t cpuset;
    pid_t main_tid = getpid();  /* main thread의 TID (= PID) */
    if (sched_getaffinity(main_tid, sizeof(cpuset), &cpuset) == 0) {
        pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset);
        printf("[Worker] CPU affinity inherited from main thread\n");
    }
    
    printf("[Worker] Starting continuous busy_work...\n");
    
    while (!shutdown_requested) {
        busy_wait_iterations(busy_iterations);
    }
    
    printf("[Worker] Stopped.\n");
    return NULL;
}

static int setup_serial(const char *port) {
    int fd = open(port, O_RDWR | O_NOCTTY | O_SYNC);
    if (fd < 0) {
        perror("Failed to open serial port");
        return -1;
    }

    struct termios tty;
    if (tcgetattr(fd, &tty) != 0) {
        perror("tcgetattr failed");
        close(fd);
        return -1;
    }

    cfsetospeed(&tty, BAUD_RATE);
    cfsetispeed(&tty, BAUD_RATE);

    tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;
    tty.c_cflag |= (CLOCAL | CREAD);
    tty.c_cflag &= ~(PARENB | PARODD);
    tty.c_cflag &= ~CSTOPB;
    tty.c_cflag &= ~CRTSCTS;

    tty.c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP | INLCR | IGNCR | ICRNL | IXON);
    tty.c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
    tty.c_oflag &= ~OPOST;

    tty.c_cc[VMIN] = 0;
    tty.c_cc[VTIME] = 1;

    if (tcsetattr(fd, TCSANOW, &tty) != 0) {
        perror("tcsetattr failed");
        close(fd);
        return -1;
    }

    return fd;
}

static void send_led_signal(int fd, const char *msg) {
    if (fd >= 0) {
        write(fd, msg, strlen(msg));
        fsync(fd);
    }
}

static double get_time_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1000000.0;
}

/**
 * metrics_thread - HTTP server for Prometheus metrics
 * Listens on port 9101 and serves /metrics endpoint
 */
static void *metrics_thread(void *arg) {
    (void)arg;
    int server_fd, client_fd;
    struct sockaddr_in address;
    int opt = 1;
    
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("[Metrics] Socket creation failed");
        return NULL;
    }
    
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt));
    
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(METRICS_PORT);
    
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("[Metrics] Bind failed");
        close(server_fd);
        return NULL;
    }
    
    if (listen(server_fd, 3) < 0) {
        perror("[Metrics] Listen failed");
        close(server_fd);
        return NULL;
    }
    
    printf("[Metrics] Prometheus metrics server started on port %d\n", METRICS_PORT);
    
    while (!shutdown_requested) {
        struct timeval tv;
        tv.tv_sec = 1;
        tv.tv_usec = 0;
        
        fd_set readfds;
        FD_ZERO(&readfds);
        FD_SET(server_fd, &readfds);
        
        int activity = select(server_fd + 1, &readfds, NULL, NULL, &tv);
        if (activity < 0 && errno != EINTR) {
            continue;
        }
        
        if (activity <= 0) continue;
        
        socklen_t addrlen = sizeof(address);
        client_fd = accept(server_fd, (struct sockaddr *)&address, &addrlen);
        if (client_fd < 0) continue;
        
        /* Read request (simple - just consume it) */
        char buffer[1024];
        read(client_fd, buffer, sizeof(buffer));
        
        /* Generate Prometheus metrics response */
        char metrics_body[2048];
        int body_len = snprintf(metrics_body, sizeof(metrics_body),
            "# HELP led_delay_ms LED control delay in milliseconds\n"
            "# TYPE led_delay_ms gauge\n"
            "led_delay_ms{container=\"timpani\"} %.2f\n"
            "# HELP led_interval_ms LED toggle interval in milliseconds\n"
            "# TYPE led_interval_ms gauge\n"
            "led_interval_ms{container=\"timpani\"} %.2f\n"
            "# HELP led_state Current LED state (0=OFF, 1=ON)\n"
            "# TYPE led_state gauge\n"
            "led_state{container=\"timpani\"} %d\n"
            "# HELP led_signal_count Total LED toggle count\n"
            "# TYPE led_signal_count counter\n"
            "led_signal_count{container=\"timpani\"} %lu\n",
            metrics_delay_ms,
            metrics_interval_ms,
            metrics_led_state,
            metrics_signal_count
        );
        
        char response[4096];
        int resp_len = snprintf(response, sizeof(response),
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            "Content-Length: %d\r\n"
            "Connection: close\r\n"
            "\r\n%s",
            body_len, metrics_body
        );
        
        write(client_fd, response, resp_len);
        close(client_fd);
    }
    
    close(server_fd);
    printf("[Metrics] Prometheus metrics server stopped\n");
    return NULL;
}

int main(int argc, char *argv[]) {
    sigset_t sig_set;
    int signo = SIGNO_TT;
    const char *serial_port = DEFAULT_SERIAL_PORT;
    double last_time, current_time, actual_interval;
    double computation_start_time = 0.0;
    pthread_t worker_tid;
    pthread_t metrics_tid;

    /* Disable stdout buffering for immediate log output in container */
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    /* 환경변수에서 busy_iterations 읽기 */
    busy_iterations = get_busy_iterations();

    /* Parse command line arguments */
    if (argc > 1) {
        serial_port = argv[1];
    }

    printf("=== LED TIMPANI Controller (signal-based) ===\n");
    printf("Serial port: %s\n", serial_port);
    printf("Toggle interval: %.0fms (TIMPANI signal)\n", EXPECTED_INTERVAL_MS);
    printf("Busy iterations: %d\n", busy_iterations);
    printf("Metrics port: %d\n", METRICS_PORT);
    printf("!!  CPU 부하와 무관하게 정확한 주기 유지  !!\n");
    printf("Architecture: Worker thread + Signal handler\n");
    printf("================================================\n");

    /* Start metrics thread for Prometheus */
    if (pthread_create(&metrics_tid, NULL, metrics_thread, NULL) != 0) {
        perror("Failed to create metrics thread");
        /* Continue without metrics - not fatal */
    } else {
        printf("Metrics thread started\n");
    }

    /* 시작 시 동기화 파일 삭제 (이전 실행에서 남은 파일 정리) */
    if (unlink(SYNC_FILE) == 0) {
        printf("Removed old sync file: %s\n", SYNC_FILE);
    }

    /* Set process name for TIMPANI-N to identify this task */
    prctl(PR_SET_NAME, "led_timpani", 0, 0, 0);

    /* Setup shutdown signal handlers (SIGINT, SIGTERM) */
    struct sigaction sa;
    sa.sa_handler = shutdown_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    /* Register handler for SIGRTMIN+2 to prevent default termination */
    struct sigaction sa_tt;
    sa_tt.sa_handler = tt_signal_handler;
    sigemptyset(&sa_tt.sa_mask);
    sa_tt.sa_flags = 0;
    sigaction(signo, &sa_tt, NULL);

    /* Block SIGNO_TT for synchronous handling via sigwait */
    sigemptyset(&sig_set);
    sigaddset(&sig_set, signo);
    if (sigprocmask(SIG_BLOCK, &sig_set, NULL) == -1) {
        perror("sigprocmask failed");
        return EXIT_FAILURE;
    }

    /* Open serial port to Arduino */
    serial_fd = setup_serial(serial_port);
    if (serial_fd < 0) {
        fprintf(stderr, "Warning: Could not open serial port %s\n", serial_port);
        fprintf(stderr, "Running in dry-run mode (no LED control)\n");
    } else {
        printf("Connected to %s\n", serial_port);
    }

    /* Start worker thread for continuous busy_work */
    if (pthread_create(&worker_tid, NULL, worker_thread, NULL) != 0) {
        perror("Failed to create worker thread");
        return EXIT_FAILURE;
    }
    printf("Worker thread started\n");

    /* Main loop: wait for TIMPANI-N periodic signal */
    struct timespec timeout;
    timeout.tv_sec = 1;
    timeout.tv_nsec = 0;

    last_time = get_time_ms();

    while (!shutdown_requested) {
        int ret = sigtimedwait(&sig_set, NULL, &timeout);
        if (ret == -1) {
            if (errno == EAGAIN) {
                continue;
            } else if (errno == EINTR) {
                continue;
            } else {
                perror("sigtimedwait failed");
                break;
            }
        }
        if (ret == signo) {
            // 연산(시그널 수신~LED 토글) 시작 시각 기록
            computation_start_time = get_time_ms();
            // 첫 신호 수신 시 동기화 파일 생성 (led_normal 시작 트리거)
            if (!sync_file_created) {
                FILE *f = fopen(SYNC_FILE, "w");
                if (f) {
                    fclose(f);
                    printf("Sync file created: %s\n", SYNC_FILE);
                }
                sync_file_created = true;
            }
            signal_count++;
            led_state = !led_state;
            send_led_signal(serial_fd, led_state ? "1" : "0");
            // LED 상태를 파일에 기록 (normal 동기화용)
            {
                FILE *sf = fopen(LED_STATE_FILE, "w");
                if (sf) {
                    fprintf(sf, "%d", led_state ? 1 : 0);
                    fclose(sf);
                }
            }
            // 연산(시그널 수신~LED 토글) 종료 시각
            double computation_end_time = get_time_ms();
            double computation_duration = computation_end_time - computation_start_time; // ms
            // interval 측정 (이전 신호로부터 경과 시간)
            current_time = computation_end_time;
            actual_interval = current_time - last_time;
            // Prometheus metrics 업데이트
            // Grafana delay: 정상(연산<500ms)이면 interval-500, 부하(연산>=500ms)이면 연산시간
            if (computation_duration < 500.0) {
                metrics_delay_ms = actual_interval - 500.0;  // interval 대비 지연
                if (metrics_delay_ms < 0) metrics_delay_ms = 0;
            } else {
                metrics_delay_ms = computation_duration;  // 연산 시간 자체가 delay
            }
            metrics_interval_ms = actual_interval;
            metrics_led_state = led_state ? 1 : 0;
            metrics_signal_count = signal_count;
            if (computation_duration > 100.0) {
                printf("[Timpani %lu] !! LED %s (interval: %.1fms, delay: %.1fms) - DELAY WARNING\n", signal_count, led_state ? "ON" : "OFF", actual_interval, computation_duration);
            } else {
                printf("[Timpani %lu] LED %s (interval: %.1fms, delay: %.1fms)\n", signal_count, led_state ? "ON" : "OFF", actual_interval, computation_duration);
            }
            fflush(stdout);
            last_time = current_time;
        } else {
            printf("Unexpected signal received: %d\n", ret);
        }
    }

    /* Wait for worker thread to finish */
    pthread_join(worker_tid, NULL);

    /* Wait for metrics thread to finish */
    pthread_join(metrics_tid, NULL);

    unlink(SYNC_FILE);

    printf("LED TIMPANI Controller terminated. Total toggles: %lu\n", signal_count);
    return EXIT_SUCCESS;
}
