
import re, joblib, pandas as pd, yaml
from pathlib import Path
from rank_bm25 import BM25Okapi

def tok(s: str):
    return re.findall(r"[A-Za-z0-9]+", (s or "").lower())

cfg = yaml.safe_load(open("Week 6/configs/index_config.yaml", "r", encoding="utf-8"))
ds_path = Path(cfg["docstore"]["path"])
bm25_path = Path(cfg["bm25"]["index_path"])

ds = pd.read_parquet(ds_path)  # expects column 'text' (+ optional 'source_doc_id')
corpus_tokens = [tok(t) for t in ds["text"].astype(str).tolist()]
bm25 = BM25Okapi(corpus_tokens)

payload = {
    "bm25": bm25,
    "corpus_size": len(corpus_tokens),
    "doc_ids": ds.get("source_doc_id", pd.Series(range(len(ds)))).astype(str).tolist(),
}

bm25_path.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(payload, bm25_path)
print(f"✅ Saved BM25 with metadata to {bm25_path}")
