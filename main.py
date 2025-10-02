from fastapi import FastAPI
from backend_app.routers import chat, voice

app = FastAPI()

app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(voice.router, prefix="/voice", tags=["Voice"])


@app.get("/")
def root():
    return {"msg": "Medical Chatbot Backend Running"}
