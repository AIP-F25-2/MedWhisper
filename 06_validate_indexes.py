import os, json, argparse, faiss, joblib, pandas as pd, yaml

def ok(msg): print(f"[OK] {msg}")
def bad(msg): print(f"[FAIL] {msg}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    faiss_path = cfg["faiss"]["index_path"]
    bm25_path  = cfg["bm25"]["index_path"]
    ds_path    = cfg["docstore"]["path"]

    assert os.path.exists(faiss_path), f"Missing: {faiss_path}"
    assert os.path.exists(bm25_path),  f"Missing: {bm25_path}"
    assert os.path.exists(ds_path),    f"Missing: {ds_path}"

    ds = pd.read_parquet(ds_path)
    ok(f"Docstore loaded: rows={len(ds)}, cols={list(ds.columns)}")

    index = faiss.read_index(faiss_path)
    ok(f"FAISS index loaded: ntotal={index.ntotal}")

    obj = joblib.load(bm25_path)
    assert "bm25" in obj, "Invalid bm25_index.joblib"
    ok("BM25 joblib looks OK")

    print("\n✅ Validation complete!")

if __name__ == "__main__":
    main()
