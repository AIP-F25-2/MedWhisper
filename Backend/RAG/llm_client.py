import google.generativeai as genai
from typing import Optional, Dict, Any
import logging
from config import config
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.gemini_api_key = config.GEMINI_API_KEY
        self.primary_model = None
        self.fallback_available = False
        
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.primary_model = genai.GenerativeModel(config.GEMINI_MODEL)
            logger.info(f"Gemini {config.GEMINI_MODEL} initialized")
        else:
            logger.warning("GEMINI_API_KEY not set. Using fallback only.")
    
    def generate(self, prompt: str, temperature: float = None, 
                max_tokens: int = None, top_p: float = None) -> Optional[str]:
        """Generate response using primary model with fallback"""
        temperature = temperature or config.TEMPERATURE
        max_tokens = max_tokens or config.MAX_TOKENS
        top_p = top_p or config.TOP_P
        
        # Try primary model (Gemini)
        if self.primary_model:
            try:
                response = self._generate_gemini(prompt, temperature, max_tokens, top_p)
                if response:
                    return response
            except Exception as e:
                logger.error(f"Gemini generation failed: {e}")
        
        # Fallback to ClinicalCamel (simulated - requires actual API/local setup)
        logger.info("Using fallback model")
        return self._generate_fallback(prompt, temperature, max_tokens)
    
    def _generate_gemini(self, prompt: str, temperature: float, 
                        max_tokens: int, top_p: float) -> Optional[str]:
        """Generate using Gemini API"""
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=top_p,
            )
            
            safety_settings = [
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            ]
            
            response = self.primary_model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Check if response was blocked or empty
            if response and hasattr(response, 'text') and response.text:
                return response.text
            elif response and hasattr(response, 'parts') and response.parts:
                # Try to extract text from parts
                return "".join([part.text for part in response.parts if hasattr(part, 'text')])
            else:
                # Response was blocked or empty
                logger.warning(f"Gemini response empty or blocked. Finish reason: {getattr(response, 'finish_reason', 'unknown')}")
                return None
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
    
    def _generate_fallback(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """
        Fallback generation using ClinicalCamel (simulated with improved medical reasoning)
        
        This represents the ClinicalCamel-70B model behavior:
        - Trained on clinical data
        - Good for general medical questions
        - Not patient-specific
        """
        import re
        
        # Check if this is a general medical question (not patient-specific)
        if "Question:" in prompt and "general medical knowledge" in prompt.lower():
            # Extract the question
            question_match = re.search(r'Question: (.*?)(?:\n|$)', prompt, re.DOTALL)
            if question_match:
                question = question_match.group(1).strip()
                
                # ClinicalCamel simulation - provides medical knowledge responses
                # In production, this would call actual ClinicalCamel API or local model
                response = f"""**Based on Clinical Medical Knowledge (ClinicalCamel):**

I'll provide information about: {question}

This is a general medical knowledge question. While I cannot access specific patient records in this context, I can provide evidence-based medical information based on clinical training.

**Note:** This response is generated using the ClinicalCamel fallback model, which specializes in general medical knowledge. For patient-specific information, ensure proper medical records are available in the system.

**Important:** For comprehensive and patient-specific medical information, please ensure:
1. The Gemini API is properly configured for optimal performance
2. Relevant medical records are available in the database
3. Always consult qualified healthcare providers for medical decisions

For the best experience and most accurate patient-specific responses, please configure the GEMINI_API_KEY."""

                return response
        
        # Try to extract relevant context information
        context_match = re.search(r'RETRIEVED CONTEXT:(.*?)PATIENT QUERY:', prompt, re.DOTALL)
        
        if context_match:
            context_text = context_match.group(1).strip()
            # Extract key information from documents
            doc_contents = re.findall(r'Content: (.*?)(?=Document \d+|$)', context_text, re.DOTALL)
            
            if doc_contents:
                # Create a basic response from retrieved content
                response_parts = ["**Based on available medical records (ClinicalCamel mode):**\n"]
                
                for i, content in enumerate(doc_contents[:3], 1):  # Use top 3 documents
                    content_clean = content.strip()[:200]  # First 200 chars
                    if content_clean:
                        response_parts.append(f"{i}. {content_clean}")
                
                response_parts.append("\n**Note:** This response is generated using the ClinicalCamel fallback model.")
                response_parts.append("For optimal performance and comprehensive analysis, please configure the Gemini API key.")
                
                return "\n".join(response_parts)
        
        # Generic fallback
        fallback_response = """**ClinicalCamel Fallback Mode:**

I apologize, but I'm unable to generate a detailed response at this moment.

**Recommendations:**
1. Consult with appropriate medical professionals
2. Review the patient's complete medical history
3. Follow established clinical guidelines
4. Consider all available diagnostic information

**System Note:** This is the ClinicalCamel fallback model. For best results:
- Configure GEMINI_API_KEY for the primary Gemini model
- Ensure medical records are properly indexed in the database

**Important:** This fallback response should not be used for clinical decision-making."""
        
        return fallback_response
    
    def generate_with_context(self, query: str, context_docs: list, 
                            system_prompt: str = None, use_fallback_for_general: bool = False) -> str:
        """Generate response with retrieved context"""
        if not system_prompt:
            system_prompt = """You are MedWhisper, an AI medical assistant specialized in clinical decision support.

Your responsibilities:
1. Provide evidence-based medical information
2. Always cite sources from the provided context
3. Never make up information not present in the context
4. Acknowledge uncertainty when information is incomplete
5. Prioritize patient safety in all recommendations
6. Use clear, professional medical language

Guidelines:
- Reference specific document IDs when citing information
- Distinguish between facts and clinical interpretations
- Flag any potential safety concerns
- Recommend further investigation when appropriate"""
        
        # Check if we should use fallback (ClinicalCamel) instead
        # Use fallback when: NO documents OR documents are irrelevant
        if use_fallback_for_general and len(context_docs) == 0:
            logger.info("No relevant retrieval results - routing to ClinicalCamel (fallback) for general medical knowledge")
            
            # ClinicalCamel fallback - for general medical questions without good retrieval
            # Uses LLM's medical training directly (simulating ClinicalCamel behavior)
            general_medical_prompt = f"""You are a helpful medical AI assistant. Answer the following medical question in PLAIN TEXT format for a chat interface.

Question: {query}

CRITICAL FORMATTING RULES:
- Use PLAIN TEXT only - NO Markdown, NO asterisks (**), NO special formatting
- For bullet points, use simple dashes (-) or numbers (1., 2., 3.)
- Use line breaks for readability
- Keep it conversational and easy to read
- Make each point on its own line
- Don't use bold, italics, or any special characters
- Write as if sending a text message

Provide a clear, readable answer:"""
            
            response = self.generate(general_medical_prompt, temperature=0.3, max_tokens=1024)
            
            # Clean up the response - remove any metadata and Markdown
            if response:
                # Remove common LLM artifacts
                response = response.replace("**Based on Clinical Medical Knowledge (ClinicalCamel):**", "").strip()
                response = response.replace("**[Response generated by ClinicalCamel - General Medical Knowledge Mode]**", "").strip()
                
                # Remove Markdown formatting for plain text
                import re
                # Remove bold **text** -> text
                response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)
                # Remove italic *text* -> text (but keep bullet points with single *)
                response = re.sub(r'(?<!\*)\*(?!\*)([^\*]+?)(?<!\*)\*(?!\*)', r'\1', response)
                # Clean up any remaining markdown headers
                response = re.sub(r'^#+\s+', '', response, flags=re.MULTILINE)
                
                # Add disclaimer at the end (plain text)
                response += "\n\nNote: This information is for educational purposes only. Always consult with a qualified healthcare provider for medical advice."
            
            return response
        
        # Otherwise use primary model (Gemini) with retrieved context
        # Build context from documents
        context_text = self._format_context(context_docs)
        
        prompt = f"""{system_prompt}

RETRIEVED CONTEXT:
{context_text}

PATIENT QUERY:
{query}

INSTRUCTIONS:
- Base your response on the provided context
- Cite document IDs in format [DocID: xxx]
- If context is insufficient, explicitly state this
- Provide reasoning for clinical suggestions
- Include relevant temporal information if available

RESPONSE:"""
        
        return self.generate(prompt)
    
    def _format_context(self, context_docs: list) -> str:
        """Format retrieved documents for prompt"""
        if not context_docs:
            return "No relevant context found."
        
        formatted = []
        for i, doc in enumerate(context_docs, 1):
            doc_text = f"""
Document {i} [DocID: {doc.get('doc_id', 'unknown')}]
Type: {doc.get('doc_type', 'unknown')}
Patient: {doc.get('patient_id', 'unknown')}
Timestamp: {doc.get('timestamp', 'unknown')}
Relevance Score: {doc.get('retrieval_score', 0):.3f}
Content: {doc.get('content', '')[:500]}
"""
            formatted.append(doc_text)
        
        return "\n".join(formatted)

