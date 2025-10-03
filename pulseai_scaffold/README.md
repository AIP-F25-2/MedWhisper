







# PulseAI Scaffold

Clinical AI chatbot.

Completed:
- Backend and frontend connected
- Rasa replies working
- GitHub repo cleaned

In progress:
- UI redesign
- **api/** – FastAPI backend for chat, Rasa, and AI integrations
- **web/** – React (Vite) frontend for a beautiful, responsive chat UI
- **bots/** – Reserved for future bot integrations
- **docs/** – Project notes, setup guides, and architecture docs

## What Can PulseAI Do?

- Chat with users in real time using a clean, modern interface
- Connect to Rasa for free, local clinical chatbot responses
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

3. **Set up the frontend**
	 - Go to the `web/` folder
	 - Install Node dependencies:
		 ```bash
		 npm install
		 ```
	 - Start the development server:
		 ```bash
		 npm run dev
		 ```

4. **(Optional) Run Rasa for local chatbot**
	 - If you want to use Rasa, start the server:
		 ```bash
		 rasa run --port 5005
		 ```

## Documentation & Help

Check out the `docs/` folder for step-by-step instructions, environment setup, and architecture diagrams. If you get stuck, you’ll likely find answers there.

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

## Contributing

We welcome pull requests and issues! If you have ideas, suggestions, or want to help, please see `docs/CONTRIBUTING.md` for guidelines.

## License & Disclaimer

This project is for educational and informational use only. It does not provide medical advice.
