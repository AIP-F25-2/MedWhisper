# main.py

from fastapi import FastAPI, Request, Response, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, httpx, logging
import openai
from dotenv import load_dotenv
import speech_recognition as sr
import tempfile
import base64
from PIL import Image
import io


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
logger = logging.getLogger("medwhisper")
logging.basicConfig(level=logging.INFO)

# Backend selection: 'rasa' or 'gemini'. Default to 'gemini'.
QA_BACKEND = os.getenv("QA_BACKEND", "gemini").lower()
GEMINI_QA_URL = os.getenv("GEMINI_QA_URL", "https://b946f3a056f1.ngrok-free.app/ml/qa")

app = FastAPI(title="Med-Whisper Gateway")

# Allow the React dev server to call the API
# (add more origins if you use a different port or host)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    sender: str
    message: str

class ImageChatRequest(BaseModel):
    sender: str
    message: str
    image_data: str  # base64 encoded image



from fastapi.responses import StreamingResponse, JSONResponse
import asyncio

@app.post("/chat")
async def chat(req: ChatRequest):
    """Forward message to OpenAI with streaming if API key is set, else Rasa. Returns AI reply."""
    logger.info(f"/chat from sender={req.sender!r}: {req.message!r} -> backend={QA_BACKEND}")
    try:
        reply = ""
        if QA_BACKEND == "rasa":
            rasa_url = "http://localhost:5005/webhooks/rest/webhook"
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    rasa_url,
                    json={"sender": req.sender, "message": req.message},
                    headers={"Content-Type": "application/json"},
                )
                r.raise_for_status()
                logger.info(f"Raw Rasa response: {r.text}")
                data = r.json()
            replies = [m.get("text") for m in data if isinstance(m, dict) and "text" in m]
            reply = replies[0] if replies else "Sorry, I couldn't answer that."
            # Recursively unwrap reply if it is a JSON string with 'replies' or 'text'
            def extract_plain_text(val):
                import json
                if isinstance(val, str) and val.strip().startswith("{"):
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, dict):
                            if parsed.get("text") and isinstance(parsed["text"], str):
                                return extract_plain_text(parsed["text"])
                            if parsed.get("replies") and isinstance(parsed["replies"], list) and parsed["replies"]:
                                return extract_plain_text(parsed["replies"][0])
                    except Exception as inner_json_err:
                        logger.error(f"Inner JSON decode error: {inner_json_err}. Raw reply: {val}")
                        pass
                return val
            reply = extract_plain_text(reply)
        else:
            # Use Gemini QA with OpenAI fallback
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    payload = {"q": req.message, "role": "doctor"}
                    r = await client.post(
                        GEMINI_QA_URL,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    r.raise_for_status()
                    logger.info(f"Raw Gemini QA response: {r.text}")
                    data = r.json()
                # For doctor role, include confidence and citations if available
                reply = data.get("answer_text") or data.get("answer") or data.get("text") or "Sorry, I couldn't answer that."
                
                # Add confidence and citations for doctor responses
                if "confidence" in data:
                    reply += f"\n\nConfidence: {data['confidence']}"
                if "citations" in data and data["citations"]:
                    citations_str = ", ".join(data["citations"])
                    reply += f"\nCitations: {citations_str}"
            except Exception as gemini_error:
                logger.warning(f"Gemini service unavailable: {gemini_error}. Falling back to OpenAI...")
                # Fallback to OpenAI
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are Med-Whisper, a helpful medical AI assistant. Provide accurate medical information but always remind users this is for informational purposes only and not a substitute for professional medical advice."},
                            {"role": "user", "content": req.message}
                        ],
                        max_tokens=500,
                        temperature=0.7
                    )
                    reply = response.choices[0].message.content
                    reply += "\n\n⚠️ This information is for educational purposes only. Always consult with a healthcare professional for medical advice."
                except Exception as openai_error:
                    logger.error(f"OpenAI fallback also failed: {openai_error}")
                    reply = """I'm experiencing technical difficulties right now, but I can share some general health information:

**Common Health Tips:**
• Maintain a balanced diet with fruits and vegetables
• Exercise regularly (at least 150 minutes per week)
• Get adequate sleep (7-9 hours for adults)
• Stay hydrated by drinking plenty of water
• Practice good hygiene (regular handwashing)
• Schedule regular check-ups with your healthcare provider

**When to seek immediate medical attention:**
• Severe chest pain or difficulty breathing
• Signs of stroke (sudden weakness, confusion, severe headache)
• High fever with severe symptoms
• Severe allergic reactions
• Any symptoms that seem serious or unusual

⚠️ **Important:** This is general information only. For specific medical concerns, always consult with a qualified healthcare professional."""
        return JSONResponse(content={"text": reply})
    except Exception as e:
        logger.error(f"Error in /chat: {e}")
        return JSONResponse(content={"text": f"[ERROR]: {str(e)}"}, status_code=500)

