import duckdb, pandas as pd
con = duckdb.connect("2_database/medwhisper.duckdb")

print("\n=== Ingest manifest (latest 5) ===")
print(con.execute("""
  SELECT status, source_path, n_chunks, updated_at
  FROM ingest_manifest
  ORDER BY updated_at DESC
  LIMIT 5
""").df())

print("\n=== Pending chunks to embed ===")
print(con.execute("""
  SELECT COUNT(*) AS pending_to_embed
  FROM documents d
  LEFT JOIN embeddings e ON e.doc_id = d.doc_id
  WHERE e.doc_id IS NULL
""").df())
