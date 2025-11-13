import duckdb
import os

DB_PATH = os.getenv("DB_PATH", "2_database/medwhisper.duckdb")

# How many chunks per table we want to embed *for now*.
# Example: 250000 per table. If ~40 tables → about 10M chunks.
PER_TABLE_EMBED_LIMIT = int(os.getenv("PER_TABLE_EMBED_LIMIT", "250000"))

con = duckdb.connect(DB_PATH)

print("=== Building embed_queue ===")
print(f"PER_TABLE_EMBED_LIMIT = {PER_TABLE_EMBED_LIMIT}")

# Create table with the doc_ids we want to embed in this phase
con.execute(f"""
    CREATE OR REPLACE TABLE embed_queue AS
    SELECT doc_id
    FROM (
        SELECT
            doc_id,
            table_name,
            ROW_NUMBER() OVER (
                PARTITION BY table_name
                ORDER BY doc_id
            ) AS rn
        FROM documents
    )
    WHERE rn <= {PER_TABLE_EMBED_LIMIT};
""")

total_docs = con.execute("SELECT COUNT(*) FROM embed_queue").fetchone()[0]
tables = con.execute("""
    SELECT COUNT(DISTINCT d.table_name)
    FROM documents d
    JOIN embed_queue q ON q.doc_id = d.doc_id
""").fetchone()[0]

print(f"embed_queue rows (planned to embed now): {total_docs:,}")
print(f"tables covered: {tables}")

con.close()
print("✓ embed_queue created.")
