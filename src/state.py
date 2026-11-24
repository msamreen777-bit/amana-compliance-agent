from typing import TypedDict, Annotated, List, Optional
import operator
from src.schemas import ComplianceAuditReport

class ComplianceState(TypedDict):
    # Initial input data
    transaction_id: str
    entity_name: str
    country_of_origin: str
    transaction_amount_usd: float
    raw_dossier_text: str
    
    # Deliberation findings accumulated by worker agents
    regulatory_findings: Annotated[List[str], operator.add]
    sanctions_findings: Annotated[List[str], operator.add]
    
    # Review gates and scoring
    risk_score: float
    requires_human_review: bool
    human_analyst_feedback: Optional[str]
    
    # Final verified audit report
    final_report: Optional[ComplianceAuditReport]
    audit_trail: Annotated[List[str], operator.add]

