import uuid
import json
from datetime import datetime
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from core.config import settings
from core.supabase_client import supabase
from agents.parser_agent import parser_agent, ParsedProblem
from agents.intent_router_agent import intent_router, RoutingDecision
from agents.solver_agent import solver_agent, SolverOutput
from agents.verifier_agent import verifier_agent, VerifierOutput
from agents.explainer_agent import explainer_agent, ExplainerOutput
from services.rag_service import rag_service

# ============================================================================
# 1. STATE SCHEMA - Defines what data flows through the graph
# ============================================================================

class AgentTrace(TypedDict):
    agent_name: str
    timestamp: str
    status: str  # "success", "error", "pending"
    confidence: Optional[float]
    details: Dict[str, Any]

class MathMentorState(TypedDict):
    # Session Management
    session_id: str
    hitl_status: str  # "pending", "approved", "rejected", "completed"
    hitl_reason: Optional[str]
    hitl_required: bool
    hitl_feedback: Optional[str]
    
    # Input Data
    media_url: Optional[str]
    media_type: str  # "image", "audio", "text"
    raw_input: str  # Raw OCR/ASR output
    confirmed_text: str  # User-confirmed text after OCR/ASR review
    
    # Parser Output
    parsed_problem: Optional[Dict[str, Any]]
    
    # Router Output
    routing_decision: Optional[Dict[str, Any]]
    
    # RAG Context
    rag_context: List[Dict[str, Any]]
    rag_sources: List[str]
    
    # Solver Output
    solution: Optional[Dict[str, Any]]
    
    # Verifier Output
    verification: Optional[Dict[str, Any]]
    
    # Explainer Output
    explanation: Optional[Dict[str, Any]]
    
    # Final Output
    final_output: Optional[Dict[str, Any]]
    
    # Agent Trace (for UI display)
    agent_trace: List[AgentTrace]
    
    # Memory & Learning
    memory_used: bool
    similar_problems: List[Dict[str, Any]]
    
    # Metadata
    created_at: str
    updated_at: str
    error_message: Optional[str]

# ============================================================================
# 2. HELPER FUNCTIONS - State management & Supabase integration
# ============================================================================

def create_initial_state(session_id: str, confirmed_text: str, media_type: str = "text", media_url: Optional[str] = None) -> MathMentorState:
    """Create initial state for a new session"""
    now = datetime.now().isoformat()
    return {
        "session_id": session_id,
        "hitl_status": "pending",
        "hitl_reason": None,
        "hitl_required": False,
        "hitl_feedback": None,
        "media_url": media_url,
        "media_type": media_type,
        "raw_input": confirmed_text,
        "confirmed_text": confirmed_text,
        "parsed_problem": None,
        "routing_decision": None,
        "rag_context": [],
        "rag_sources": [],
        "solution": None,
        "verification": None,
        "explanation": None,
        "final_output": None,
        "agent_trace": [],
        "memory_used": False,
        "similar_problems": [],
        "created_at": now,
        "updated_at": now,
        "error_message": None
    }

def save_session_to_supabase(state: MathMentorState):
    """Save current state to Supabase for HITL persistence"""
    try:
        supabase.table("sessions").upsert({
            "id": state["session_id"],
            "user_input": state["confirmed_text"],
            "media_url": state["media_url"],
            "media_type": state["media_type"],
            "ocr_text": state["raw_input"],
            "parsed_problem": state["parsed_problem"],
            "solution": json.dumps(state["solution"]) if state["solution"] else None,
            "hitl_status": state["hitl_status"],
            "hitl_feedback": state["hitl_feedback"],
            "created_at": state["created_at"],
            "updated_at": state["updated_at"]
        }).execute()
    except Exception as e:
        print(f"Error saving session to Supabase: {str(e)}")

def load_session_from_supabase(session_id: str) -> Optional[MathMentorState]:
    """Load existing state from Supabase (for HITL resume)"""
    try:
        response = supabase.table("sessions").select("*").eq("id", session_id).execute()
        if response.data and len(response.data) > 0:
            row = response.data[0]
            return {
                "session_id": row["id"],
                "hitl_status": row["hitl_status"],
                "hitl_reason": None,
                "hitl_required": row["hitl_status"] == "pending_approval",
                "hitl_feedback": row.get("hitl_feedback"),
                "media_url": row.get("media_url"),
                "media_type": row.get("media_type", "text"),
                "raw_input": row.get("ocr_text", ""),
                "confirmed_text": row.get("user_input", ""),
                "parsed_problem": row.get("parsed_problem"),
                "routing_decision": None,
                "rag_context": [],
                "rag_sources": [],
                "solution": json.loads(row["solution"]) if row.get("solution") else None,
                "verification": None,
                "explanation": None,
                "final_output": None,
                "agent_trace": [],
                "memory_used": False,
                "similar_problems": [],
                "created_at": row.get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat(),
                "error_message": None
            }
    except Exception as e:
        print(f"Error loading session from Supabase: {str(e)}")
    return None

