import re
from typing import Dict, List, Tuple, Any
from config import config
import logging
from embeddings import BioClinicalBERTEmbedder
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafetyGate:
    def __init__(self, embedder: BioClinicalBERTEmbedder = None):
        self.embedder = embedder
        
        # Medical safety keywords
        self.critical_terms = [
            "suicide", "self-harm", "overdose", "cardiac arrest", "respiratory failure",
            "septic shock", "anaphylaxis", "severe hemorrhage", "stroke", "myocardial infarction"
        ]
        
        self.unsafe_patterns = [
            r"ignore.*warning",
            r"skip.*safety",
            r"bypass.*protocol",
            r"don't tell.*doctor"
        ]
        
        self.disclaimer_required_terms = [
            "diagnosis", "treatment", "medication", "dosage", "surgery",
            "prescription", "therapy", "prognosis"
        ]
    
    def check_query_safety(self, query: str) -> Tuple[bool, str]:
        """Check if query is safe to process"""
        query_lower = query.lower()
        
        # Check for critical medical emergencies
        for term in self.critical_terms:
            if term in query_lower and "emergency" in query_lower:
                return False, f"CRITICAL: Query mentions emergency condition '{term}'. Immediate medical attention required."
        
        # Check for unsafe patterns
        for pattern in self.unsafe_patterns:
            if re.search(pattern, query_lower):
                return False, f"UNSAFE: Query contains pattern that bypasses safety protocols."
        
        return True, "Query passed safety check"
    
    def check_response_safety(self, response: str) -> Tuple[bool, List[str]]:
        """Check if generated response is safe"""
        warnings = []
        
        # Check response length
        if len(response) > config.MAX_RESPONSE_LENGTH:
            warnings.append("Response exceeds maximum safe length")
        
        # Check for absolute medical claims without citations
        absolute_patterns = [
            r"always\s+(?:give|use|prescribe)",
            r"never\s+(?:give|use|prescribe)",
            r"definitely\s+(?:has|needs|requires)",
            r"must\s+(?:take|receive|undergo)"
        ]
        
        for pattern in absolute_patterns:
            if re.search(pattern, response.lower()):
                if "[DocID:" not in response:
                    warnings.append(f"Absolute medical claim without citation: {pattern}")
        
        # Check for required disclaimers
        response_lower = response.lower()
        requires_disclaimer = any(term in response_lower for term in self.disclaimer_required_terms)
        
        disclaimer_present = any(phrase in response_lower for phrase in [
            "consult", "healthcare provider", "medical professional", "doctor",
            "not a substitute", "seek medical"
        ])
        
        if requires_disclaimer and not disclaimer_present:
            warnings.append("Medical advice provided without appropriate disclaimer")
        
        is_safe = len(warnings) == 0
        return is_safe, warnings
    
    def add_safety_disclaimer(self, response: str) -> str:
        """Add safety disclaimer to response"""
        disclaimer = "\n\n⚠️ IMPORTANT: This information is for educational purposes only and should not replace professional medical advice. Always consult with qualified healthcare providers for diagnosis and treatment decisions."
        
        if disclaimer.lower() not in response.lower():
            return response + disclaimer
        
        return response
    
    def check_hallucination(self, response: str, context_docs: List[Dict[str, Any]]) -> Tuple[float, bool]:
        """Check for potential hallucination by comparing response to context"""
        if not context_docs or not self.embedder:
            return 0.0, False
        
        # Extract claims from response (sentences)
        sentences = re.split(r'[.!?]\s+', response)
        claims = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not claims:
            return 0.0, False
        
        # Get context content
        context_texts = [doc.get('content', '') for doc in context_docs]
        context_combined = " ".join(context_texts)
        
        # Compute semantic similarity between claims and context
        claim_embeddings = self.embedder.encode(claims)
        context_embedding = self.embedder.encode([context_combined])[0]
        
        # Calculate cosine similarity
        similarities = np.dot(claim_embeddings, context_embedding)
        avg_similarity = float(np.mean(similarities))
        
        is_grounded = avg_similarity >= config.HALLUCINATION_THRESHOLD
        
        return avg_similarity, is_grounded
    
    def verify_citations(self, response: str, retrieved_doc_ids: List[str]) -> Tuple[bool, List[str]]:
        """Verify that all cited documents exist in retrieved set"""
        # Extract cited doc IDs from response
        cited_ids = re.findall(r'\[DocID:\s*([^\]]+)\]', response)
        
        invalid_citations = []
        for cited_id in cited_ids:
            if cited_id.strip() not in retrieved_doc_ids:
                invalid_citations.append(cited_id)
        
        all_valid = len(invalid_citations) == 0
        return all_valid, invalid_citations

class AntiHallucinationChecker:
    def __init__(self, embedder: BioClinicalBERTEmbedder):
        self.embedder = embedder
        self.threshold = config.HALLUCINATION_THRESHOLD
    
    def check_factual_consistency(self, response: str, context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive hallucination check"""
        if not context_docs:
            return {
                "grounded": False,
                "confidence": 0.0,
                "issue": "No context documents provided"
            }
        
        # Split response into checkable claims
        claims = self._extract_medical_claims(response)
        
        if not claims:
            return {
                "grounded": True,
                "confidence": 1.0,
                "issue": None
            }
        
        # Check each claim against context
        context_texts = [doc.get('content', '') for doc in context_docs]
        
        grounding_scores = []
        for claim in claims:
            score = self._check_claim_grounding(claim, context_texts)
            grounding_scores.append(score)
        
        avg_score = np.mean(grounding_scores)
        is_grounded = avg_score >= self.threshold
        
        return {
            "grounded": is_grounded,
            "confidence": float(avg_score),
            "num_claims": len(claims),
            "issue": None if is_grounded else "Response contains claims not supported by context"
        }
    
    def _extract_medical_claims(self, text: str) -> List[str]:
        """Extract medical claims from text"""
        # Split into sentences
        sentences = re.split(r'[.!?]\n', text)
        
        # Filter for medical claims (sentences with medical terms)
        medical_indicators = [
            "patient", "diagnosis", "treatment", "symptom", "condition",
            "medication", "test", "result", "procedure", "clinical"
        ]
        
        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            if any(indicator in sentence.lower() for indicator in medical_indicators):
                claims.append(sentence)
        
        return claims
    
    def _check_claim_grounding(self, claim: str, context_texts: List[str]) -> float:
        """Check if a claim is grounded in context"""
        if not context_texts:
            return 0.0
        
        claim_embedding = self.embedder.encode([claim])[0]
        context_embeddings = self.embedder.encode(context_texts)
        
        # Get max similarity to any context document
        similarities = np.dot(context_embeddings, claim_embedding)
        max_similarity = float(np.max(similarities))
        
        return max_similarity




