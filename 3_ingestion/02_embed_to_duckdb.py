import duckdb
from dotenv import load_dotenv
from tqdm import tqdm

from utils.duck import connect, ensure_base_tables
from utils.embedding import encode_texts

load_dotenv()
BATCH=1024

def main():
    con = connect()
    ensure_base_tables(con)

    rows = con.execute("""
        SELECT d.doc_id, d.text
        FROM documents d
        LEFT JOIN embeddings e ON e.doc_id = d.doc_id
        WHERE e.doc_id IS NULL
        ORDER BY d.doc_id
    """).fetchall()

    print(f"to embed: {len(rows)}")
    for i in tqdm(range(0, len(rows), BATCH), desc="Embedding"):
        batch = rows[i:i+BATCH]
        ids   = [r[0] for r in batch]
        texts = [r[1] for r in batch]
        vecs  = encode_texts(texts, batch_size=128, normalize=True)
        con.executemany("INSERT INTO embeddings(doc_id, embedding) VALUES (?, ?)",
                        [(int(i), v.tolist()) for i, v in zip(ids, vecs)])
        con.commit()

    print("done: embeddings")
    con.close()

if __name__ == "__main__":
    main()
