import os, glob, json, time
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import yaml
import warnings

from utils.duck import connect, ensure_base_tables
from utils.chunking import split_words, row_to_text
import pyarrow as pa
import pyarrow.parquet as pq


# silence mixed-type dtype warnings (safe for our text-only use)
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

load_dotenv()
cfg = yaml.safe_load(open("3_ingestion/config/datasets.yaml", "r", encoding="utf-8"))

RAW_ROOTS = [os.path.expandvars(os.path.expanduser(p)) for p in cfg.get("raw_roots", [])]
PATTERNS = cfg.get("include_patterns", ["**/*.csv", "**/*.parquet", "**/*.xlsx", "**/*.xls", "**/*.csv.gz"])
HINTS    = cfg.get("table_hints", {})

CHUNK_WORDS   = int(os.getenv("CHUNK_WORDS", "200"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "40"))

# tune via .env for quicker visible progress if desired
CSV_CHUNKSIZE = int(os.getenv("CSV_CHUNKSIZE", "200000"))  # rows per pandas read_csv chunk
INSERT_BATCH  = int(os.getenv("INSERT_BATCH", "50000"))    # rows per DuckDB insert batch

def list_files():
    for root in RAW_ROOTS:
        for pat in PATTERNS:
            yield from glob.glob(str(Path(root) / pat), recursive=True)

def non_empty_str_cols(df: pd.DataFrame):
    out = []
    for c in df.columns:
        try:
            if (pd.api.types.is_string_dtype(df[c]) or df[c].dtype == object):
                if df[c].dropna().astype(str).str.strip().ne("").any():
                    out.append(c)
        except Exception:
            pass
    return out

def sanitize_strings_only(df: pd.DataFrame) -> pd.DataFrame:
    str_cols = [c for c in df.columns if (pd.api.types.is_string_dtype(df[c]) or df[c].dtype == object)]
    if str_cols:
        df[str_cols] = df[str_cols].fillna("")
    return df

def iter_rows(df: pd.DataFrame, table: str, hint: dict):
    prefer  = hint.get("prefer_text_cols") or []
    id_cols = hint.get("id_cols") or []
    df = sanitize_strings_only(df)
    for _, row in df.iterrows():
        d    = row.to_dict()
        text = row_to_text(d, prefer_cols=prefer, max_cols=12)
        if not text.strip():
            continue
        meta = {k: d.get(k) for k in (id_cols[:3] if id_cols else [])}
        yield text, meta

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
    row = con.execute(
        "SELECT file_size, file_mtime, status, n_chunks FROM ingest_manifest WHERE source_path = ?",
        [source_path]
    ).fetchone()
    if row is None:
        return None
    return {"file_size": row[0], "file_mtime": row[1], "status": row[2], "n_chunks": row[3]}

def manifest_upsert(con, source_path, file_size, file_mtime, status, n_chunks=None):
    con.execute("""
        INSERT INTO ingest_manifest(source_path, file_size, file_mtime, status, n_chunks, updated_at)
        VALUES (?, ?, ?, ?, ?, now())
        ON CONFLICT (source_path) DO UPDATE SET
            file_size   = excluded.file_size,
            file_mtime  = excluded.file_mtime,
            status      = excluded.status,
            n_chunks    = excluded.n_chunks,
            updated_at  = now();
    """, [source_path, file_size, file_mtime, status, n_chunks])

def clean_file(con, source_path):
    con.execute("""
        DELETE FROM embeddings
        WHERE doc_id IN (SELECT doc_id FROM documents WHERE source_path = ?);
    """, [source_path])
    con.execute("DELETE FROM documents WHERE source_path = ?", [source_path])
    con.commit()

