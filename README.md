# arxiv-rag

> Semantic search and Q&A over 1,000+ arXiv ML papers — RAG pipeline with
> Airflow ingestion, MLflow tracking, automated evaluation, FastAPI, pgvector,
> Gemini API, and React.

![CI](https://github.com/your-username/arxiv-rag/actions/workflows/ci.yml/badge.svg)

---

## What it does

You type a question like *"How does self-attention work?"* and the system searches
over 1,000+ machine learning research papers it has already read and indexed. It
finds the most relevant passages, then uses Google's Gemini AI to write you a
focused answer — with citations back to the exact papers it used.

Behind the scenes, a scheduled pipeline runs every night to fetch new papers from
arXiv, read them, break them into pieces, convert each piece into a mathematical
fingerprint (an embedding), and store everything in a database that can be searched
by meaning rather than just keywords. Every search and every nightly run is tracked
so you can see how the system's accuracy changes over time.

---

## Architecture

```
                    ┌─────────────────────────────────────────────────────┐
                    │                  Docker Compose                     │
                    │                                                     │
  [Browser] ──────▶ │  ┌───────────┐   /api/*   ┌────────────────────┐  │
                    │  │  React    │ ──────────▶ │     FastAPI        │  │
                    │  │ :3000     │ ◀────────── │     :8000          │  │
                    │  └───────────┘             └──────┬──────┬──────┘  │
                    │                                   │      │          │
                    │              ┌────────────────────┘      │          │
                    │              ▼                           ▼          │
                    │  ┌──────────────────────┐   ┌─────────────────┐   │
                    │  │  PostgreSQL + pgvector│   │     MLflow      │   │
                    │  │  :5432               │   │     :5001       │   │
                    │  └──────────────────────┘   └─────────────────┘   │
                    │              ▲                                      │
                    │              │ store chunks + vectors               │
                    │  ┌───────────┴──────────┐                          │
                    │  │  Airflow  :8080       │  (runs nightly)          │
                    │  └──────────────────────┘                          │
                    └─────────────────────────────────────────────────────┘
                                   │                    │
                          embed /  │                    │ fetch papers
                          generate │                    ▼
                                   │           ┌─────────────────┐
                                   └─────────▶ │   Gemini API    │
                                               │   (Google)      │
                                               └─────────────────┘
                                                        +
                                               ┌─────────────────┐
                                               │   arXiv API     │
                                               │   (public)      │
                                               └─────────────────┘
```

**Ingestion flow** (Airflow, nightly):
`arXiv API → PDF download → text extraction → chunking → Gemini embedding → pgvector`

**Query flow** (user request):
`React → FastAPI → Gemini embedding → pgvector similarity search → Gemini generation → React`

---

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/your-username/arxiv-rag.git
cd arxiv-rag
cp .env.example .env          # then add your GEMINI_API_KEY

# 2. Start all services
docker-compose up --build

# 3. Trigger initial ingestion
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer attention mechanism", "max_papers": 20}'
```

Services once running:

| Service | URL |
|---|---|
| React UI | http://localhost:3000 |
| FastAPI docs | http://localhost:8000/docs |
| Airflow UI | http://localhost:8080 |
| MLflow UI | http://localhost:5001 |

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL 16 + pgvector |
| ORM | SQLAlchemy 2.0 async |
| LLM + Embeddings | Google Gemini (`gemini-2.0-flash`, `text-embedding-004`) |
| Pipeline | Apache Airflow 2.9 |
| Experiment tracking | MLflow 2.x |
| Frontend | React 18 + Vite |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Screenshots

*Coming in Phase 9 — after the full stack is running.*

---

## Project Structure

```
arxiv-rag/
├── backend/          # FastAPI app + all services
├── airflow/          # DAG for nightly ingestion
├── evaluation/       # Golden test set + evaluation scripts
├── frontend/         # React UI
├── docs/             # Project specs and teaching notes
└── docker-compose.yml
```

---

## Development

```bash
# Run backend tests (no API keys needed)
cd backend
pip install -e .[dev]
pytest tests/ -m "not integration"

# Lint
ruff check .
```
