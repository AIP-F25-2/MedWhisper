import os, pandas as pd

BASE = "1_data/1_raw/1_mimic-iv-2.1"
REPORT = "11_docs/dataset_summary.csv"

records = []

def profile_folder(subdir):
    folder = os.path.join(BASE, subdir)
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith(".csv"):
            continue
        path = os.path.join(folder, fn)
        # get just headers (fast, zero data rows)
        cols = list(pd.read_csv(path, nrows=0).columns)
        # count rows (header excluded)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            rows = sum(1 for _ in f) - 1

        records.append({
            "folder": subdir,
            "file": fn,
            "rows": rows,
            "columns_count": len(cols),
            "columns": "; ".join(cols)  # keep full, tidy in one cell
        })

for sub in ("1_hosp", "2_icu"):
    profile_folder(sub)

df = pd.DataFrame(records)
df.sort_values(["folder","file"], inplace=True)
df.reset_index(drop=True, inplace=True)
df.to_csv(REPORT, index=False)

print(f"✅ Wrote summary for {len(df)} CSVs to {REPORT}")
print(df[["folder","file","rows","columns_count"]].head(10))