def csv_chunk_reader(path: str):
    """
    Stream CSV in chunks. Try fast C engine first; if it errors (OOM/tokenizing),
    fall back to Python engine. Do NOT pass low_memory with engine='python'.
    """
    try:
        return pd.read_csv(
            path,
            chunksize=CSV_CHUNKSIZE,
            dtype_backend="numpy_nullable",
            on_bad_lines="skip",
            engine="c"
        )
    except Exception:
        return pd.read_csv(
            path,
            chunksize=CSV_CHUNKSIZE,
            dtype_backend="numpy_nullable",
            on_bad_lines="skip",
            engine="python"
        )
def parquet_chunk_reader(path: str, rows_per_batch: int = None):
    if rows_per_batch is None:
        rows_per_batch = int(os.getenv("PARQUET_BATCH_ROWS", "200000"))
    pf = pq.ParquetFile(path)
    for rg in range(pf.num_row_groups):
        table = pf.read_row_group(rg)
        for batch in table.to_batches(max_chunksize=rows_per_batch):
            yield pa.Table.from_batches([batch]).to_pandas()

def read_any_iter(path: str):
    p = path.lower()
    if p.endswith(".csv") or p.endswith(".csv.gz") or p.endswith(".gz"):
        return csv_chunk_reader(path)
    if p.endswith(".parquet") or p.endswith(".pq"):
        return parquet_chunk_reader(path)
    if p.endswith(".xlsx") or p.endswith(".xls"):
        return [pd.read_excel(path)]
    raise ValueError(f"Unsupported file type: {path}")


def file_sig(path: Path):
    st = Path(path).stat()
    return int(st.st_size), int(st.st_mtime)

def main():
    con = connect()
    ensure_base_tables(con)
    ensure_manifest(con)

    next_id = (con.execute("SELECT COALESCE(MAX(doc_id),0) FROM documents").fetchone()[0] or 0) + 1

    files = list(list_files())
    print(f"Found {len(files)} files")

    # Per-file loop with explicit prints so you see progress even before tqdm updates totals
    for idx, path in enumerate(files, 1):
        source_path = str(Path(path))
        table = Path(path).stem
        hint  = dict(HINTS.get(table, {}))
        fsize, fmtime = file_sig(path)

        print(f"[{idx}/{len(files)}] Processing: {source_path}", flush=True)

        # Skip already-done & unchanged files
        mrow = manifest_get(con, source_path)
        if mrow and mrow["status"] == "done" and mrow["file_size"] == fsize and mrow["file_mtime"] == fmtime:
            print("  ↪ already done, skipping\n", flush=True)
            continue

        manifest_upsert(con, source_path, fsize, fmtime, status="in_progress", n_chunks=None)
        clean_file(con, source_path)

        inserts = []
        total_chunks_for_file = 0

        try:
            chunk_iter = read_any_iter(path)
        except Exception as e:
            manifest_upsert(con, source_path, fsize, fmtime, status="in_progress", n_chunks=0)
            print(f"  [SKIP] {path}: {e}\n", flush=True)
            continue

        # show per-chunk activity (no fixed total available → leave=False keeps the console clean)
        for df in tqdm(chunk_iter, desc=f"  chunks for {Path(path).name}", leave=False):
            if not hint.get("prefer_text_cols"):
                hint["prefer_text_cols"] = non_empty_str_cols(df)[:8]
            if not hint.get("id_cols"):
                hint["id_cols"] = [c for c in df.columns if c.lower().endswith(("id", "_id"))][:3]

            for text, meta in iter_rows(df, table, hint):
                for chunk in split_words(text, CHUNK_WORDS, CHUNK_OVERLAP):
                    inserts.append((next_id, table, source_path, json.dumps(meta), chunk))
                    next_id += 1
                    total_chunks_for_file += 1

                if len(inserts) >= INSERT_BATCH:
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

        manifest_upsert(con, source_path, fsize, fmtime, status="done", n_chunks=total_chunks_for_file)
        con.commit()
        print(f"  ✓ done: {total_chunks_for_file} chunks\n", flush=True)

    print("done: documents")
    con.close()

if __name__ == "__main__":
    main()
