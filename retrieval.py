# week6_api/retrieval.py
import argparse
from .models import search_faiss, search_bm25, search_hybrid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["faiss","bm25","hybrid"], default="hybrid")
    ap.add_argument("--q", required=True)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    if args.engine == "faiss":
        rows = search_faiss(args.q, args.k)
    elif args.engine == "bm25":
        rows = search_bm25(args.q, args.k)
    else:
        rows = search_hybrid(args.q, args.k)

    for r in rows:
        fa = r.get("faiss", r.get("score", 0.0))
        bm = r.get("bm25",  r.get("score", 0.0))
        combo = r.get("combo", 0.0)
        print(f"\n[{r['rank']}] doc={r['doc_id']} chunk={r['chunk_id']} "
            f"faiss={fa:.4f} bm25={bm:.4f} combo={combo:.4f}")
        print(r["text"])


if __name__ == "__main__":
    main()
