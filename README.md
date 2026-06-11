<img width="136" height="729" alt="webhook" src="https://github.com/user-attachments/assets/1f6354a8-a50b-4ec5-b901-96e2b6ddb1d7" />
# SRE CI/CD Pipeline
# 🚀 SRE CI/CD Pipeline

> A production-grade CI/CD pipeline built with Jenkins, Docker, Kubernetes, and Prometheus — automating the full software delivery lifecycle from code commit to monitored deployment.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Pipeline Stages](#pipeline-stages)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Kubernetes Manifests](#kubernetes-manifests)
- [Monitoring](#monitoring)
- [API Endpoints](#api-endpoints)
- [Problems Solved](#problems-solved)
- [Screenshots](#screenshots)

---

## Overview

This project implements a fully automated CI/CD pipeline following Site Reliability Engineering (SRE) best practices. Every `git push` to the `main` branch automatically triggers the pipeline — building, testing, scanning, pushing, and deploying the application to a Kubernetes cluster with zero downtime.

**Key capabilities:**
- Automatic pipeline trigger via GitHub webhooks
- Docker image build and push to DockerHub registry
- Trivy vulnerability scanning on every build
- Kubernetes rolling deployments with zero downtime
- Auto rollback on deployment failure
- Full observability with Prometheus and Grafana

---

## Architecture

```
Developer
    │
    │  git push
    ▼
┌─────────────┐
│   GitHub    │──── Webhook ────▶ Jenkins
└─────────────┘                      │
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                  │
                    ▼                 ▼                  ▼
             Docker Build        Trivy Scan        Run Tests
                    │                 │                  │
                    └─────────────────┴──────────────────┘
                                      │
                                      ▼
                              DockerHub Registry
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │   Kubernetes Cluster    │
                         │   ┌──────────────────┐  │
                         │   │  Pod 1 (Flask)   │  │
                         │   │  Pod 2 (Flask)   │  │
                         │   │  Pod 3 (Flask)   │  │
                         │   └──────────────────┘  │
                         └────────────────────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │  Prometheus + Grafana   │
                         │  (Monitoring Stack)     │
                         └────────────────────────┘
```

---

## Tech Stack

| Category | Technology |
|---|---|
| Application | Python 3.12, Flask, Gunicorn |
| Containerization | Docker |
| CI/CD | Jenkins (Groovy Pipeline) |
| Container Registry | DockerHub |
| Orchestration | Kubernetes (Minikube) |
| Security Scanning | Trivy |
| Monitoring | Prometheus, Grafana |
| Version Control | Git, GitHub |
| Scripting | Bash, Groovy |

---

## Pipeline Stages

```
┌──────────────────────────────────────────────────────────────┐
│                    Jenkins Pipeline                           │
│                                                              │
│  1. Checkout SCM    → Pull latest code from GitHub           │
│  2. Checkout        → Verify workspace                       │
│  3. Build Image     → docker build + tag with BUILD_NUMBER   │
│  4. Test Container  → Health check with retry logic          │
│  5. Trivy Scan      → Vulnerability scan (CRITICAL/HIGH)     │
│  6. Push to Hub     → Push :tag and :latest to DockerHub     │
│  7. K8s Deploy      → Rolling update to Kubernetes           │
│  8. Verify Rollout  → Confirm all 3 pods are running         │
│                                                              │
│  Post: Rollback on failure + cleanup + workspace wipe        │
└──────────────────────────────────────────────────────────────┘
```

### Rollback Strategy

If any stage fails after deployment, the pipeline automatically runs:
```bash
kubectl rollout undo deployment/python-app
```
This reverts to the last known good deployment instantly.

---

## Project Structure

```
sre-cicd-pipeline/
├── app/
│   ├── app.py                  # Flask application
│   └── requirements.txt        # Python dependencies
├── k8s/
│   ├── deployment.yaml         # K8s Deployment (3 replicas, rolling update)
│   └── service.yaml            # K8s NodePort Service
├── Dockerfile                  # Multi-stage Docker build
├── Jenkinsfile                 # Groovy pipeline definition
└── README.md
```

---

## Setup Instructions

### Prerequisites

```bash
# Required tools
Docker        >= 24.0
Minikube      >= 1.35
kubectl       >= 1.35
Jenkins       LTS
Helm          >= 3.0
ngrok         (for webhook tunneling on local)
```

### Step 1 — Clone Repository

```bash
git clone https://github.com/Jimmyvrushabh/sre-cicd-pipeline.git
cd sre-cicd-pipeline
```

### Step 2 — Start Minikube

```bash
minikube start
kubectl get nodes
```

### Step 3 — Start Jenkins

```bash
docker run -d \
  --name jenkins \
  -p 8081:8080 \
  -p 50001:50000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v jenkins_home:/var/jenkins_home \
  --add-host=host.docker.internal:host-gateway \
  jenkins/jenkins:lts
```

### Step 4 — Configure Jenkins

```bash
# Fix Docker socket permissions
docker exec -u 0 jenkins chmod 666 /var/run/docker.sock

# Copy kubeconfig into Jenkins
docker exec -u 0 jenkins mkdir -p /var/jenkins_home/.kube
docker cp ~/.kube/config jenkins:/var/jenkins_home/.kube/config
docker cp ~/.minikube jenkins:/var/jenkins_home/.minikube

# Fix cert paths
docker exec -u 0 jenkins \
  sed -i 's|/home/vrush/.minikube|/var/jenkins_home/.minikube|g' \
  /var/jenkins_home/.kube/config

# Start kubectl proxy for Jenkins → K8s connectivity
kubectl proxy \
  --address='0.0.0.0' \
  --port=9090 \
  --accept-hosts='.*' \
  --disable-filter=true &

# Point kubeconfig to proxy
docker exec -u 0 jenkins bash -c \
  "KUBECONFIG=/var/jenkins_home/.kube/config \
   kubectl config set-cluster minikube \
   --server=http://host.docker.internal:9090 \
   --insecure-skip-tls-verify=true"
```

### Step 5 — Add DockerHub Credentials in Jenkins

```
Jenkins UI → Manage Jenkins → Credentials
→ System → Global credentials → Add Credentials
  Kind     : Username with password
  Username : <your-dockerhub-username>
  Password : <your-dockerhub-password>
  ID       : dockerhub-credentials
```

### Step 6 — Configure GitHub Webhook

```bash
# Expose Jenkins via ngrok
ngrok http 8081
```

```
GitHub → repo Settings → Webhooks → Add webhook
  Payload URL : https://<ngrok-url>/github-webhook/
  Content type: application/json
  Events      : Just the push event
```

```
Jenkins → CiCd Projects → Configure
→ Build Triggers
→ ✅ GitHub hook trigger for GITScm polling
```

### Step 7 — Install Monitoring Stack

```bash
# Add Helm repo
helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus + Grafana
helm install monitoring \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin123

# Access Grafana
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80 &
# Open: http://localhost:3000 (admin/admin123)
```

---

## Kubernetes Manifests

### Deployment — Rolling Update Strategy

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # 1 extra pod during update
    maxUnavailable: 0  # Zero downtime guaranteed
```

### Health Probes

```yaml
readinessProbe:
  httpGet:
    path: /ready    # Pod ready for traffic?
    port: 5000
livenessProbe:
  httpGet:
    path: /health   # Pod still alive?
    port: 5000
```

### Resource Limits

```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

---

## Monitoring

### Prometheus
Scrapes metrics from all K8s components every 15 seconds.

```bash
# Access Prometheus
kubectl port-forward -n monitoring \
  svc/monitoring-kube-prometheus-prometheus 9191:9090 &
# Open: http://localhost:9191
```

**Useful PromQL queries:**
```promql
# Running pods
kube_pod_status_phase{phase="Running"}

# Node memory available
node_memory_MemAvailable_bytes

# Container CPU usage
container_cpu_usage_seconds_total

# Pod restart count
kube_pod_container_status_restarts_total
```

### Grafana Dashboards

| Dashboard | ID | Description |
|---|---|---|
| K8s Cluster Overview | 3119 | CPU, Memory, Pod count |
| Pod Monitoring | 6417 | Per-pod metrics |
| Node Exporter | 1860 | Node-level metrics |

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Application home |
| `/health` | GET | Liveness check |
| `/ready` | GET | Readiness check |
| `/version` | GET | Build version info |
| `/metrics` | GET | Prometheus metrics |

### Sample Responses

```json
// GET /health
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-06-11T02:00:00.000Z"
}

// GET /version
{
  "version": "1.0.0",
  "build": "32",
  "environment": "production"
}
```

---

## Problems Solved

### 1. Jenkins ↔ Kubernetes Networking
**Problem:** Jenkins running inside Docker couldn't reach Minikube's K8s API. The kubeconfig pointed to `127.0.0.1` which resolved to Jenkins container's localhost, not the host machine.

**Solution:**
```bash
# Used kubectl proxy to bridge the network gap
kubectl proxy --address='0.0.0.0' --port=9090 --accept-hosts='.*' &

# Updated kubeconfig server to use host.docker.internal
kubectl config set-cluster minikube \
  --server=http://host.docker.internal:9090
```

### 2. Docker Socket Permissions
**Problem:** Jenkins non-root user couldn't access `/var/run/docker.sock` after container restart.

**Solution:**
```bash
docker exec -u 0 jenkins chmod 666 /var/run/docker.sock
```

### 3. Container Health Check (curl to localhost)
**Problem:** `curl localhost:5000` failed because Jenkins and the test container are in different network namespaces.

**Solution:**
```bash
# Get container IP directly
CONTAINER_IP=$(docker inspect -f \
  '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
  test-container)
curl http://$CONTAINER_IP:5000/health
```

### 4. Minikube Port Binding
**Problem:** Minikube API bound to `127.0.0.1:PORT` only — not reachable from Docker containers.

**Solution:** Used `kubectl proxy` with `--address='0.0.0.0'` to expose on all interfaces.

---

## Startup Script

Run this every time WSL/system restarts:

```bash
#!/bin/bash
# ~/jenkins-setup.sh

minikube start
pkill -f "kubectl proxy" || true
kubectl proxy --address='0.0.0.0' --port=9090 \
  --accept-hosts='.*' --disable-filter=true &
docker start jenkins
sleep 3
docker exec -u 0 jenkins chmod 666 /var/run/docker.sock
docker exec -u 0 jenkins mkdir -p /var/jenkins_home/.kube
docker cp ~/.kube/config jenkins:/var/jenkins_home/.kube/config
docker cp ~/.minikube jenkins:/var/jenkins_home/.minikube
docker exec -u 0 jenkins \
  sed -i 's|/home/vrush/.minikube|/var/jenkins_home/.minikube|g' \
  /var/jenkins_home/.kube/config
docker exec -u 0 jenkins bash -c \
  "KUBECONFIG=/var/jenkins_home/.kube/config \
   kubectl config set-cluster minikube \
   --server=http://host.docker.internal:9090 \
   --insecure-skip-tls-verify=true"
echo "✅ All systems ready!"
```

---
[README.md](https://github.com/user-attachments/files/28822888/README.md)
## Author

**Vrushabh Chaudhari**
- GitHub: [@Jimmyvrushabh](https://github.com/Jimmyvrushabh)
- LinkedIn: [linkedin.com/in/vrushabhc22](https://linkedin.com/in/vrushabhc22)
- Email: vrushabhc200201@gmail.com

---

> Built with 💪 persistence through 30+ pipeline builds and countless networking debugging sessions.

