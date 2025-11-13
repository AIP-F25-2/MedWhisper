from typing import List

def split_words(text: str, chunk_words: int, overlap: int) -> List[str]:
    if not text:
        return []
    words = text.split()
    if not words:
        return []
    chunks, i = [], 0
    step = max(1, chunk_words - overlap)
    while i < len(words):
        chunks.append(" ".join(words[i:i+chunk_words]))
        if i + chunk_words >= len(words): break
        i += step
    return chunks

def row_to_text(row, prefer_cols=None, max_cols=12):
    prefer_cols = prefer_cols or []
    pieces = []
    for c in prefer_cols:
        if c in row and isinstance(row[c], str) and row[c].strip():
            pieces.append(f"{c}: {row[c]}")
    for c, v in row.items():
        if c in prefer_cols: 
            continue
        try:
            if isinstance(v, str) and v.strip():
                pieces.append(f"{c}: {v}")
        except Exception:
            pass
        if len(pieces) >= max_cols:
            break
    return "\n".join(pieces)
