CREATE TABLE IF NOT EXISTS ehr_provider (
  provider_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  specialty TEXT,
  npi TEXT
);

INSERT INTO ehr_provider (provider_id, name, specialty, npi) VALUES
('prov_1001','John Doe, MD','Cardiology','1111111111'),
('prov_1002','Jane Smith, DO','Family Medicine','2222222222'),
('prov_1003','Alex Patel, NP','Pediatrics','3333333333')
ON CONFLICT DO NOTHING;

-- connect aliases so vector queries work by ID or name
INSERT INTO provider_alias (provider_id, normalized_alias, source)
SELECT 'prov_1001','johndoemd','ehr' UNION ALL
SELECT 'prov_1002','janesmithdo','ehr' UNION ALL
SELECT 'prov_1003','alexpatelnp','ehr'
ON CONFLICT DO NOTHING;

-- a few demo rules tied to each provider
INSERT INTO provider_rule (rule_id, provider_canonical_name, provider_id, title, body, tags, doc_id, version)
VALUES
('r_demo_2','Jane Smith, DO','prov_1002','Referral Routing',
 'Use portal first. If portal down: Step 1: Call office. Step 2: Email referrals@clinic.example', ARRAY['referral','portal'],'demo2.docx','2025-10-12'),
('r_demo_3','Alex Patel, NP','prov_1003','After-hours Coverage',
 '- Page main line\n- Step 1: Document in EHR inbox\n- Step 2: Mark as urgent if fever > 102F', ARRAY['after-hours'],'demo3.docx','2025-10-12')
ON CONFLICT DO NOTHING;
