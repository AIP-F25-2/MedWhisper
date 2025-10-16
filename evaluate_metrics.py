# Week 6/utils/evaluate_metrics.py (robust, prints results)
import json, yaml, numpy as np
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]  # .../Week 6
CFG_GT       = BASE / "configs" / "ground_truth.yaml"
VAL_PARQ     = BASE / "index" / "RetrievalValidation.parquet"
METRICS_PATH = BASE / "index" / "metrics.json"
DUCK_DB      = BASE.parent / "Week 4" / "medwhisper.db"

# ---------- Load ground truth ----------
with open(CFG_GT, "r", encoding="utf-8") as f:
    gt_raw = yaml.safe_load(f) or {}
# expected shape:
# k: 5
# queries:
#   - id: sob_exertion
#     text: "shortness of breath after exertion"
#     relevant_source_doc_ids: ["cond_136", "cond_2267"]
queries = gt_raw.get("queries", []) if isinstance(gt_raw, dict) else []
K = int(gt_raw.get("k", 5)) if isinstance(gt_raw, dict) else 5

# Build ground-truth map: query text -> set of relevant doc ids (strings)
ground_truth = {}
for q in queries:
    text = (q or {}).get("text", "")
    rel = (q or {}).get("relevant_source_doc_ids", []) or []
    ground_truth[text] = set(str(x) for x in rel)

# ---------- Load validation results (parquet preferred; DuckDB fallback) ----------
try:
    if VAL_PARQ.exists():
        val_df = pd.read_parquet(VAL_PARQ)
    else:
        import duckdb
        con = duckdb.connect(str(DUCK_DB))
        val_df = con.execute("SELECT * FROM RetrievalValidation").fetchdf()
        VAL_PARQ.parent.mkdir(parents=True, exist_ok=True)
        val_df.to_parquet(VAL_PARQ)
except Exception as e:
    raise RuntimeError(
        f"Could not load validation data. Ensure either {VAL_PARQ} exists "
        f"or table RetrievalValidation is present in {DUCK_DB}. Original error: {e}"
    )

# ---------- Normalize column names ----------
val_df.columns = [c.lower() for c in val_df.columns]

# Derive standardized columns
def first_present(cols, candidates):
    for c in candidates:
        if c in cols:
            return c
    return None

q_col   = first_present(val_df.columns, ["query", "q"])
eng_col = first_present(val_df.columns, ["engine", "retriever", "method"])
rank_col= first_present(val_df.columns, ["rank", "rnk"])
doc_col = first_present(val_df.columns, ["doc_id", "source_doc_id", "doc", "id"])

needed = {"query": q_col, "engine": eng_col, "rank": rank_col, "doc_id": doc_col}
missing = [k for k, v in needed.items() if v is None]
if missing:
    raise ValueError(
        f"Validation data is missing required columns {missing}. "
        f"Found: {val_df.columns.tolist()}"
    )

# Keep just what we need
val_df = val_df[[q_col, eng_col, rank_col, doc_col]].copy()
val_df.columns = ["query", "engine", "rank", "doc_id"]

# Ensure rank is numeric and sort
val_df["rank"] = pd.to_numeric(val_df["rank"], errors="coerce").fillna(1e9).astype(int)
val_df = val_df.sort_values(["query", "engine", "rank"]).reset_index(drop=True)

# Trim to top-K if more were produced
val_df = val_df.groupby(["query", "engine"], as_index=False).head(K)

# ---------- Metric helpers ----------
def compute_scores(df: pd.DataFrame, gt_map: dict[str, set[str]]):
    scores = {"MRR": 0.0, "MAP": 0.0, "nDCG": 0.0}
    queries = list(gt_map.keys())
    n = max(len(queries), 1)
    df = df.drop_duplicates(subset=["query", "engine", "doc_id"])


    for q in queries:
        rel_docs = gt_map.get(q, set())
        if not rel_docs:
            continue
        q_docs = df[df["query"] == q].sort_values("rank")["doc_id"].astype(str).tolist()
        if not q_docs:
            continue

        # MRR
        rr = 0.0
        for r, d in enumerate(q_docs, 1):
            if d in rel_docs:
                rr = 1.0 / r
                break

        # MAP
        hits, prec_sum = 0, 0.0
        for r, d in enumerate(q_docs, 1):
            if d in rel_docs:
                hits += 1
                prec_sum += hits / r
        ap = prec_sum / max(len(rel_docs), 1)

        # nDCG (binary relevance)
        rel_vec = [1 if d in rel_docs else 0 for d in q_docs]
        dcg = sum((2**rel - 1) / np.log2(i + 2) for i, rel in enumerate(rel_vec))
        ideal_len = min(len(rel_docs), len(rel_vec))
        ideal = sum((2**1 - 1) / np.log2(i + 2) for i in range(ideal_len))
        ndcg = dcg / ideal if ideal > 0 else 0.0

        scores["MRR"] += rr
        scores["MAP"] += ap
        scores["nDCG"] += ndcg

    for k in scores:
        avg = scores[k] / max(len(queries), 1)
        scores[k] = round(min(avg, 1.0), 3)
    return scores

# ---------- Evaluate per engine ----------
results = []
for engine in sorted(val_df["engine"].unique()):
    eng_df = val_df[val_df["engine"] == engine]
    sc = compute_scores(eng_df, ground_truth)
    sc["engine"] = engine
    results.append(sc)
    print(f"{engine.upper()} => {sc}")

# ---------- Write back to metrics.json ----------
try:
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)
except FileNotFoundError:
    metrics = {}

for old in ("retrieval_metrics", "quality"):
    metrics.pop(old, None)

metrics["retrieval_metrics"] = results

with open(METRICS_PATH, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

print(f"\n✅ Retrieval metrics written to: {METRICS_PATH}")
