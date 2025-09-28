
import duckdb
from pathlib import Path

# Connect to the DuckDB file (creates it if not exists)
con = duckdb.connect("medwhisper.db")

# Read and apply the schema.sql file
schema_path = Path("sql/schema.sql")
with open(schema_path, "r", encoding="utf-8") as f:
    schema_sql = f.read()

con.execute(schema_sql)
print("✅ Schema applied: tables and base timeline created")
