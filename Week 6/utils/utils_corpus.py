from pathlib import Path
import shutil
import duckdb, pandas as pd

def get_docstore(db_path: str, corpus_sql: str, where_clause: str,
                 out_parquet: Path, prefer_existing: bool,
                 source_parquet: Path | None):
    """
    Returns DataFrame with [doc_id, text].

    Priority:
      1) If prefer_existing and source_parquet exists (Week-5 docstore), copy to out_parquet and load it.
      2) Else if out_parquet already exists, load it.
      3) Else build from SQL and save to out_parquet.
    """
    if prefer_existing and source_parquet and source_parquet.exists():
        out_parquet.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_parquet, out_parquet)

    if out_parquet.exists():
        return pd.read_parquet(out_parquet)

    con = duckdb.connect(db_path)
    q = corpus_sql.strip()
    if where_clause.strip():
        if where_clause.strip().lower().startswith("where"):
            q = f"SELECT * FROM ({q}) base {where_clause}"
        else:
            q = f"SELECT * FROM ({q}) base WHERE {where_clause}"
    df = con.execute(q).df()
    df = df.dropna(subset=["text"]).reset_index(drop=True)

    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_parquet, index=False)
    return df
