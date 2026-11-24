from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.state import ComplianceState
from src.agents.regulatory_agent import regulatory_auditor_node
from src.agents.sanctions_agent import sanctions_screener_node
from src.agents.evaluator import compliance_evaluator_node

def route_after_evaluation(state: ComplianceState):
    """Conditional router: Routes to Human Review if risk score is high, otherwise finishes."""
    if state.get("requires_human_review", False):
        return "human_review"
    return END

def human_review_node(state: ComplianceState) -> dict:
    """Human-in-the-Loop Node placeholder for analyst oversight."""
    print("\n⚠️ [HUMAN-IN-THE-LOOP ALERT]: High risk detected. Case paused for compliance analyst review.")
    return {
        "audit_trail": ["Transaction paused for mandatory Compliance Officer sign-off."]
    }

def create_compliance_graph():
    workflow = StateGraph(ComplianceState)

    # 1. Add all nodes
    workflow.add_node("regulatory_auditor", regulatory_auditor_node)
    workflow.add_node("sanctions_screener", sanctions_screener_node)
    workflow.add_node("compliance_evaluator", compliance_evaluator_node)
    workflow.add_node("human_review", human_review_node)

    # 2. Add edges (Regulatory & Sanctions run in parallel from start)
    workflow.set_entry_point("regulatory_auditor")
    workflow.add_edge("regulatory_auditor", "sanctions_screener")
    workflow.add_edge("sanctions_screener", "compliance_evaluator")

    # 3. Add conditional edge for Human-in-the-Loop
    workflow.add_conditional_edges(
        "compliance_evaluator",
        route_after_evaluation,
        {
            "human_review": "human_review",
            END: END
        }
    )
    workflow.add_edge("human_review", END)

    # Compile with memory checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    return app

compliance_graph = create_compliance_graph()

if __name__ == "__main__":
    import uuid
    from rich import print as rprint

    # Test Case: High-risk scenario (PEP + Large wire + Shell company red flags)
    sample_transaction: ComplianceState = {
        "transaction_id": str(uuid.uuid4()),
        "entity_name": "Al-Bahrani Logistics FZE",
        "country_of_origin": "Iran",
        "transaction_amount_usd": 750000.0,
        "raw_dossier_text": (
            "Managing director is Tariq Al-Bahrani, former Deputy Minister of Transport. "
            "Company holds bearer shares, lacks a physical lease inside the mainland, and is wiring $750,000 "
            "as an advance fee for maritime equipment with no bill of lading attached."
        ),
        "regulatory_findings": [],
        "sanctions_findings": [],
        "risk_score": 0.0,
        "requires_human_review": False,
        "human_analyst_feedback": None,
        "final_report": None,
        "audit_trail": []
    }

    config = {"configurable": {"thread_id": "test-case-001"}}
    print("\n🚀 Starting Amana Multi-Agent Compliance Audit...")
    result = compliance_graph.invoke(sample_transaction, config)

    print("\n================ FINAL COMPLIANCE VERDICT ================")
    rprint(result["final_report"])
    print("\n================ AUDIT TRAIL ================")
    for log in result["audit_trail"]:
        print(f"• {log}")
