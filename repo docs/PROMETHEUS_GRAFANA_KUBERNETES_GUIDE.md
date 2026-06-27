# Prometheus, Grafana & Kubernetes Deployment Guide — HAR MLOps Pipeline

This guide extends the AWS deployment guide with two additional layers:

1. **Prometheus + Grafana** — scrape live monitoring signals from the FastAPI inference
   service and visualise them on a dashboard.
2. **Kubernetes** — run the inference container on a Kubernetes cluster instead of (or
   alongside) ECS Fargate.

Both layers work with the same Docker image and runtime contract that already exist in the
repository. No source-code changes are required for the basic setup; the Prometheus
integration requires adding one lightweight dependency.

**Thesis reference:** The 3-layer monitoring design (confidence, temporal, drift) is defined
in Chapter 6. The runtime contract and Docker image structure are in Chapters 3 and 5.

---

## Part 1 — Prometheus Integration

### What signals to expose

The `_run_monitoring()` function in `src/api/app.py` already computes these signals on
every inference request:

| Signal | Source in code | Prometheus metric name |
|---|---|---|
| Mean confidence | `layer1_confidence.mean_confidence` | `har_mean_confidence` |
| Confidence status | `layer1_confidence.status` | `har_confidence_healthy` (0/1) |
| Temporal consistency | `layer2_temporal.consistency_ratio` | `har_temporal_consistency` |
| Max drift z-score | `layer3_drift.max_drift` | `har_drift_zscore_max` |
| Drift status | `layer3_drift.status` | `har_drift_healthy` (0/1) |
| Inference requests | every `/upload/*` call | `har_inference_requests_total` |
| Accuracy (labeled only) | `evaluation.accuracy` | `har_labeled_accuracy` |

### Step 1.1 — Add prometheus-fastapi-instrumentator

```bash
pip install prometheus-fastapi-instrumentator
```

Add it to `config/requirements.txt`:

```
prometheus-fastapi-instrumentator>=6.1.0
```

### Step 1.2 — Wire the /metrics endpoint into app.py

Add the following block near the top of `src/api/app.py`, after the existing imports:

```python
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge, Counter

# -- Custom HAR monitoring gauges --
har_mean_confidence   = Gauge("har_mean_confidence",    "Mean softmax confidence for the current batch")
har_confidence_ok     = Gauge("har_confidence_healthy", "1 = HEALTHY, 0 = WARNING (layer 1)")
har_temporal          = Gauge("har_temporal_consistency","Temporal consistency ratio (layer 2)")
har_drift_max         = Gauge("har_drift_zscore_max",   "Max channel drift z-score (layer 3)")
har_drift_ok          = Gauge("har_drift_healthy",      "1 = HEALTHY, 0 = WARNING (layer 3)")
har_labeled_accuracy  = Gauge("har_labeled_accuracy",   "Accuracy on labeled uploads")
har_requests          = Counter("har_inference_requests_total", "Total inference requests", ["mode"])
```

Then expose the default `/metrics` endpoint:

```python
# Place this after app = FastAPI(...) is defined
Instrumentator().instrument(app).expose(app)
```

Finally, after `_run_monitoring()` returns in each upload handler, update the gauges:

```python
mon = monitoring_result   # the dict returned by _run_monitoring()

l1 = mon.get("layer1_confidence", {})
l2 = mon.get("layer2_temporal", {})
l3 = mon.get("layer3_drift", {})

har_mean_confidence.set(l1.get("mean_confidence", 0.0))
har_confidence_ok.set(1 if l1.get("status") == "HEALTHY" else 0)
har_temporal.set(l2.get("consistency_ratio", 0.0))
har_drift_max.set(l3.get("max_drift", 0.0))
har_drift_ok.set(1 if l3.get("status") in ("HEALTHY", "SKIPPED") else 0)
har_requests.labels(mode="labeled" if is_labeled else "unlabeled").inc()
```

After this change, `GET http://localhost:8000/metrics` returns all metrics in Prometheus
text format.

---

### Step 1.3 — Run Prometheus locally (Docker Compose)

Add a `prometheus/prometheus.yml` config file at the repository root:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: har_pipeline
    static_configs:
      - targets: ["har-api:8000"]   # service name in docker-compose
