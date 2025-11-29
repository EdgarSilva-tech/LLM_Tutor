📌 PROJECT: LLM Tutor — Multi-Agent AI Teaching System

⭐ Overview

LLM Tutor is a modular, production-style AI system built with multiple cooperating LLM-powered services:

RAG Service for answering calculus questions using retrieval over curated AP exam solutions.

Quiz Generation Service that creates pedagogically aligned quizzes based on learning objectives.

Evaluation / Grading Service that scores student responses with rubric-based LLM grading.

Auth Service with proper JWT authentication to manage secure access.


The system demonstrates end-to-end AI engineering skills including:
service-oriented architecture, RAG design, LLM prompting, curriculum-based quiz generation, automated evaluation with Opik, and scalable FastAPI deployments.


---

🏗️ Architecture Diagram

┌───────────────────────┐
                    │        Auth Service    │
                    │  JWT issuance & verify │
                    └───────────┬────────────┘
                                │
                ┌───────────────┼────────────────┐
                │                               │
       ┌────────▼─────────┐             ┌────────▼─────────┐
       │    RAG Service   │             │ Quiz Gen Service  │
       │ Retrieve + LLM   │             │   LO-based items  │
       │ Calculus corpus  │             │ JSON-structured   │
       └─────────┬────────┘             └─────────┬────────┘
                 │                                  │
                 ▼                                  ▼
       ┌──────────────────────┐          ┌──────────────────────┐
       │ Evaluation Service   │  <────── │  Student Responses   │
       │ LLM grading, rubric  │          │   Feedback & scores  │
       └──────────────────────┘          └──────────────────────┘

                   ┌───────────────┐
                   │     Opik      │
                   │ Traces, eval, │
                   │  metrics      │
                   └───────────────┘


---

🔍 Key Features

1. Retrieval-Augmented Generation (RAG)

Chunked AP Calculus FRQ solution dataset

Normalization & question parsing

Latency-controlled retrieval

LLM answer generation with source grounding


2. Quiz Generation

Topic, difficulty, style and LO structured inputs

Generates:

MCQ

Short-answer

Conceptual questions


Guaranteed JSON structure

Ensures variability & alignment with learning objectives


3. AI Grader

Takes question + rubric + student answer

Uses LLM to produce:

Score

Explanation

Feedback


Detects misconceptions and missing steps


4. Evaluation with Opik

Includes full evaluation pipeline using custom datasets:

Calculus QA dataset (derivatives, integrals, limits, series, FTC…)

Quiz specification dataset (LO + constraints → expected outcomes)

Grader/Feedback dataset

Runs metrics such as:

Correctness

Faithfulness

Key validity

Schema compliance

Difficulty/style adherence

LO alignment

Feedback helpfulness

Hallucination


Dataset-driven quality gates for CI



---

🔧 Tech Stack

FastAPI microservices

OpenAI LLM APIs

Opik for tracing, evaluation & metrics

Pydantic model validation

Docker containerization

Python (async / sync)

SQLite / local FS for light state management

GitHub Actions (planned) for CI-based evaluation

