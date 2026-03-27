# Docker — Explained in Very Simple English

> **Audience:** Someone who knows Python but is new to Docker.  
> **Goal:** Understand *what* each file does, *why* it exists, and *how* it fits into the thesis.

---

## What is Docker? (One Paragraph)

Imagine you have a Python script that works perfectly on your laptop. But when your examiner runs it on their machine, it breaks because they have a different Python version or different packages. **Docker solves this.** It wraps your code + Python + all packages + all settings inside a sealed box called a **container**. Anyone who runs that container gets the exact same environment. No "it works on my machine" problem.

---

## The Big Picture — How Our 3 Docker Files Work Together

```
docker-compose.yml          ← The MANAGER (starts everything, wires everything together)
    │
    ├── Dockerfile.inference  ← Recipe for the API container (serves predictions)
    └── Dockerfile.training   ← Recipe for the training container (trains the model)
```

- **Dockerfile** = a recipe to *build* an image (like a blueprint)
- **Image** = the result of building a Dockerfile (like a frozen snapshot)
- **Container** = a running image (like an app that is actually started)
- **docker-compose.yml** = starts and connects multiple containers at once

---

## Part 1 — General Dockerfile Structure (Pseudocode)

Think of a Dockerfile as a step-by-step cooking recipe:

```
STEP 1 — FROM      → Pick your starting ingredients (base image)
STEP 2 — LABEL     → Write your name on the box (metadata)
STEP 3 — ENV       → Set the kitchen temperature before cooking (environment variables)
STEP 4 — WORKDIR   → Go to the right room to cook (set working directory)
STEP 5 — RUN       → Install tools and equipment (install system packages)
STEP 6 — COPY      → Bring your ingredients into the kitchen (copy files)
STEP 7 — RUN       → Cook / prepare the ingredients (install Python packages)
STEP 8 — EXPOSE    → Open a window for people to receive food (open a port)
STEP 9 — HEALTHCHECK → Hire a taster to check if the food is ready (health check)
STEP 10 — CMD      → Serve the food / start the app (run command)
```

### Why this ORDER matters

Docker builds in layers. Each line = one layer.  
If you change line 8, Docker only rebuilds from line 8 onwards — it reuses the previous layers from cache.  
**That is why `COPY requirements.txt` and `RUN pip install` come BEFORE copying the rest of the code.**  
Your code changes every day, but your packages don't. So packages are cached and installation is fast.

```
COPY requirements.txt   ← rarely changes → stays cached → fast
RUN pip install         ← rarely changes → stays cached → fast
COPY src/               ← changes often  → rebuilds    → that's fine, it's just file copy
```

---

## Part 2 — Dockerfile.inference (Line by Line)

**File:** `docker/Dockerfile.inference`  
**Purpose:** Serve the trained HAR model as a web API so anyone can send sensor data and get a prediction back.  
**Role in Thesis:** This is the "production deployment" component. It proves the model is not just a script — it is a real deployable service. It demonstrates Stage 4 (Inference) and the FastAPI serving layer.

```dockerfile
FROM python:3.11-slim
```
> **Why?** Start with a lightweight Python 3.11 image. "slim" means no unnecessary tools installed — keeps the image small. 
> You do not want a 2 GB base image just to run a Python API.

---

```dockerfile
LABEL maintainer="thesis-student"
LABEL description="HAR Model Inference API"
LABEL version="1.0.0"
```
> **Why?** Labels are like sticky notes on the container. They tell people what this container is for.  
> Not required to run, but good practice and expected in professional MLOps work.

---

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MODEL_PATH=/app/models/pretrained/fine_tuned_model_1dcnnbilstm.keras
```
> **Why?** These are settings for Python and pip inside the container.  
> - `PYTHONDONTWRITEBYTECODE=1` → Do not create `.pyc` bytecode files inside the container (saves space).  
> - `PYTHONUNBUFFERED=1` → Print logs immediately, do not wait to buffer them (so you can see logs in real time).  
> - `PIP_NO_CACHE_DIR=1` → Do not keep pip download cache (saves space in the container image).  
> - `PIP_DISABLE_PIP_VERSION_CHECK=1` → Do not waste time checking if pip is outdated every install.  
> - `MODEL_PATH=...` → Tells the app where to find the trained model file.

---

```dockerfile
WORKDIR /app
```
> **Why?** Sets the working directory inside the container to `/app`.  
> All future commands (COPY, RUN, CMD) happen relative to this folder.  
> Think of it as `cd /app` inside the container.

---

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*
```
> **Why?** Install `curl` — a tiny tool used by the health check to ping the API and confirm it is alive.  
> `--no-install-recommends` keeps it minimal. `rm -rf /var/lib/apt/lists/*` deletes the package list after install to save space.  
> For inference, we only need `curl` — no compilers, no git, nothing heavy.

