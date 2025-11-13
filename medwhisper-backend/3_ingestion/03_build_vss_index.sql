-- 3_ingestion/03_build_vss_index.sql
LOAD 'vss';

-- Ensure we have the expected tables (documents, embeddings)
-- documents: doc_id BIGINT PRIMARY KEY, table_name TEXT, source_path TEXT, meta TEXT, text TEXT
-- embeddings: doc_id BIGINT PRIMARY KEY, embedding <array or vector>

-- 1) If your 'embedding' column is not VECTOR(768), convert it once.
--    This covers the common case where it's a LIST/FLOAT array.
--    (If it's already VECTOR(768), DuckDB will error on this ALTER; you can ignore the error.)
BEGIN TRANSACTION;
PRAGMA ignore_errors=1;
ALTER TABLE embeddings
  ALTER COLUMN embedding
  SET DATA TYPE VECTOR(768)
  USING to_vector(embedding);
COMMIT;

-- 2) Fast metadata lookup for search results
CREATE OR REPLACE VIEW vss_lookup AS
SELECT d.doc_id, d.table_name, d.source_path, d.meta, d.text
FROM documents d;

-- 3) Create VSS index on embeddings (cosine metric recommended for SBERT-like models)
CREATE INDEX IF NOT EXISTS vss_embeddings_idx
ON embeddings USING vss(embedding) WITH (metric='cosine');

-- 4) Help the planner
ANALYZE;
