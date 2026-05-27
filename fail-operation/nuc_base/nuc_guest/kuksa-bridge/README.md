# Fail-Operation Guest - KUKSA Subscriber

NUC Guest에서 실행되는 KUKSA databroker 구독자입니다. 
버튼 이벤트를 수신하여 워크로드 컨테이너를 실행합니다.

## 설정 파일

`.env` 파일을 통해 컨테이너 설정을 관리합니다.

### .env 파일 형식

```bash
# Container image to use for workload
CONTAINER_IMAGE=stress-ng

# Container name (fixed, will not change on each run)
CONTAINER_NAME=failop-workload

# Stress-ng CPU cores
STRESS_CPU=2

# Stress-ng timeout
STRESS_TIMEOUT=30s
```

### 설정 변경 방법

1. `.env` 파일 수정
2. 컨테이너 재시작 (자동으로 새 설정 로드)

```bash
# .env 파일 수정
vi /home/lge/work/sdv-blueprint/fail-operation/nuc_base/nuc_guest/kuksa-bridge/.env

# 재시작 (자동으로 새 설정 적용)
docker restart failop-kuksa-bridge-guest
```

## 빌드

```bash
cd /home/lge/work/sdv-blueprint/fail-operation/nuc_base/nuc_guest/kuksa-bridge
docker build -t failop-kuksa-bridge-guest:latest .
```

## 실행

```bash
docker run --rm -d \
  --name failop-kuksa-bridge-guest \
  --network host \
  -v /home/lge/work/sdv-blueprint/fail-operation/nuc_base/nuc_guest/kuksa-bridge/.env:/app/.env \
  -e PYTHONUNBUFFERED=1 \
  failop-kuksa-bridge-guest:latest
```

## 로그 확인

```bash
# 실시간 로그 모니터링
docker logs failop-kuksa-bridge-guest -f

# 최근 로그
docker logs failop-kuksa-bridge-guest --tail=20
```

## 동작 방식

1. **KUKSA Databroker 연결**
   - 포트: `55556` (fail-operation databroker)
   - 시그널: `Vehicle.Cabin.FailOperation.ButtonPressed`

2. **버튼 이벤트 처리**
   - 버튼 PRESSED → 워크로드 컨테이너 실행
   - 버튼 RELEASED → 액션 없음

3. **컨테이너 실행**
   - 기존 컨테이너가 있으면 삭제 후 새로 실행
   - `.env` 파일에서 설정 로드
   - `podman run`으로 실행

## 주의사항

- 컨테이너 이름은 `.env`에서 설정한 이름으로 고정됩니다
- 동일 이름의 컨테이너가 실행 중이면 자동으로 삭제 후 재실행
- Runtime에 `.env` 파일 수정 가능 (재시작 또는 다음 버튼 이벤트 시 적용)
