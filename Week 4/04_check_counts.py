import duckdb
con = duckdb.connect("medwhisper.db")

groups = {
  "RAW": [
    "raw_patients","raw_encounters","raw_conditions",
    "raw_procedures","raw_medications","raw_observations"
  ],
  "CURATED": [
    "patients_curated","encounters_curated","conditions_curated",
    "procedures_curated","medications_curated","observations_curated",
    "timeline_events"
  ]
}

for label, tables in groups.items():
    print(f"\n== {label} ==")
    for t in tables:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t:24s} {n}")