---

```dockerfile
COPY config/requirements.txt /app/requirements.txt
```
> **Why?** Copy ONLY the requirements file first (not the whole code yet).  
> This is the "layer caching trick" — if requirements.txt hasn't changed, Docker skips the next `pip install` step and uses the cached layer. Saves minutes of build time.

---

```dockerfile
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn tensorflow numpy pandas scipy pyyaml pydantic prometheus-client python-multipart
```
> **Why?** Install only what inference needs — not the full training stack.  
> No `mlflow`, no `dvc`, no `scikit-learn` training tools. Keeps the image lean.  
> `uvicorn` = ASGI server that runs the FastAPI app. `python-multipart` = needed to accept CSV file uploads via the API.

---

```dockerfile
COPY src/ /app/src/
COPY config/ /app/config/
COPY docker/api/ /app/docker_api/
```
> **Why?** Now copy the actual code. This is done AFTER pip install so that code changes do not invalidate the pip cache.  
> `src/` has the full pipeline logic. `config/` has YAML configs and thresholds. `docker_api/` is a legacy lightweight API kept only for debugging purposes.

---

```dockerfile
RUN mkdir -p /app/models /app/logs
```
> **Why?** Create empty folders inside the container. The model files and logs will be mounted from your machine at runtime via `volumes:` in docker-compose.yml. These folders just need to exist beforehand.

---

```dockerfile
ENV PYTHONPATH=/app:/app/src:$PYTHONPATH
```
> **Why?** Tell Python where to look for imports. Without this, `from src.api.app import ...` would fail with `ModuleNotFoundError`.  
> `/app` and `/app/src` are added to the import search path.

---

```dockerfile
EXPOSE 8000
```
> **Why?** Tell Docker "this container will listen on port 8000".  
> This does NOT actually open the port — it is just documentation. The port is opened in docker-compose.yml with `ports: "8000:8000"`.  
> Think of this as putting a label on a door saying "this is the front door".

---

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1
```
> **Why?** Every 30 seconds, Docker pings the `/api/health` endpoint.  
> If it fails 3 times in a row → Docker marks the container as "unhealthy" and can restart it.  
> This is how the system self-heals. In an MLOps context, this proves the API is always alive and being monitored.

---

```dockerfile
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```
> **Why?** This is the final command that runs when the container starts.  
> `uvicorn` = the web server. `src.api.app:app` = the FastAPI app object inside `src/api/app.py`.  
> `--host 0.0.0.0` = accept connections from outside the container (not just localhost).  
> `--port 8000` = listen on port 8000.

---

## Part 3 — Dockerfile.training (Line by Line)

**File:** `docker/Dockerfile.training`  
**Purpose:** Provide a fully reproducible environment to train the 1D-CNN-BiLSTM HAR model.  
**Role in Thesis:** This is the "reproducibility" component. It proves that anyone can re-train the exact same model from scratch with the same data. It is used by the `training` and `preprocessing` services in docker-compose and by the CI/CD pipeline.

```dockerfile
FROM python:3.11-slim
```
> Same as inference — start light.

---

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```
> Same settings as inference. No `MODEL_PATH` here because training does not load a pre-existing model — it creates one.

---

```dockerfile
WORKDIR /app
```
> Same — all work happens in `/app`.

---

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*
```
> **Why more packages than inference?**  
> Training needs `build-essential` (C/C++ compiler) because some Python packages (like certain scipy/numpy ops) need to compile C extensions during install.  
> `git` is needed because DVC uses git under the hood to track data versions.  
> Inference does not need any of this — it just loads a ready model and runs it.

---

```dockerfile
COPY config/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install mlflow dvc tensorflow keras scikit-learn pandas numpy scipy pyyaml
```
> **Why install from requirements.txt AND individual packages?**  
> `requirements.txt` has the full pinned lock — installs everything. The extra `pip install` line adds specific training tools as an explicit safety net in case they are not pinned.  
> Training container needs: `mlflow` (experiment tracking), `dvc` (data version control), `tensorflow/keras` (model), `scikit-learn` (metrics).

---

```dockerfile
COPY src/ /app/src/
COPY config/ /app/config/
RUN mkdir -p /app/data /app/models /app/mlruns /app/logs
ENV PYTHONPATH=/app/src:$PYTHONPATH
```
> Same logic — copy code after packages, create folders, set Python path.

---

```dockerfile
CMD ["python", "-c", "print('HAR Training Container Ready. Use: python src/train.py')"]
```
> **Why a print statement, not `python src/train.py`?**  
> Training is NOT meant to run automatically when the container starts. You trigger it manually with a specific command.  
> The default CMD is just a helpful message. In docker-compose.yml, the `profiles: [training]` setting means this container does not even start unless you explicitly ask for it.

---

## Part 4 — docker-compose.yml (Service by Service)

**File:** `docker-compose.yml` (at the root of the project)  
**Purpose:** Start ALL containers together with one command, wire them together so they can talk to each other, and manage ports, volumes, and dependencies.  
**Role in Thesis:** This is the "full system deployment" component. Running `docker-compose up -d` boots the entire monitoring stack — API + MLflow + Prometheus + Grafana + Alertmanager — in minutes.

### The Core Concept: Services, Networks, Volumes

```
Services   = individual containers (each does one job)
Networks   = a private Wi-Fi for containers to talk to each other
Volumes    = shared folders between your machine and the container
Ports      = doors in the container wall that let the outside world in
```

---

### Service 1 — `mlflow`

```yaml
mlflow:
  image: python:3.11-slim
  ports:
    - "5000:5000"
  volumes:
    - ./mlruns:/mlflow/mlruns
  command: mlflow server --host 0.0.0.0 --port 5000
