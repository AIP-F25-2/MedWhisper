import os, duckdb
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
DB_PATH = os.getenv("DB_PATH","2_database/medwhisper.duckdb")
MODEL  = os.getenv("MODEL_NAME","pritamdeka/S-Biomed-Roberta-snli-multinli-stsb")

app = FastAPI(title="MedWhisper Search API")
model = SentenceTransformer(MODEL)
con = duckdb.connect(DB_PATH)
con.execute("LOAD 'vss';")

class Hit(BaseModel):
    doc_id: int
    score: float
    table_name: str
    meta: str
    text: str

class SearchResponse(BaseModel):
    query: str
    k: int
    hits: List[Hit]

@app.get("/health")
def health(): return {"ok": True}

@app.get("/search", response_model=SearchResponse)
def search(q: str = Query(..., min_length=2), k: int = 5):
    qvec = model.encode([q], normalize_embeddings=True)[0].tolist()
    rows = con.execute(f"""
        SELECT r.id AS doc_id, r.distance AS score, d.table_name, d.meta, d.text
        FROM vss_search('vss_embeddings_idx', array{qvec}, top_k:={k}) r
        JOIN vss_lookup d ON d.doc_id = r.id
        ORDER BY r.distance ASC
    """).fetchall()
    hits = [Hit(doc_id=int(a), score=float(b), table_name=c, meta=d, text=e) for (a,b,c,d,e) in rows]
    return SearchResponse(query=q, k=k, hits=hits)
