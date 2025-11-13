# 3_ingestion/00_curate_giant_csvs.py
import os, duckdb, pathlib
from dotenv import load_dotenv
load_dotenv()

RAW_HOSP = r"D:/MedWhisper-Data Engineer/1_data/1_raw/1_mimic-iv-2.1/1_hosp"
ART = "1_data/artifacts"
pathlib.Path(ART).mkdir(parents=True, exist_ok=True)

SAMPLE_PCT = float(os.getenv("CURATE_SAMPLE_PCT", "1.0"))
print("[CURATOR] SAMPLE_PCT =", SAMPLE_PCT)

USE_SAMPLE = SAMPLE_PCT > 0 and SAMPLE_PCT < 1
sample_pred = f"WHERE random() < {SAMPLE_PCT}" if USE_SAMPLE else ""

con = duckdb.connect()
con.execute(f"PRAGMA threads={os.cpu_count()}")
con.execute("PRAGMA memory_limit='6GB'")

# ---- Read raw CSVs into DuckDB temp views ----
emar_detail_csv = f"{RAW_HOSP}/emar_detail.csv"
emar_csv        = f"{RAW_HOSP}/emar.csv"
lab_csv         = f"{RAW_HOSP}/labevents.csv"

con.execute(f"CREATE OR REPLACE TEMP VIEW emar_detail_v AS SELECT * FROM read_csv_auto('{emar_detail_csv}', union_by_name=TRUE, SAMPLE_SIZE=-1)")
con.execute(f"CREATE OR REPLACE TEMP VIEW emar_v        AS SELECT * FROM read_csv_auto('{emar_csv}', union_by_name=TRUE, SAMPLE_SIZE=-1)")
con.execute(f"CREATE OR REPLACE TEMP VIEW lab_v         AS SELECT * FROM read_csv_auto('{lab_csv}', union_by_name=TRUE, SAMPLE_SIZE=-1)")

# ---- Inspect emar_detail columns dynamically ----
cols = [r[1].lower() for r in con.execute("PRAGMA table_info('emar_detail_v')").fetchall()]

def exists(col):
    return any(col.lower() == c for c in cols)

# Safe column references (only include if present)
safe_parts = []
for name in ["field_name", "field_value", "value", "event_txt",
             "route", "dose", "dose_unit", "original_order_typ",
             "parent_field_ordinal", "label"]:
    if exists(name):
        safe_parts.append(f"COALESCE(CAST(emar_detail_v.{name} AS VARCHAR), '')")

detail_expr = " || ' | ' || ".join(safe_parts) if safe_parts else "''"

# ---- Curate emar_detail_curated.parquet ----
emar_out = f"{ART}/emar_detail_curated.parquet"
con.execute(f"""
COPY (
  SELECT
    emar_v.subject_id,
    emar_v.hadm_id,
    emar_detail_v.emar_id,
    {detail_expr} AS detail_text
  FROM emar_detail_v
  LEFT JOIN emar_v ON emar_detail_v.emar_id = emar_v.emar_id
  {sample_pred}
)
TO '{emar_out}' (FORMAT PARQUET, COMPRESSION ZSTD);
""")
print(f"✓ wrote {emar_out}")

# ---- Curate labevents_curated.parquet ----
lab_out = f"{ART}/labevents_curated.parquet"
lab_sample = ("AND random() < " + str(SAMPLE_PCT)) if USE_SAMPLE else ""
con.execute(f"""
COPY (
  SELECT
    subject_id,
    itemid,
    COALESCE(CAST(charttime AS VARCHAR), '') AS charttime,
    COALESCE(value, '') AS value,
    COALESCE(CAST(valuenum AS VARCHAR), '') AS valuenum,
    COALESCE(valueuom, '') AS valueuom,
    COALESCE(flag, '') AS flag
  FROM lab_v
  WHERE value IS NOT NULL OR valuenum IS NOT NULL OR flag IS NOT NULL
  {lab_sample}
)
TO '{lab_out}' (FORMAT PARQUET, COMPRESSION ZSTD);
""")
print(f"✓ wrote {lab_out}")
