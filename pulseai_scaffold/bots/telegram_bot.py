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
API_BASE = os.getenv("API_BASE", "http://localhost:8002")

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
        "👋 Hi! I am your PulseAI bot with advanced capabilities:\n\n"
        "💬 **Text**: Ask me any clinical question\n"
        "🎤 **Voice**: Send voice messages for hands-free interaction\n" 
        "📷 **Images**: Send photos for visual medical guidance\n\n"
        "ℹ️ This is for informational purposes only—not medical diagnosis.\n\n"
        "Try sending me a message, voice note, or photo!",
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
        reply = data.get("text", "").strip()
        if not reply:
            reply = "No response"
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

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages with medical questions"""
    user_id = str(update.effective_user.id)
    caption = update.message.caption or "What can you tell me about this image?"
    
    try:
        # Get the highest resolution photo
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Download image data
        import io
        import base64
        
        image_bytes = io.BytesIO()
        await file.download_to_memory(image_bytes)
        image_bytes.seek(0)
        
        # Convert to base64
        image_b64 = base64.b64encode(image_bytes.read()).decode()
        image_data_uri = f"data:image/jpeg;base64,{image_b64}"
        
        logging.info(f"Received photo from user_id={user_id}: {caption}")
        
        # Send to image processing endpoint
        response = requests.post(f"{API_BASE}/chat/image", 
                               json={"sender": user_id, "message": caption, "image_data": image_data_uri})
        
        if response.status_code == 200:
            data = response.json()
            reply = data.get("text", "Sorry, I couldn't analyze the image.")
        else:
            reply = "Sorry, there was an error processing your image. Please try again."
        
        # Save to chat history
        try:
            chat_file = os.path.join(os.path.dirname(__file__), f"chat_{user_id}.txt")
            with open(chat_file, "a", encoding="utf-8") as f:
                f.write(f"User (photo): {caption}\nBot: {reply}\n---\n")
        except Exception as log_err:
            logging.error(f"Failed to save chat history for user_id={user_id}: {log_err}")
        
        await update.message.reply_text(reply)
        
    except Exception as e:
        logging.error(f"Error processing photo from user_id={user_id}: {e}")
        await update.message.reply_text("Sorry, I couldn't process your image. Please try again or describe your symptoms in text.")

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
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
        
        # Send to voice processing endpoint
        with open(wav_path, 'rb') as audio_file:
            files = {'audio_file': ('voice.wav', audio_file, 'audio/wav')}
            data = {'sender': user_id}
            response = requests.post(f"{API_BASE}/chat/voice", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            reply = result.get("text", "Sorry, I couldn't understand your voice message.")
            transcribed_text = result.get("transcribed_text", "")
        else:
            reply = "Sorry, there was an error processing your voice message."
            transcribed_text = ""
        
        logging.info(f"Voice message from user_id={user_id}, transcribed: {transcribed_text}")
        
        # Save to chat history
        try:
            chat_file = os.path.join(os.path.dirname(__file__), f"chat_{user_id}.txt")
            with open(chat_file, "a", encoding="utf-8") as f:
                f.write(f"User (voice): {transcribed_text}\nBot: {reply}\n---\n")
        except Exception as log_err:
            logging.error(f"Failed to save chat history for user_id={user_id}: {log_err}")
        
        await update.message.reply_text(reply)
        
    except Exception as err:
        logging.error(f"Voice transcription failed for user_id={user_id}: {err}")
        await update.message.reply_text("Sorry, I couldn't understand your voice message. Please try speaking clearly or use text.")
    finally:
        # Clean up temp files
        try:
            os.unlink(ogg_path)
            if os.path.exists(wav_path):
                os.unlink(wav_path)
        except:
            pass

def main():
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not set.")
        return
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    print("🚀 Bot is running with Image and Voice support...")
    app.run_polling()


if __name__ == "__main__":
    main()
