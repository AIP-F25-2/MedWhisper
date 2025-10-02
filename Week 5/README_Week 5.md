# Week-5: Retrieval Setup (FAISS + BM25 + Hybrid)

In **Week-4**, I created and curated the DuckDB database (`medwhisper.db`).  
In **Week-5**, I built a **retrieval layer** so that we can search and extract useful information from the database efficiently.  

This retrieval layer is very important because:
- Doctors/patients might use **different words** for the same thing.  
  - Example: “high blood pressure” vs “hypertension”  
- Sometimes we need **exact keyword matches**.  
  - Example: “120 mmHg” should exactly match in blood pressure readings.  
- To handle both, I created **three retrieval methods**:  
  1. **FAISS (semantic)** → understands meaning/synonyms.  
  2. **BM25 (keyword)** → exact keyword match.  
  3. **Hybrid (FAISS + BM25)** → combines both.

---

## ⚙️ Environment Setup

I set up a clean Python environment so that there are no conflicts with Week-4.

### 1. Create and activate virtual environment:

   python -m venv .venv
   .\.venv\Scripts\activate.bat   # activate in Windows CMD

### 2. Install required libraries:

   
    python -m pip install --upgrade pip
    pip install "numpy<2.0" duckdb==1.0.0 pandas==2.2.2 pyarrow==17.0.0 joblib==1.4.2
    pip install sentence-transformers==2.7.0
    pip install faiss-cpu==1.8.0.post1
    pip install rank-bm25==0.2.2

### 3. Verify installation:
    
    python -c "import numpy, duckdb, pandas, pyarrow, joblib; print('Core OK')"
    python -c "import faiss; print('FAISS OK')"
    python -c "from rank_bm25 import BM25Okapi; from sentence_transformers import SentenceTransformer; print('Retrieval libs OK')"
    
#### Output:
    Core OK
    FAISS OK
    Retrieval libs OK
✅ Now the environment is ready for retrieval setup

## 📂 Folder Structure 

MedWhisper/
├── Week 4/
│   └── medwhisper.db           # Database built in Week-4
│
├── Week 5/
│   ├── embeddings_faiss.py     # Builds FAISS semantic index
│   ├── bm25_retriever.py       # Builds and queries BM25 index
│   ├── hybrid_retriever.py     # Combines FAISS + BM25 for hybrid search
│   ├── index/                  # Folder for generated indexes
│   │   ├── faiss.index
│   │   ├── docstore.parquet
│   │   ├── manifest.json
│   │   └── bm25_index.joblib
│   └── README_Week5.md

## 🛠️ Step 1: Build Semantic Index (FAISS)

#### Why?
FAISS lets us search by meaning instead of only keywords.
This is useful when queries use synonyms or related terms.

#### What I did:

Took data from observations_curated table.

Combined columns: code, description, value, unit → into one text string.

Generated embeddings using SentenceTransformers (all-MiniLM-L6-v2).

Stored vectors in faiss.index.

Saved text mapping in docstore.parquet.

#### Command:
python ".\Week 5\embeddings_faiss.py" \
  --db ".\Week 4\medwhisper.db" \
  --out-dir ".\Week 5\index" \
  --sql "SELECT observation_id AS id, CONCAT_WS(' ', COALESCE(code,''), COALESCE(description,''), COALESCE(CAST(value AS VARCHAR),''), COALESCE(unit,'')) AS text FROM observations_curated WHERE code IS NOT NULL OR description IS NOT NULL OR value IS NOT NULL OR unit IS NOT NULL"

#### Output:
[week5][embeddings_faiss] Connected to .\Week 4\medwhisper.db
[week5][embeddings_faiss] Rows fetched: 88156
[week5][embeddings_faiss] Chunks: 88156
Batches: 100%
[week5][embeddings_faiss] Done

#### Files produced:
- faiss.index → stores embeddings (semantic vectors).

- docstore.parquet → maps IDs to text chunks.

- manifest.json → info about the index.

✅ Semantic search is ready.

## 🛠️ Step 2: Build Keyword Index (BM25)

#### Why?
BM25 is good when we need exact matches.
For example, “120 mmHg” should be found exactly, not just semantically.

#### What I did:

Loaded text chunks from docstore.parquet.

Created BM25 keyword index.

Saved it as bm25_index.joblib.

#### Build Command:
python ".\Week 5\bm25_retriever.py" build \
  --docstore ".\Week 5\index\docstore.parquet" \
  --out ".\Week 5\index\bm25_index.joblib"

#### Query Example (blood pressure):
python ".\Week 5\bm25_retriever.py" query \
  --index ".\Week 5\index\bm25_index.joblib" \
  --docstore ".\Week 5\index\docstore.parquet" \
  -q "blood pressure" --k 5

#### Output:
- [1] score=5.437 doc=obs_6   Diastolic Blood Pressure 78.0 mm[Hg]
- [2] score=5.437 doc=obs_7   Systolic Blood Pressure 143.0 mm[Hg]
- [3] score=5.437 doc=obs_41  Diastolic Blood Pressure 78.0 mm[Hg]
- [4] score=5.437 doc=obs_42  Systolic Blood Pressure 123.0 mm[Hg]
- [5] score=5.437 doc=obs_88  Diastolic Blood Pressure 76.0 mm[Hg]

✅ Keyword search is ready.

## 🛠️ Step 3: Hybrid Retrieval (FAISS + BM25)

#### Why?
Neither semantic nor keyword alone is perfect:

- FAISS can understand synonyms but might miss exact keywords.

- BM25 finds exact terms but can’t handle meaning.

**Solution**: Combine both with a parameter alpha.

alpha = 0.0 → only FAISS

alpha = 1.0 → only BM25

alpha = 0.5 → equal weight (hybrid)

#### Command (example with alpha=0.5):
python ".\Week 5\hybrid_retriever.py" \
  -q "high blood pressure" --k 5 --alpha 0.5 \
  --faiss ".\Week 5\index\faiss.index" \
  --docstore ".\Week 5\index\docstore.parquet" \
  --bm25 ".\Week 5\index\bm25_index.joblib"
#### Output:
- Query: high blood pressure   alpha(BM25)=0.5

[1] doc=obs_79119  faiss=0.6033 bm25=5.4370 combo=1.0000
     8480-6 Systolic Blood Pressure 103.0 mm[Hg]

[2] doc=obs_26297  faiss=0.0000 bm25=5.4370 combo=0.5000
     8462-4 Diastolic Blood Pressure 68.0 mm[Hg]
✅ Hybrid retrieval is ready.

#### 📊 Observations:

FAISS → good for semantic matches (finds related meaning).

BM25 → good for exact keyword matches.

Hybrid → balances both and gives the best overall results

### 📂 Files Delivered

These are the files I produced in Week-5:

**Scripts (my code):**

embeddings_faiss.py → builds FAISS semantic index.

bm25_retriever.py → builds BM25 keyword index and runs queries.

hybrid_retriever.py → combines FAISS + BM25 into one retrieval method.

**Indexes (generated output):***

faiss.index → FAISS semantic vectors for observations.

docstore.parquet → maps IDs → actual text chunks.

manifest.json → stores index metadata.

bm25_index.joblib → BM25 keyword index.