```

Extend `docker-compose.yml` with Prometheus and Grafana services:

```yaml
services:
  har-api:
    build:
      context: .
      dockerfile: docker/Dockerfile.inference
    ports:
      - "8000:8000"

  prometheus:
    image: prom/prometheus:v2.51.0
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"
    depends_on:
      - har-api

  grafana:
    image: grafana/grafana:10.4.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  grafana-data:
```

Start everything:

```bash
docker compose up --build
```

- FastAPI: `http://localhost:8000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`  (login: admin / admin)

---

### Step 1.4 — Configure Grafana data source

1. Open Grafana → **Connections → Data sources → Add data source**.
2. Choose **Prometheus**.
3. Set URL to `http://prometheus:9090` (Docker network name).
4. Click **Save & test** — you should see "Data source is working".

---

### Step 1.5 — Build the HAR monitoring dashboard

Create a new dashboard and add the following panels:

#### Panel: Mean Confidence over time

```promql
har_mean_confidence
```

Use a **Time series** panel. Add a threshold line at `0.70` (the `confidence_warn_threshold`
from `config/mlflow_config.yaml`) to visualise when Layer 1 trips.

#### Panel: Drift z-score over time

```promql
har_drift_zscore_max
```

Add a threshold line at `1.8` (the `drift_zscore_threshold`). Colour the region above the
line red.

#### Panel: Temporal consistency

```promql
har_temporal_consistency
```

Values below ~0.5 indicate the model is producing inconsistent activity transitions within
a session.

#### Panel: Confidence health rate (%)

```promql
100 * avg_over_time(har_confidence_healthy[5m])
```

Shows what fraction of recent uploads were HEALTHY over a 5-minute rolling window.

#### Panel: Request rate

```promql
rate(har_inference_requests_total[1m])
```

Break out by `mode` label to compare labeled vs. unlabeled upload volume.

#### Panel: Labeled accuracy (when labels are present)

```promql
har_labeled_accuracy
```

Only populated on labeled uploads. Useful for sanity-checking accuracy against the
deployed model's known LOUO baseline (~44 %).

---

## Part 2 — Kubernetes Deployment

Kubernetes replaces ECS Fargate as the container orchestrator. The Docker image and runtime
contract layout are identical. Only the infrastructure manifests change.

### Prerequisites

- A running Kubernetes cluster (e.g. AWS EKS, GKE, or local `minikube` / `kind`).
- `kubectl` configured and pointing at your cluster (`kubectl cluster-info`).
- The inference image already pushed to ECR (or any registry your cluster can pull from) —
  see Step 1 of the AWS Deployment Guide.
- `helm` installed if you want to deploy Prometheus and Grafana via the community chart.

---

### Step 2.1 — Create the inference Deployment and Service

Save the following as `k8s/inference-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: har-inference
  labels:
    app: har-inference
spec:
  replicas: 1
  selector:
    matchLabels:
      app: har-inference
  template:
    metadata:
      labels:
        app: har-inference
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port:   "8000"
        prometheus.io/path:   "/metrics"
    spec:
      serviceAccountName: har-inference-sa   # see Step 2.2 for IAM binding
      initContainers:
        - name: pull-contract
          image: amazon/aws-cli:2.15.0
          command:
            - aws
            - s3
            - cp
            - s3://your-bucket-name/runtime-contract/model_d1_final_20260528/
            - /app/contract/
            - --recursive
          volumeMounts:
            - name: contract-vol
              mountPath: /app/contract
      containers:
        - name: har-api
          image: <account-id>.dkr.ecr.eu-central-1.amazonaws.com/har-pipeline:latest
          ports:
            - containerPort: 8000
          env:
            - name: CONTRACT_DIR
              value: /app/contract
            - name: MODEL_PATH
              value: /app/contract/model_d1_final_20260528.keras
            - name: SCALER_PATH
              value: /app/contract/garmin_train_scaler.json
            - name: LABEL_ORDER
              value: /app/contract/label_order.json
            - name: BASELINE_PATH
              value: /app/contract/garmin_train_scaled_baseline.json
          volumeMounts:
            - name: contract-vol
              mountPath: /app/contract
          resources:
            requests:
              cpu: "500m"
              memory: "1.5Gi"
            limits:
              cpu: "1"
              memory: "2Gi"
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
      volumes:
        - name: contract-vol
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: har-inference-svc
spec:
  selector:
    app: har-inference
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
```

