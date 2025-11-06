import os, glob, json, time
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import yaml

from utils.duck import connect, ensure_base_tables
from utils.chunking import split_words, row_to_text

load_dotenv()
cfg = yaml.safe_load(open("3_ingestion/config/datasets.yaml","r",encoding="utf-8"))

RAW_ROOTS = [os.path.expandvars(os.path.expanduser(p)) for p in cfg.get("raw_roots",[])]
PATTERNS = cfg.get("include_patterns", ["**/*.csv","**/*.parquet","**/*.xlsx","**/*.xls"])
HINTS    = cfg.get("table_hints", {})

CHUNK_WORDS   = int(os.getenv("CHUNK_WORDS","200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP","40"))

def list_files():
    for root in RAW_ROOTS:
        for pat in PATTERNS:
            yield from glob.glob(str(Path(root)/pat), recursive=True)

def read_any(path: str):
    p = path.lower()
    # friendlier dtype backend for mixed columns
    if p.endswith(".csv") or p.endswith(".csv.gz") or p.endswith(".gz"):
        return pd.read_csv(path, dtype_backend="numpy_nullable", low_memory=False)
    if p.endswith(".parquet") or p.endswith(".pq"):
        return pd.read_parquet(path)
    if p.endswith(".xlsx") or p.endswith(".xls"):
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {path}")

def non_empty_str_cols(df: pd.DataFrame):
    out=[]
    for c in df.columns:
        try:
            if (pd.api.types.is_string_dtype(df[c]) or df[c].dtype==object):
                if df[c].dropna().astype(str).str.strip().ne("").any():
                    out.append(c)
        except Exception:
            pass
    return out

def sanitize_strings_only(df: pd.DataFrame) -> pd.DataFrame:
    """Fill NA only for string/object columns (avoid Arrow/int casting errors)."""
    str_cols = [c for c in df.columns if (pd.api.types.is_string_dtype(df[c]) or df[c].dtype==object)]
    if str_cols:
        df[str_cols] = df[str_cols].fillna("")
    return df

def iter_rows(df: pd.DataFrame, table: str, hint: dict):
    prefer = hint.get("prefer_text_cols") or []
    id_cols= hint.get("id_cols") or []
    df = sanitize_strings_only(df)
    for _, row in df.iterrows():
        d=row.to_dict()
        text = row_to_text(d, prefer_cols=prefer, max_cols=12)
        if not text.strip():
            continue
        meta = {k: d.get(k) for k in (id_cols[:3] if id_cols else [])}
        yield text, meta

def file_sig(path: Path):
    st = Path(path).stat()
    return int(st.st_size), int(st.st_mtime)

def ensure_manifest(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS ingest_manifest(
            source_path TEXT PRIMARY KEY,
            file_size   BIGINT,
            file_mtime  BIGINT,
            status      TEXT,          -- 'in_progress' | 'done'
            n_chunks    BIGINT,
            updated_at  TIMESTAMP
        );
    """)

def manifest_get(con, source_path):
    row = con.execute("SELECT file_size, file_mtime, status, n_chunks FROM ingest_manifest WHERE source_path = ?", [source_path]).fetchone()
    if row is None: return None
    return {"file_size": row[0], "file_mtime": row[1], "status": row[2], "n_chunks": row[3]}

def manifest_upsert(con, source_path, file_size, file_mtime, status, n_chunks=None):
    con.execute("""
        INSERT INTO ingest_manifest(source_path, file_size, file_mtime, status, n_chunks, updated_at)
        VALUES (?, ?, ?, ?, ?, now())
        ON CONFLICT (source_path) DO UPDATE SET
            file_size=excluded.file_size,
            file_mtime=excluded.file_mtime,
            status=excluded.status,
            n_chunks=excluded.n_chunks,
            updated_at=now();
    """, [source_path, file_size, file_mtime, status, n_chunks])

def clean_file(con, source_path):
    # delete embeddings for this file's chunks, then the chunks
    con.execute("""
        DELETE FROM embeddings
        WHERE doc_id IN (SELECT doc_id FROM documents WHERE source_path = ?);
    """, [source_path])
    con.execute("DELETE FROM documents WHERE source_path = ?", [source_path])
    con.commit()

def main():
    con = connect()
    ensure_base_tables(con)
    ensure_manifest(con)

    next_id = (con.execute("SELECT COALESCE(MAX(doc_id),0) FROM documents").fetchone()[0] or 0) + 1

    files = list(list_files())
    print(f"Found {len(files)} files")

    for path in tqdm(files, desc='Extracting'):
        source_path = str(Path(path))
        table = Path(path).stem
        hint  = dict(HINTS.get(table, {}))
        fsize, fmtime = file_sig(path)

        # --- resume/skip logic ---
        mrow = manifest_get(con, source_path)
        if mrow and mrow["status"] == "done" and mrow["file_size"] == fsize and mrow["file_mtime"] == fmtime:
            # already ingested and file unchanged -> skip
            continue

        # mark in progress and clean any partial prior data
        manifest_upsert(con, source_path, fsize, fmtime, status="in_progress", n_chunks=None)
        clean_file(con, source_path)

        # read file
        try:
            df = read_any(path)
        except Exception as e:
            # record failure and continue
            manifest_upsert(con, source_path, fsize, fmtime, status="in_progress", n_chunks=0)
            print(f"[SKIP] {path}: {e}")
            continue

        if not hint.get("prefer_text_cols"):
            hint["prefer_text_cols"] = non_empty_str_cols(df)[:8]
        if not hint.get("id_cols"):
            hint["id_cols"] = [c for c in df.columns if c.lower().endswith(("id","_id"))][:3]

        inserts=[]
        for text, meta in iter_rows(df, table, hint):
            for chunk in split_words(text, CHUNK_WORDS, CHUNK_OVERLAP):
                inserts.append( (next_id, table, source_path, json.dumps(meta), chunk) )
                next_id += 1

            # write in micro-batches to keep memory bounded
            if len(inserts) >= 50_000:
                con.executemany(
                    "INSERT INTO documents(doc_id, table_name, source_path, meta, text) VALUES (?,?,?,?,?)",
                    inserts
                )
                con.commit()
                inserts.clear()

        if inserts:
            con.executemany(
                "INSERT INTO documents(doc_id, table_name, source_path, meta, text) VALUES (?,?,?,?,?)",
                inserts
            )
            con.commit()

        # finalize manifest
        n_chunks = con.execute("SELECT COUNT(*) FROM documents WHERE source_path = ?", [source_path]).fetchone()[0]
        manifest_upsert(con, source_path, fsize, fmtime, status="done", n_chunks=n_chunks)
        con.commit()

    print("done: documents")
    con.close()

if __name__ == "__main__":
    main()
