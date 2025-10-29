CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

-- Seed a tiny sample so the API returns something on day 1
INSERT INTO provider_rule (rule_id, provider_canonical_name, title, body, tags, doc_id, version)
VALUES
('r_demo_1','John Doe, MD','Referral Preferences',
 'Prefers faxed referrals only. Use cover sheet X. Step 1: Prepare cover sheet X. Step 2: Fax to 555-0100.',
 ARRAY['referral','fax'],'demo.docx','2025-10-12')
ON CONFLICT DO NOTHING;
