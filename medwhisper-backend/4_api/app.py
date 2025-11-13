# 4_api/app.py
import os, json, duckdb
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "2_database/medwhisper.duckdb")
MODEL_NAME = os.getenv("MODEL_NAME", "pritamdeka/S-Biomed-Roberta-snli-multinli-stsb")

app = FastAPI(title="MedWhisper Search API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ---- model + DB ----
_model = None
def embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
        _model.max_seq_length = 256
    return _model

con = duckdb.connect(DB_PATH, read_only=False)
# Try to load VSS extension
_has_vss = True
try:
    con.execute("LOAD 'vss';")
except Exception:
    _has_vss = False

# ---- schemas ----
class Hit(BaseModel):
    doc_id: int
    score: float           # similarity: higher is better
    table_name: str
    source_path: Optional[str] = None
    meta: Any
    text_preview: str

class SearchResponse(BaseModel):
    query: str
    k: int
    vss: bool
    hits: List[Hit]

class SearchRequest(BaseModel):
    q: str
    top_k: int = 5
    table_filter: Optional[List[str]] = None
    meta_contains: Optional[Dict[str, str]] = None

# ---- helpers ----
def _encode_query(q: str):
    return embedder().encode([q], normalize_embeddings=True)[0].tolist()

def _json_load(m):
    if m is None: return None
    if isinstance(m, str):
        try:
            return json.loads(m)
        except Exception:
            return m
    return m

# ---- endpoints ----
@app.get("/health")
def health():
    try:
        docs = con.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        embs = con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    except Exception:
        docs = embs = -1
    return {"ok": True, "docs": docs, "embeddings": embs, "vss": _has_vss, "model": MODEL_NAME}

@app.get("/doc/{doc_id}")
def get_doc(doc_id: int):
    row = con.execute("""
        SELECT doc_id, table_name, source_path, meta, text
        FROM documents WHERE doc_id = ?
    """, [doc_id]).fetchone()
    if not row:
        raise HTTPException(404, "doc not found")
    return {
        "doc_id": int(row[0]),
        "table_name": row[1],
        "source_path": row[2],
        "meta": _json_load(row[3]),
        "text": row[4],
    }

@app.get("/search", response_model=SearchResponse)
def search_get(q: str = Query(..., min_length=2), k: int = 5):
    """
    Fast path using DuckDB VSS index (if available).
    Returns top-k hits with cosine similarity = 1 - distance.
    """
    qvec = _encode_query(q)
    if _has_vss:
        rows = con.execute(f"""
            SELECT r.id AS doc_id, (1 - r.distance) AS sim, d.table_name, d.source_path, d.meta, substr(d.text,1,500) AS text_preview
            FROM vss_search('vss_embeddings_idx', array{qvec}, top_k:={k}) AS r
            JOIN vss_lookup d ON d.doc_id = r.id
            ORDER BY r.distance ASC
        """).fetchall()
        hits = [
            Hit(
                doc_id=int(a),
                score=float(b),
                table_name=c,
                source_path=d,
                meta=_json_load(e),
                text_preview=f,
            )
            for (a,b,c,d,e,f) in rows
        ]
        return SearchResponse(query=q, k=k, vss=True, hits=hits)
    else:
        # Fallback to brute-force cosine if VSS is not present
        import numpy as np
        qv = np.array(qvec, dtype="float32")
        rows = con.execute("""
            SELECT e.doc_id, e.embedding, d.table_name, d.source_path, d.meta, substr(d.text,1,500) AS text_preview
            FROM embeddings e
            JOIN documents d ON d.doc_id = e.doc_id
        """).fetchall()
        hits = []
        for doc_id, emb, tbl, sp, meta, preview in rows:
            e = np.array(emb, dtype="float32")
            an, bn = np.linalg.norm(e), np.linalg.norm(qv)
            sim = float(e.dot(qv)/(an*bn)) if an > 0 and bn > 0 else 0.0
            hits.append((sim, int(doc_id), tbl, sp, _json_load(meta), preview))
        hits.sort(key=lambda x: x[0], reverse=True)
        top = hits[:k]
        return SearchResponse(
            query=q, k=k, vss=False,
            hits=[Hit(doc_id=h[1], score=h[0], table_name=h[2], source_path=h[3], meta=h[4], text_preview=h[5]) for h in top]
        )

@app.post("/search", response_model=SearchResponse)
def search_post(req: SearchRequest):
    """
    POST version with optional filters (table_filter, meta_contains).
    """
    q = req.q
    k = req.top_k
    qvec = _encode_query(q)

    where_clauses = []
    params: List[Any] = []

    if req.table_filter:
        ph = ",".join(["?"]*len(req.table_filter))
        where_clauses.append(f"d.table_name IN ({ph})")
        params.extend(req.table_filter)

    if req.meta_contains:
        for k_, v_ in req.meta_contains.items():
            where_clauses.append("CAST(d.meta AS VARCHAR) LIKE ?")
            params.append(f'%"{k_}":"{v_}"%')

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    if _has_vss:
        rows = con.execute(f"""
            WITH base AS (
              SELECT d.doc_id, d.table_name, d.source_path, d.meta, substr(d.text,1,500) AS text_preview
              FROM vss_lookup d
              {where_sql}
            )
            SELECT r.id AS doc_id, (1 - r.distance) AS sim, b.table_name, b.source_path, b.meta, b.text_preview
            FROM vss_search('vss_embeddings_idx', array{qvec}, top_k:={k}) r
            JOIN base b ON b.doc_id = r.id
            ORDER BY r.distance ASC
        """, params).fetchall()
        hits = [
            Hit(doc_id=int(a), score=float(b), table_name=c, source_path=d, meta=_json_load(e), text_preview=f)
            for (a,b,c,d,e,f) in rows
        ]
        return SearchResponse(query=q, k=k, vss=True, hits=hits)

    # fallback brute-force if no VSS
    import numpy as np
    qv = np.array(qvec, dtype="float32")
    rows = con.execute(f"""
        SELECT e.doc_id, e.embedding, d.table_name, d.source_path, d.meta, substr(d.text,1,500) AS text_preview
        FROM embeddings e
        JOIN documents d ON d.doc_id = e.doc_id
        {where_sql}
    """, params).fetchall()
    hits = []
    for doc_id, emb, tbl, sp, meta, preview in rows:
        e = np.array(emb, dtype="float32")
        an, bn = np.linalg.norm(e), np.linalg.norm(qv)
        sim = float(e.dot(qv)/(an*bn)) if an > 0 and bn > 0 else 0.0
        hits.append((sim, int(doc_id), tbl, sp, _json_load(meta), preview))
    hits.sort(key=lambda x: x[0], reverse=True)
    top = hits[:k]
    return SearchResponse(
        query=q, k=k, vss=False,
        hits=[Hit(doc_id=h[1], score=h[0], table_name=h[2], source_path=h[3], meta=h[4], text_preview=h[5]) for h in top]
    )