def add_agent_trace(state: MathMentorState, agent_name: str, status: str, confidence: Optional[float] = None, details: Dict[str, Any] = {}) -> MathMentorState:
    """Add agent execution to trace for UI display"""
    trace_entry: AgentTrace = {
        "agent_name": agent_name,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "confidence": confidence,
        "details": details
    }
    state["agent_trace"].append(trace_entry)
    state["updated_at"] = datetime.now().isoformat()
    return state

# ============================================================================
# 3. AGENT NODES - Each agent as a graph node
# ============================================================================

async def parser_node(state: MathMentorState) -> MathMentorState:
    """Parser Agent Node - Converts raw text to structured problem"""
    try:
        print(f"[Parser] Processing session: {state['session_id']}")
        
        # Check memory for similar problems first
        similar = await rag_service.find_similar_problems(state["confirmed_text"], limit=2)
        if similar:
            state["similar_problems"] = similar
            state["memory_used"] = True
        
        # Parse the problem
        parsed: ParsedProblem = await parser_agent.parse(state["confirmed_text"])
        state["parsed_problem"] = parsed.dict()
        state = add_agent_trace(state, "Parser", "success", confidence=1.0 if not parsed.needs_clarification else 0.5, details={"topic": parsed.topic, "needs_clarification": parsed.needs_clarification})
        
        # Check if HITL needed due to ambiguity
        if parsed.needs_clarification:
            state["hitl_required"] = True
            state["hitl_reason"] = parsed.ambiguity_reason or "Problem information is ambiguous or incomplete"
            state["hitl_status"] = "pending_approval"
            save_session_to_supabase(state)
        
        print(f"[Parser] Complete. Needs Clarification: {parsed.needs_clarification}")
        
    except Exception as e:
        state = add_agent_trace(state, "Parser", "error", details={"error": str(e)})
        state["error_message"] = f"Parser failed: {str(e)}"
        state["hitl_required"] = True
        state["hitl_reason"] = state["error_message"]
    
    return state

async def intent_router_node(state: MathMentorState) -> MathMentorState:
    """Intent Router Agent Node - Classifies and routes the problem"""
    try:
        print(f"[Router] Routing session: {state['session_id']}")
        
        if not state["parsed_problem"]:
            raise ValueError("No parsed problem available")
        
        # Route the problem
        routing: RoutingDecision = await intent_router.route(state["parsed_problem"])
        state["routing_decision"] = routing.dict()
        state = add_agent_trace(state, "Intent Router", "success", confidence=1.0 if not routing.out_of_scope else 0.3, details={"topic": routing.topic, "strategy": routing.solver_strategy})
        
        # Check if out of scope → HITL
        if routing.out_of_scope:
            state["hitl_required"] = True
            state["hitl_reason"] = routing.reroute_reason or "Problem is outside supported math topics"
            state["hitl_status"] = "pending_approval"
            save_session_to_supabase(state)
        
        print(f"[Router] Complete. Topic: {routing.topic}, Out of Scope: {routing.out_of_scope}")
        
    except Exception as e:
        state = add_agent_trace(state, "Intent Router", "error", details={"error": str(e)})
        state["error_message"] = f"Router failed: {str(e)}"
        state["hitl_required"] = True
        state["hitl_reason"] = state["error_message"]
    
    return state

async def rag_retrieval_node(state: MathMentorState) -> MathMentorState:
    """RAG Retrieval Node - Fetches relevant knowledge base chunks"""
    try:
        print(f"[RAG] Retrieving context for session: {state['session_id']}")
        
        if not state["routing_decision"]:
            raise ValueError("No routing decision available")
        
        # Get RAG query from routing decision
        rag_query = state["routing_decision"].get("rag_query", state["confirmed_text"])
        rag_categories = state["routing_decision"].get("rag_categories", ["formulas"])
        
        # Retrieve from vector store
        chunks = await rag_service.search(rag_query, categories=rag_categories, top_k=settings.RAG_TOP_K)
        state["rag_context"] = chunks
        state["rag_sources"] = [c.get("metadata", {}).get("source", "Unknown") for c in chunks]
        state = add_agent_trace(state, "RAG Retrieval", "success", confidence=1.0, details={"chunks_retrieved": len(chunks), "sources": state["rag_sources"]})
        
        print(f"[RAG] Complete. Retrieved {len(chunks)} chunks")
        
    except Exception as e:
        state = add_agent_trace(state, "RAG Retrieval", "error", details={"error": str(e)})
        # Continue anyway - RAG is optional enhancement
    
    return state

