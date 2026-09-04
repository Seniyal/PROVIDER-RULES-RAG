# Changelog

A running record of behaviors and issues found while reading and testing this codebase.

- backend/db/init.sql only creates the `ehr_provider` table, but then tries to INSERT into `provider_alias` and `provider_rule` — both of which are documented in the README's DDL section but never actually created anywhere in the repo. Confirmed live: starting a fresh `docker compose up -d db` produces `ERROR: relation "provider_alias" does not exist`, and the init script's failure causes the entire Postgres container to exit (code 3) rather than come up in a partially-seeded state.

- As a direct consequence, `GET /providers/{provider_id}/rules` can never work even if the db container were kept alive some other way — its first query is `SELECT normalized_alias FROM provider_alias WHERE provider_id = %s`, and that table doesn't exist. Confirmed by running that exact query directly against a freshly initialized database — it fails with the same "relation does not exist" error.

- frontend/vite.config.ts's dev proxy forwards `/api/*` to `http://localhost:8080`, but the backend runs on port 8000 everywhere else in the project — docker-compose.yml's `ports: ["8000:8000"]`, the backend Dockerfile's `EXPOSE 8000`/CMD, and uvicorn's own default port. Every frontend API call made through `npm run dev` would hit a port nothing is listening on.

- parse_steps() in main.py can mislabel non-step preamble text as "Step 1" — confirmed live against the project's own demo seed data (init.sql's demo2 rule, "Use portal first. If portal down: Step 1: Call office. Step 2: Email referrals@clinic.example"): the primary regex only matches one real step, so the len(steps) <= 1 fallback kicks in and does a plain re.split on "Step N:", which returns the preamble text as if it were the first step. The parsed output is `["Use portal first. If portal down:", "Call office.", "Email referrals@clinic.example"]` — a sentence fragment shown as "Step 1" to whoever is reading it.

- The same fallback also leaves stray bullet-point hyphens attached to step text — confirmed live against init.sql's demo3 rule ("- Page main line\n- Step 1: Document in EHR inbox\n- Step 2: Mark as urgent if fever > 102F"): the parsed output is `["- Page main line -", "Document in EHR inbox -", "Mark as urgent if fever > 102F"]`, with leading/trailing "-" characters bleeding into the step text since the fallback's plain re.split doesn't strip the bullet markers the way the primary regex's negative lookahead is meant to.

- frontend/package.json's lint script (`eslint . --ext js,jsx ...`) only checks `.js`/`.jsx` files, but the entire frontend source tree is TypeScript (`.tsx`/`.ts`) — `npm run lint` never actually lints any real source file in this project.
