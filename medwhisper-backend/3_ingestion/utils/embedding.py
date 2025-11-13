# 3_ingestion/utils/embedding.py
import os
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

_model = None

def get_model() -> SentenceTransformer:
    """
    Lazily load and cache the SentenceTransformer model.
    Uses MODEL_NAME from .env, or a default biomedical model.
    """
    global _model
    if _model is None:
        model_name = os.getenv("MODEL_NAME", "pritamdeka/S-Biomed-Roberta-snli-multinli-stsb")
        print(f"[INFO] Loading embedding model: {model_name}")
        _model = SentenceTransformer(model_name)
        # optional: limit max length a bit to save memory
        try:
            _model.max_seq_length = 256
        except Exception:
            pass
    return _model

def encode_texts(
    texts: List[str],
    batch_size: int = 128,
    normalize: bool = True,
) -> np.ndarray:
    """
    Encode a list of texts into float32 numpy array [N, D].

    NOTE: We **do not** pass unsupported kwargs like num_workers.
    This keeps it compatible with older sentence-transformers versions.
    """
    model = get_model()

    # Ensure list of strings
    safe_texts = [t if isinstance(t, str) else "" for t in texts]

    # SentenceTransformer.encode will:
    # - handle batching internally
    # - return a numpy array when convert_to_numpy=True
    embeddings = model.encode(
        safe_texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=normalize,
        convert_to_numpy=True,   # crucial: direct numpy
    )

    # Make sure dtype is float32 to save space
    return embeddings.astype("float32")
