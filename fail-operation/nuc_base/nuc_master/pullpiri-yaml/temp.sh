---
apiVersion: v1
kind: Scenario
metadata:
  name: failop-containers-launch
spec:
  condition: null
  action: launch
  target: failop-all-workloads
---
apiVersion: v1
kind: Package
metadata:
  label: null
  name: failop-all-workloads
spec:
  pattern:
    - type: plain
  models:
    - name: guest-bridge
      node: guest
      resources:
        volume:
        network:
    - name: led-timpani
      node: guest
      resources:
        volume:
        network:
    - name: led-normal
      node: guest
      resources:
        volume:
        network:
---
apiVersion: v1
kind: Model
metadata:
  name: guest-bridge
  annotations:
    io.piccolo.annotations.package-type: failop-workload
    io.piccolo.annotations.package-name: failop-all-workloads
    io.piccolo.annotations.package-network: default
  labels:
    app: guest-bridge
spec:
  containers:
    - name: kuksa-bridge-container
      image: localhost/failop-kuksa-bridge-guest:latest
  terminationGracePeriodSeconds: 0
  restartPolicy: Never
---
apiVersion: v1
kind: Model
metadata:
  name: led-timpani
  annotations:
    io.piccolo.annotations.package-type: failop-workload
    io.piccolo.annotations.package-name: failop-all-workloads
    io.piccolo.annotations.package-network: default
  labels:
    app: led-timpani
spec:
  containers:
    - name: led-timpani-container
      image: localhost/led-timpani-controller:latest
  terminationGracePeriodSeconds: 0
  restartPolicy: Never
---
apiVersion: v1
kind: Model
metadata:
  name: led-normal
  annotations:
    io.piccolo.annotations.package-type: failop-workload
    io.piccolo.annotations.package-name: failop-all-workloads
    io.piccolo.annotations.package-network: default
  labels:
    app: led-normal
spec:
  containers:
    - name: led-normal-container
      image: localhost/led-normal-controller:latest
  terminationGracePeriodSeconds: 0
  restartPolicy: Never



---