```

> **What it does:** Runs the MLflow tracking server. Every time you train the model, the training metrics (accuracy, loss, parameters) get logged here.  
> **Port 5000:** Opens `http://localhost:5000` — you can go there in your browser to see all experiment runs.  
> **Volume `./mlruns:/mlflow/mlruns`:** The experiment data is stored in `mlruns/` on your machine (not inside the container). This means if the container is deleted, the data survives.  
> **Role in thesis:** Proves experiment tracking is automated and reproducible — a core MLOps requirement.

---

### Service 2 — `inference`

```yaml
inference:
  build:
    context: .
    dockerfile: docker/Dockerfile.inference
  ports:
    - "8000:8000"
  volumes:
    - ./models:/app/models:ro
  depends_on:
    - mlflow
```

> **What it does:** Builds and runs the FastAPI inference API using `Dockerfile.inference`.  
> **Port 8000:** Opens `http://localhost:8000` — you can POST sensor data here and get a prediction back.  
> **Volume `:ro`** means read-only — the container can read the model file but cannot change it. Safety measure.  
> **`depends_on: mlflow`** — Docker waits for MLflow to start first before starting the inference API.  
> **Role in thesis:** The deployed model. Examiners can hit this endpoint to see the system working live.

---

### Service 3 — `training`

```yaml
training:
  build:
    context: .
    dockerfile: docker/Dockerfile.training
  volumes:
    - ./data:/app/data
    - ./models:/app/models
    - ./mlruns:/app/mlruns
  profiles:
    - training
```

> **What it does:** Builds the training container using `Dockerfile.training`. Mounts your real data and models folders.  
> **`profiles: [training]`** = This container does NOT start with `docker-compose up`. You must explicitly run `docker-compose --profile training up training`. This prevents accidentally re-training every time.  
> **Volumes for data AND mlruns:** Training reads data, writes models, and logs metrics to MLflow — all on your real machine folders.  
> **Role in thesis:** Reproducible training. Same container = same training environment = same results.

---

### Service 4 — `preprocessing`

```yaml
preprocessing:
  build:
    context: .
    dockerfile: docker/Dockerfile.training
  command: python src/sensor_data_pipeline.py
  profiles:
    - preprocessing
```

> **What it does:** Reuses the training image but runs the preprocessing script instead.  
> **Same Dockerfile, different command** — efficient, no need for a 4th Dockerfile.  
> **`profiles: [preprocessing]`** = on-demand only, same as training.  
> **Role in thesis:** Shows preprocessing is also reproducible and isolated.

---

### Service 5 — `prometheus`

```yaml
prometheus:
  image: prom/prometheus:v2.50.1
  ports:
    - "9090:9090"
  volumes:
    - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - ./config/alerts:/etc/prometheus/rules:ro
```

> **What it does:** Prometheus is a time-series database that constantly scrapes (pulls) metrics from the inference API.  
> Every 30 seconds it asks the inference API: "How many predictions made? What is the confidence score distribution? Any drift?"  
> **Port 9090:** You can query metrics at `http://localhost:9090`.  
> **Volume with alert rules:** Loads our alert rules from `config/alerts/har_alerts.yml` — if confidence drops below threshold, it fires an alert.  
> **Role in thesis:** This is the 3-layer monitoring system (confidence + temporal + drift). Without Prometheus, monitoring is just print statements.

---

### Service 6 — `alertmanager`

```yaml
alertmanager:
  image: prom/alertmanager:v0.27.0
  ports:
    - "9093:9093"
  volumes:
    - ./config/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
```