@app.post("/chat/image")
async def chat_image(req: ImageChatRequest):
    """Process image with medical question using intelligent fallback system."""
    logger.info(f"/chat/image from sender={req.sender!r}: {req.message!r}")
    
    try:
        # Try OpenAI Vision API first
        logger.info("Attempting image analysis with OpenAI Vision...")
        
        # Decode base64 image
        image_data = req.image_data
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are Med-Whisper, a medical AI assistant. Analyze medical images and provide helpful information. Always include appropriate medical disclaimers."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Medical question about this image: {req.message}"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        reply = response.choices[0].message.content
        reply += "\n\n⚠️ **Medical Disclaimer:** This analysis is for educational purposes only. Always consult with a qualified healthcare professional for proper medical diagnosis and treatment."
        
        logger.info("OpenAI Vision analysis successful")
        return JSONResponse(content={"text": reply})
        
    except Exception as openai_error:
        logger.warning(f"OpenAI Vision failed: {openai_error}. Using fallback image analysis...")
        
        # Intelligent fallback - provide helpful medical guidance based on question and image type
        question_lower = req.message.lower()
        
        # Try to detect image type from base64 header or question content
        image_type_indicators = {
            'dental': ['tooth', 'teeth', 'dental', 'x-ray', 'xray', 'jaw', 'crown', 'filling', 'root canal', 'cavity'],
            'skin': ['rash', 'skin', 'spot', 'bump', 'mole', 'acne', 'eczema', 'dermatitis'],
            'wound': ['wound', 'cut', 'injury', 'bandage', 'healing', 'scar', 'bleeding'],
            'eye': ['eye', 'vision', 'pupil', 'iris', 'retina', 'cataract', 'glaucoma'],
            'bone': ['bone', 'fracture', 'break', 'orthopedic', 'joint', 'arthritis']
        }
        
        # Detect likely image type
        detected_type = 'general'
        for img_type, keywords in image_type_indicators.items():
            if any(word in question_lower for word in keywords):
                detected_type = img_type
                break
        
        # Provide specialized analysis based on detected type
        if detected_type == 'dental':
            reply = """**🦷 Dental X-Ray Analysis**

I can see you've uploaded what appears to be a dental X-ray image. Here's general dental health guidance:

**Common Dental Findings on X-Rays:**
• **Cavities (Decay)**: Dark spots or areas in teeth
• **Bone Loss**: Changes around tooth roots
• **Impacted Teeth**: Teeth that haven't fully erupted
• **Root Issues**: Problems at tooth foundations
• **Restorations**: Existing fillings, crowns, or implants

**Dental Health Maintenance:**
• Brush twice daily with fluoride toothpaste
• Floss daily to remove plaque between teeth
• Regular dental check-ups every 6 months
• Limit sugary and acidic foods/drinks
• Don't use teeth as tools

**When to See a Dentist:**
• Tooth pain or sensitivity
• Swelling in gums or face
• Bleeding gums
• Changes in bite or jaw alignment
• Any concerning changes visible on X-rays

**Emergency Dental Situations:**
• Severe tooth pain
• Dental trauma or injury
• Swelling that affects breathing/swallowing
• Broken or knocked-out teeth"""

        elif detected_type == 'skin':
            reply = """**🔍 Skin Condition Analysis**

I can see you've uploaded an image with a question about skin-related symptoms. Here's general dermatological guidance:

**Common Skin Conditions:**
• **Rashes**: Can be caused by allergies, infections, or irritants
• **Moles**: Monitor for changes in size, color, or shape (ABCDE rule)
• **Acne**: Usually treatable with proper skincare routines
• **Eczema/Dermatitis**: Often requires moisturizing and avoiding triggers

**When to See a Dermatologist:**
• Any new or changing moles
• Persistent rashes lasting more than a few days
• Signs of infection (pus, spreading redness, warmth)
• Any concerning changes in skin appearance"""

        elif detected_type == 'wound':
            reply = """**🩹 Wound Care Analysis**

Based on your wound-related question, here's general wound care guidance:

**Basic Wound Care:**
• Clean hands before touching wound
• Gently clean with water or saline
• Apply antibiotic ointment if recommended
• Cover with sterile bandage
• Change dressing daily or when soiled

**Signs of Infection to Watch For:**
• Increased redness or warmth
• Pus or unusual discharge
• Red streaking from wound
• Fever or increased pain
• Wound not healing after several days

**Seek Medical Attention If:**
• Deep cuts requiring stitches
• Signs of infection present
• Embedded objects or debris
• Unable to stop bleeding"""

        elif detected_type == 'eye':
            reply = """**👁️ Eye/Vision Analysis**

Based on your eye-related image question, here's general ophthalmological guidance:

**Common Eye Conditions:**
• **Conjunctivitis**: Red, itchy, or watery eyes
• **Styes**: Small lumps on eyelid
• **Vision Changes**: Blurriness, double vision, or loss
• **Eye Injuries**: Trauma or foreign objects

**Eye Care Tips:**
• Regular eye exams (annually or as recommended)
• Protect eyes from UV radiation
• Follow 20-20-20 rule for screen use
• Don't rub eyes with dirty hands

**When to See an Eye Doctor:**
• Sudden vision changes
• Eye pain or severe discomfort
• Flashing lights or dark spots
• Eye injuries or chemicals in eye"""

        elif detected_type == 'bone':
            reply = """**🦴 Orthopedic/Bone Analysis**

Based on your bone/joint-related image, here's general orthopedic guidance:

**Common Bone/Joint Issues:**
• **Fractures**: Complete or partial breaks in bones
• **Sprains**: Ligament injuries
• **Arthritis**: Joint inflammation and pain
• **Dislocations**: Joints out of normal position

**General Care:**
• R.I.C.E. for acute injuries (Rest, Ice, Compression, Elevation)
• Maintain good posture and ergonomics
• Regular exercise for bone health
• Adequate calcium and vitamin D

**When to Seek Orthopedic Care:**
• Severe pain or inability to move
• Visible deformity after injury
• Numbness or tingling
• Signs of infection around injury site"""
            reply = """**Image Analysis - Skin-Related Concern**

I can see you've uploaded an image with a question about skin-related symptoms. While I cannot directly analyze the image, here's general guidance:

**Common Skin Conditions:**
• **Rashes**: Can be caused by allergies, infections, or irritants
• **Moles**: Monitor for changes in size, color, or shape (ABCDE rule)
• **Acne**: Usually treatable with proper skincare routines
• **Eczema/Dermatitis**: Often requires moisturizing and avoiding triggers

**When to See a Dermatologist:**
• Any new or changing moles
• Persistent rashes lasting more than a few days
• Signs of infection (pus, spreading redness, warmth)
• Any concerning changes in skin appearance"""

        elif any(word in question_lower for word in ['wound', 'cut', 'injury', 'bandage', 'healing']):
            reply = """**Image Analysis - Wound/Injury Concern**

Based on your wound-related question, here's general wound care guidance:

**Basic Wound Care:**
• Clean hands before touching wound
• Gently clean with water or saline
• Apply antibiotic ointment if recommended
• Cover with sterile bandage
• Change dressing daily or when soiled

**Signs of Infection to Watch For:**
• Increased redness or warmth
• Pus or unusual discharge
• Red streaking from wound
• Fever or increased pain
• Wound not healing after several days

**Seek Medical Attention If:**
• Deep cuts requiring stitches
• Signs of infection present
• Embedded objects or debris
• Unable to stop bleeding"""

        elif any(word in question_lower for word in ['swelling', 'inflammation', 'red', 'painful']):
            reply = """**Image Analysis - Swelling/Inflammation Concern**

For swelling or inflammatory conditions, here's general guidance:

**Common Causes:**
• Injury or trauma
• Infection
• Allergic reactions
• Underlying medical conditions

**General Management:**
• **R.I.C.E.**: Rest, Ice, Compression, Elevation
• Over-the-counter anti-inflammatory medications (if appropriate)
• Avoid heat initially for acute injuries
• Monitor for worsening symptoms

**When to Seek Care:**
• Severe or worsening swelling
• Signs of infection
• Difficulty moving affected area
• Numbness or tingling
• Swelling after potential serious injury"""

        else:
            reply = f"""**Image Analysis - Medical Question**

Thank you for sharing your image with the question: "{req.message}"

While I cannot directly process images at the moment, I can provide general medical guidance:

**General Health Assessment Tips:**
• Document any changes in symptoms over time
• Note associated symptoms (pain, fever, etc.)
• Consider when symptoms first appeared
• Think about potential triggers or causes

**When to Consult Healthcare Providers:**
• Any concerning or persistent symptoms
• Sudden onset of severe symptoms
• Changes in previously stable conditions
• When you're unsure about symptom significance

**Documentation for Medical Visits:**
• Take clear photos to show your healthcare provider
• Keep a symptom diary
• List all medications and supplements
• Prepare questions in advance"""

        reply += """

**🔧 Technical Note:** Image processing is temporarily using text-based analysis. For visual assessment, please consult with a healthcare professional who can properly examine the image.

⚠️ **Important Medical Disclaimer:** This information is for educational purposes only and does not constitute medical advice, diagnosis, or treatment. Always consult with a qualified healthcare professional for proper medical evaluation of any health concerns."""

        return JSONResponse(content={"text": reply})