The `initContainer` downloads the runtime contract from S3 into a shared `emptyDir` volume
before the main container starts — the same pattern as the ECS startup script.

Apply it:

```bash
kubectl apply -f k8s/inference-deployment.yaml
```

---

### Step 2.2 — IAM permissions for the Pod (EKS IRSA)

On EKS, pods authenticate to AWS via IAM Roles for Service Accounts (IRSA) — no
credentials stored in the cluster.

```bash
# Create the service account and bind it to the S3 read role created in the AWS guide
eksctl create iamserviceaccount \
  --cluster=<your-cluster-name> \
  --namespace=default \
  --name=har-inference-sa \
  --attach-policy-arn=arn:aws:iam::<account-id>:policy/har-s3-read-policy \
  --approve
```

The `serviceAccountName: har-inference-sa` in the Deployment manifest above references
this account.

---

### Step 2.3 — Expose the service via an Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: har-ingress
  annotations:
    kubernetes.io/ingress.class: "alb"           # AWS Load Balancer Controller
    alb.ingress.kubernetes.io/scheme: "internet-facing"
    alb.ingress.kubernetes.io/target-type: "ip"
spec:
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: har-inference-svc
                port:
                  number: 80
```

```bash
kubectl apply -f k8s/ingress.yaml
kubectl get ingress har-ingress   # shows the ALB DNS name after ~2 minutes
```

---

### Step 2.4 — Deploy Prometheus and Grafana with Helm

The [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
chart installs Prometheus, Grafana, and the Prometheus Operator in one command.

```bash
# Add the community Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install the stack into a dedicated namespace
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=your-grafana-password
```

Check that everything came up:

```bash
kubectl get pods -n monitoring
```

---

### Step 2.5 — Add a ServiceMonitor for the inference pod

The `prometheus.io/scrape` annotations on the Deployment (Step 2.1) are picked up
automatically by the Prometheus Operator. Alternatively, create an explicit
`ServiceMonitor` for more control:

```yaml
# k8s/servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: har-inference-monitor
  namespace: monitoring
  labels:
    release: monitoring   # must match the Helm release label
spec:
  selector:
    matchLabels:
      app: har-inference
  namespaceSelector:
    matchNames:
      - default
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

```bash
kubectl apply -f k8s/servicemonitor.yaml
```

Prometheus will now scrape `http://har-inference-svc.default.svc:80/metrics` every 15
seconds.

---

### Step 2.6 — Access Grafana on Kubernetes

```bash
# Forward Grafana to your local machine
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring
```

Open `http://localhost:3000`, log in with `admin` / `your-grafana-password`, and follow
the same dashboard-building steps from Part 1, Sections 1.4 and 1.5. The Prometheus data
source is pre-configured by the Helm chart at `http://prometheus-operated:9090`.

---

### Step 2.7 — Horizontal Pod Autoscaling (optional)

If request volume grows, add a HorizontalPodAutoscaler:

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: har-inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: har-inference
  minReplicas: 1
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

```bash
kubectl apply -f k8s/hpa.yaml
```

The cluster will spin up additional inference pods automatically when CPU load exceeds 70 %.

---

## Summary: What Changes vs Local

| | Local / Docker Compose | ECS Fargate (AWS guide) | Kubernetes |
|---|---|---|---|
| Container runtime | Docker Engine | AWS Fargate | kubelet on cluster nodes |
| Orchestrator | docker-compose | ECS Service | Deployment + HPA |
| Public entry point | localhost:8000 | ALB DNS name | Ingress ALB DNS name |
| Runtime contract source | local folder | S3 (startup script) | S3 (initContainer) |
| IAM auth | env credentials | ECS task role | IRSA service account |
| Prometheus | docker-compose service | EC2/ECS sidecar | Helm kube-prometheus-stack |
| Grafana | docker-compose service | EC2/ECS sidecar | Helm kube-prometheus-stack |

Everything that stays the same: the Docker image, the runtime contract folder structure,
the FastAPI serving code, the 3-layer monitoring logic, and the `/metrics` endpoint.
Kubernetes and Prometheus only change where the container runs and how its signals are
collected — the pipeline itself is unchanged.
