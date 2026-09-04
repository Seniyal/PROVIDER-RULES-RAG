# Changelog

A running record of behaviors and issues found while reading and testing this codebase.

- backend/db/init.sql only creates the `ehr_provider` table, but then tries to INSERT into `provider_alias` and `provider_rule` — both of which are documented in the README's DDL section but never actually created anywhere in the repo. Confirmed live: starting a fresh `docker compose up -d db` produces `ERROR: relation "provider_alias" does not exist`, and the init script's failure causes the entire Postgres container to exit (code 3) rather than come up in a partially-seeded state.

- As a direct consequence, `GET /providers/{provider_id}/rules` can never work even if the db container were kept alive some other way — its first query is `SELECT normalized_alias FROM provider_alias WHERE provider_id = %s`, and that table doesn't exist. Confirmed by running that exact query directly against a freshly initialized database — it fails with the same "relation does not exist" error.
