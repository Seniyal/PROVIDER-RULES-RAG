# Provider Rules RAG System — Build Blueprint & Starter Code

This is a production‑oriented blueprint (with working starter code) to implement the system for surfacing provider rules during healthcare contact center calls.

## 0) High‑Level Architecture

```
SharePoint/Docs  --->  Ingestion Worker  --->  Embeddings  --->  Vector DB
 (Word, PDF)          (parse, extract)        (MiniLM)          (FAISS/Pinecone)
                            |                      |                    \
                            v                      v                     \
                        Rule Store  <--------  Metadata/Rules  <----------+
                        (Postgres)

EHR API  --->  Mapping/Resolver (name ↔ provider_id)  --->  Backend API (FastAPI)  --->  React Agent UI
                                                   (RAG: retrieve → synthesize → JSON)
```

## 1) Data Contracts

### Rule JSON (returned to frontend)

```json
{
  "provider_id": "prov_4827",
  "provider_name": "John Doe, MD",
  "rules": [
    {
      "rule_id": "r_9c0e...",
      "title": "Referral Prefs",
      "body": "Prefers faxed referrals only; use cover sheet X.",
      "source": {
        "doc_id": "sp_123",
        "doc_url": "https://sharepoint/...",
        "page": 4,
        "version": "2025-10-12"
      },
      "tags": ["referral", "fax"],
      "last_updated": "2025-10-12T14:03:00Z",
      "confidence": 0.92,
      "steps": ["Prepare cover sheet X", "Fax to 555-0100"]
    }
  ]
}
```

### Database Tables (DDL)

```sql
CREATE TABLE IF NOT EXISTS provider_alias (
  alias_id SERIAL PRIMARY KEY,
  provider_id TEXT NULL,
  normalized_alias TEXT NOT NULL,
  source TEXT CHECK (source IN ('doc','ehr','manual')) DEFAULT 'doc',
  UNIQUE(provider_id, normalized_alias)
);

CREATE TABLE IF NOT EXISTS provider_rule (
  rule_id TEXT PRIMARY KEY,
  provider_canonical_name TEXT NOT NULL,
  provider_id TEXT NULL,
  title TEXT,
  body TEXT NOT NULL,
  tags TEXT[],
  doc_id TEXT,
  doc_url TEXT,
  page INT,
  version TEXT,
  last_updated TIMESTAMPTZ DEFAULT now()
);
```

## 2) Ingestion Pipeline (SharePoint/Word → Rules)

Key steps:
- Crawl SharePoint (Graph or REST) for Word/PDF docs
- Parse documents (`python-docx`, `pypdf`)
- Extract candidate rule blocks by headings/heuristics
- Entity extraction for provider names and rule types (regex + RapidFuzz/spaCy)
- Normalize names and upsert into `provider_rule` and `provider_alias`
- Chunk and embed; upsert vectors into FAISS (or managed vector DB)

The starter implementation is in `backend/ingest/ingest.py` and aligns with this flow. Swap FAISS with Pinecone/Weaviate in production if needed.

## 3) Provider Name ↔ EHR ID Resolution

Strategy:
- Deterministic normalization (strip punctuation/honorifics)
- RapidFuzz token‑set ratio against EHR roster with threshold (≥ 90)
- Persist approved links in `provider_alias(provider_id, normalized_alias, source='ehr'|'manual')`
- Add an admin UI for reconciliation (future work)

## 4) Backend API (FastAPI)

OpenAPI sketch:

```
GET /providers/{provider_id}/rules
  -> 200 { provider_id, provider_name, rules: Rule[] }
GET /healthz
```

Implemented in `backend/app/main.py`:
- `GET /providers/{provider_id}/rules`: Retrieves rules by vector search on provider aliases; falls back to canonical name filter
- `GET /healthz`: Basic health

Environment variables (see `.env.example`):
- `PG_DSN` — Postgres DSN
- `INDEX_PATH` — FAISS index path
- `EMBED_MODEL` — sentence-transformers model name

## 5) Frontend

The starter UI is in `frontend/` (React + Vite + Tailwind). Create a panel that calls the backend endpoint, e.g. `GET /providers/{providerId}/rules`, and presents steps or body text.

## 6) Deployment (Docker + Options)

Example Dockerfile for backend is included at `backend/Dockerfile`. For local DB:
- `docker compose up -d db adminer`
- Connect via Adminer on http://localhost:8081

In production, consider:
- ECS Fargate (private subnets) + RDS Postgres + managed vector DB
- Lambda + API Gateway for bursty workloads

## 7) Security & Compliance Checklist (HIPAA‑friendly)

- Data minimization: avoid PHI in logs
- TLS in transit; encryption at rest
- JWT/OIDC for agents; per‑tenant RBAC
- Private networking; no public DB
- Structured logs and auditability
- Redaction of PII/PHI before persistence
- Vendor BAAs if PHI may flow through LLMs

## 8) Monitoring, Quality & Ops

- Metrics: qps, p95 latency, vector hit rate, no‑result rate
- Tracing: OpenTelemetry spans
- Logging: correlation IDs, doc/version lineage
- Evaluation: recall@k, drift checks on re‑index

## 9) Updates & Re‑Indexing

- On SharePoint change or nightly: re‑parse changed docs only
- Maintain `embedding_version`; rebuild vectors if the model changes

## 10) Testing Strategy

- Unit: parsing, normalization, resolver
- Integration: end‑to‑end retrieval over seeded corpus
- Contract: `/providers/{id}/rules` response schema

## 11) Environment Variables (example)

```
PG_DSN=postgresql://app:app@localhost:5432/rules
INDEX_PATH=./faiss.index
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## 12) Quick Start

- Backend
  - `cd backend && cp .env.example .env`
  - `pip install -r requirements.txt`
  - `uvicorn app.main:app --reload`
- Database
  - `docker compose up -d db adminer`
  - `psql postgresql://app:app@localhost:5432/rules -c "\dt"`
- Ingestion
  - `python backend/ingest/ingest.py`
- Frontend
  - `cd frontend && npm install && npm run dev`

## 13) Notes

- Use Pinecone/Weaviate/Milvus for horizontal scale
- Prefer `pymupdf`/`unstructured` for heavy PDF workflows
- Consider on‑prem connectors if LLM usage must be under BAA

