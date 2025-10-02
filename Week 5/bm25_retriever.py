# Build and query a BM25 keyword index over the docstore created during the FAISS step.
import re
import argparse
import joblib
import pandas as pd
from typing import List
from rank_bm25 import BM25Okapi

def info(msg: str) -> None:
    print(f"[week5][bm25] {msg}", flush=True)

def tokenize(s: str) -> List[str]:
    # simple, robust tokenizer: lowercase alphanumerics
    return re.findall(r"[A-Za-z0-9]+", (s or "").lower())

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="Build a BM25 index from a docstore.parquet")
    b.add_argument("--docstore", required=True, help="Path to docstore.parquet")
    b.add_argument("--out", required=True, help="Where to save bm25_index.joblib")

    q = sub.add_parser("query", help="Query an existing BM25 index")
    q.add_argument("--index", required=True, help="Path to bm25_index.joblib")
    q.add_argument("--docstore", required=True, help="Path to docstore.parquet")
    q.add_argument("--q", required=True, help="Query string")
    q.add_argument("--k", type=int, default=5, help="Top-k results")

    args = ap.parse_args()

    if args.cmd == "build":
        df = pd.read_parquet(args.docstore)
        texts = df["text"].astype(str).tolist()
        bm25 = BM25Okapi([tokenize(t) for t in texts])
        joblib.dump({"bm25": bm25, "docstore": args.docstore}, args.out)
        info(f"BM25 saved → {args.out} (docs={len(texts)})")
    else:
        obj = joblib.load(args.index)
        bm25 = obj["bm25"]
        df = pd.read_parquet(args.docstore)
        scores = bm25.get_scores(tokenize(args.q))
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:args.k]
        for rank, i in enumerate(top_idx, 1):
            row = df.iloc[i]
            print(f"\n[{rank}] score={scores[i]:.3f} "
                  f"doc={row.get('source_doc_id','?')} chunk={row.get('chunk_id','?')}")
            print(str(row['text']).replace("\n", " ")[:400])

if __name__ == "__main__":
    main()
