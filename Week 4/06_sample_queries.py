import duckdb
import pandas as pd

con = duckdb.connect("medwhisper.db")

# Queries
queries = {
    "top_conditions": """
        SELECT code, description, COUNT(*) AS n
        FROM conditions_curated
        GROUP BY 1,2
        ORDER BY n DESC
        LIMIT 5
    """,
    "top_medications": """
        SELECT code, description, COUNT(*) AS n
        FROM medications_curated
        GROUP BY 1,2
        ORDER BY n DESC
        LIMIT 5
    """,
    "timeline_preview": """
        SELECT * FROM timeline_events
        ORDER BY event_time
        LIMIT 5
    """
}

# Run and save results
for name, sql in queries.items():
    df = con.execute(sql).fetchdf()
    print(f"\n== {name} ==")
    print(df)
    df.to_csv(f"data/exports/{name}.csv", index=False)
    print(f"✅ Saved → data/exports/{name}.csv")
