import duckdb

con = duckdb.connect("2_database/medwhisper.duckdb")
# See what the exact source_path was (copy it from output if needed)
rows = con.execute("""
  SELECT source_path, status, n_chunks, updated_at
  FROM ingest_manifest
  WHERE source_path LIKE '%labevents_curated.parquet%'
""").fetchall()
print("Before:", rows)

# Option 1 (recommended): mark it as done so extractor skips it
con.execute("""
  UPDATE ingest_manifest
  SET status='done'
  WHERE source_path LIKE '%labevents_curated.parquet%';
""")

# Option 2: delete the manifest row (uncomment if you prefer deletion)
# con.execute("""
#   DELETE FROM ingest_manifest
#   WHERE source_path LIKE '%labevents_curated.parquet%';
# """)

rows = con.execute("""
  SELECT source_path, status, n_chunks, updated_at
  FROM ingest_manifest
  WHERE source_path LIKE '%labevents_curated.parquet%'
""").fetchall()
print("After :", rows)

con.close()
print("✓ Manifest updated")
