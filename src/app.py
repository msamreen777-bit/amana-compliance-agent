import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from src.graph import compliance_graph
from src.state import ComplianceState

app = FastAPI(
    title="Amana — Autonomous Regulatory Compliance & Sanctions Auditor",
    description="Agentic AI platform for automated DIFC, ADGM, and CBUAE compliance auditing.",
    version="1.0.0"
)

class AuditRequest(BaseModel):
    entity_name: str = Field(..., example="Al-Bahrani Logistics FZE")
    country_of_origin: str = Field(..., example="Iran")
    transaction_amount_usd: float = Field(..., example=750000.0)
    raw_dossier_text: str = Field(
        ..., 
        example="Managing director is former Deputy Minister. Company holds bearer shares with no mainland lease."
    )

audit_database: Dict[str, Any] = {}

@app.get("/")
def health_check():
    return {
        "service": "Amana Compliance Agent",
        "status": "operational",
        "jurisdiction_coverage": ["CBUAE", "DIFC", "ADGM"],
        "engine": "LangGraph Stateful Multi-Agent"
    }

@app.post("/api/v1/audit/transaction")
def audit_transaction(request: AuditRequest):
    """Triggers autonomous multi-agent compliance evaluation across DIFC/CBUAE rulebooks."""
    transaction_id = str(uuid.uuid4())
    
    initial_state: ComplianceState = {
        "transaction_id": transaction_id,
        "entity_name": request.entity_name,
        "country_of_origin": request.country_of_origin,
        "transaction_amount_usd": request.transaction_amount_usd,
        "raw_dossier_text": request.raw_dossier_text,
        "regulatory_findings": [],
        "sanctions_findings": [],
        "risk_score": 0.0,
        "requires_human_review": False,
        "human_analyst_feedback": None,
        "final_report": None,
        "audit_trail": []
    }

    config = {"configurable": {"thread_id": transaction_id}}
    result = compliance_graph.invoke(initial_state, config)
    
    audit_database[transaction_id] = result
    report_dict = result["final_report"].model_dump() if result["final_report"] else None
    
    return {
        "transaction_id": transaction_id,
        "requires_human_review": result.get("requires_human_review", False),
        "audit_report": report_dict,
        "audit_trail": result.get("audit_trail", [])
    }

@app.get("/api/v1/audit/{transaction_id}")
def get_audit(transaction_id: str):
    """Retrieves full audit report and decision trail by transaction ID."""
    if transaction_id not in audit_database:
        raise HTTPException(status_code=404, detail="Transaction audit not found")
    record = audit_database[transaction_id]
    return {
        "transaction_id": transaction_id,
        "audit_report": record["final_report"].model_dump() if record["final_report"] else None,
        "audit_trail": record.get("audit_trail", [])
    }
