# Changelog

A running record of behaviors and issues found while reading and testing this codebase.

- backend/db/init.sql only creates the `ehr_provider` table, but then tries to INSERT into `provider_alias` and `provider_rule` — both of which are documented in the README's DDL section but never actually created anywhere in the repo. Confirmed live: starting a fresh `docker compose up -d db` produces `ERROR: relation "provider_alias" does not exist`, and the init script's failure causes the entire Postgres container to exit (code 3) rather than come up in a partially-seeded state.

- As a direct consequence, `GET /providers/{provider_id}/rules` can never work even if the db container were kept alive some other way — its first query is `SELECT normalized_alias FROM provider_alias WHERE provider_id = %s`, and that table doesn't exist. Confirmed by running that exact query directly against a freshly initialized database — it fails with the same "relation does not exist" error.

- frontend/vite.config.ts's dev proxy forwards `/api/*` to `http://localhost:8080`, but the backend runs on port 8000 everywhere else in the project — docker-compose.yml's `ports: ["8000:8000"]`, the backend Dockerfile's `EXPOSE 8000`/CMD, and uvicorn's own default port. Every frontend API call made through `npm run dev` would hit a port nothing is listening on.

- parse_steps() in main.py can mislabel non-step preamble text as "Step 1" — confirmed live against the project's own demo seed data (init.sql's demo2 rule, "Use portal first. If portal down: Step 1: Call office. Step 2: Email referrals@clinic.example"): the primary regex only matches one real step, so the len(steps) <= 1 fallback kicks in and does a plain re.split on "Step N:", which returns the preamble text as if it were the first step. The parsed output is `["Use portal first. If portal down:", "Call office.", "Email referrals@clinic.example"]` — a sentence fragment shown as "Step 1" to whoever is reading it.

- The same fallback also leaves stray bullet-point hyphens attached to step text — confirmed live against init.sql's demo3 rule ("- Page main line\n- Step 1: Document in EHR inbox\n- Step 2: Mark as urgent if fever > 102F"): the parsed output is `["- Page main line -", "Document in EHR inbox -", "Mark as urgent if fever > 102F"]`, with leading/trailing "-" characters bleeding into the step text since the fallback's plain re.split doesn't strip the bullet markers the way the primary regex's negative lookahead is meant to.

- frontend/package.json's lint script (`eslint . --ext js,jsx ...`) only checks `.js`/`.jsx` files, but the entire frontend source tree is TypeScript (`.tsx`/`.ts`) — `npm run lint` never actually lints any real source file in this project.

- ProviderSearch.tsx's `debouncedQ` is misleadingly named — it's computed via `useMemo(() => q.trim(), [q])`, which has no delay mechanism at all; a new fetch fires on every keystroke, not after the user pauses typing.

- RulesPanel.tsx has two leftover debug `console.log` statements (`providerId =`, `Fetching`) that fire in the browser console every time a provider is selected.

- backend/.env.example is formatted as a bash heredoc snippet (`cat > .env <<'EOF' ... EOF`) meant to be run in a shell, not copied as a file — but the README's own Quick Start says to `cp .env.example .env`. Confirmed live: doing that literally still works (python-dotenv extracts the real PG_DSN/INDEX_PATH/EMBED_MODEL values from the middle of the file), but it emits a "could not parse statement" warning and adds a bogus `EOF=None` key.

- docker-compose.yml defines no frontend service at all, even though frontend/Dockerfile exists — `docker compose up` only ever brings up `db`, `adminer`, and `backend`. The frontend is only ever meant to run via `npm install && npm run dev` outside Docker, per the README's own instructions; the Dockerfile appears to be unused/orphaned.

- backend/ingest/ingest.py never imports or uses `faiss` at all — it saves raw vectors via `np.save(INDEX_PATH + ".npy", vecs)` and a separate `.meta` JSON file, not an actual FAISS index. main.py's vector-loading code, meanwhile, checks for a file at the literal `INDEX_PATH` (no suffix) and calls `faiss.read_index()` on it, which expects FAISS's own binary serialization format, not a numpy array.

