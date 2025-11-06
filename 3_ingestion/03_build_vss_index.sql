LOAD 'vss';
SET threads TO 4;

CREATE OR REPLACE TABLE vss_embeddings AS
SELECT d.doc_id::UBIGINT AS id, e.embedding AS embedding
FROM embeddings e
JOIN documents d ON d.doc_id = e.doc_id;

CREATE OR REPLACE INDEX vss_embeddings_idx
ON vss_embeddings USING vss(embedding);

CREATE OR REPLACE VIEW vss_lookup AS
SELECT v.id AS doc_id, d.table_name, d.source_path, d.meta, d.text
FROM vss_embeddings v
JOIN documents d ON d.doc_id = v.id::UBIGINT;
