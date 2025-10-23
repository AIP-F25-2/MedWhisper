from fastapi import APIRouter
from backend.backend_app.services.text_engine import generate_response

router = APIRouter()

@router.post("/")
def chat_endpoint(user_input: str):
    bot_reply = generate_response(user_input)
    return {"user_input": user_input, "bot_response": bot_reply}
