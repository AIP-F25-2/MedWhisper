import json, time, logging
from pathlib import Path
from datetime import datetime

import duckdb, pandas as pd, numpy as np, yaml
from tqdm import tqdm
from joblib import dump
from rank_bm25 import BM25Okapi
import faiss
from sentence_transformers import SentenceTransformer

from utils.utils_corpus import get_docstore

# ---- Load config ----
CFG_PATH = "configs/index_config.yaml"
with open(CFG_PATH, "r") as f:
    CFG = yaml.safe_load(f)

DB_PATH   = Path(CFG["db_path"])
INDEX_DIR = Path(CFG["index_dir"]); INDEX_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR   = Path(CFG["log_dir"]);   LOG_DIR.mkdir(parents=True, exist_ok=True)
METRICS_F = INDEX_DIR / CFG["metrics_file"]

# ---- Logging ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "index_build.log"), logging.StreamHandler()],
)
log = logging.getLogger("week6-build")

# ---- DocStore (reuse Week-5 if present, else build from SQL) ----
doc_parquet = INDEX_DIR / CFG["docstore"]["filename"]
source_parquet = Path(CFG["docstore"]["source_path"]) if CFG["docstore"]["source_path"] else None
log.info("Preparing DocStore...")
t0 = time.time()
doc_df = get_docstore(
    db_path=str(DB_PATH),
    corpus_sql=CFG.get("sql", {}).get("corpus_query", ""),
    where_clause=CFG.get("sql", {}).get("where", ""),
    out_parquet=doc_parquet,
    prefer_existing=bool(CFG["docstore"]["prefer_existing"]),
    source_parquet=source_parquet
)
doc_elapsed = time.time() - t0
doc_count = len(doc_df)
avg_doc_len = float(np.mean([len(str(t).split()) for t in doc_df["text"]])) if doc_count else 0.0
log.info(f"DocStore ready: {doc_count} docs | avg tokens ~ {avg_doc_len:.1f}")

# ---- Write DocStore into DuckDB (team-ready) ----
if CFG["duckdb"]["write_docstore"]:
    con = duckdb.connect(str(DB_PATH))
    t_doc = CFG["duckdb"]["tables"]["docstore"]
   
# Ensure doc_id column exists
if "doc_id" not in doc_df.columns:
    doc_df = doc_df.reset_index().rename(columns={"index": "doc_id"})

# Keep only relevant columns
if "text" in doc_df.columns:
    tmp_df = doc_df[["doc_id", "text"]]
else:
    raise ValueError("DocStore must have a 'text' column")

# Recreate table from the dataframe to ensure the correct schema
con.register("tmp_doc", tmp_df)
con.execute(f"DROP TABLE IF EXISTS {t_doc}")
con.execute(f"CREATE TABLE {t_doc} AS SELECT * FROM tmp_doc")
log.info(f"DuckDB: wrote {len(tmp_df)} rows into {t_doc}")


# ---- BM25 ----
bm25_enabled = bool(CFG["bm25"]["enabled"])
bm25_file = INDEX_DIR / CFG["bm25"]["filename"]
bm25_build_sec, bm25_vocab = 0.0, 0

if bm25_enabled:
    log.info("Building BM25...")
    tokenized = [str(t).lower().split() for t in doc_df["text"].tolist()]
    t0 = time.time()
    bm25_model = BM25Okapi(tokenized)
    bm25_build_sec = time.time() - t0
    bm25_vocab = len(set(tok for doc in tokenized for tok in doc))
    dump({"bm25": bm25_model, "doc_ids": doc_df["doc_id"].tolist()}, bm25_file)
    log.info(f"Saved BM25 -> {bm25_file} ({bm25_build_sec:.2f}s) | vocab~{bm25_vocab}")

# ---- FAISS ----
faiss_enabled = bool(CFG["faiss"]["enabled"])
faiss_file = INDEX_DIR / CFG["faiss"]["filename"]
faiss_build_sec, vector_dim, faiss_bytes = 0.0, 0, 0