async def solver_node(state: MathMentorState) -> MathMentorState:
    """Solver Agent Node - Generates the mathematical solution"""
    try:
        print(f"[Solver] Solving session: {state['session_id']}")
        
        if not state["parsed_problem"] or not state["routing_decision"]:
            raise ValueError("Missing parsed problem or routing decision")
        
        # Solve with RAG context
        solution: SolverOutput = await solver_agent.solve(
            parsed_problem=state["parsed_problem"],
            routing_decision=state["routing_decision"],
            rag_context=state["rag_context"]
        )
        state["solution"] = solution.dict()
        state = add_agent_trace(state, "Solver", "success", confidence=solution.confidence_score, details={"method": solution.method_used, "tools": solution.tools_used})
        
        # Low confidence → Will be caught by Verifier
        print(f"[Solver] Complete. Confidence: {solution.confidence_score}")
        
    except Exception as e:
        state = add_agent_trace(state, "Solver", "error", details={"error": str(e)})
        state["error_message"] = f"Solver failed: {str(e)}"
        # Create minimal solution for verifier to catch
        state["solution"] = {
            "final_answer": "Unable to solve",
            "confidence_score": 0.3,
            "steps": [],
            "needs_verification": True
        }
    
    return state

async def verifier_node(state: MathMentorState) -> MathMentorState:
    """Verifier Agent Node - Validates solution correctness"""
    try:
        print(f"[Verifier] Verifying session: {state['session_id']}")
        
        if not state["solution"]:
            raise ValueError("No solution available to verify")
        
        # Verify the solution
        verification: VerifierOutput = await verifier_agent.verify(
            parsed_problem=state["parsed_problem"],
            solution=state["solution"],
            routing_decision=state["routing_decision"],
            rag_context=state["rag_context"]
        )
        state["verification"] = verification.dict()
        state = add_agent_trace(state, "Verifier", "success", confidence=verification.correctness_score, details={"checks_passed": sum(1 for c in verification.checks_performed if c.passed), "total_checks": len(verification.checks_performed)})
        
        # HITL Decision Point
        if verification.hitl_required:
            state["hitl_required"] = True
            state["hitl_reason"] = verification.hitl_reason
            state["hitl_status"] = "pending_approval"
            state["hitl_suggested_corrections"] = verification.suggested_corrections
            save_session_to_supabase(state)
            print(f"[Verifier] HITL Required: {verification.hitl_reason}")
        else:
            print(f"[Verifier] Complete. Valid: {verification.solution_valid}")
        
    except Exception as e:
        state = add_agent_trace(state, "Verifier", "error", details={"error": str(e)})
        state["error_message"] = f"Verifier failed: {str(e)}"
        state["hitl_required"] = True
        state["hitl_reason"] = state["error_message"]
    
    return state

async def explainer_node(state: MathMentorState) -> MathMentorState:
    """Explainer Agent Node - Creates student-friendly explanation"""
    try:
        print(f"[Explainer] Generating explanation for session: {state['session_id']}")
        
        if not state["solution"] or not state["verification"]:
            raise ValueError("Missing solution or verification")
        
        # Generate explanation
        explanation: ExplainerOutput = await explainer_agent.explain(
            parsed_problem=state["parsed_problem"],
            solution=state["solution"],
            verification=state["verification"],
            routing_decision=state["routing_decision"],
            rag_context=state["rag_context"]
        )
        state["explanation"] = explanation.dict()
        state = add_agent_trace(state, "Explainer", "success", confidence=explanation.confidence_indicator, details={"sections": len(explanation.step_by_step_explanation), "student_friendly": explanation.student_friendly})
        
        # Build final output
        state["final_output"] = {
            "answer": state["solution"]["final_answer"],
            "explanation": explanation.dict(),
            "confidence": state["verification"]["correctness_score"],
            "rag_sources": state["rag_sources"],
            "agent_trace": state["agent_trace"]
        }
        state["hitl_status"] = "completed"
        save_session_to_supabase(state)
        
        print(f"[Explainer] Complete. Student Friendly: {explanation.student_friendly}")
        
    except Exception as e:
        state = add_agent_trace(state, "Explainer", "error", details={"error": str(e)})
        state["error_message"] = f"Explainer failed: {str(e)}"
        state["hitl_status"] = "error"
    
    return state

async def hitl_node(state: MathMentorState) -> MathMentorState:
    """HITL Node - Pauses workflow for human review"""
    print(f"[HITL] Session {state['session_id']} paused for human review")
    state = add_agent_trace(state, "HITL", "pending", details={"reason": state["hitl_reason"]})
    save_session_to_supabase(state)
    return state

# ============================================================================
# 4. CONDITIONAL EDGES - Routing logic based on state
# ============================================================================

