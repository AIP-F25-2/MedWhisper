# Week-4: Database Setup & Workflow Finalisation

## Environment
- **Python**: 3.11 (installed from python.org, running inside VS Code terminal)  
- **DuckDB**: 1.4.0 (installed via `pip install duckdb pandas`)  
- **Editor/IDE**: Visual Studio Code  
- **Data Source**: Synthea sample CSVs (100 patients) 

## Pipeline Steps
1. Created folder structure under `MedWhisper/week4`.  
2. Applied `schema.sql` → defined base tables and unified `timeline_events` view.  
3. Loaded raw Synthea CSVs (`data/synthea/*.csv`) into DuckDB (`raw_*` tables).  
4. Built curated tables (`*_curated`) from raw tables and refreshed `timeline_events`.  
5. Verified row counts between raw and curated using `04_check_counts.py`.  
6. Exported curated tables to CSV under `data/exports/`.  
7. Ran sample queries (`06_sample_queries.py`) to get top conditions, medications, and timeline preview.  
8. Generated sample CSVs (`top_conditions.csv`, `top_medications.csv`, `timeline_preview.csv`) for easy review.  

## Row Counts
| Table            | Rows   |
|------------------|--------|
| patients         | 111    |
| encounters       | 5924   |
| conditions       | 4140   |
| procedures       | 17993  |
| medications      | 4926   |
| observations     | 88156  |
| timeline_events  | 124265 |


## Sample Queries & Insights
- **Top 5 Conditions**
  - Medication review due (892)  
  - Stress (330)  
  - Gingivitis (302)  
  - Full-time employment (300)  
  - Part-time employment (199)  

- **Top 5 Medications**
  - Hydrochlorothiazide 25 MG Oral Tablet (698)  
  - Insulin isophane human 70 UNIT/ML (527)  
  - Alendronic acid 10 MG Oral Tablet (523)  
  - Lisinopril 10 MG Oral Tablet (462)  
  - 24 HR Metformin hydrochloride 500 MG ER Oral Tablet (387)  

- **Timeline Preview (first 5 rows)**  
  Shows a mix of condition onset and encounters in chronological order:  
  - Chronic sinusitis (condition onset)  
  - Encounter for symptom (procedure)  
  - Encounter for problem (procedure)  
  - Well child visit (procedure)  

## Files Delivered
- **Database**
  - `medwhisper.db` → main DuckDB file (raw + curated tables + views)

- **SQL**
  - `sql/schema.sql` → base schema + timeline view

- **Scripts**
  - `01_apply_schema.py` → apply schema to DB  
  - `02_load_raw.py` → load raw Synthea CSVs → raw tables  
  - `03_build_curated.py` → build curated tables + timeline view  
  - `04_check_counts.py` → compare row counts raw vs curated  
  - `05_export_curated.py` → export curated tables to CSV  
  - `06_sample_queries.py` → run queries + export sample results  

- **Exports**
  - `patients.csv`  
  - `encounters.csv`  
  - `conditions.csv`  
  - `procedures.csv`  
  - `medications.csv`  
  - `observations.csv`  
  - `timeline_events.csv`  
  - `top_conditions.csv`  
  - `top_medications.csv`  
  - `timeline_preview.csv`  

## 📖 Usage Guide

Run the scripts step by step from the VS Code terminal.

1. Go into the Week 4 folder:
   ```bash
   cd "Week 4"
2. Run each script in order:
    python 01_apply_schema.py
    python 02_load_raw.py
    python 03_build_curated.py
    python 04_check_counts.py
    python 05_export_curated.py
    python 06_sample_queries.py

## How to Connect to DuckDB

The database file is medwhisper.db (created in Week 4).
You don’t open it directly — you connect to it with DuckDB in Python.

-- Example: 

import duckdb

# open in read-only mode for safety
con = duckdb.connect("medwhisper.db", read_only=True)

# list all tables
print(con.execute("SHOW TABLES").fetchall())

# preview 5 patients
print(con.execute("SELECT * FROM patients_curated LIMIT 5").fetchdf())



## Notes
- The curated schema ensures clean IDs, datatypes, and consistent patient history across all tables.  
- The unified `timeline_events` view merges conditions, encounters, medications, procedures, and observations into a single chronological view, simplifying downstream analytics and app integration.  
- Row counts between raw and curated tables match exactly, validating that no data was lost or duplicated during transformation.  
- Sample queries confirm dataset quality and highlight medically meaningful patterns (e.g., most frequent conditions and medications).  
- Exported CSVs make it easy for teammates to consume the curated data without needing to query the full DuckDB database.  
