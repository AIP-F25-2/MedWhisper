import duckdb
con = duckdb.connect("2_database/1_medwhisper.duckdb")

print("\nTables in DB:")
print(con.execute("SHOW TABLES").fetchdf())

for t in ["patients","admissions","diagnoses_icd","procedures_icd",
          "prescriptions","labevents","d_labitems","d_icd_diagnoses",
          "d_icd_procedures","d_hcpcs","services","transfers","drgcodes","icustays"]:
    print(f"\n--- {t} ---")
    print(con.execute(f"PRAGMA table_info('{t}')").fetchdf())
