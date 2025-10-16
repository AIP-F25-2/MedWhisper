# Test OpenAI connectivity
from fastapi import FastAPI
import os, openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()

@app.get("/openai-test")
def openai_test():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello!"}],
            max_tokens=20
        )
        return {"ok": True, "reply": response.choices[0].message["content"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}