> **What it does:** Receives alerts FROM Prometheus and routes them to email/Slack/webhook.  
> Prometheus detects the problem → sends alert to Alertmanager → Alertmanager decides who to notify.  
> **Port 9093:** You can see active alerts at `http://localhost:9093`.  
> **Role in thesis:** Completes the monitoring loop. Alerts are evidence that the system responds to model degradation automatically.

---

### Service 7 — `grafana`

```yaml
grafana:
  image: grafana/grafana:10.3.1
  ports:
    - "3000:3000"
  volumes:
    - grafana_data:/var/lib/grafana
    - ./config/grafana:/etc/grafana/provisioning:ro
  environment:
    - GF_SECURITY_ADMIN_USER=admin
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
```

> **What it does:** Grafana reads from Prometheus and displays beautiful dashboards.  
> **Port 3000:** Open `http://localhost:3000` → login with `admin/admin` → see live model health charts.  
> **`${GRAFANA_PASSWORD:-admin}`** = use the `GRAFANA_PASSWORD` environment variable if set, otherwise default to `admin`.  
> **`grafana_data` volume** = Grafana stores dashboards in a named Docker volume (persists even if container restarts).  
> **Role in thesis:** Visual proof of real-time monitoring. A screenshot or live demo for the examiner.

---

### Networks — How Containers Talk to Each Other

```yaml
networks:
  har-network:
    driver: bridge
```

> **Why?** All 7 services are on the same private network called `har-network`.  
> This means the inference container can talk to MLflow using `http://mlflow:5000` (the service name, not `localhost`).  
> Without a shared network, containers cannot see each other at all.  
> `bridge` = the standard Docker network mode — creates a virtual network switch.

---

### Volumes — How Data Persists

```yaml
volumes:
  mlflow-data:
  prometheus_data:
  grafana_data:
  alertmanager_data:
```

> **Why named volumes?** Some data (Grafana dashboards, Prometheus time-series data) should survive container restarts.  
> Named volumes are managed by Docker and stored somewhere safe on your machine.  
> In contrast, `- ./mlruns:/app/mlruns` (bind mounts) map directly to a folder on your machine so you can open/edit files directly.

---

## Part 5 — Port Reference (All at a Glance)

| Port | Container | What You See There |
|------|-----------|-------------------|
| `8000` | inference (FastAPI) | POST sensor CSV → get HAR prediction |
| `5000` | MLflow | All experiment runs, metrics, model versions |
| `9090` | Prometheus | Raw metrics, query time-series data |
| `9093` | Alertmanager | Active alerts, silences |
| `3000` | Grafana | Live monitoring dashboards |

**Format: `HOST:CONTAINER`**  
`"8000:8000"` means: my machine's port 8000 → container's port 8000.  
`"5000:5000"` means: my machine's port 5000 → container's port 5000.  
You could change the left number to avoid conflicts: `"15000:5000"` → MLflow at `localhost:15000`.

---

## Part 6 — How to Run Everything

```bash
# Start the always-on services (MLflow + API + Prometheus + Alertmanager + Grafana)
docker-compose up -d

# Watch live logs
docker-compose logs -f

# Run training (on demand)
docker-compose --profile training run training python src/train.py

# Run preprocessing (on demand)
docker-compose --profile preprocessing run preprocessing

# Stop everything
docker-compose down

# Stop and delete all data volumes (nuclear option)
docker-compose down -v
```

---

## Part 7 — Role in the Master's Thesis

| Docker File | Chapter | What It Proves |
|-------------|---------|----------------|
| `Dockerfile.inference` | Chapter 4 (Implementation) | Model is deployed as a real API, not just a script |
| `Dockerfile.training` | Chapter 4 (Implementation) | Training is reproducible — same environment = same results |
| `docker-compose.yml` | Chapter 4 + Chapter 5 | Full MLOps stack deployed in one command |
| Prometheus + Grafana in compose | Chapter 4 (Monitoring) | 3-layer monitoring is live and automated |
| Alertmanager in compose | Chapter 4 (Monitoring) | Alerts fire automatically when model degrades |
| `depends_on` + `networks` in compose | Chapter 4 | Services are orchestrated and connected properly |
| Health checks in compose | Chapter 4 | System is self-healing and production-grade |

---

## Summary — One Sentence Per File

| File | One Sentence |
|------|-------------|
| `Dockerfile.inference` | Builds a sealed container that runs the FastAPI prediction API on port 8000. |
| `Dockerfile.training` | Builds a sealed container with all tools needed to train the model reproducibly. |
| `docker-compose.yml` | Starts all 7 services at once, connects them on a private network, and maps ports and folders. |
