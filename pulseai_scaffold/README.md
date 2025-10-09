# PulseAI Scaffold


Clinical AI chatbot with web and Telegram interfaces.

Completed:
- Backend and frontend connected
- Rasa replies working
- GitHub repo cleaned


In progress:
- UI redesign
- **api/** – FastAPI backend for chat, Rasa, and AI integrations
- **web/** – React (Vite) frontend for a beautiful, responsive chat UI
- **bots/** – Telegram bot integration (text, quick replies, chat history, voice transcription)
- **docs/** – Project notes, setup guides, and architecture docs

## What Can PulseAI Do?

- Chat with users in real time using a clean, modern web interface
- Connect to Rasa for free, local clinical chatbot responses
- Telegram bot: chat, quick reply buttons, chat history, and voice message transcription (requires ffmpeg)
- Easily switch backend between Rasa and OpenAI (if you have an API key)
- Designed for rapid prototyping and easy extension

## How to Get Started

1. **Clone the repository**
	 ```bash
	 git clone https://github.com/AIP-F25-2/MedWhisper.git
	 cd pulseai_scaffold
	 ```


2. **Set up the backend**
	 - Go to the `api/` folder
	 - Create a `.env` file for your environment variables (see examples in `docs/`)
	 - Install Python dependencies:
		 ```bash
		 pip install -r requirements.txt
		 ```
	 - Start the FastAPI server:
		 ```bash
		 uvicorn main:app --reload
		 ```

3. **Set up the Telegram bot**
	 - Go to the `bots/` folder
	 - Create a `.env` file with your Telegram bot token:
		 ```env
		 TELEGRAM_TOKEN=your-telegram-bot-token-here
		 ```
	 - Install Python dependencies:
		 ```bash
		 pip install -r requirements.txt
		 ```
	 - (Optional, for voice transcription) Install ffmpeg and add it to your system PATH.
	 - Start the Telegram bot:
		 ```bash
		 python telegram_bot.py
		 ```
	 - Features:
		 - Text chat, quick reply buttons, chat history per user
		 - Voice message transcription (if ffmpeg is available)

4. **Set up the frontend**
	 - Go to the `web/` folder
	 - Install Node dependencies:
		 ```bash
		 npm install
		 ```
	 - Start the development server:
		 ```bash
		 npm run dev
		 ```

5. **(Optional) Run Rasa for local chatbot**
	 - If you want to use Rasa, start the server:
		 ```bash
		 rasa run --port 5005
		 ```


## Documentation & Help

All setup and usage instructions are included in this README. For further help, open an issue or check the code comments.

## What’s Been Done So Far?

- FastAPI backend set up and integrated with Rasa for free, local chatbot responses
- Removed OpenAI dependency for cost-free operation
- Environment variable and .env management for backend configuration
- Debugging and patching to ensure correct Rasa port usage (5005)
- React (Vite) frontend chat UI implemented with real-time streaming responses
- UI redesigned to match the main PulseAI website: blue/white palette, rounded corners, modern buttons
- Disclaimer updated for educational/informational use
- GitHub repository cleaned of secrets and .env files using BFG Repo-Cleaner
- README file completed and improved for clarity and onboarding

## License & Disclaimer

This project is for educational and informational use only. It does not provide medical advice.
