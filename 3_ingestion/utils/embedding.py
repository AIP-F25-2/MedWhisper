import os, numpy as np
from typing import List
from sentence_transformers import SentenceTransformer

_model = None
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(os.getenv("MODEL_NAME","pritamdeka/S-Biomed-Roberta-snli-multinli-stsb"))
    return _model

def encode_texts(texts: List[str], batch_size: int = 128, normalize: bool = True) -> np.ndarray:
    m = get_model()
    vecs = m.encode(texts, batch_size=batch_size, show_progress_bar=True, normalize_embeddings=normalize)
    return np.asarray(vecs, dtype="float32")
