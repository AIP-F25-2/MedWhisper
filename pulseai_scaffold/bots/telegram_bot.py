import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests

logging.basicConfig(level=logging.INFO)
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi, I'm PulseAI bot!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    try:
        r = requests.post(f"{API_BASE}/chat", json={"sender": str(update.effective_user.id), "message": msg})
        data = r.json()
        reply = data["replies"][0] if data["replies"] else "No response"
    except Exception as e:
        reply = f"Error: {e}"
    await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
