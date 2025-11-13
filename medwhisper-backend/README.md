# MedWhisper Backend (DuckDB + Vectors + FastAPI)

## How to run
pip install -r requirements.txt
python 3_ingestion/01_extract_text.py
python 3_ingestion/02_embed_to_duckdb.py
duckdb -init 3_ingestion/03_build_vss_index.sql 2_database/medwhisper.duckdb
uvicorn 4_api.app:app --reload --port 8000

GET http://localhost:8000/search?q=insulin dose&k=5
