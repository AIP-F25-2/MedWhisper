import os
import io
import json
from typing import Dict, Any, List

import numpy as np
from PIL import Image

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from tensorflow.keras.models import load_model
from groq import Groq


# =========================
# CONFIG
# =========================

MODEL_DIR = "models"              # folder with all .h5 models
IMG_SIZE = (224, 224)             # change if your models expect different size
CLASS_NAMES = ["class1", "class2"]  # <-- replace with your actual labels

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    raise RuntimeError("Set GROQ_API_KEY environment variable.")

LLM_MODEL_NAME = "llama-3.3-70b-versatile"  # or any other Groq model name

groq_client = Groq(api_key=GROQ_API_KEY)


# =========================
# LOAD ALL MODELS
# =========================

models: List[Dict[str, Any]] = []  # list of {"name": ..., "model": ...}


def load_all_models():
    if not os.path.isdir(MODEL_DIR):
        raise RuntimeError(f"MODEL_DIR not found: {MODEL_DIR}")

    for fname in os.listdir(MODEL_DIR):
        if not fname.endswith(".h5"):
            continue
        path = os.path.join(MODEL_DIR, fname)
        try:
            print(f"Loading model: {path}")
            m = load_model(path)
            models.append({"name": fname, "model": m})
        except Exception as e:
            print(f"Failed to load {path}: {e}")

    if not models:
        raise RuntimeError("No .h5 models loaded. Check MODEL_DIR.")


load_all_models()
print(f"✅ Loaded {len(models)} models.")


# =========================
# IMAGE PREPROCESSING
# =========================

def preprocess_image(file_bytes: bytes) -> np.ndarray:
    """
    Convert uploaded image bytes into a model-ready batch array.
    """
    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except Exception as e:
        raise ValueError(f"Cannot open image: {e}")

    img = img.resize(IMG_SIZE)
    arr = np.array(img).astype("float32") / 255.0
    arr = np.expand_dims(arr, axis=0)  # (1, H, W, C)
    return arr


# =========================
# RUN ALL MODELS
# =========================

def run_all_models_on_image(image_batch: np.ndarray) -> Dict[str, Any]:
    """
    Run every loaded model on the preprocessed image.
    Returns per-model predictions and a simple majority-vote ensemble.
    """
    per_model_results = []
    votes: Dict[str, int] = {}

    for item in models:
        name = item["name"]
        model = item["model"]

        preds = model.predict(image_batch, verbose=0)[0]  # shape: (num_classes,)
        top_idx = int(np.argmax(preds))

        if top_idx < len(CLASS_NAMES):
            top_class = CLASS_NAMES[top_idx]
        else:
            top_class = f"class_{top_idx}"

        confidence = float(preds[top_idx])

        per_model_results.append(
            {
                "model_name": name,
                "top_class": top_class,
                "confidence": confidence,
                "raw_probs": preds.tolist(),
            }
        )

        votes[top_class] = votes.get(top_class, 0) + 1

    # Majority vote
    best_class, best_votes = max(votes.items(), key=lambda x: x[1])
    total_models = len(models)
    vote_share = best_votes / total_models

    ensemble = {
        "predicted_class": best_class,
        "votes": votes,
        "vote_share": vote_share,
        "num_models": total_models,
    }

    return {
        "per_model": per_model_results,
        "ensemble": ensemble,
    }


# =========================
# LLM EXPLANATION
# =========================

def explain_with_llm(ensemble_result: Dict[str, Any]) -> str:
    """
    Send the classification summary to the LLM for a natural language explanation.
    """
    prompt = f"""
You are an AI assistant explaining image classification results
from multiple models to a non-technical user.

These are the predictions (JSON):

{json.dumps(ensemble_result, indent=2)}

Based on this:
1. Explain in simple language what the most likely class/diagnosis is.
2. Comment briefly on whether the models agree or disagree.
3. Do NOT give medical treatment or health advice. Only describe what the models see.
Use 1–2 short paragraphs.
""".strip()

    resp = groq_client.chat.completions.create(
        model=LLM_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=300,
    )

    return resp.choices[0].message.content.strip()


# =========================
# FASTAPI APP
# =========================

app = FastAPI(
    title="Multi-model Image Classification + LLM Explanation",
    description=(
        "Upload an image, run multiple Keras .h5 models, "
        "and get an LLM explanation of the combined predictions."
    ),
    version="1.0.0",
)


@app.get("/")
async def root():
    return {
        "message": "Use POST /analyze with an image file.",
        "num_models_loaded": len(models),
    }


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Accept an image, run all .h5 models, and return predictions + LLM explanation.
    """
    # 1. Read image
    try:
        file_bytes = await file.read()
        image_batch = preprocess_image(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    # 2. Run all models
    try:
        ensemble_result = run_all_models_on_image(image_batch)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference error: {e}")

    # 3. Get LLM explanation
    try:
        explanation = explain_with_llm(ensemble_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

    # 4. Return response
    return JSONResponse(
        content={
            "ensemble_result": ensemble_result,
            "llm_explanation": explanation,
        }
    )
