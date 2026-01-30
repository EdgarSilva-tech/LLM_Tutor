📘 LLM Tutor — Multi-Agent AI Teaching System

LLM Tutor is a modular, production-grade AI system for Calculus tutoring that combines Retrieval-Augmented Generation (RAG), automatic quiz generation, and LLM-based evaluation. It is built as a set of focused FastAPI microservices with strong emphasis on reliability, observability, and testability.

---

## Table of Contents
- Overview
- Architecture
- Services and Endpoints
- Messaging Topology
- Data Stores
- Ingress / Frontend
- Local Development
- Kubernetes (Minikube)
- End-to-End Tests
- Configuration (Environment Variables)
- Security Notes
- License

---

## Overview
- RAG service answers user questions with grounded context from a vectorized Postgres (pgvector).
- Quiz service generates quizzes synchronously or enqueues async jobs; also submits answers for evaluation.
- Evaluation service grades answers (async worker) and exposes feedback/status.
- Auth service provides JWT authentication; all business endpoints are protected.
- NGINX Ingress routes paths (`/auth`, `/quiz`, `/evaluation`, `/rag`) to the correct backends and serves the SPA at `/`.

---

## Architecture

![System Architecture](assets/Architecture.png)

Key flows:
- User hits Ingress; requests to `/auth|/quiz|/evaluation|/rag` are routed to the corresponding service; `/` serves the React/Vite frontend via a tiny nginx.
- Quiz generation can be synchronous (`/quiz/generate-quiz`, `/quiz/create-quiz`) or asynchronous (`/quiz/generate-async` → RabbitMQ → worker).
- Answer evaluation is async (`/quiz/submit-answers` → RabbitMQ → evaluation consumer). Results persist to Postgres and are cached in Redis; clients poll job endpoints.
- RAG service queries pgvector and caches embeddings/queries in Redis.
- NGINX annotations apply timeouts/body size and enable upstream retries for resilient rollouts.

---

## Services and Endpoints

All services are FastAPI apps. Endpoints below reflect external paths as seen via Ingress.

- Auth Service
  - POST `/auth/token` — OAuth2 password flow; returns JWT
  - POST `/auth/signup` — Create user
  - GET  `/auth/users/me` — Current user info (protected)

- Quiz Service
  - POST `/quiz/generate-quiz` — Generate and return questions (sync)
  - POST `/quiz/create-quiz` — Create quiz, store in Redis, return `quiz_id`
  - POST `/quiz/generate-async` — Queue async generation (202; Redis status)
  - GET  `/quiz/jobs/{id}` — Poll async job status (`queued/processing/done`)
  - POST `/quiz/submit-answers` — Enqueue evaluation (202)
  - GET  `/quiz/get-quizz-questions` — List cached quiz requests for user

- Evaluation Service
  - POST `/evaluation/eval-service` — Grade a set of QA pairs (sync)
  - POST `/evaluation/eval-service/evaluate_answer` — Grade a single QA pair (sync)
  - GET  `/evaluation/eval-service/get-feedback` — List saved feedbacks for user
  - GET  `/evaluation/eval-service/jobs/{id}` — Poll async evaluation result

- RAG Service
  - POST `/rag/question-answer` — Answer question using vector search context
  - POST `/rag/embed` — Generate embedding and cache
  - GET  `/rag/search` — Similarity search for text

Health endpoints are available on each service (e.g., `/health`), primarily for probes and diagnostics.

---

## Messaging Topology
- Exchange: `app.events`
- Queues:
  - `quiz.create.q` (DLQ: `quiz.create.dlq`) — quiz generation jobs
  - `quiz.generate.q` (DLQ: `quiz.generate.dlq`) — answer evaluation jobs
- Publishers:
  - Quiz Service publishes:
    - `quiz.create.request` (async generation)
    - `quiz.generate.request` (submit-answers)
- Consumers:
  - Quiz Generator Worker consumes `quiz.create.q` and writes questions to Redis (`Quiz user:quiz_id`)
  - Evaluation Consumer consumes `quiz.generate.q`, persists feedback to Postgres, and sets Redis key (`Eval user:job_id`)

---

## Data Stores
- Redis
  - Keys (per user): `Quiz user:quiz_id`, `Eval user:job_id`
  - Used for fast job status, quiz cache, and RAG embedding/query cache
- Postgres (single cluster) with multiple logical databases:
  - `Users` — Auth service (accounts, credentials metadata)
  - `Evaluation` — Evaluation service (grading/feedback records)
  - `Khan_Academy` — RAG service (lesson chunks + pgvector embeddings)
  - Note: database names are configured via envs/`k8s/*.yaml`; defaults above reflect the manifests in this repo.

---

## Ingress / Frontend
- Kubernetes NGINX Ingress routes:
  - `/auth(/|$)(.*)` → `auth-service:8001`
  - `/quiz(/|$)(.*)` → `quizz-service:8004`
  - `/evaluation(/|$)(.*)` → `evaluation-service:8003`
  - `/rag(/|$)(.*)` → `rag-service:8002`
