from fastapi import FastAPI, HTTPException, Query

from pydantic import BaseModel
import os, json, re
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Optional heavy deps — make app runnable without them (no vector search fallback)
FAISS_AVAILABLE = False
EMBEDDINGS_AVAILABLE = False
faiss = None
SentenceTransformer = None
try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = True
except Exception:
    FAISS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    EMBEDDINGS_AVAILABLE = True
except Exception:
    EMBEDDINGS_AVAILABLE = False

load_dotenv()
# Provide sensible default for local dev
PG_DSN = os.getenv("PG_DSN") or "postgresql://app:app@localhost:5432/rules"
INDEX_PATH = os.getenv("INDEX_PATH", "./faiss.index")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

app = FastAPI(title="Provider Rules API", version="0.1.0")

# ---------- MOCK EHR ----------
@app.get("/ehr/providers")
def ehr_providers():
    with pg.cursor() as cur:
        cur.execute("SELECT provider_id, name, specialty, npi FROM ehr_provider ORDER BY name ASC")
        return {"providers": cur.fetchall()}

@app.get("/ehr/providers/search")
def ehr_providers_search(q: str = Query("", min_length=0)):
    q_like = f"%{q}%"
    with pg.cursor() as cur:
        cur.execute("""
          SELECT provider_id, name, specialty, npi
          FROM ehr_provider
          WHERE name ILIKE %s OR specialty ILIKE %s OR npi ILIKE %s
          ORDER BY name ASC
          LIMIT 20
        """, (q_like, q_like, q_like))
        return {"providers": cur.fetchall()}

@app.get("/ehr/providers/{provider_id}")
def ehr_provider_get(provider_id: str):
    with pg.cursor() as cur:
        cur.execute("SELECT provider_id, name, specialty, npi FROM ehr_provider WHERE provider_id = %s", (provider_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Provider not found")
        return {"provider": row}


# --- DB ---
pg = psycopg2.connect(PG_DSN, cursor_factory=RealDictCursor)
pg.autocommit = True

# --- Embeddings & FAISS (optional) ---
embedder = None
index = None
meta = {"items": []}
if EMBEDDINGS_AVAILABLE:
    try:
        embedder = SentenceTransformer(EMBED_MODEL)  # type: ignore[call-arg]
    except Exception:
        embedder = None
        EMBEDDINGS_AVAILABLE = False

if FAISS_AVAILABLE:
    try:
        if os.path.exists(INDEX_PATH) and os.path.exists(INDEX_PATH + ".meta"):
            index = faiss.read_index(INDEX_PATH)  # type: ignore[union-attr]
            meta = json.load(open(INDEX_PATH + ".meta"))
        else:
            # 384 dims for MiniLM-L6-v2
            index = faiss.IndexFlatIP(384)  # type: ignore[union-attr]
            meta = {"items": []}
    except Exception:
        index = None
        meta = {"items": []}

# Works even when sentences end with things like "portal down: Step 1: ..."
# Ultra-tolerant step parser — handles:
# "Step 1: ... Step 2: ...", bullets, weird spacing, no newlines, etc.
STEP_RE = re.compile(
    r"(?i)(?:^|[\n.:;]\s*)(?:step\s*\d+[:.)]\s*)([^-•\n]+?)(?=(?:\s*(?:step\s*\d+[:.)]|[-•]\s)|$))"
)

def parse_steps(text: str):
    # Normalize the text — ensure consistent spaces
    text = text.replace("\r", " ").replace("\n", " ")
    steps = [s.strip().rstrip(" .)") for s in STEP_RE.findall(text)]
    # Fallback: if still only 1, try simple split
    if len(steps) <= 1 and "Step 2" in text:
        parts = re.split(r"Step\s*\d+[:.)]\s*", text, flags=re.I)
        steps = [p.strip() for p in parts if p.strip()]
    return steps or None


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

    # 2) Vector search if available, otherwise fallback to SQL filter
    rule_ids: list[str] = []
    can_vector = bool(EMBEDDINGS_AVAILABLE and FAISS_AVAILABLE and embedder is not None and index is not None and len(meta.get("items", [])) > 0)
    if can_vector:
        try:
            query_text = " ".join(aliases)
            qv = embedder.encode([query_text], normalize_embeddings=True).astype("float32")  # type: ignore[attr-defined]
            D, I = index.search(qv, 20)  # type: ignore[union-attr]
            rule_ids = [meta["items"][i]["rule_id"] for i in I[0] if i != -1] if len(I) else []
        except Exception:
            rule_ids = []

    rules: list[Rule] = []
    with pg.cursor() as cur:
        if rule_ids:
            cur.execute("""
              SELECT rule_id, provider_canonical_name, title, body, tags, doc_id, doc_url, page, version, last_updated
              FROM provider_rule WHERE rule_id = ANY(%s)
            """, (rule_ids,))
        else:
            # Fallback: try matching by provider_id or canonical name
            cur.execute(
                """
                SELECT rule_id, provider_canonical_name, title, body, tags, doc_id, doc_url, page, version, last_updated
                FROM provider_rule
                WHERE provider_id = %s
                   OR provider_canonical_name ILIKE %s
                LIMIT 20
                """,
                (provider_id, f"%{provider_id}%",),
            )

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
