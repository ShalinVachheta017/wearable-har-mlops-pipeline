# AWS Deployment Guide — HAR MLOps Pipeline

This guide explains how to deploy the thesis inference pipeline to AWS using the existing
Docker inference image and runtime contract. No code changes are needed. Only infrastructure
wiring changes between local and cloud execution.

**Thesis reference:** The offline-first architecture, runtime contract design, and Docker
image structure are defined in Chapter 3 and Chapter 5 of the thesis report.

---

## What Already Exists in This Repository

| Asset | Local path | What it is |
|---|---|---|
| Inference Docker image | `docker/Dockerfile.inference` | Lean serving image — FastAPI + runtime dependencies only |
| Training Docker image | `docker/Dockerfile.training` | Full training stack + Stage 1–7 pipeline entry point |
| Compose config | `docker-compose.yml` | Wires both images for local orchestration |
| Runtime contract | `models/runtime_contract/model_d1_final_20260528/` | Model, scaler, label order, baseline, integrity manifest |
| FastAPI app | `src/api/app.py` | Serving entry point — reads contract via environment variables |

All of the above travel to AWS unchanged. The cloud layer only changes where things run,
not what they do.

---

## Overview of the AWS Stack

```
User uploads CSV
        |
Application Load Balancer  (public HTTPS entry point)
        |
ECS Task  (your Docker inference image pulled from ECR)
        |
FastAPI app  (loads runtime contract artifacts from S3 at startup)
        |
Stages 1 to 7 run exactly as in local thesis execution
        |
Returns: monitoring signals + governance decision + predictions
```

---

## Step 1 — Push the Inference Image to ECR

ECR (Elastic Container Registry) is AWS's private Docker image store.

```bash
# 1. Create a repository in ECR (one time only)
aws ecr create-repository --repository-name har-pipeline --region eu-central-1

# 2. Authenticate Docker to your AWS account
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS \
  --password-stdin <account-id>.dkr.ecr.eu-central-1.amazonaws.com

# 3. Build the inference image from the repo root
docker build -f docker/Dockerfile.inference -t har-pipeline:latest .

# 4. Tag it for ECR
docker tag har-pipeline:latest \
  <account-id>.dkr.ecr.eu-central-1.amazonaws.com/har-pipeline:latest

# 5. Push
docker push \
  <account-id>.dkr.ecr.eu-central-1.amazonaws.com/har-pipeline:latest
```

Replace `<account-id>` with your 12-digit AWS account ID and `eu-central-1` with your
chosen region.

---

## Step 2 — Upload the Runtime Contract to S3

S3 replaces DVC remote storage in the cloud deployment. The runtime contract folder is
uploaded as-is. The folder structure must stay intact because FastAPI resolves all artifact
paths relative to it.

**What to upload:**

```
s3://your-bucket-name/runtime-contract/model_d1_final_20260528/
    ├── model_d1_final_20260528.keras     (frozen model)
    ├── garmin_train_scaler.json          (train-only scaler)
    ├── label_order.json                  (fixed 11-class label mapping)
    ├── garmin_train_scaled_baseline.json (monitoring baseline)
    ├── model_contract.json               (schema, units, windowing metadata)
    └── artifact_md5.json                 (integrity hashes)
```

**Upload command:**

```bash
aws s3 cp models/runtime_contract/model_d1_final_20260528/ \
  s3://your-bucket-name/runtime-contract/model_d1_final_20260528/ \
  --recursive
```

**What does NOT go to S3:**
- Raw training data or session CSV files
- Jupyter notebooks
- Source code — that is already baked into the Docker image

---

## Step 3 — Create an IAM Role for the ECS Task

The running container needs permission to read from S3. This is done through an IAM role,
not hardcoded credentials.