- Typical annotations:
  - `nginx.ingress.kubernetes.io/rewrite-target: /$2`
  - `nginx.ingress.kubernetes.io/proxy-read-timeout: "120"`
  - `nginx.ingress.kubernetes.io/proxy-send-timeout: "120"`
  - `nginx.ingress.kubernetes.io/proxy-body-size: "10m"`
  - `nginx.ingress.kubernetes.io/proxy-next-upstream: "error timeout http_502 http_503 http_504"`
  - `nginx.ingress.kubernetes.io/proxy-next-upstream-tries: "3"`
  - `nginx.ingress.kubernetes.io/proxy-next-upstream-timeout: "5s"`
- Frontend SPA is served by a minimal `nginx:alpine` image (client-side routing supported via `try_files ... /index.html`).

---

## Local Development

You can run the full stack locally in two ways; choose one:

Option A — Docker Compose (quick local stack)

```bash
docker-compose up --build
```

Option B — Run services individually (example: RAG):

```bash
cd services/rag_service
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

Useful ports (default):
- Auth: 8001
- RAG: 8002
- Evaluation: 8003
- Quiz: 8004
- RabbitMQ: 5672 (AMQP), 15672 (management UI)
- Postgres: 5432 (compose maps 5433 → 5432 for local debug)

---

## Kubernetes (Minikube)

Why Minikube?
- This project is designed for Kubernetes first (Ingress routing, rolling updates, probes, HPA/KEDA-ready patterns).
- Minikube gives you a local single-node Kubernetes cluster to validate the exact wiring used in production: NGINX Ingress, path rewrites, upstream retries, and service-to-service networking.
- Unlike Docker Compose (which is fine for a quick local stack), Minikube lets you test the real entrypoint (Ingress), the exact URLs your frontend uses, and cluster behavior during rollouts.

Quick workflow:
1) Start cluster and enable Ingress:

```bash
minikube addons enable ingress
minikube service -n ingress-nginx ingress-nginx-controller --url
```

2) Export the base URL (PowerShell example):

```powershell
$env:E2E_BASE_URL = (minikube service -n ingress-nginx ingress-nginx-controller --url | Select-Object -First 1)
```

3) Apply manifests and wait for rollouts:

```bash
kubectl apply -f k8s/app-config.yaml
kubectl apply -f k8s/auth.yaml
kubectl apply -f k8s/rag.yaml
kubectl apply -f k8s/quizz.yaml
kubectl apply -f k8s/evaluation.yaml
kubectl apply -f k8s/ingress-apis.yaml
kubectl apply -f k8s/ingress-frontend.yaml
kubectl -n llm-tutor rollout status deploy/auth-service
kubectl -n llm-tutor rollout status deploy/rag-service
kubectl -n llm-tutor rollout status deploy/quizz-service
kubectl -n llm-tutor rollout status deploy/evaluation-service
```

4) Open the app via the Ingress URL:
- Use the URL from step 1 for both the frontend and API calls.
- Do not hit service ClusterIPs directly; the app expects path-based routing via Ingress.

Alternative (port-forward Ingress):

```bash
kubectl -n ingress-nginx port-forward svc/ingress-nginx-controller 8080:80
# Use http://127.0.0.1:8080
```

Always access the frontend and API via the Ingress URL so client-side routing and `/auth|/quiz|/rag|/evaluation` path routing work.

---

## End-to-End Tests

Set environment and run:

```bash
export E2E_BASE_URL="$(minikube service -n ingress-nginx ingress-nginx-controller --url | head -n1)"
pytest -m e2e -q
```

PowerShell:

```powershell
$env:E2E_BASE_URL = (minikube service -n ingress-nginx ingress-nginx-controller --url | Select-Object -First 1)
pytest -m e2e -q
```

Notes:
- E2E tests assume an Ingress URL and valid user credentials.
- Use the same BASE URL that your frontend uses, not service cluster IPs.

---

## Configuration (Environment Variables)

Common:
- `OPENAI_API_KEY` — access for embeddings and LLM calls
- `SECRET_KEY`, `ALGORITHM` — JWT signing and verification
- Redis:
  - `REDIS_ENDPOINT`, `REDIS_PASSWORD`, optionally `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_USERNAME`
- RabbitMQ:
  - `RABBITMQ_URL` (amqp://user:pass@rabbitmq:5672/%2F)
  - `RABBITMQ_EXCHANGE` (default `app.events`)
  - `RABBITMQ_ROUTING_KEY_GENERATE` (quiz.create.request)
  - `RABBITMQ_ROUTING_KEY` (quiz.generate.request)
- Postgres / RAG:
  - `PG_PASSWORD`, `DB_NAME`, `PORT` (default 5432)

Kubernetes specifics are provided via `k8s/*.yaml` (`ConfigMap` + `Secret`).

---

## Security Notes
- All business endpoints require JWT; only `/auth/signup`, `/auth/token`, and health checks are public.
- Keep secrets out of VCS. Use Kubernetes Secrets or GitHub Actions secrets for CI.
- NGINX Ingress applies upstream retry and timeouts to mitigate transient pod issues during rollouts.

---

## License
MIT

---

## Author
Edgar Silva
