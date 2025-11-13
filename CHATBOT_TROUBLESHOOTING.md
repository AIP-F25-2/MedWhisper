# 🔧 Chatbot Connection Troubleshooting Guide

## 🔴 **Your Current Issue: "Not Connected"**

You're getting the error: `Failed to load resource: net::ERR_CONNECTION_REFUSED :8001/chat:1`

This means your **FastAPI backend server** is not running on port 8001.

## 🏗️ **Complete Architecture**

```
React Frontend (port 3000)
    ↓ (fetch to localhost:8001/chat)
FastAPI Backend (port 8001) ← **THIS IS MISSING!**
    ↓ (forwards to localhost:5005/webhooks/rest/webhook)
Rasa Server (port 5005)
    ↓ (calls custom actions via)
Rasa Actions Server (port 5055)
```

## ✅ **Solution: Start All Required Services**

### **Method 1: Use Complete Launcher (Recommended)**

```powershell
# Run the complete launcher
.\start_complete_chatbot.bat
```

This will start all 4 services automatically.

### **Method 2: Manual Start (Step by Step)**

**Step 1: Start FastAPI Backend**
```powershell
cd pulseai_scaffold\api
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8001
```

**Step 2: Start Rasa Actions Server**
```powershell
cd RasaBot
.\rasa_venv\Scripts\Activate.ps1
rasa run actions
```

**Step 3: Start Rasa Server**
```powershell
# In a new terminal
cd RasaBot
.\rasa_venv\Scripts\Activate.ps1
rasa run --enable-api --cors "*"
```

**Step 4: Start React Frontend**
```powershell
# In a new terminal
cd MedWhisper
npm start
```

## 🔍 **Verification Steps**

After starting all services, verify they're running:

### **1. Check FastAPI Backend**
Open: http://localhost:8001/docs
- Should show FastAPI documentation
- If you get "connection refused", FastAPI isn't running

### **2. Check Rasa Server**
Open: http://localhost:5005
- Should show Rasa API documentation
- If you get "connection refused", Rasa isn't running

### **3. Test the Complete Flow**
```powershell
# Test FastAPI → Rasa connection
curl -X POST http://localhost:8001/chat -H "Content-Type: application/json" -d "{\"sender\":\"test\",\"message\":\"hello\"}"
```

### **4. Check React Frontend**
Open: http://localhost:3000
- Chatbot should appear in bottom-right
- Try sending a message

## 🐛 **Common Issues & Solutions**

### Issue: "Python not found" when starting FastAPI
**Solution**: Install Python or use full path:
```powershell
C:\Python310\python.exe -m uvicorn main:app --reload --port 8001
```

### Issue: "Module not found" for FastAPI dependencies
**Solution**: Install requirements:
```powershell
cd pulseai_scaffold\api
pip install fastapi uvicorn httpx python-dotenv
```

### Issue: "Rasa command not found"
**Solution**: Activate virtual environment:
```powershell
cd RasaBot
.\rasa_venv\Scripts\Activate.ps1
```

### Issue: "Port 8001 already in use"
**Solution**: Kill process using port:
```powershell
netstat -ano | findstr :8001
taskkill /PID <PID_NUMBER> /F
```

### Issue: "CORS error" in browser console
**Solution**: FastAPI CORS is configured, but make sure:
- FastAPI is running on port 8001
- React is running on port 3000
- Both are localhost

### Issue: Rasa returns "Sorry, I couldn't process that"
**Solution**: 
1. Check Rasa server is running: http://localhost:5005
2. Check actions server is running: http://localhost:5055
3. Verify model is trained: `rasa train`

## 📋 **Quick Checklist**

Before testing the chatbot:

- [ ] FastAPI running on port 8001
- [ ] Rasa server running on port 5005  
- [ ] Rasa actions running on port 5055
- [ ] React app running on port 3000
- [ ] All services show no errors in console
- [ ] Browser can access http://localhost:8001/docs
- [ ] Browser can access http://localhost:5005

## 🎯 **Expected Flow**

1. **User types message** in React chatbot
2. **React sends POST** to `localhost:8001/chat`
3. **FastAPI receives** message and forwards to `localhost:5005/webhooks/rest/webhook`
4. **Rasa processes** message using trained model
5. **Rasa calls actions** server if needed (localhost:5055)
6. **Rasa returns** response to FastAPI
7. **FastAPI returns** response to React
8. **React displays** bot reply in chat

## 🆘 **Still Not Working?**

1. **Check all console windows** for error messages
2. **Verify Python versions** (use Python 3.10 for Rasa)
3. **Check firewall/antivirus** isn't blocking ports
4. **Try restarting** all services in order
5. **Check Windows Defender** isn't blocking connections

## 📞 **Quick Test Commands**

```powershell
# Test FastAPI
curl http://localhost:8001/docs

# Test Rasa  
curl http://localhost:5005

# Test complete flow
curl -X POST http://localhost:8001/chat -H "Content-Type: application/json" -d "{\"sender\":\"test\",\"message\":\"hello\"}"
```

---

**Bottom Line**: You need to start the FastAPI backend on port 8001. The complete launcher script will do this automatically! 🚀
