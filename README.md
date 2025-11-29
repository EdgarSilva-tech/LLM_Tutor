📘 LLM Tutor — Multi-Agent AI Teaching System

LLM Tutor is a modular, production-grade AI system designed to teach Calculus using Retrieval-Augmented Generation (RAG), automatic quiz generation, and LLM-based evaluation of student answers.

It is built as a multi-service architecture with strong emphasis on quality, evaluation, and observability.


---

🚀 Features

1. RAG-powered Calculus Q&A Service

Retrieves curated AP Calculus FRQ explanations

Normalizes user questions

Generates grounded solutions with citations

Uses deterministic preprocessing + chunking + embeddings


2. Quiz Generation Service

Generates quizzes from structured specifications:

Topic

Difficulty

Style (computational / conceptual / mixed)

Number of questions


Produces valid JSON with:

Stem

Options

Correct answer

Metadata and tags



3. Grading & Evaluation Service

Uses LLM to:

Grade student answers

Provide feedback and improvement steps

Detect misconceptions

Align feedback with rubrics


Supports both free-form answers and short-answer formats


4. Auth Service

Full JWT authentication

Protects all agents

Centralized user identity layer


5. Opik Integration

Full trace logging

Dataset-based evaluation

Custom metrics

Quality gates for development and production:

Correctness

Faithfulness

Schema compliance

LO alignment

Difficulty/style adherence

Hallucination detection




---

🏗️ Architecture

LLM_Tutor
├── services
│   ├── auth_service
│   ├── rag_service
│   ├── quiz_gen_service
│   └── evaluation_service
├── eval/
│   ├── datasets/
│   ├── evaluators/
│   ├── runners/
│   ├── shared/
│   └── reports/
└── docker-compose.yml

Each service is a FastAPI microservice with its own dependencies, prompts, and evaluation hooks.


---

🔧 Tech Stack

FastAPI (microservices)

Python / Async

OpenAI API

Opik for evaluation & observability

Docker

Pydantic

Vector search (custom or FAISS/Pinecone)

JWT Authentication



---

📊 Evaluation

LLM Tutor includes a complete evaluation pipeline based on Opik:

Included datasets

Calculus QA dataset

Quiz specifications dataset

Grader/Feedback dataset


Metrics

Correctness

Faithfulness

Schema compliance

Key validity

LO alignment

Difficulty/style adherence

Hallucination detection

Feedback quality

Diversity of questions


Goal

Guarantee consistent quality in:

RAG answers

Quiz generation

Feedback and grading



---

🧪 Running the Services

docker-compose up --build

or run individually:

cd services/rag_service
uvicorn main:app --reload --host 0.0.0.0 --port 8001


---

🧭 Roadmap

[ ] CI/CD pipeline running Opik eval splits

[ ] Student proficiency modeling

[ ] Semantic distractor generation

[ ] Multi-modal support (OCR equations)

[ ] Fine-tuned instructor model for more stable grading

[ ] Web UI for students



---

📄 License

MIT


---

✨ Author

Edgar Silva
