import os, pathlib, re

BASE = "1_data/1_raw/1_mimic-iv-2.1"
OUT = "2_database/4_staging_views.sql"

def to_ident(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

views=[]
for sub in ("1_hosp","2_icu"):
    folder=os.path.join(BASE,sub)
    for fn in sorted(os.listdir(folder)):
        if fn.endswith(".csv"):
            csv=os.path.join(folder,fn).replace("\\","/")
            name=f"stg_{to_ident(sub)}_{to_ident(fn[:-4])}"
            v=f"""CREATE OR REPLACE VIEW {name} AS
SELECT * FROM read_csv_auto('{csv}', header=True, sample_size=-1);"""
            views.append(v)

with open(OUT,"w",encoding="utf-8") as f:
    f.write("-- Auto-generated staging views for all CSVs\n\n")
    f.write(";\n".join(views)+";\n")

print(f"✅ Wrote {OUT} with {len(views)} views.")
