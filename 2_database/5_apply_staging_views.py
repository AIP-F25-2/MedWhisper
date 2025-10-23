import duckdb, pathlib
DB="2_database/1_medwhisper.duckdb"
SQL="2_database/4_staging_views.sql"

con=duckdb.connect(DB)
con.execute(pathlib.Path(SQL).read_text(encoding="utf-8"))
print("✅ Applied staging views.")
print(con.execute("SELECT COUNT(*) AS n FROM information_schema.views").df())
