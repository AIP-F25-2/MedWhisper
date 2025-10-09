from telegram import ReplyKeyboardMarkup
from telegram import Audio, Voice
from telegram.ext import MessageHandler, filters
import speech_recognition as sr
from pydub import AudioSegment
import tempfile

# Cleaned-up Telegram bot for PulseAI
import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import requests

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quick_replies = [
        ["What are the symptoms of flu?", "How to prevent COVID-19?"],
        ["What is a healthy diet?", "When should I see a doctor?"]
    ]
    reply_markup = ReplyKeyboardMarkup(quick_replies, resize_keyboard=True)
    await update.message.reply_text(
        "Hi! I am your PulseAI bot. Ask me a clinical question. (Info only—no diagnosis.)",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a message and I'll try to help!")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "PulseAI Bot: An informational clinical chatbot.\n\nThis bot provides general health information and answers to clinical questions. It does not provide medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for medical concerns."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    user_id = str(update.effective_user.id)
    logging.info(f"Received message from user_id={user_id}: {msg}")
    try:
        r = requests.post(f"{API_BASE}/chat", json={"sender": user_id, "message": msg})
        data = r.json()
        reply = data["replies"][0] if data.get("replies") else "No response"
    except Exception as e:
        reply = f"Error: {e}"
    # Save chat history
    try:
        chat_file = os.path.join(os.path.dirname(__file__), f"chat_{user_id}.txt")
        with open(chat_file, "a", encoding="utf-8") as f:
            f.write(f"User: {msg}\nBot: {reply}\n---\n")
        logging.info(f"Chat history written to {chat_file}")
    except Exception as log_err:
        logging.error(f"Failed to save chat history for user_id={user_id}: {log_err}")
    quick_replies = [
        ["What are the symptoms of flu?", "How to prevent COVID-19?"],
        ["What is a healthy diet?", "When should I see a doctor?"]
    ]
    reply_markup = ReplyKeyboardMarkup(quick_replies, resize_keyboard=True)
    await update.message.reply_text(reply, reply_markup=reply_markup)

def main():
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not set.")
        return
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    print("Bot is running...")
    app.run_polling()

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as ogg_file:
        await file.download_to_drive(ogg_file.name)
        ogg_path = ogg_file.name
    wav_path = ogg_path.replace('.ogg', '.wav')
    try:
        # Convert OGG (opus) to WAV
        AudioSegment.from_ogg(ogg_path).export(wav_path, format='wav')
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        logging.info(f"Transcribed voice from user_id={user_id}: {text}")
        # Process as normal chat
        try:
            r = requests.post(f"{API_BASE}/chat", json={"sender": user_id, "message": text})
            data = r.json()
            reply = data["replies"][0] if data.get("replies") else "No response"
        except Exception as e:
            reply = f"Error: {e}"
        # Save chat history
        try:
            chat_file = os.path.join(os.path.dirname(__file__), f"chat_{user_id}.txt")
            with open(chat_file, "a", encoding="utf-8") as f:
                f.write(f"User (voice): {text}\nBot: {reply}\n---\n")
            logging.info(f"Chat history written to {chat_file}")
        except Exception as log_err:
            logging.error(f"Failed to save chat history for user_id={user_id}: {log_err}")
        await update.message.reply_text(reply)
    except Exception as err:
        logging.error(f"Voice transcription failed for user_id={user_id}: {err}")
        await update.message.reply_text("Sorry, I couldn't understand your voice message.")


if __name__ == "__main__":
    main()
