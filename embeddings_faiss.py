# Create text embeddings from DuckDB and build a FAISS index for semantic search.

import os, re, json, argparse
from typing import List, Tuple
import duckdb, pandas as pd, numpy as np
from sentence_transformers import SentenceTransformer
import faiss

def info(m): print(f"[week5][embeddings_faiss] {m}", flush=True)

def detect_notes(con, table=None, id_col=None, text_col=None) -> Tuple[str,str,str]:
    if table and id_col and text_col:
        cols = con.execute(
            f"select column_name from information_schema.columns where table_name='{table}'"
        ).fetchdf().column_name.tolist()
        if id_col in cols and text_col in cols:
            return table, id_col, text_col
        raise ValueError("Provided columns not found on the given table.")
    tables = con.execute(
        "select table_name from information_schema.tables where table_schema='main'"
    ).fetchdf().table_name.tolist()
    candidates = [t for t in tables if any(k in t.lower() for k in ["note","discharge","summary","report"])] or tables
    txt_keys = {"text","note","notes","description","content","report","observation","chart"}
    for t in candidates:
        cols = con.execute(
            f"select column_name,data_type from information_schema.columns where table_name='{t}'"
        ).fetchdf()
        varchar = cols[cols.data_type.str.contains("VARCHAR|TEXT", case=False, regex=True)].column_name.tolist()
        text_pick = None
        for c in cols.column_name.tolist():
            if c in varchar and (c.lower() in txt_keys or any(k in c.lower() for k in txt_keys)):
                text_pick = c; break
        if not text_pick and varchar:
            text_pick = varchar[0]
        if not text_pick:
            continue
        ids = [c for c in cols.column_name.tolist() if c.lower()=="id" or c.lower().endswith("_id")]
        id_pick = ids[0] if ids else cols.column_name.iloc[0]
        return t, id_pick, text_pick
    raise RuntimeError("Could not detect notes table; pass --table --id-col --text-col")

def chunk(text: str, size: int=220, overlap: int=40) -> List[str]:
    import re
    toks = re.findall(r"\S+", text or "")
    out, i = [], 0
    while i < len(toks):
        out.append(" ".join(toks[i:i+size]))
        i += max(1, size - overlap)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out-dir", default="week5/index")
    ap.add_argument("--table"); ap.add_argument("--id-col"); ap.add_argument("--text-col")
    ap.add_argument("--sql", help="Custom SQL returning: id, text")
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--chunk-size", type=int, default=220)
    ap.add_argument("--chunk-overlap", type=int, default=40)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--no-normalize", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    con = duckdb.connect(args.db, read_only=True)
    info(f"Connected to {args.db}")

    if args.sql:
        q = args.sql
    else:
        t, idc, txt = detect_notes(con, args.table, args.id_col, args.text_col)
        info(f"Using table={t} id={idc} text={txt}")
        q = f"select {idc} as id, {txt} as text from {t} where {txt} is not null"
    df_src = con.execute(q).fetchdf()
    info(f"Rows fetched: {len(df_src)}")

    rows = []
    for _, r in df_src.iterrows():
        for ci, ch in enumerate(chunk(r["text"], args.chunk_size, args.chunk_overlap)):
            if ch.strip():
                rows.append({"source_doc_id": r["id"], "chunk_id": ci, "text": ch})
    ds = pd.DataFrame(rows)
    if ds.empty: raise RuntimeError("No chunks produced.")
    ds.reset_index(drop=True, inplace=True)
    info(f"Chunks: {len(ds)}")

    model = SentenceTransformer(args.model); model.max_seq_length = 512
    embs = model.encode(ds["text"].tolist(), batch_size=args.batch_size,
                        convert_to_numpy=True, show_progress_bar=True,
                        normalize_embeddings=not args.no_normalize)
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim) if not args.no_normalize else faiss.IndexFlatL2(dim)
    index.add(embs)

    faiss_path = os.path.join(args.out_dir, "faiss.index")
    docstore = os.path.join(args.out_dir, "docstore.parquet")
    faiss.write_index(index, faiss_path)
    ds.assign(faiss_id=np.arange(len(ds))).to_parquet(docstore, index=False)

    with open(os.path.join(args.out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({
            "db": os.path.abspath(args.db),
            "sql": args.sql or q,
            "model": args.model,
            "normalize": not args.no_normalize,
            "chunk_size": args.chunk_size,
            "chunk_overlap": args.chunk_overlap,
            "embeddings_dim": int(dim),
            "faiss_index_path": os.path.abspath(faiss_path),
            "docstore_path": os.path.abspath(docstore)
        }, f, indent=2)
    info("Done")

if __name__ == "__main__":
    main()
