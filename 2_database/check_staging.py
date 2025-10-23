import duckdb

con = duckdb.connect("2_database/1_medwhisper.duckdb")

print("✅ Connected to medwhisper.duckdb\n")

# Check how many views exist
print("Total views in DB:")
print(con.execute("SELECT COUNT(*) AS n FROM information_schema.views").fetchdf(), "\n")

# Show a few sample view names
print("Sample of staging views:")
print(con.execute("""
    SELECT table_name
    FROM information_schema.views
    WHERE table_name LIKE 'stg_%'
    ORDER BY table_name
    LIMIT 10
""").fetchdf(), "\n")

# Check structure of 3 important ones
for v in ["stg_1_hosp_admissions", "stg_1_hosp_patients", "stg_2_icu_icustays"]:
    print(f"--- {v} ---")
    print(con.execute(f"PRAGMA table_info('{v}')").fetchdf(), "\n")

con.close()
