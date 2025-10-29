from fastapi import FastAPI
from pydantic import BaseModel
import os, json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import re

load_dotenv()
PG_DSN = os.getenv("PG_DSN")
if not PG_DSN:
    raise ValueError("PG_DSN environment variable is required")
INDEX_PATH = os.getenv("INDEX_PATH", "./faiss.index")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

app = FastAPI(title="Provider Rules API", version="0.1.0")

# --- DB ---
pg = psycopg2.connect(PG_DSN, cursor_factory=RealDictCursor)
pg.autocommit = True

# --- Embeddings & FAISS ---
embedder = SentenceTransformer(EMBED_MODEL)

if os.path.exists(INDEX_PATH) and os.path.exists(INDEX_PATH + ".meta"):
    index = faiss.read_index(INDEX_PATH)
    meta = json.load(open(INDEX_PATH + ".meta"))
else:
    index = faiss.IndexFlatIP(384)  # dims for MiniLM-L6-v2
    meta = {"items": []}

STEP_RE = re.compile(r"(?:^|\n)(?:step\s*\d+[:.)]|-\s|•\s)(.+)", re.I)
def parse_steps(text: str):
    return [m.group(1).strip() for m in STEP_RE.finditer(text)] or None

class Rule(BaseModel):
    rule_id: str
    title: str | None = None
    body: str
    tags: list[str] = []
    source: dict | None = None
    last_updated: str | None = None
    confidence: float | None = None
    steps: list[str] | None = None

class RuleResponse(BaseModel):
    provider_id: str
    provider_name: str
    rules: list[Rule]

@app.get("/healthz")
def health():
    return {"ok": True}

@app.get("/providers/{provider_id}/rules", response_model=RuleResponse)
def get_rules(provider_id: str):
    # 1) Try aliases for this provider_id
    with pg.cursor() as cur:
        cur.execute("SELECT normalized_alias FROM provider_alias WHERE provider_id = %s", (provider_id,))
        aliases = [r["normalized_alias"] for r in cur.fetchall()]
    if not aliases:
        aliases = [provider_id]

    # 2) Vector search against alias text
    query_text = " ".join(aliases)
    qv = embedder.encode([query_text], normalize_embeddings=True).astype("float32")
    D, I = index.search(qv, 20)
    rule_ids = [meta["items"][i]["rule_id"] for i in I[0] if i != -1] if len(I) else []

    rules: list[Rule] = []
    with pg.cursor() as cur:
        if rule_ids:
            cur.execute("""
              SELECT rule_id, provider_canonical_name, title, body, tags, doc_id, doc_url, page, version, last_updated
              FROM provider_rule WHERE rule_id = ANY(%s)
            """, (rule_ids,))
        else:
            # Fallback: simple text filter on canonical name to show something useful
            cur.execute("""
              SELECT rule_id, provider_canonical_name, title, body, tags, doc_id, doc_url, page, version, last_updated
              FROM provider_rule
              WHERE provider_canonical_name ILIKE %s
              LIMIT 20
            """, (f"%{provider_id}%",))
        for r in cur.fetchall():
            rules.append(Rule(
                rule_id=r["rule_id"],
                title=r["title"],
                body=r["body"],
                tags=r["tags"] or [],
                source={"doc_id": r["doc_id"], "doc_url": r["doc_url"], "page": r["page"], "version": r["version"]},
                last_updated=r["last_updated"].isoformat() if r["last_updated"] else None,
                steps=parse_steps(r["body"]),
            ))
    return RuleResponse(provider_id=provider_id, provider_name=aliases[0], rules=rules)
