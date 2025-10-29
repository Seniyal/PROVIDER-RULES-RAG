import os, json
import faiss
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
PG_DSN = os.getenv("PG_DSN")
if not PG_DSN:
    raise ValueError("PG_DSN environment variable is required")
INDEX_PATH = os.getenv("INDEX_PATH", "./faiss.index")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

pg = psycopg2.connect(PG_DSN, cursor_factory=RealDictCursor)
pg.autocommit = True

model = SentenceTransformer(EMBED_MODEL)

if os.path.exists(INDEX_PATH) and os.path.exists(INDEX_PATH + ".meta"):
    index = faiss.read_index(INDEX_PATH)
    meta = json.load(open(INDEX_PATH + ".meta"))
else:
    index = faiss.IndexFlatIP(384)
    meta = {"items": []}

def upsert_vectors():
    with pg.cursor() as cur:
        cur.execute("SELECT rule_id, title, body FROM provider_rule ORDER BY last_updated DESC LIMIT 1000")
        rows = cur.fetchall()
    texts = [(r["rule_id"], (r["title"] or "") + "\n" + r["body"]) for r in rows]
    if not texts:
        print("No rules found to index.")
        return
    vecs = model.encode([t for _, t in texts], normalize_embeddings=True).astype("float32")
    index.reset()
    index.add(vecs)
    meta["items"] = [{"rule_id": rid} for rid, _ in texts]
    faiss.write_index(index, INDEX_PATH)
    json.dump(meta, open(INDEX_PATH + ".meta", "w"))
    print(f"Indexed {len(texts)} rules.")

if __name__ == "__main__":
    upsert_vectors()
