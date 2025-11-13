# 3_ingestion/02_embed_to_duckdb.py
import os
from typing import List, Tuple
import duckdb
import numpy as np
from tqdm import tqdm

from utils.embedding import encode_texts

DB_PATH     = os.getenv("DB_PATH", "2_database/medwhisper.duckdb")
EMBED_BATCH = int(os.getenv("EMBED_BATCH", "64"))      # model batch size
FETCH_BATCH = int(os.getenv("FETCH_BATCH", "5000"))    # how many doc_ids to fetch from DB per page


def has_embed_queue(con) -> bool:
    """Check if embed_queue table exists."""
    return con.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = 'embed_queue'
    """).fetchone()[0] > 0


def fetch_pending_count(con) -> int:
    """
    Count how many docs still need embeddings.
    If embed_queue exists → only count docs in queue.
    Otherwise → count all docs.
    """
    if has_embed_queue(con):
        return con.execute("""
            SELECT COUNT(*)
            FROM documents d
            JOIN embed_queue q ON q.doc_id = d.doc_id
            LEFT JOIN embeddings e ON e.doc_id = d.doc_id
            WHERE e.doc_id IS NULL
        """).fetchone()[0]
    else:
        return con.execute("""
            SELECT COUNT(*)
            FROM documents d
            LEFT JOIN embeddings e ON e.doc_id = d.doc_id
            WHERE e.doc_id IS NULL
        """).fetchone()[0]


def fetch_next_ids(con, after_doc_id: int, limit: int) -> List[int]:
    """
    Get the next batch of doc_ids that still need embeddings.
    If embed_queue exists → restrict to queue.
    """
    if has_embed_queue(con):
        rows = con.execute("""
            SELECT d.doc_id
            FROM documents d
            JOIN embed_queue q ON q.doc_id = d.doc_id
            LEFT JOIN embeddings e ON e.doc_id = d.doc_id
            WHERE e.doc_id IS NULL
              AND d.doc_id > ?
            ORDER BY d.doc_id
            LIMIT ?
        """, [after_doc_id, limit]).fetchall()
    else:
        rows = con.execute("""
            SELECT d.doc_id
            FROM documents d
            LEFT JOIN embeddings e ON e.doc_id = d.doc_id
            WHERE e.doc_id IS NULL
              AND d.doc_id > ?
            ORDER BY d.doc_id
            LIMIT ?
        """, [after_doc_id, limit]).fetchall()

    return [r[0] for r in rows]


def fetch_texts(con, ids: List[int]) -> List[Tuple[int, str]]:
    if not ids:
        return []
    ph = ",".join(["?"] * len(ids))
    rows = con.execute(
        f"SELECT doc_id, text FROM documents WHERE doc_id IN ({ph}) ORDER BY doc_id",
        ids
    ).fetchall()
    return [(int(r[0]), r[1]) for r in rows]


def insert_embeddings(con, rows: List[Tuple[int, np.ndarray]]) -> None:
    if not rows:
        return
    try:
        con.executemany(
            "INSERT INTO embeddings (doc_id, embedding) VALUES (?, ?)",
            [(doc_id, vec.tolist()) for (doc_id, vec) in rows]
        )
    except Exception:
        con.executemany(
            "INSERT INTO embeddings (doc_id, embedding) VALUES (?, to_vector(?))",
            [(doc_id, vec.tolist()) for (doc_id, vec) in rows]
        )
    con.commit()


def main():
    con = duckdb.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS embeddings(
          doc_id BIGINT PRIMARY KEY,
          embedding FLOAT[]
        );
    """)

    use_queue = has_embed_queue(con)
    print(f"[INFO] embed_queue present: {use_queue}")

    total_pending = fetch_pending_count(con)
    if total_pending == 0:
        print("Nothing to embed. ✓")
        con.close()
        return

    print(f"to embed: {total_pending}")
    pbar = tqdm(total=total_pending, desc="Embedding", unit="chunk", dynamic_ncols=True)

    last_id = -1
    try:
        while True:
            ids = fetch_next_ids(con, last_id, FETCH_BATCH)
            if not ids:
                break

            texts_rows = fetch_texts(con, ids)
            i = 0
            while i < len(texts_rows):
                batch_rows = texts_rows[i:i+EMBED_BATCH]
                doc_ids = [r[0] for r in batch_rows]
                texts   = [r[1] or "" for r in batch_rows]

                vecs = encode_texts(texts, batch_size=EMBED_BATCH, normalize=True)
                vec_rows = list(zip(doc_ids, vecs))
                insert_embeddings(con, vec_rows)

                pbar.update(len(batch_rows))
                i += EMBED_BATCH

            last_id = ids[-1]
    except KeyboardInterrupt:
        print("\nInterrupted by user. Progress saved up to last committed batch.")
    finally:
        pbar.close()
        left = fetch_pending_count(con)
        print({"pending_to_embed": left})
        con.close()
        print("done: embeddings" if left == 0 else "partial: embeddings")


if __name__ == "__main__":
    main()
