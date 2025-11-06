# MedWhisper Chatbot Setup Guide

This guide will help you set up and run the MedWhisper AI Chatbot on your website.

## Overview

The chatbot is a beautiful, modern UI component that appears at the bottom-right corner of your website. It connects to your FastAPI backend to provide intelligent medical information responses.

## Features

- 🎨 **Beautiful Modern UI** - Gradient design matching your brand colors
- 💬 **Real-time Chat** - Instant messaging with typing indicators
- 📱 **Responsive Design** - Works perfectly on all devices
- 🚀 **Quick Replies** - Pre-defined questions for easy interaction
- 💡 **Smart Positioning** - Fixed at bottom-right, non-intrusive
- 🔔 **Notification Badge** - Shows unread messages count
- ✨ **Smooth Animations** - Professional transitions and effects

## Setup Instructions

### 1. Start the FastAPI Backend

First, navigate to the API directory and start the backend server:

```bash
cd pulseai_scaffold/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### 2. Start the React Frontend

In a new terminal, navigate to the MedWhisper directory and start the React app:

```bash
cd MedWhisper
npm install
npm start
```

The app will open at `http://localhost:3000`

### 3. Test the Chatbot

1. Open your browser to `http://localhost:3000`
2. Look for the floating chat button at the bottom-right corner
3. Click the button to open the chatbot
4. Try asking a question or click on the quick reply suggestions

## Configuration

### API Endpoint

The chatbot connects to the backend at `http://localhost:8000/chat`. If you need to change this:

1. Open `src/components/Chatbot.jsx`
2. Find the line: `const API_BASE = 'http://localhost:8000';`
3. Update it to your backend URL

### Customization

You can customize the chatbot appearance by editing `src/components/Chatbot.jsx`:

- **Colors**: Update the gradient colors (currently `#014A93` and `#2B6FDF`)
- **Size**: Modify `width` and `height` in the chat window styles
- **Position**: Change `bottom-6 right-6` in the main container
- **Quick Replies**: Edit the `quickReplies` array

## How It Works

1. **User Interface**: The chatbot component is a React component with state management
2. **Message Flow**: 
   - User types a message
   - Message is sent to FastAPI backend at `/chat` endpoint
   - Backend processes with OpenAI/Rasa
   - Response is displayed in the chat
3. **Storage**: Each user gets a unique ID for session management

## Troubleshooting

### Chatbot not responding?

- Make sure the FastAPI backend is running on port 8000
- Check browser console for CORS errors
- Verify the API_BASE URL in Chatbot.jsx

### CORS errors?

- The backend CORS settings allow `localhost:3000`
- If using a different port, update `main.py` CORS settings

### Styling issues?

- Make sure Tailwind CSS is properly configured
- Check that all classes are valid Tailwind utilities

## Environment Requirements

- Node.js (v14 or higher)
- Python (v3.8 or higher)
- npm or yarn
- Modern web browser

## Next Steps

- Configure OpenAI API key in `.env` for smarter responses
- Add voice input feature
- Customize the chatbot personality
- Add chat history persistence
- Implement user authentication

## Support

For issues or questions, please refer to the main project documentation or contact the development team.

---

**Note**: This chatbot is for informational purposes only and does not provide medical diagnosis or treatment advice. Users should always consult qualified healthcare professionals for medical concerns.

