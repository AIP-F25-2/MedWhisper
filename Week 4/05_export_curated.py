import duckdb
con = duckdb.connect("medwhisper.db")

exports = {
    "patients_curated": "data/exports/patients.csv",
    "encounters_curated": "data/exports/encounters.csv",
    "conditions_curated": "data/exports/conditions.csv",
    "procedures_curated": "data/exports/procedures.csv",
    "medications_curated": "data/exports/medications.csv",
    "observations_curated": "data/exports/observations.csv",
    "timeline_events": "data/exports/timeline_events.csv",
}

for table, path in exports.items():
    con.execute(f"COPY {table} TO '{path}' (HEADER, DELIMITER ',')")
    print(f"Exported {table} → {path}")