- As a direct result, `os.path.exists(INDEX_PATH)` in main.py is always False no matter how many times ingest.py has been run, so `index` stays an empty `faiss.IndexFlatIP(384)` and `can_vector` is always False. The vector-search branch of get_rules() is permanently dead code — every request falls through to the SQL ILIKE fallback, regardless of ingestion. The "RAG" part of this RAG system can never actually engage as built.

- `rapidfuzz` is listed in requirements.txt and is central to the README's "Provider Name ↔ EHR ID Resolution" strategy ("RapidFuzz token-set ratio against EHR roster with threshold ≥ 90"), but it's never imported or used anywhere in the actual code — the fuzzy-matching resolution described in section 3 doesn't exist; only exact alias lookups and SQL ILIKE substring matching are implemented.

- `python-docx` and `pypdf` are both listed in requirements.txt and central to the README's "Ingestion Pipeline (SharePoint/Word → Rules)" section ("Parse documents (python-docx, pypdf)"), but neither is imported or used anywhere in the code — there is no document-parsing logic at all in this repo.

- More broadly, the entire "SharePoint/Docs → Ingestion Worker" pipeline shown in the README's architecture diagram (crawling SharePoint, parsing Word/PDF, entity extraction, name normalization) doesn't exist anywhere in the code — no SharePoint/Graph API client, no spaCy usage, nothing. ingest.py only reads rows already present in `provider_rule` and embeds them; nothing in this repo populates that table from source documents.

- main.py connects to Postgres at module import time (`pg = psycopg2.connect(PG_DSN, ...)`, line 64) with no retry logic, and docker-compose.yml's `backend` service has `depends_on: - db` with no healthcheck/condition — `depends_on` alone only waits for the db container to start, not for Postgres to actually be ready to accept connections. If the backend container starts before Postgres finishes its own startup, uvicorn crashes immediately on import rather than retrying.

- docker-compose.yml exposes raw Postgres directly to the host (`ports: ["5432:5432"]`) and runs Adminer, a full DB admin GUI, on `8081` with no auth of its own — reachable with the trivial default credentials (`app`/`app`) set right in the same file. This directly contradicts the project's own README security checklist, which lists "Private networking; no public DB" as a requirement.

- Neither the root .gitignore nor backend/.dockerignore exclude the ingestion pipeline's output files (`faiss.index.npy`, `faiss.index.meta`) — confirmed by grep, no match anywhere. Since these files encode embeddings of the actual provider rule text, they could be accidentally committed after running `ingest.py`, in tension with the README's own checklist item about avoiding PHI persistence.

- The `confidence` field is shown as a real computed value (`0.92`) in the README's example API response and exists on the `Rule` Pydantic model, but it's never actually set anywhere `Rule(...)` is constructed in `get_rules()` — every real response has `confidence: null`.

- frontend/src/index.css still has the default Vite/React template's dark-theme boilerplate in `:root` (`background-color: #242424`, near-white `color: rgba(255,255,255,.87)`), never updated when the app was actually styled with Tailwind's light theme (`bg-gray-100 text-gray-900`) in App.tsx. Since `body` sets no background of its own, this causes a brief dark-background flash before React mounts and the app's own light-themed div paints over it.

- ProviderSearch.tsx's already-un-debounced search effect gets doubled in development by `React.StrictMode` (used in main.tsx), which intentionally double-invokes effects there. The first fetch's result is discarded via the effect's `cancelled` flag, but the actual HTTP request still goes out both times, since nothing uses an AbortController to actually cancel it — every keystroke fires two real network requests, not one.

- `get_rules()` never returns 404 for an unknown provider_id — it always returns 200 with an empty `rules` array, and `provider_name` falls back to just echoing the raw `provider_id` string back (since `aliases` defaults to `[provider_id]` when no real alias exists). This is unlike the sibling `ehr_provider_get` endpoint, which correctly raises a 404 for an ID that doesn't exist.

- The result-count cap of 20 is hardcoded independently in three separate places in main.py — the alias-based SQL fallback's `LIMIT 20`, the vector search's `index.search(qv, 20)`, and the canonical-name SQL fallback's `LIMIT 20` — with no shared named constant anywhere.