def should_trigger_hitl_after_parser(state: MathMentorState) -> str:
    """Check if HITL needed after Parser"""
    if state.get("hitl_required"):
        return "hitl"
    return "router"

def should_trigger_hitl_after_router(state: MathMentorState) -> str:
    """Check if HITL needed after Router"""
    if state.get("hitl_required"):
        return "hitl"
    return "rag"

def should_trigger_hitl_after_verifier(state: MathMentorState) -> str:
    """Check if HITL needed after Verifier"""
    if state.get("hitl_required"):
        return "hitl"
    return "explainer"

def should_resume_from_hitl(state: MathMentorState) -> str:
    """Check if HITL approved and should resume"""
    if state.get("hitl_status") == "approved":
        # Determine where to resume based on what was completed
        if state.get("parsed_problem") and not state.get("routing_decision"):
            return "router"
        elif state.get("routing_decision") and not state.get("solution"):
            return "rag"
        elif state.get("solution") and not state.get("verification"):
            return "verifier"
        elif state.get("verification") and not state.get("explanation"):
            return "explainer"
    return "hitl"  # Stay in HITL if not approved

# ============================================================================
# 5. BUILD THE GRAPH - Compile LangGraph
# ============================================================================

def build_math_mentor_graph() -> StateGraph:
    """Build and compile the complete multi-agent graph"""
    
    # Initialize graph with state schema
    workflow = StateGraph(MathMentorState)
    
    # Add all nodes
    workflow.add_node("parser", parser_node)
    workflow.add_node("router", intent_router_node)
    workflow.add_node("rag", rag_retrieval_node)
    workflow.add_node("solver", solver_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("explainer", explainer_node)
    workflow.add_node("hitl", hitl_node)
    
    # Set entry point
    workflow.add_edge(START, "parser")
    
    # Parser → Router or HITL
    workflow.add_conditional_edges(
        "parser",
        should_trigger_hitl_after_parser,
        {
            "router": "router",
            "hitl": "hitl"
        }
    )
    
    # Router → RAG or HITL
    workflow.add_conditional_edges(
        "router",
        should_trigger_hitl_after_router,
        {
            "rag": "rag",
            "hitl": "hitl"
        }
    )
    
    # RAG → Solver (always)
    workflow.add_edge("rag", "solver")
    
    # Solver → Verifier (always)
    workflow.add_edge("solver", "verifier")
    
    # Verifier → Explainer or HITL
    workflow.add_conditional_edges(
        "verifier",
        should_trigger_hitl_after_verifier,
        {
            "explainer": "explainer",
            "hitl": "hitl"
        }
    )
    
    # Explainer → END (always)
    workflow.add_edge("explainer", END)
    
    # HITL → Resume or Stay
    workflow.add_conditional_edges(
        "hitl",
        should_resume_from_hitl,
        {
            "router": "router",
            "rag": "rag",
            "verifier": "verifier",
            "explainer": "explainer",
            "hitl": "hitl"
        }
    )
    
    # Compile with memory saver for checkpointing
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app

# ============================================================================
# 6. GRAPH INSTANCE - Singleton for easy import
# ============================================================================

math_mentor_graph = build_math_mentor_graph()

# ============================================================================
# 7. HELPER FUNCTIONS FOR API ENDPOINTS
# ============================================================================

async def run_graph_initial(session_id: str, confirmed_text: str, media_type: str = "text", media_url: Optional[str] = None) -> MathMentorState:
    """Run graph from start for new session"""
    initial_state = create_initial_state(session_id, confirmed_text, media_type, media_url)
    
    # Run the graph
    final_state = await math_mentor_graph.ainvoke(initial_state, config={"configurable": {"thread_id": session_id}})
    
    return final_state

async def run_graph_resume(session_id: str, hitl_decision: str, corrected_solution: Optional[str] = None) -> MathMentorState:
    """Resume graph from HITL pause"""
    # Load existing state from Supabase
    state = load_session_from_supabase(session_id)
    if not state:
        raise ValueError(f"Session {session_id} not found")
    
    # Update state based on HITL decision
    state["hitl_status"] = "approved" if hitl_decision == "approve" else "rejected"
    state["hitl_feedback"] = corrected_solution if corrected_solution else hitl_decision
    
    if hitl_decision == "approve" and corrected_solution:
        # User corrected the solution
        if state["solution"]:
            state["solution"]["final_answer"] = corrected_solution
    
    # Resume graph from checkpoint
    final_state = await math_mentor_graph.ainvoke(state, config={"configurable": {"thread_id": session_id}})
    
    return final_state

async def get_session_state(session_id: str) -> Optional[MathMentorState]:
    """Get current session state (for polling)"""
    return load_session_from_supabase(session_id)