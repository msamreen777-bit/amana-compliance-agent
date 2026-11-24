from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class RiskFactor(BaseModel):
    category: Literal["AML", "Sanctions", "PEP", "Jurisdiction_Risk", "Shell_Company"]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    explanation: str = Field(description="Factual evidence from dossier and regulatory text")
    source_citation: str = Field(description="Exact rule cited, e.g. 'DIFC AML Section 4.2'")

class ComplianceAuditReport(BaseModel):
    entity_name: str
    overall_verdict: Literal["APPROVED", "FLAGGED_FOR_MANUAL_REVIEW", "REJECTED"]
    risk_score: float = Field(ge=0.0, le=100.0, description="0 is clean, 100 is critical risk")
    sanctions_hit: bool = False
    pep_match: bool = False
    identified_risks: List[RiskFactor] = []
    recommended_action: str
    confidence_score: float = Field(ge=0.0, le=1.0)