Create a role named `har-ecs-task-role` with the following inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name",
        "arn:aws:s3:::your-bucket-name/*"
      ]
    }
  ]
}
```

Attach the trust relationship for ECS tasks:

```json
{
  "Principal": { "Service": "ecs-tasks.amazonaws.com" },
  "Action": "sts:AssumeRole"
}
```

---

## Step 4 — Create the ECS Task Definition

The Task Definition is the blueprint for your container. Key settings:

| Setting | Value |
|---|---|
| Image URI | `<account-id>.dkr.ecr.eu-central-1.amazonaws.com/har-pipeline:latest` |
| CPU | 1 vCPU (minimum) |
| Memory | 2 GB (model inference requires at least 1.5 GB) |
| Task role | `har-ecs-task-role` (created in Step 3) |
| Port | 8000 (FastAPI default) |

**Environment variables** — these tell FastAPI where to find the runtime contract inside
the container after it downloads from S3:

```
CONTRACT_DIR   = /app/contract
MODEL_PATH     = /app/contract/model_d1_final_20260528.keras
SCALER_PATH    = /app/contract/garmin_train_scaler.json
LABEL_ORDER    = /app/contract/label_order.json
BASELINE_PATH  = /app/contract/garmin_train_scaled_baseline.json
```

**Container startup script** (add to the inference Dockerfile as an entrypoint or add to
the task command):

```bash
#!/bin/bash
# Download runtime contract from S3 at container startup
aws s3 cp s3://your-bucket-name/runtime-contract/model_d1_final_20260528/ \
  /app/contract/ --recursive

# Start FastAPI
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

The existing `src/api/app.py` already reads paths from environment variables — no code
change is needed.

---

## Step 5 — Create an ECS Cluster and Service

```bash
# Create cluster
aws ecs create-cluster --cluster-name har-pipeline-cluster

# Create service (runs the task definition continuously)
aws ecs create-service \
  --cluster har-pipeline-cluster \
  --service-name har-inference-service \
  --task-definition har-pipeline-task:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
      subnets=[subnet-xxxxx],
      securityGroups=[sg-xxxxx],
      assignPublicIp=ENABLED
  }"
```

Use Fargate so AWS manages the underlying server — no EC2 instance to maintain.

---

## Step 6 — Put an Application Load Balancer in Front

The ALB gives you a stable public HTTPS URL and routes traffic to the ECS container.

```
POST https://your-alb-url.eu-central-1.elb.amazonaws.com/upload/labeled
POST https://your-alb-url.eu-central-1.elb.amazonaws.com/upload/unlabeled
```

These are the same endpoints already defined in `src/api/app.py`. The ALB simply forwards
the request to port 8000 of the running ECS task.

---

## What Changes vs Local Execution

| | Local thesis | AWS |
|---|---|---|
| Docker image source | `docker build` locally | Pulled from ECR |
| Runtime contract location | `models/runtime_contract/` folder | S3 bucket, downloaded at container startup |
| FastAPI runs on | `localhost:8000` | ECS Fargate container behind ALB |
| Entry point URL | `http://localhost:8000` | `https://your-alb-url.amazonaws.com` |
| Artifact versioning | DVC local remote | S3 (same content, different location) |
| Code changes needed | None | None |

---

## What Stays Completely the Same

- All 7 pipeline stages (ingestion through trigger decision)
- Runtime contract structure — model, scaler, label order, baseline travel together
- FastAPI serving code in `src/api/app.py`
- Governance logic, monitoring signals, trigger policy
- The same-folder invariant — the contract folder is downloaded as one unit from S3

The runtime contract design from Chapter 3 of the thesis is exactly what makes this
possible: because the model, scaler, and baseline are always promoted and deployed together
as one folder, moving from local execution to AWS requires no restructuring of the artifact
layout.

---

## Future Extensions (mentioned in thesis Chapter 8)

- **Auto-scaling:** ECS can scale the number of running containers based on request volume
- **Model update without image rebuild:** Upload a new runtime contract folder to S3 and
  restart the ECS task — the container pulls the new contract at startup
- **Azure equivalent:** Azure Container Apps + Azure Blob Storage follow the same pattern;
  only the CLI commands and service names change
- **MLflow on AWS:** Point the MLflow tracking URI to an RDS database and S3 artifact store
  to move experiment tracking to the cloud alongside the serving layer
