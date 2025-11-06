# MedWhisper RAG API - Integration Guide

**For Frontend Team**

---

## 🌐 **API Endpoint**

### **Base URL:**
```
https://37e4626b0be7.ngrok-free.app
```

### **Interactive Documentation:**
```
https://37e4626b0be7.ngrok-free.app/docs
```
*Use this to test the API in your browser!*

---

## 🔓 **Authentication**

**No API key required!** Just send requests directly.

---

## 📡 **Main Endpoint: `/query`**

### **POST** `/query`

Send a medical question and get an AI-generated answer.

### **Request:**

```json
{
  "query": "What are the symptoms of diabetes?",
  "user_id": "telegram_user_123",
  "user_role": "student"
}
```

### **Response:**

```json
{
  "success": true,
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "telegram_user_123",
  "response": "Diabetes symptoms include increased thirst, frequent urination, extreme hunger, unexplained weight loss, fatigue, and blurred vision. [DocID: diag_001]",
  "user_role": "student",
  "model_used": "Gemini (Primary)",
  "retrieved_documents": 5,
  "safe": true,
  "warnings": []
}
```

### **Important:** Use `response` field to show to users!

---

## 📋 **Request Parameters**

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `query` | string | ✅ Yes | Medical question | "What are diabetes symptoms?" |
| `user_id` | string | ✅ Yes | Unique user ID | "telegram_123456" |
| `user_role` | string | ❌ No | User's role (default: "student") | "student", "clinician", "researcher" |
| `patient_id` | string | ❌ No | For patient-specific queries | "10000032" |

---

## 👥 **User Roles**

| Role | Description | Gets Metrics? | Gets Citations? |
|------|-------------|---------------|-----------------|
| **student** | Medical students, general users | ❌ No | ❌ No |
| **clinician** | Doctors, medical professionals | ✅ Yes | ✅ Yes |
| **researcher** | Data scientists, researchers | ✅ Yes | ✅ Yes |
| **auditor** | Compliance, quality assurance | ✅ Yes (all) | ✅ Yes |

**Recommendation:** Use `"student"` for general users in Telegram bot.

---

## 💻 **Integration Examples**

### **JavaScript/React:**

```javascript
async function askMedWhisper(question, userId) {
    const response = await fetch('https://37e4626b0be7.ngrok-free.app/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: question,
            user_id: userId,
            user_role: 'student'
        })
    });
    
    const data = await response.json();
    return data.response; // Show this to user
}

// Usage
const answer = await askMedWhisper("What is diabetes?", "user_123");
console.log(answer);
```

### **Python (Telegram Bot):**

```python
import requests

def get_medical_answer(question, user_id):
    response = requests.post(
        'https://37e4626b0be7.ngrok-free.app/query',
        json={
            'query': question,
            'user_id': str(user_id),
            'user_role': 'student'
        },
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json()['response']
    else:
        return "Sorry, I couldn't process your question."

# Usage in Telegram bot
answer = get_medical_answer(user_message, telegram_user_id)
bot.send_message(chat_id, answer)
```

### **cURL (Testing):**

```bash
curl -X POST "https://37e4626b0be7.ngrok-free.app/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the symptoms of diabetes?",
    "user_id": "test_user",
    "user_role": "student"
  }'
```

---

## 🎯 **Other Endpoints**

### **GET** `/health`
Check if API is online.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "rag_engine_ready": true
}
```

### **GET** `/roles`
Get list of available user roles.

**Response:**
```json
{
  "roles": [
    {
      "id": "student",
      "name": "Instructor / Medical Student",
      "description": "Educational responses without technical metrics"
    },
    ...
  ]
}
```

---

## ⏱️ **Response Times**

| Query Type | Expected Time |
|------------|---------------|
| Simple question | 3-5 seconds |
| Patient-specific | 5-8 seconds |
| Complex query | 8-12 seconds |

**Recommendation:** Set timeout to 30 seconds.

---

## ⚠️ **Important Notes**

### **Availability:**
- ✅ **Active during:** Development hours (notify team of your schedule)
- ❌ **Offline when:** Backend developer's PC is off
- 🔄 **For Production:** Will be deployed to cloud for 24/7 availability

### **URL Stability:**
- Current URL is **temporary** (ngrok development)
- URL may change if backend restarts ngrok
- Backend team will notify of any URL changes
- For production, will have permanent URL

### **Error Handling:**

```javascript
try {
    const data = await fetch(API_URL + '/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, user_id, user_role: 'student' })
    }).then(r => r.json());
    
    if (data.success) {
        return data.response;
    } else {
        return "Sorry, I couldn't process your question.";
    }
} catch (error) {
    console.error('API Error:', error);
    return "The medical assistant is currently unavailable. Please try again later.";
}
```

---

## 🧪 **Testing**

### **Quick Test:**
Visit the interactive docs: https://37e4626b0be7.ngrok-free.app/docs

1. Click on `/query` endpoint
2. Click "Try it out"
3. Modify the example JSON
4. Click "Execute"
5. See the response!

### **Sample Questions to Test:**
- "What are the symptoms of diabetes?"
- "Show me insulin administration records"
- "What is hypertension?"
- "Explain sepsis treatment"

---

## 📊 **Response Format Details**

### **Success Response:**
```json
{
  "success": true,
  "query_id": "uuid-here",
  "user_id": "your-user-id",
  "response": "The answer text to display",
  "user_role": "student",
  "model_used": "Gemini (Primary)",
  "retrieved_documents": 5,
  "confidence_score": 0.89,  // Only for clinician/researcher/auditor
  "citations_valid": true,    // Only for clinician/researcher/auditor
  "safe": true,
  "warnings": []
}
```

### **Error Response:**
```json
{
  "detail": "Error message here"
}
```

---

## 🎯 **Quick Start Checklist**

- [ ] Test API using `/docs` endpoint
- [ ] Implement basic query function
- [ ] Add error handling
- [ ] Set 30-second timeout
- [ ] Test with sample questions
- [ ] Handle offline/timeout scenarios
- [ ] Display `response` field to users

---

## 📞 **Support**

**Questions or Issues?**
- Contact backend team
- Check `/docs` for interactive testing
- Review error messages in response

---

## 🚀 **Production Deployment**

**Current:** Development (ngrok tunnel)  
**Coming Soon:** Production deployment with:
- ✅ Permanent URL
- ✅ 24/7 availability  
- ✅ Better performance
- ✅ SSL/HTTPS

---

## 📝 **Quick Reference**

```javascript
// Minimum working example
const API_URL = 'https://37e4626b0be7.ngrok-free.app';

async function ask(question, userId) {
    const res = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query: question,
            user_id: userId,
            user_role: 'student'
        })
    });
    const data = await res.json();
    return data.response;
}
```

---

**Last Updated:** October 23, 2025  
**API Version:** 1.0.0  
**Status:** Development

---

**Happy coding! 🎉**

