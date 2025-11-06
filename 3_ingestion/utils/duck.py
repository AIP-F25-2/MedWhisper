import os, duckdb
from pathlib import Path

def connect():
    db_path = os.getenv("DB_PATH", "2_database/medwhisper.duckdb")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(db_path)
    con.execute("INSTALL json; LOAD json;")
    con.execute("INSTALL vss;")
    return con

def ensure_base_tables(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id     BIGINT PRIMARY KEY,
            table_name TEXT,
            source_path TEXT,
            meta       JSON,
            text       TEXT
        );
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            doc_id   BIGINT,
            embedding FLOAT[768]
        );
    """)
