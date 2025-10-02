# Blend FAISS semantic scores with BM25 keyword scores for better retrieval.
import re
import argparse
import joblib
import numpy as np
import pandas as pd
import faiss
from typing import List
from sentence_transformers import SentenceTransformer

def tokenize(s: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9]+", (s or "").lower())

def minmax_norm(x: np.ndarray) -> np.ndarray:
    if x.size == 0:
        return x
    mn, mx = float(np.min(x)), float(np.max(x))
    if mx - mn < 1e-9:
        return np.ones_like(x) if mx > 0 else np.zeros_like(x)
    return (x - mn) / (mx - mn)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True, help="Query")
    ap.add_argument("--k", type=int, default=5, help="Top-k results to show")
    ap.add_argument("--alpha", type=float, default=0.5, help="BM25 weight (0=FAISS only, 1=BM25 only)")
    ap.add_argument("--faiss", required=True, help="Path to faiss.index")
    ap.add_argument("--docstore", required=True, help="Path to docstore.parquet")
    ap.add_argument("--bm25", required=True, help="Path to bm25_index.joblib")
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2",
                    help="MUST MATCH the embeddings model used to build FAISS")
    ap.add_argument("--faiss_topn", type=int, default=30)
    ap.add_argument("--bm25_topn", type=int, default=30)
    args = ap.parse_args()

    # Load docstore
    ds = pd.read_parquet(args.docstore)

    # FAISS candidates
    index = faiss.read_index(args.faiss)
    model = SentenceTransformer(args.model)
    q_vec = model.encode([args.q], convert_to_numpy=True, normalize_embeddings=True)
    Df, If = index.search(q_vec, args.faiss_topn)  # cosine sim if normalized
    f_ids, f_scores = If[0], Df[0]

    # BM25 candidates
    obj = joblib.load(args.bm25)
    bm25 = obj["bm25"]
    all_scores = bm25.get_scores(tokenize(args.q))
    b_ids = np.argsort(-all_scores)[:args.bm25_topn]
    b_scores = all_scores[b_ids]

    # Merge IDs and compute blended score
    fdict = {int(i): float(s) for i, s in zip(f_ids.tolist(), f_scores.tolist())}
    bdict = {int(i): float(s) for i, s in zip(b_ids.tolist(), b_scores.tolist())}
    all_ids = sorted(set(fdict) | set(bdict))
    f_arr = np.array([fdict.get(i, 0.0) for i in all_ids], dtype=np.float32)
    b_arr = np.array([bdict.get(i, 0.0) for i in all_ids], dtype=np.float32)

    combo = (1.0 - args.alpha) * minmax_norm(f_arr) + args.alpha * minmax_norm(b_arr)
    order = np.argsort(-combo)[:args.k]

    print(f"\nQuery: {args.q}   alpha(BM25)={args.alpha}")
    for rank, oi in enumerate(order, 1):
        idx = all_ids[oi]
        row = ds.iloc[idx]
        print(f"\n[{rank}] doc={row.get('source_doc_id','?')} chunk={row.get('chunk_id','?')} "
              f"faiss={fdict.get(idx,0):.4f} bm25={bdict.get(idx,0):.4f} combo={combo[oi]:.4f}")
        print(str(row['text']).replace('\n',' ')[:400])

if __name__ == "__main__":
    main()
