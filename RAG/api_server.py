"""
REST API Server for MedWhisper RAG System
For integration with Telegram Bot and other frontends
"""

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import uvicorn
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from rag_engine import MedWhisperRAG

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key Security (set via environment variable)
API_KEY = os.getenv("MEDWHISPER_API_KEY", "medwhisper-secret-key-change-this")
logger.info(f"API Key loaded: {API_KEY[:10]}..." if len(API_KEY) > 10 else "API Key loaded")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key from request header"""
    if api_key == API_KEY:
        return api_key
    raise HTTPException(
        status_code=403,
        detail="Invalid or missing API key. Include 'X-API-Key' in request headers."
    )

# Initialize FastAPI app
app = FastAPI(
    title="MedWhisper RAG API",
    description="Medical Question Answering API with RAG",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG engine (singleton)
rag_engine = None

# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for medical queries"""
    query: str = Field(..., description="Medical question or query")
    user_id: str = Field(..., description="User ID (e.g., Telegram user ID)")
    user_role: str = Field(
        default="clinician",
        description="User role: researcher, clinician, student, or auditor"
    )
    patient_id: Optional[str] = Field(None, description="Patient ID for patient-specific queries")
    include_differential: bool = Field(False, description="Include differential diagnosis")
    include_timeline: bool = Field(False, description="Include temporal timeline")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What are the symptoms of diabetes?",
                "user_id": "telegram_123456",
                "user_role": "student",
                "patient_id": None,
                "include_differential": False,
                "include_timeline": False
            }
        }

class QueryResponse(BaseModel):
    """Response model for medical queries"""
    response: str  # Only required field
    success: Optional[bool] = None
    query_id: Optional[str] = None
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    model_used: Optional[str] = None
    retrieved_documents: Optional[int] = None
    confidence_score: Optional[float] = None
    citations_valid: Optional[bool] = None
    safe: Optional[bool] = None
    warnings: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "query_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "telegram_123456",
                "response": "Diabetes symptoms include...",
                "user_role": "student",
                "model_used": "Gemini",
                "retrieved_documents": 5,
                "confidence_score": 0.89,
                "citations_valid": True,
                "safe": True,
                "warnings": []
            }
        }

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    rag_engine_ready: bool

@app.on_event("startup")
async def startup_event():
    """Initialize RAG engine on startup"""
    global rag_engine
    logger.info("Starting MedWhisper API server...")
    try:
        rag_engine = MedWhisperRAG()
        rag_engine.build_knowledge_base()
        logger.info("RAG engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG engine: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global rag_engine
    if rag_engine:
        rag_engine.close()
    logger.info("MedWhisper API server shut down")

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "rag_engine_ready": rag_engine is not None
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if rag_engine else "initializing",
        "version": "1.0.0",
        "rag_engine_ready": rag_engine is not None
    }

@app.post("/query", response_model=QueryResponse, response_model_exclude_none=True)
async def process_query(request: QueryRequest):
    """
    Process a medical query with RAG
    
    Args:
        request: QueryRequest with query text, user info, and options
    
    Returns:
        QueryResponse with answer and metadata
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    # Validate user role
    valid_roles = ["researcher", "clinician", "student", "auditor"]
    if request.user_role not in valid_roles:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid user_role. Must be one of: {valid_roles}"
        )
    
    try:
        logger.info(f"Processing query from user {request.user_id} (role: {request.user_role})")
        
        # Process query through RAG engine
        result = rag_engine.query(
            query_text=request.query,
            patient_id=request.patient_id,
            include_differential=request.include_differential,
            include_timeline=request.include_timeline,
            user_role=request.user_role
        )
        
        # Determine model used
        is_fallback = result.get('used_fallback', False) or result['num_retrieved_docs'] == 0
        model_used = "ClinicalCamel (Fallback)" if is_fallback else "Gemini (Primary)"
        
        # CLEAN RESPONSE FOR FALLBACK (no retrieval)
        if is_fallback:
            logger.info(f"✅ Fallback response: {result['query_id']}")
            return {
                "response": result['response'],
                "source": "General Medical Knowledge (ClinicalCamel)",
                "confidence": "N/A - No database retrieval",
                "citations": "None - Answer based on medical training"
            }
        
        # FULL RESPONSE FOR RETRIEVAL-BASED QUERIES WITH CONFIDENCE & CITATIONS
        response_data = {
            "response": result['response'],
            "source": f"Database Retrieval ({result['num_retrieved_docs']} documents)",
            "confidence": f"{result['grounding_score']:.2%}",
            "citations_valid": "Yes" if result['citations_valid'] else "No",
            "model_used": model_used,
            "retrieved_documents": result['num_retrieved_docs']
        }
        
        # Add detailed metadata for non-student roles
        if request.user_role != "student":
            response_data["query_id"] = result['query_id']
            response_data["user_id"] = request.user_id
            response_data["user_role"] = request.user_role
            response_data["safe"] = result['safe']
            response_data["warnings"] = result.get('safety_warnings', [])
        
        logger.info(f"Query processed successfully: {result['query_id']}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/roles")
async def get_roles():
    """Get available user roles"""
    return {
        "roles": [
            {
                "id": "researcher",
                "name": "Clinical Researcher / Data Scientist",
                "description": "Full access with detailed metrics for research"
            },
            {
                "id": "clinician",
                "name": "Resident / Clinician",
                "description": "Clinical decision support with citations"
            },
            {
                "id": "student",
                "name": "Instructor / Medical Student",
                "description": "Educational responses without technical metrics"
            },
            {
                "id": "auditor",
                "name": "AI Safety Reviewer / Compliance Officer",
                "description": "Full audit trail and compliance metrics"
            }
        ]
    }

# For Telegram Bot Integration
class TelegramUpdate(BaseModel):
    """Telegram webhook update model"""
    message: dict
    user_role: str = "student"  # Default role for new users

@app.post("/telegram/webhook")
async def telegram_webhook(update: TelegramUpdate):
    """
    Webhook endpoint for Telegram bot
    
    The Telegram bot should send:
    - message: Telegram message object
    - user_role: User's role from their profile
    """
    try:
        # Extract message details
        chat_id = update.message.get('chat', {}).get('id')
        user_id = update.message.get('from', {}).get('id')
        message_text = update.message.get('text', '')
        
        if not message_text:
            return {"error": "No message text provided"}
        
        # Process through RAG
        query_request = QueryRequest(
            query=message_text,
            user_id=str(user_id),
            user_role=update.user_role
        )
        
        response = await process_query(query_request)
        
        # Return response formatted for Telegram
        return {
            "chat_id": chat_id,
            "text": response.response,
            "parse_mode": "Markdown"
        }
        
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {
            "error": str(e)
        }

if __name__ == "__main__":
    # Run the API server
    import os
    port = int(os.getenv("PORT", 8010))  # Default to 8010, or use PORT env var
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

