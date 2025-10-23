import duckdb, os

DB = "2_database/1_medwhisper.duckdb"
SCHEMA = "2_database/2_schema.sql"

if os.path.exists(DB):
    os.remove(DB)

con = duckdb.connect(DB)
con.execute(open(SCHEMA, "r", encoding="utf-8").read())
con.close()

print("✅ Created 1_medwhisper.duckdb from 2_schema.sql")
