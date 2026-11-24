import uuid
import pytest
from src.graph import compliance_graph
from src.state import ComplianceState

def test_high_risk_transaction_flagged():
    """Verify that high-risk entities with PEP/FATF factors are caught and flagged."""
    txn_id = str(uuid.uuid4())
    state: ComplianceState = {
        "transaction_id": txn_id,
        "entity_name": "Test Offshore Maritime Ltd",
        "country_of_origin": "Iran",
        "transaction_amount_usd": 900000.0,
        "raw_dossier_text": "Entity owned by former government minister Tariq Al-Bahrani. Has bearer shares.",
        "regulatory_findings": [],
        "sanctions_findings": [],
        "risk_score": 0.0,
        "requires_human_review": False,
        "human_analyst_feedback": None,
        "final_report": None,
        "audit_trail": []
    }
    
    result = compliance_graph.invoke(state, {"configurable": {"thread_id": txn_id}})
    
    report = result["final_report"]
    assert report is not None
    assert report.risk_score >= 60.0
    assert report.overall_verdict in ["REJECTED", "FLAGGED_FOR_MANUAL_REVIEW"]

def test_clean_low_risk_transaction():
    """Verify that legitimate commercial transactions pass cleanly."""
    txn_id = str(uuid.uuid4())
    state: ComplianceState = {
        "transaction_id": txn_id,
        "entity_name": "Dubai Logistics Solutions LLC",
        "country_of_origin": "United Arab Emirates",
        "transaction_amount_usd": 12000.0,
        "raw_dossier_text": (
            "Standard commercial invoice for warehouse logistics services. "
            "Clean company registry in Dubai Mainland, verified commercial license with full UBO documentation."
        ),
        "regulatory_findings": [],
        "sanctions_findings": [],
        "risk_score": 0.0,
        "requires_human_review": False,
        "human_analyst_feedback": None,
        "final_report": None,
        "audit_trail": []
    }
    
    result = compliance_graph.invoke(state, {"configurable": {"thread_id": txn_id}})
    
    report = result["final_report"]
    assert report is not None
    assert report.risk_score < 50.0
    assert report.overall_verdict == "APPROVED"
