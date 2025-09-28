import duckdb

con = duckdb.connect("medwhisper.db")

# 1) Patients (raw)
con.execute("""
CREATE OR REPLACE TABLE raw_patients AS
SELECT * FROM read_csv_auto('data/synthea/patients.csv', header=True);
""")

# 2) Encounters (raw)
con.execute("""
CREATE OR REPLACE TABLE raw_encounters AS
SELECT * FROM read_csv_auto('data/synthea/encounters.csv', header=True);
""")

# 3) Conditions (raw)
con.execute("""
CREATE OR REPLACE TABLE raw_conditions AS
SELECT * FROM read_csv_auto('data/synthea/conditions.csv', header=True);
""")

# 4) Procedures (raw)
con.execute("""
CREATE OR REPLACE TABLE raw_procedures AS
SELECT * FROM read_csv_auto('data/synthea/procedures.csv', header=True);
""")

# 5) Medications (raw)
con.execute("""
CREATE OR REPLACE TABLE raw_medications AS
SELECT * FROM read_csv_auto('data/synthea/medications.csv', header=True);
""")

# 6) Observations (raw)
con.execute("""
CREATE OR REPLACE TABLE raw_observations AS
SELECT * FROM read_csv_auto('data/synthea/observations.csv', header=True);
""")

print("✅ Raw tables created from CSVs: raw_*")

