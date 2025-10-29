import os, json
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import numpy as np

load_dotenv()
PG_DSN = os.getenv("PG_DSN")
INDEX_PATH = os.getenv("INDEX_PATH", "./faiss.index")  # reuse this stem
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

pg = psycopg2.connect(PG_DSN, cursor_factory=RealDictCursor)
pg.autocommit = True

model = SentenceTransformer(EMBED_MODEL)

def upsert_vectors():
    with pg.cursor() as cur:
        cur.execute("SELECT rule_id, title, body FROM provider_rule ORDER BY last_updated DESC LIMIT 2000")
        rows = cur.fetchall()
    if not rows:
        print("No rules found to index.")
        return
    texts = [(r["rule_id"], ((r["title"] or "") + "\n" + r["body"]).strip()) for r in rows]
    vecs = model.encode([t for _, t in texts], normalize_embeddings=True).astype("float32")
    meta = {"items": [{"rule_id": rid} for rid, _ in texts]}
    np.save(INDEX_PATH + ".npy", vecs)                 # -> ./faiss.index.npy
    json.dump(meta, open(INDEX_PATH + ".meta", "w"))   # -> ./faiss.index.meta
    print(f"Indexed {len(texts)} rules -> {INDEX_PATH}.npy")

if __name__ == "__main__":
    upsert_vectors()

