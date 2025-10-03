## Progress & Completed Work

- FastAPI backend set up and integrated with Rasa for free, local chatbot responses
- Removed OpenAI dependency for cost-free operation
- Environment variable and .env management for backend configuration
- Debugging and patching to ensure correct Rasa port usage (5005)
- React (Vite) frontend chat UI implemented with real-time streaming responses
- UI redesigned to match main PulseAI website: blue/white palette, rounded corners, modern buttons
- Disclaimer updated for educational/informational use
- GitHub repository cleaned of secrets and .env files using BFG Repo-Cleaner
- README file completed and improved for clarity and onboarding

# PulseAI Scaffold

PulseAI is a multimodal clinical AI assistant platform. This scaffold provides a modular starting point for building, testing, and deploying PulseAI features.

## Structure

- **api/** : FastAPI backend gateway for chat, Rasa, and AI integrations
- **web/** : React (Vite) frontend chat UI, styled to match the PulseAI website
- **bots/** : (Reserved for future bot integrations)
- **docs/** : Project notes, setup guides, and architecture documentation

## Features

- Modern, responsive chat UI with real-time streaming responses
- Rasa integration for local, free clinical chatbot
- Easy backend switching between Rasa and OpenAI (if API key available)
- Modular codebase for rapid prototyping and extension

## Getting Started

1. **Clone the repository**
	 ```bash
	 git clone https://github.com/AIP-F25-2/MedWhisper.git
	 cd pulseai_scaffold
	 ```

2. **Backend Setup**
	 - Navigate to `api/`
	 - Create a `.env` file for environment variables (see `docs/` for example)
	 - Install dependencies:
		 ```bash
		 pip install -r requirements.txt
		 ```
	 - Start FastAPI server:
		 ```bash
		 uvicorn main:app --reload
		 ```

3. **Frontend Setup**
	 - Navigate to `web/`
	 - Install dependencies:
		 ```bash
		 npm install
		 ```
	 - Start development server:
		 ```bash
		 npm run dev
		 ```


5. **Rasa Server (Optional)**
	 - Start Rasa server locally for free chatbot responses:
		 ```bash
		 rasa run --port 5005
		 ```

## Documentation

- See `docs/` for step-by-step instructions, environment setup, and architecture diagrams.

## Contributing

Pull requests and issues are welcome! Please see `docs/CONTRIBUTING.md` for guidelines.

## License

This project is for educational and informational use only. Not medical advice.