if faiss_enabled:
    model_name = CFG["faiss"]["model_name"]
    bs         = int(CFG["faiss"]["batch_size"])
    normalize  = bool(CFG["faiss"]["normalize"])
    index_type = CFG["faiss"]["index_type"]

    log.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    vector_dim = model.get_sentence_embedding_dimension()

    log.info("Encoding documents for FAISS...")
    E = np.zeros((doc_count, vector_dim), dtype="float32")
    start = 0
    for i in tqdm(range(0, doc_count, bs)):
        chunk = doc_df["text"].iloc[i:i+bs].tolist()
        emb = model.encode(chunk, batch_size=bs, convert_to_numpy=True, show_progress_bar=False)
        E[start:start+len(emb)] = emb
        start += len(emb)

    if normalize:
        faiss.normalize_L2(E)

    index = faiss.IndexFlatIP(vector_dim) if index_type == "IndexFlatIP" else faiss.IndexFlatL2(vector_dim)
    t0 = time.time(); index.add(E); faiss_build_sec = time.time() - t0
    faiss.write_index(index, str(faiss_file)); faiss_bytes = faiss_file.stat().st_size
    log.info(f"Saved FAISS -> {faiss_file} ({faiss_build_sec:.2f}s, {faiss_bytes/1e6:.1f} MB)")

# ---- metrics.json ----
metrics = {
    "built_at": datetime.utcnow().isoformat() + "Z",
    "doc_count": doc_count,
    "avg_doc_len": round(avg_doc_len, 2),
    "artifacts": {
        "docstore_parquet": str(doc_parquet),
        "bm25_index": str(bm25_file) if bm25_enabled else None,
        "faiss_index": str(faiss_file) if faiss_enabled else None
    },
    "bm25": {
        "enabled": bm25_enabled,
        "build_seconds": round(bm25_build_sec, 3),
        "vocab_size_est": bm25_vocab,
        "bytes": (bm25_file.stat().st_size if bm25_enabled and bm25_file.exists() else 0)
    },
    "faiss": {
        "enabled": faiss_enabled,
        "model_name": (CFG["faiss"]["model_name"] if faiss_enabled else None),
        "index_type": (CFG["faiss"]["index_type"] if faiss_enabled else None),
        "vector_dim": vector_dim,
        "build_seconds": round(faiss_build_sec, 3),
        "bytes": faiss_bytes
    },
    "config": {
        "hybrid_alpha": CFG["validation"]["hybrid_alpha"],
        "topk": CFG["validation"]["topk"],
        "reuse_docstore_from_week5": bool(CFG["docstore"]["prefer_existing"])
    },
    "docstore_build_seconds": round(doc_elapsed, 3),
}
with open(METRICS_F, "w") as f:
    json.dump(metrics, f, indent=2)
log.info(f"Wrote metrics -> {METRICS_F}")

# ---- Write snapshot metadata into DuckDB ----
if CFG["duckdb"]["save_metadata"]:
    con = duckdb.connect(str(DB_PATH))
    t_meta = CFG["duckdb"]["tables"]["index_metadata"]
    con.execute(f"CREATE TABLE IF NOT EXISTS {t_meta} AS SELECT 1 AS _init WHERE FALSE")
    meta_df = pd.DataFrame([{
        "built_at": metrics["built_at"],
        "doc_count": metrics["doc_count"],
        "avg_doc_len": metrics["avg_doc_len"],
        "bm25_enabled": metrics["bm25"]["enabled"],
        "bm25_vocab_est": metrics["bm25"]["vocab_size_est"],
        "faiss_enabled": metrics["faiss"]["enabled"],
        "vector_dim": metrics["faiss"]["vector_dim"],
        "embedding_model": metrics["faiss"]["model_name"] or "",
        "faiss_path": metrics["artifacts"]["faiss_index"] or "",
        "bm25_path": metrics["artifacts"]["bm25_index"] or "",
        "faiss_bytes": metrics["faiss"]["bytes"] or 0
    }])
    con.register("tmp_meta", meta_df)
    con.execute(f"DROP TABLE IF EXISTS {t_meta}")
    con.execute(f"CREATE TABLE {t_meta} AS SELECT * FROM tmp_meta")

    log.info(f"DuckDB: wrote snapshot -> {t_meta}")

log.info(" Build complete.")
