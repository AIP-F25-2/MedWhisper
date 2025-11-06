"""
LangGraph Orchestrator for Multi-Agent MedWhisper RAG
Implements: Retriever → Summarizer → Image-Examiner → Safety-Gate → Responder
"""

import logging
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from agents import RetrieverAgent, SummarizerAgent, SafetyGateAgent, ResponderAgent
from agents.image_examiner_agent import ImageExaminerAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state structure for LangGraph
class MedWhisperState(TypedDict, total=False):
    # Input
    query: str
    patient_id: str
    user_role: str
    include_differential: bool
    include_timeline: bool
    
    # Retriever outputs
    retrieved_docs: list
    num_retrieved: int
    retrieval_completed: bool
    
    # Summarizer outputs
    summary: str
    key_findings: list
    summarization_completed: bool
    
    # Image-Examiner outputs (placeholder)
    image_findings: list
    image_analysis_completed: bool
    
    # Responder outputs
    response: str
    model_used: str
    used_fallback: bool
    response_generated: bool
    
    # Safety-Gate outputs
    safe: bool
    safety_warnings: list
    citations_valid: bool
    invalid_citations: list
    is_grounded: bool
    grounding_score: float
    hallucination_issue: str
    safety_check_completed: bool
    
    # Error handling
    error: str


class MedWhisperOrchestrator:
    """
    LangGraph-based orchestrator for multi-agent RAG pipeline
    
    Agent Chain:
    Retriever → Summarizer → Image-Examiner → Safety-Gate → Responder
    """
    
    def __init__(self):
        logger.info("[Orchestrator] Initializing multi-agent pipeline...")
        
        # Initialize agents
        self.retriever_agent = RetrieverAgent()
        self.summarizer_agent = SummarizerAgent()
        self.image_examiner_agent = ImageExaminerAgent()  # Placeholder
        self.responder_agent = ResponderAgent()
        self.safety_gate_agent = SafetyGateAgent()
        
        # Build LangGraph
        self.graph = self._build_graph()
        
        logger.info("[Orchestrator] Multi-agent pipeline initialized ✅")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph agent chain
        
        Flow:
        START → Retriever → Summarizer → Image-Examiner → Responder → Safety-Gate → END
        """
        # Create graph
        workflow = StateGraph(MedWhisperState)
        
        # Add nodes (agents)
        workflow.add_node("retriever", self.retriever_agent)
        workflow.add_node("summarizer", self.summarizer_agent)
        workflow.add_node("image_examiner", self.image_examiner_agent)
        workflow.add_node("responder", self.responder_agent)
        workflow.add_node("safety_gate", self.safety_gate_agent)
        
        # Define edges (agent chain)
        workflow.set_entry_point("retriever")
        workflow.add_edge("retriever", "summarizer")
        workflow.add_edge("summarizer", "image_examiner")
        workflow.add_edge("image_examiner", "responder")
        workflow.add_edge("responder", "safety_gate")
        workflow.add_edge("safety_gate", END)
        
        # Compile graph
        app = workflow.compile()
        
        logger.info("[Orchestrator] Agent chain: Retriever → Summarizer → Image-Examiner → Responder → Safety-Gate")
        
        return app
    
    def run(self, query: str, patient_id: str = None, user_role: str = "student",
            include_differential: bool = False, include_timeline: bool = False) -> Dict[str, Any]:
        """
        Execute the multi-agent pipeline
        
        Args:
            query: User's medical question
            patient_id: Optional patient ID for patient-specific queries
            user_role: User role (student/clinician/researcher/auditor)
            include_differential: Include differential diagnosis
            include_timeline: Include patient timeline
            
        Returns:
            Final state with response and all agent outputs
        """
        logger.info(f"[Orchestrator] Starting pipeline for query: {query[:50]}...")
        
        # Initialize state
        initial_state = {
            "query": query,
            "patient_id": patient_id,
            "user_role": user_role,
            "include_differential": include_differential,
            "include_timeline": include_timeline,
        }
        
        try:
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            logger.info(f"[Orchestrator] Pipeline complete ✅")
            logger.info(f"  - Retrieved: {final_state.get('num_retrieved', 0)} docs")
            logger.info(f"  - Model: {final_state.get('model_used', 'unknown')}")
            logger.info(f"  - Safe: {final_state.get('safe', False)}")
            logger.info(f"  - Grounded: {final_state.get('is_grounded', False)}")
            
            return final_state
            
        except Exception as e:
            logger.error(f"[Orchestrator] Pipeline failed: {e}")
            return {
                "query": query,
                "response": f"I apologize, but an error occurred: {str(e)}",
                "error": str(e),
                "safe": False,
                "used_fallback": True
            }
    
    def close(self):
        """Cleanup agent resources"""
        if hasattr(self.retriever_agent, 'close'):
            self.retriever_agent.close()


# Convenience function
def create_orchestrator() -> MedWhisperOrchestrator:
    """Factory function to create orchestrator"""
    return MedWhisperOrchestrator()