@app.post("/chat/voice")
async def chat_voice(audio_file: UploadFile = File(...), sender: str = Form(...)):
    """Process voice message and respond with text."""
    logger.info(f"/chat/voice from sender={sender!r}")
    try:
        # Save uploaded audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Use speech recognition
        r = sr.Recognizer()
        with sr.AudioFile(tmp_file_path) as source:
            audio = r.record(source)
        
        # Convert speech to text
        try:
            text = r.recognize_google(audio)
            logger.info(f"Voice transcribed: {text}")
        except sr.UnknownValueError:
            return JSONResponse(content={"text": "Sorry, I couldn't understand your voice message. Please try speaking more clearly."})
        except sr.RequestError:
            return JSONResponse(content={"text": "Sorry, there was an error processing your voice message. Please try again."})
        
        # Process as regular chat using the same fallback system as /chat
        try:
            # Try OpenAI first
            logger.info("Processing voice transcription with OpenAI...")
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Med-Whisper, a helpful medical AI assistant. Provide accurate medical information but always remind users this is for informational purposes only."},
                    {"role": "user", "content": text}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            reply = response.choices[0].message.content
            reply += "\n\n⚠️ This information is for educational purposes only. Always consult with a healthcare professional for medical advice."
            
        except Exception as openai_error:
            logger.warning(f"OpenAI failed for voice: {openai_error}. Using built-in medical responses...")
            
            # Use the same intelligent fallback as the regular /chat endpoint
            text_lower = text.lower()
            
            # Use the same medical knowledge base as /chat endpoint
            if any(word in text_lower for word in ['flu', 'influenza', 'fever', 'cold']):
                reply = """**Flu and Cold Information:**

**Common Flu Symptoms:**
• High fever (usually 100.4°F/38°C or higher)
• Body aches and muscle pain
• Fatigue and weakness
• Headache
• Dry cough
• Sore throat

**Treatment:**
• Rest and plenty of fluids
• Over-the-counter fever reducers
• Antiviral medications (if prescribed early)
• Warm salt water gargles for sore throat

**When to Seek Medical Care:**
• Difficulty breathing or shortness of breath
• High fever that doesn't respond to medication
• Severe or persistent vomiting
• Signs of dehydration"""

            elif any(word in text_lower for word in ['covid', 'coronavirus', 'pandemic']):
                reply = """**COVID-19 Information:**

**Common Symptoms:**
• Fever or chills
• Cough (usually dry)
• Shortness of breath
• Fatigue
• Loss of taste or smell
• Sore throat
• Body aches

**Prevention:**
• Vaccination when eligible
• Wear masks in crowded spaces
• Practice social distancing
• Wash hands frequently
• Avoid touching face

**When to Test:**
• If you have symptoms
• After close contact with positive case
• Before gathering with vulnerable people"""

            elif any(word in text_lower for word in ['diet', 'nutrition', 'food', 'healthy eating']):
                reply = """**Healthy Diet Guidelines:**

**Balanced Nutrition:**
• 5-9 servings of fruits and vegetables daily
• Whole grains over refined grains
• Lean proteins (fish, poultry, beans)
• Limited processed foods and added sugars
• Adequate hydration (8 glasses water daily)

**Heart-Healthy Foods:**
• Fatty fish (salmon, mackerel)
• Nuts and seeds
• Olive oil and avocados
• Leafy green vegetables
• Berries and citrus fruits

**General Guidelines:**
• Eat regular, balanced meals
• Control portion sizes
• Limit sodium and saturated fats
• Choose nutrient-dense foods"""

            elif any(word in text_lower for word in ['doctor', 'medical care', 'emergency', 'hospital']):
                reply = """**When to Seek Medical Care:**

**Emergency Situations (Call 911):**
• Chest pain or difficulty breathing
• Signs of stroke (FAST: Face drooping, Arm weakness, Speech difficulty, Time to call)
• Severe allergic reactions
• Loss of consciousness
• Severe bleeding

**Urgent Care Needed:**
• High fever with severe symptoms
• Persistent vomiting or diarrhea
• Signs of serious infection
• Moderate injuries requiring attention

**Regular Check-ups:**
• Annual physical exams
• Preventive screenings as recommended
• Dental cleanings every 6 months
• Eye exams as needed"""

            else:
                reply = f"""**Medical Information (Voice Response)**

Thank you for your voice question: "{text}"

**General Health Guidance:**
• Monitor your symptoms and their progression
• Stay hydrated and get adequate rest
• Follow basic preventive health measures
• Keep track of any changes or concerns

**Preventive Health Tips:**
• Regular exercise (150 minutes moderate activity weekly)
• Balanced diet with plenty of fruits and vegetables
• Adequate sleep (7-9 hours nightly)
• Regular medical check-ups
• Stress management techniques

**When to Consult Healthcare Providers:**
• Persistent or worsening symptoms
• New or concerning changes in health
• Questions about medications or treatments
• Preventive care and screenings"""

            reply += """

🎤 **Voice Message Processed Successfully**

⚠️ **Important:** This is general information only. For specific medical concerns, always consult with a qualified healthcare professional."""
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        return JSONResponse(content={"text": reply})
    except Exception as e:
        logger.error(f"Error in /chat/voice: {e}")
        return JSONResponse(content={"text": "Sorry, I couldn't process your voice message. Please try speaking clearly or use text input."}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
